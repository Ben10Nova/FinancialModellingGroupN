"""Strategy logic shared by the Streamlit app. Mirrors vol-control_pair_v1.ipynb line for line;
test_strategy.py checks that the default numbers match the notebook."""
from dataclasses import dataclass
from itertools import groupby
import numpy as np, pandas as pd, statsmodels.api as sm, yfinance as yf

SECTORS = ['XLB', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLU', 'XLV', 'XLY']
ASSETS = ['SPY'] + SECTORS
TICKERS = ASSETS + ['^SP500TR', '^IRX']
DATA_START, DATA_END = '1999-01-01', '2025-12-31'


@dataclass(frozen=True)
class Params:
    start: str = '2006-01-01'
    end: str = '2025-12-31'
    target_vol: float = 0.15
    vol_days: int = 21
    max_lev: float = 2.0
    pair_vol_days: int = 63
    beta_years: int = 1
    z_win: int = 60
    z_in: float = 2.0
    z_out: float = 0.5
    pair_size: float = 1.0
    cost: float = 0.0010
    fin_spread: float = 0.0050
    short_fee: float = 0.0025


def load_prices(start=DATA_START, end=DATA_END):
    raw = yf.download(TICKERS, start=start, end=pd.Timestamp(end) + pd.Timedelta(days=1),
                      auto_adjust=True, progress=False)['Close'][TICKERS]
    if not raw[ASSETS + ['^SP500TR']].notna().all().all():
        raise RuntimeError('Price download incomplete (Yahoo rate limit?). Please reload in a minute.')
    px = raw.copy()
    px['^IRX'] = px['^IRX'].ffill()
    return px.dropna()


def load_live(start='2024-01-01'):
    # prices up to today; dropna also drops today's row if an index has not printed yet
    raw = yf.download(TICKERS, start=start, auto_adjust=True, progress=False)['Close'][TICKERS]
    raw['^IRX'] = raw['^IRX'].ffill()
    return raw.dropna()


def month_end_flag(idx):
    me = ~idx.to_period('M').duplicated(keep='last')            # last trading day of each month
    if len(idx) and idx[-1] != idx[-1] + pd.offsets.BMonthEnd(0):
        me[-1] = False                                          # live data: today is not a month-end just because it is the last row
    return me


def spy_exposure(px, p, pair_ret=None):
    # one risk budget: the spread sleeve's realised vol is taken out first, the equity sleeve gets the rest
    vol = px['SPY'].pct_change().rolling(p.vol_days).std() * np.sqrt(252)
    budget = p.target_vol if pair_ret is None else \
             np.sqrt((p.target_vol ** 2 - (pair_ret.rolling(p.pair_vol_days).std() * np.sqrt(252)) ** 2).clip(lower=0))
    return (budget / vol).clip(upper=p.max_lev)


def pair_returns(px, P):
    return (P.shift(1) * px[SECTORS].pct_change()).sum(axis=1)  # positions set at t-1 earn day t


def sector_betas(px, lo, hi):
    r = px[ASSETS].pct_change().loc[lo:hi]
    return r.cov()['SPY'][SECTORS] / r['SPY'].var()             # beta = cov / var


def lowbeta_pick(px, year, years):
    return tuple(sorted(sector_betas(px, str(year - years), str(year - 1)).nsmallest(2).index))


def zscore(px, a, b, win):
    s = np.log(px[a] / px[b])
    return (s - s.rolling(win).mean()) / s.rolling(win).std()


def positions(z, z_in, z_out):
    pos, p = [], 0
    for zt in z:
        if np.isnan(zt):                 p = 0
        elif p == 0 and zt > z_in:       p = -1
        elif p == 0 and zt < -z_in:      p = +1
        elif p != 0 and abs(zt) < z_out: p = 0
        pos.append(p)
    return np.array(pos, dtype=float)


def pair_targets(px, p):
    hold_year = px.index.year + (month_end_flag(px.index) & (px.index.month == 12))
    tgt = pd.DataFrame(0.0, index=px.index, columns=SECTORS)
    z_active = pd.Series(np.nan, index=px.index)
    chosen = {y: lowbeta_pick(px, y, p.beta_years) for y in range(int(p.start[:4]), hold_year.max() + 1)}
    for (a, b), ys in groupby(chosen, key=chosen.get):         # consecutive years with the same pair = one block
        ys = list(ys)
        m = np.isin(hold_year, ys)
        z = zscore(px, a, b, p.z_win).where(m)                   # nan outside the block, so a new pair starts flat
        pos = positions(z, p.z_in, p.z_out)
        for y in ys:                                             # beta-neutral legs from the prior year's betas
            my = hold_year == y
            be = sector_betas(px, str(y - 1), str(y - 1))
            wa, wb = 2 * be[b] / (be[a] + be[b]), 2 * be[a] / (be[a] + be[b])   # wa*beta_a = wb*beta_b, wa + wb = 2
            tgt.loc[my, a] += pos[my] * wa
            tgt.loc[my, b] -= pos[my] * wb
        z_active[m] = z[m]
    return tgt, chosen, z_active


def backtest(px, p, use_spy=True, pair_size=None):
    P = pair_targets(px, p)[0] * (p.pair_size if pair_size is None else pair_size)
    e = spy_exposure(px, p, pair_returns(px, P)) if use_spy else 0 * px['SPY']
    rf_d = (px['^IRX'] / 100 / 252).shift(1)

    idx = px.loc[:p.end].index[px.index.searchsorted(pd.Timestamp(p.start)) - 1:]   # from the last close before start
    R, rf = px[ASSETS].pct_change().loc[idx].values, rf_d.loc[idx].values
    e, P, me = e.loc[idx].values, P.loc[idx].values, month_end_flag(idx)

    w, rows = np.zeros(len(ASSETS)), []                         # weights: spy + 9 sectors, rest is cash
    for i in range(len(idx)):
        cash = 1 - w.sum()
        gross = w @ R[i] + cash * (rf[i] + (p.fin_spread / 252 if cash < 0 else 0)) \
                - np.abs(np.minimum(w, 0)).sum() * p.short_fee / 252
        drift = w * (1 + R[i]) / (1 + gross)                    # positions drift with prices
        tgt = drift.copy()
        if i == 0 or me[i]: tgt[0] = e[i]                       # spy: reset at month-end
        if i == 0 or (P[i] != P[i - 1]).any(): tgt[1:] = P[i]   # pair: trade only when the target changes
        turn = np.abs(tgt - drift).sum()
        rows.append((gross, gross - turn * p.cost, turn, tgt[0], np.abs(tgt).sum(), *tgt))
        w = tgt
    out = pd.DataFrame(rows, index=idx, columns=['gross', 'net', 'turnover', 'w_spy', 'gross_exposure']
                       + [f'w_{a}' for a in ASSETS])                    # target weights after each close
    return out.iloc[1:]


def monthly(r):
    return (1 + r).resample('ME').prod() - 1


def wealth(r):
    w = (1 + r).cumprod()
    return pd.concat([pd.Series(1.0, index=[w.index[0] - pd.Timedelta(days=1)]), w])


def stats(r_m, rf_m, bench_m):
    rf, b = rf_m.loc[r_m.index], bench_m.loc[r_m.index]
    ex, bex = r_m - rf, b - rf
    ols = sm.OLS(ex, sm.add_constant(bex)).fit()
    a, beta = ols.params.iloc[0], ols.params.iloc[1]
    w = (1 + r_m).cumprod()
    return pd.Series({
        'Ann. avg return': r_m.mean() * 12,
        'Ann. volatility': r_m.std() * np.sqrt(12),
        'Sharpe ratio': ex.mean() / ex.std() * np.sqrt(12),
        'Alpha (ann.)': a * 12,
        'Alpha t-stat': ols.tvalues.iloc[0],
        'Beta': beta,
        'Information ratio': a / ols.resid.std() * np.sqrt(12),
        'Max drawdown (monthly)': (w / w.cummax() - 1).min(),
    })


def var_es(r_m, level):
    """one-month value at risk at any confidence level (historical, normal, cornish-fisher) and historical expected
    shortfall. losses are positive. same formulas as risk_stats, which fixes the level at 95% / 99%"""
    from scipy.stats import norm
    S, K, z = r_m.skew(), r_m.kurt(), norm.ppf(1 - level)
    z_cf = z + (z**2 - 1) * S / 6 + (z**3 - 3 * z) * K / 24 - (2 * z**3 - 5 * z) * S**2 / 36
    q = r_m.quantile(1 - level)
    return pd.Series({'VaR, historical': -q, 'VaR, normal': -(r_m.mean() + z * r_m.std()),
                      'VaR, Cornish-Fisher': -(r_m.mean() + z_cf * r_m.std()),
                      'Expected shortfall': -r_m[r_m <= q].mean()})


def risk_stats(r_m, rf_m, bench_m):
    """tail risk and client-facing ratios, monthly returns. var/cvar are losses (positive = loss) over one month"""
    rf, b = rf_m.loc[r_m.index], bench_m.loc[r_m.index]
    ex, act = r_m - rf, r_m - b
    w = (1 + r_m).cumprod()
    S, K = r_m.skew(), r_m.kurt()                               # sample skew, excess kurtosis
    cf = lambda z: z + (z**2 - 1) * S / 6 + (z**3 - 3 * z) * K / 24 - (2 * z**3 - 5 * z) * S**2 / 36   # cornish-fisher
    var = lambda z: -(r_m.mean() + z * r_m.std())               # z = normal quantile: -1.645 (95%), -2.326 (99%)
    q = r_m.quantile(.05)
    up, dn = b > 0, b < 0
    hac = sm.OLS(ex, sm.add_constant(b - rf)).fit(cov_type='HAC', cov_kwds={'maxlags': 6})
    return pd.Series({
        'Skewness': S,
        'Excess kurtosis': K,
        'VaR 95%, historical': -q,
        'VaR 95%, normal': var(-1.645),
        'VaR 99%, normal': var(-2.326),
        'VaR 99%, Cornish-Fisher': var(cf(-2.326)),
        'CVaR 95% (expected shortfall)': -r_m[r_m <= q].mean(),
        'Worst month': r_m.min(),
        'Positive months': (r_m > 0).mean(),
        'Sortino ratio': ex.mean() / np.sqrt((ex.clip(upper=0) ** 2).mean()) * np.sqrt(12),
        'Calmar ratio': (w.iloc[-1] ** (12 / len(r_m)) - 1) / -(w / w.cummax() - 1).min(),
        'Upside capture': r_m[up].mean() / b[up].mean(),
        'Downside capture': r_m[dn].mean() / b[dn].mean(),
        'Tracking error': act.std() * np.sqrt(12),
        'Active IR (vs S&P 500 TR)': act.mean() / act.std() * np.sqrt(12) if act.std() > 0 else np.nan,
        'Alpha t-stat, Newey-West': hac.tvalues.iloc[0] if act.std() > 0 else np.nan,
    })


def rolling_greeks(r_m, rf_m, bench_m, n=60):
    """60-month rolling alpha (ann.) and beta, as in the lecture's rolling_greeks"""
    rf = rf_m.loc[r_m.index]
    ex, bex = r_m - rf, bench_m.loc[r_m.index] - rf
    beta = ex.rolling(n).cov(bex) / bex.rolling(n).var()
    return pd.DataFrame({'alpha': (ex.rolling(n).mean() - beta * bex.rolling(n).mean()) * 12, 'beta': beta}).dropna()


def monte_carlo(r_m, rf_m, bench_m, months=120, paths=10_000, block=12, seed=42):
    """block bootstrap: draw 12-month blocks of history (strategy, s&p, t-bill from the same months) and chain them"""
    X = np.column_stack([r_m, bench_m.loc[r_m.index], rf_m.loc[r_m.index]])
    starts = np.random.default_rng(seed).integers(0, len(X) - block + 1, size=(paths, months // block))
    sim = X[(starts[..., None] + np.arange(block)).reshape(paths, -1)]          # paths x months x 3
    W = np.cumprod(1 + sim[..., :2], axis=1)
    dd = (W / np.maximum.accumulate(W, axis=1) - 1).min(axis=1)
    ex = sim[..., :2] - sim[..., 2:]
    sharpe = ex.mean(axis=1) / ex.std(axis=1, ddof=1) * np.sqrt(12)
    end = W[:, -1]
    pct = lambda a, k: np.percentile(a, k, axis=0)
    table = pd.DataFrame({
        'Wealth of $1: 5th percentile': pct(end, 5), 'Wealth of $1: median': pct(end, 50),
        'Wealth of $1: mean': end.mean(axis=0), 'Wealth of $1: 95th percentile': pct(end, 95),
        'Probability of a loss': (end < 1).mean(axis=0),
        'Max drawdown: median': pct(dd, 50), 'Max drawdown: 5th percentile (bad case)': pct(dd, 5),
        'Sharpe ratio: 5th percentile': pct(sharpe, 5), 'Sharpe ratio: 95th percentile': pct(sharpe, 95),
    }, index=['Strategy (net)', 'S&P 500 TR']).T
    head = dict(beats_sp=(end[:, 0] > end[:, 1]).mean(), sharpe_above=(sharpe[:, 0] > sharpe[:, 1]).mean())
    return table, head


def run(px, p=Params()):
    bt = backtest(px, p)
    spy_only = backtest(px, p, pair_size=0)
    pair_only = backtest(px, p, use_spy=False, pair_size=1.0)
    bench_d = px['^SP500TR'].pct_change().loc[bt.index]
    rf_m = monthly((px['^IRX'] / 100 / 252).shift(1).loc[bt.index])
    bench_m = monthly(bench_d)
    st = lambda r: stats(monthly(r), rf_m, bench_m)

    table = pd.DataFrame({'Strategy (net)': st(bt.net), 'S&P 500 TR': stats(bench_m, rf_m, bench_m)})
    table.loc[['Alpha t-stat', 'Information ratio'], 'S&P 500 TR'] = np.nan
    sleeves = pd.DataFrame({'Vol-managed SPY only': st(spy_only.net), 'Pair only (+ T-bills)': st(pair_only.net),
                            'Combined strategy': st(bt.net)})
    rt = lambda r: risk_stats(monthly(r), rf_m, bench_m)
    risk = pd.DataFrame({'Strategy (net)': rt(bt.net), 'Equity sleeve': rt(spy_only.net),
                         'Spread sleeve': rt(pair_only.net), 'S&P 500 TR': risk_stats(bench_m, rf_m, bench_m)})
    yearly = pd.DataFrame({'Strategy': (1 + bt.net).groupby(bt.index.year).prod() - 1,
                           'S&P 500 TR': (1 + bench_d).groupby(bench_d.index.year).prod() - 1})
    P, chosen, _ = pair_targets(px, p)
    yearly['Pair held'] = [('/'.join(chosen[y]) if p.pair_size > 0 else '–') for y in yearly.index]
    return dict(bt=bt, spy_only=spy_only, pair_only=pair_only, bench_d=bench_d, table=table, sleeves=sleeves, risk=risk,
                rolling=rolling_greeks(monthly(bt.net), rf_m, bench_m), mc=monte_carlo(monthly(bt.net), rf_m, bench_m),
                yearly=yearly, exposure_now=float(spy_exposure(px, p, pair_returns(px, P * p.pair_size)).loc[:p.end].iloc[-1]),
                pair_now=chosen[max(chosen)])

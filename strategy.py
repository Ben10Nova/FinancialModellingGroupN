"""Strategy logic shared by the Streamlit app. Mirrors vol-control_pair_v1.ipynb line for line;
test_strategy.py checks that the default numbers match the notebook."""
from dataclasses import dataclass
from itertools import groupby
import time
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


_cooldown = {'until': 0.0}


def _download(ok, **kw):
    """yahoo with two retries. after a failed attempt, no new request for 60s: hammering a rate limit keeps it alive"""
    msg = 'Yahoo Finance is rate-limiting downloads right now. Please reload in a minute.'
    if time.time() < _cooldown['until']:
        raise RuntimeError(msg)
    for wait in (0, 3, 10):
        time.sleep(wait)
        try:
            raw = yf.download(TICKERS, auto_adjust=True, progress=False, **kw)['Close'][TICKERS]
            if ok(raw[ASSETS + ['^SP500TR']]):
                return raw
        except Exception:
            pass
    _cooldown['until'] = time.time() + 60
    raise RuntimeError(msg)


def load_prices(start=DATA_START, end=DATA_END):
    raw = _download(lambda r: r.notna().all().all(), start=start, end=pd.Timestamp(end) + pd.Timedelta(days=1))
    px = raw.copy()
    px['^IRX'] = px['^IRX'].ffill()
    return px.dropna()


def load_live(start='2024-01-01'):
    # prices up to today; dropna also drops today's row if an index has not printed yet
    raw = _download(lambda r: len(r.dropna()) > 250, start=start)
    raw['^IRX'] = raw['^IRX'].ffill()
    return raw.dropna()


def load_intraday():
    """5-minute prices of the last five sessions, New York time without the zone"""
    msg = 'Yahoo Finance is rate-limiting downloads right now. Live prices return in a minute.'
    if time.time() < _cooldown['until']:
        raise RuntimeError(msg)
    try:
        raw = yf.download(ASSETS, period='5d', interval='5m', auto_adjust=True, progress=False)['Close'][ASSETS]
        raw = raw.ffill().dropna()
    except Exception:
        raw = None
    if raw is None or raw.empty:
        _cooldown['until'] = time.time() + 60
        raise RuntimeError(msg)
    raw.index = raw.index.tz_convert('America/New_York').tz_localize(None)
    return raw


def intraday_value(bt, px, bench, bars):
    """portfolio and S&P 500 value through each session in bars, as growth of $1 since inception. each session starts
    from the previous close and holds the weights set at that close; SPY stands in for the S&P 500 during the day.
    ignores the day's financing and borrow accrual (a few basis points a year, booked at the close)."""
    W, B = (1 + bt.net).cumprod(), (1 + bench).cumprod()
    cols = [f'w_{a}' for a in ASSETS]
    out = []
    for day, b in bars.groupby(bars.index.normalize()):
        prev = px.index[px.index < day]
        if not len(prev) or prev[-1] not in W.index:
            continue
        prev = prev[-1]
        r = b / px.loc[prev, ASSETS] - 1
        session = pd.DataFrame({'pf': W[prev] * (1 + r.to_numpy() @ bt.loc[prev, cols].to_numpy()),
                                'sp': B[prev] * (1 + r['SPY'].to_numpy())}, index=b.index)
        session = pd.concat([pd.DataFrame({'pf': W[prev], 'sp': B[prev]}, index=[prev]), session])
        session.attrs['prev'] = prev
        out.append(session)
    return out                                                     # one frame per session, each led by its previous close


def month_end_flag(idx):
    me = ~idx.to_period('M').duplicated(keep='last')            # last trading day of each month
    if len(idx) and idx[-1] != idx[-1] + pd.offsets.BMonthEnd(0):
        me[-1] = False                                          # live data: today is not a month-end just because it is the last row
    return me


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
    targets = pair_targets(px, p)[0] * (p.pair_size if pair_size is None else pair_size)
    return simulate(px, p, targets, use_spy)


def simulate(px, p, targets, use_spy=True, lag=1, vol_budget=True):
    delay = lag - 1
    start = px.index.searchsorted(pd.Timestamp(p.start))
    if start < 2:
        raise ValueError('Backtest requires prices before the opening trade.')
    idx = px.index[start - 1:px.index.searchsorted(pd.Timestamp(p.end), side='right')]
    if len(idx) < 2:
        raise ValueError('Backtest requires at least one trading day in the evaluation window.')

    returns = px[ASSETS].pct_change()
    spy_vol = (returns['SPY'].rolling(p.vol_days).std() * np.sqrt(252)).shift(delay).loc[idx].to_numpy()
    month_ends = pd.Series(month_end_flag(px.index), index=px.index)
    rebalance = month_ends.shift(delay, fill_value=False).loc[idx].to_numpy()
    targets = targets.shift(delay, fill_value=0).loc[idx].to_numpy()
    r = returns.loc[idx].to_numpy()
    rf = (px['^IRX'] / 100 / 252).shift(1).loc[idx].to_numpy()

    weights = np.zeros(len(ASSETS))
    rows = []
    # The portfolio is flat before inception. Each new observation uses the weights held overnight.
    spread_returns = np.zeros(p.pair_vol_days + delay - 1 + len(idx))
    for i, day_returns in enumerate(r):
        spread_returns[i + p.pair_vol_days + delay - 1] = weights[1:] @ day_returns[1:]
        cash = 1 - weights.sum()
        cash_rate = rf[i] + (p.fin_spread / 252 if cash < 0 else 0)
        gross = weights @ day_returns + cash * cash_rate        # weights set at close t-1 earn day t: lecture 4's position.shift(1)
        gross -= np.abs(np.minimum(weights, 0)).sum() * p.short_fee / 252
        drift = weights * (1 + day_returns) / (1 + gross)
        target = drift.copy()
        if use_spy and (i == 0 or rebalance[i]):
            spread_vol = 0.0
            if vol_budget:
                window = spread_returns[i:i + p.pair_vol_days]
                spread_vol = window.std(ddof=1) * np.sqrt(252)
            budget = np.sqrt(max(p.target_vol ** 2 - spread_vol ** 2, 0))
            target[0] = min(budget / spy_vol[i], p.max_lev)
        if i == 0 or (targets[i] != targets[i - 1]).any():
            target[1:] = targets[i]
        turnover = np.abs(target - drift).sum()                 # |change in position| x cost, as in lecture 4
        rows.append((gross, gross - turnover * p.cost, turnover, target[0], np.abs(target).sum(), *target))
        weights = target

    columns = ['gross', 'net', 'turnover', 'w_spy', 'gross_exposure'] + [f'w_{a}' for a in ASSETS]
    out = pd.DataFrame(rows[1:], index=idx[1:], columns=columns)
    opening_turnover = rows[0][2]
    opening_cost = opening_turnover * p.cost
    # Compound the formation-close fee with the first trading day's return.
    out.loc[idx[1], 'net'] = (1 - opening_cost) * (1 + out.loc[idx[1], 'net']) - 1
    out.loc[idx[1], 'turnover'] += opening_turnover
    out.attrs['opening_weights'] = tuple(rows[0][5:])
    out.attrs['opening_cost'] = opening_cost
    return out


def monthly(r):
    return (1 + r).resample('ME').prod() - 1


def wealth(r):
    w = (1 + r).cumprod()
    return pd.concat([pd.Series(1.0, index=[w.index[0] - pd.Timedelta(days=1)]), w])


def drawdown(w):
    """DD_t = (HWM_t - P_t) / HWM_t with HWM_t = max_{s<=t} P_s (formula sheet). the initial $1 counts as the first peak"""
    hwm = w.cummax().clip(lower=1)
    return (hwm - w) / hwm


def stats(r_m, rf_m, bench_m):
    """monthly returns. means x12, volatilities x sqrt(12), beta not annualised (lecture 3)"""
    rf, b = rf_m.loc[r_m.index], bench_m.loc[r_m.index]
    ex, bex = r_m - rf, b - rf
    beta = ex.cov(bex) / bex.var()                              # beta = cov(R_ex, R_M,ex) / var(R_M,ex)
    a = ex.mean() - beta * bex.mean()                           # alpha = E[R_ex] - beta E[R_M,ex]
    eps = ex - a - beta * bex                                   # idiosyncratic part of R_ex = alpha + beta R_M,ex + eps
    t_alpha = sm.OLS(ex, sm.add_constant(bex)).fit().tvalues.iloc[0]   # same regression, only for alpha's t-stat
    return pd.Series({
        'Ann. avg return': r_m.mean() * 12,
        'Ann. volatility': r_m.std() * np.sqrt(12),
        'Sharpe ratio': ex.mean() / ex.std() * np.sqrt(12),     # E(R - Rf) / sigma(R - Rf), monthly x sqrt(12)
        'Alpha (ann.)': a * 12,
        'Alpha t-stat': t_alpha,
        'Beta': beta,
        'Information ratio': a / eps.std() * np.sqrt(12) if eps.std() > 0 else np.nan,   # IR = alpha / sigma(eps)
        'Max drawdown (monthly)': -drawdown((1 + r_m).cumprod()).max(),
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
    ex, act = r_m - rf, r_m - b                                 # act = R - R_b, the tracking difference
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
        'Calmar ratio': (w.iloc[-1] ** (12 / len(r_m)) - 1) / drawdown(w).max(),
        'Upside capture': r_m[up].mean() / b[up].mean(),
        'Downside capture': r_m[dn].mean() / b[dn].mean(),
        'Tracking error': act.std() * np.sqrt(12),
        'Active IR (vs S&P 500 TR)': act.mean() / act.std() * np.sqrt(12) if act.std() > 0 else np.nan,   # E(R - Rb) / sigma(R - Rb)
        'Alpha t-stat, Newey-West': hac.tvalues.iloc[0] if act.std() > 0 else np.nan,
    })


def pension_mix(r_m, rf_m, bench_m, share=0.20, fee=0.005, size=100e6):
    """a pension scheme's us equity sleeve of `size` dollars: `share` of it replaced by the strategy (net of an annual
    management fee, charged monthly), the rest left in the s&p 500 tr, back to the target split at each month-end.
    returns the mixed monthly returns and a table against keeping the whole sleeve in the s&p 500 tr"""
    b = bench_m.loc[r_m.index]
    mix = share * (r_m - fee / 12) + (1 - share) * b

    def col(m):
        w = (1 + m).cumprod()
        s, r = stats(m, rf_m, bench_m), risk_stats(m, rf_m, bench_m)
        y08 = m.loc['2008'] if (m.index.year == 2008).any() else None
        before08 = w.loc[:'2007'].iloc[-1] if (m.index.year < 2008).any() else 1.0
        return pd.Series({
            'Ann. avg return': s['Ann. avg return'], 'Ann. volatility': s['Ann. volatility'],
            'Sharpe ratio': s['Sharpe ratio'], 'Beta': s['Beta'], 'Max drawdown (monthly)': s['Max drawdown (monthly)'],
            'Upside capture': r['Upside capture'], 'Downside capture': r['Downside capture'],
            'Tracking error': r['Tracking error'],
            'Return in 2008': (1 + y08).prod() - 1 if y08 is not None else np.nan,
            'Value at the end ($)': size * w.iloc[-1],
            'Change in 2008 ($)': size * before08 * ((1 + y08).prod() - 1) if y08 is not None else np.nan,
            'Largest fall from a peak ($)': -size * (w.cummax().clip(lower=1) - w).max(),     # (HWM - P) in dollars
        })
    return mix, pd.DataFrame({'With the strategy': col(mix), 'All in the S&P 500 TR': col(b)})


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
    hwm = np.maximum(np.maximum.accumulate(W, axis=1), 1)                         # high water mark, $1 start included
    dd = -((hwm - W) / hwm).max(axis=1)                                           # max drawdown per path (negative)
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
    fan = dict(q=np.percentile(W, [5, 25, 50, 75, 95], axis=0), paths=W[:40, :, 0])   # for the fan chart
    return table, head, fan


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
    _, chosen, _ = pair_targets(px, p)
    close = bt.index[-1]
    pair_year = close.year + int(close.month == 12 and month_end_flag(px.index)[px.index.get_loc(close)])
    yearly['Pair held'] = [('/'.join(chosen[y]) if p.pair_size > 0 else '–') for y in yearly.index]
    return dict(bt=bt, spy_only=spy_only, pair_only=pair_only, bench_d=bench_d, table=table, sleeves=sleeves, risk=risk,
                rolling=rolling_greeks(monthly(bt.net), rf_m, bench_m),
                mc=monte_carlo(monthly(bt.net), rf_m, bench_m) if len(bench_m) >= 24 else None,   # live 2026: too short
                yearly=yearly, rf_m=rf_m, exposure_now=float(bt.w_spy.iloc[-1]),
                pair_year=pair_year, pair_now=chosen[pair_year] if p.pair_size > 0 else None)

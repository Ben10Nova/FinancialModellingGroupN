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


def month_end_flag(idx):
    return pd.Series(idx, index=idx).groupby(idx.to_period('M')).transform('max').values == idx.values


def spy_exposure(px, p):
    vol = px['SPY'].pct_change().rolling(p.vol_days).std() * np.sqrt(252)
    return (p.target_vol / vol).clip(upper=p.max_lev)


def sector_betas(px, lo, hi):
    r = px[ASSETS].pct_change().loc[lo:hi]
    return r[SECTORS].apply(lambda s: s.cov(r['SPY'])) / r['SPY'].var()


def lowbeta_pick(px, year, years):
    return tuple(sorted(sector_betas(px, str(year - years), str(year - 1)).nsmallest(2).index))


def zscore_position(px, a, b, win, z_in, z_out, mask=None):
    s = np.log(px[a] / px[b])
    z = (s - s.rolling(win).mean()) / s.rolling(win).std()
    if mask is not None:
        z = z.where(mask)
    pos, p = [], 0
    for zt in z:
        if np.isnan(zt):                 p = 0
        elif p == 0 and zt > z_in:       p = -1
        elif p == 0 and zt < -z_in:      p = +1
        elif p != 0 and abs(zt) < z_out: p = 0
        pos.append(p)
    return pd.Series(pos, index=z.index, dtype=float), z


def pair_targets(px, p):
    hold_year = px.index.year + (month_end_flag(px.index) & (px.index.month == 12))
    tgt = pd.DataFrame(0.0, index=px.index, columns=SECTORS)
    z_active = pd.Series(np.nan, index=px.index)
    chosen = {y: lowbeta_pick(px, y, p.beta_years) for y in range(int(p.start[:4]), hold_year.max() + 1)}
    for (a, b), ys in groupby(chosen, key=chosen.get):         # consecutive years with the same pair
        m = np.isin(hold_year, list(ys))
        pos, z = zscore_position(px, a, b, p.z_win, p.z_in, p.z_out, mask=m)   # a new pair starts flat
        tgt.loc[m, a] += pos.values[m]
        tgt.loc[m, b] -= pos.values[m]
        z_active[m] = z.values[m]
    return tgt, chosen, z_active


def backtest(px, p, use_spy=True, pair_size=None):
    pair_size = p.pair_size if pair_size is None else pair_size
    e = spy_exposure(px, p) if use_spy else pd.Series(0.0, index=px.index)
    tp = pair_targets(px, p)[0]
    me = month_end_flag(px.index)
    rf_d = (px['^IRX'] / 100 / 252).shift(1)

    i0 = px.index.searchsorted(pd.Timestamp(p.start)) - 1
    keep = (np.arange(len(px)) >= i0) & (px.index <= pd.Timestamp(p.end))
    idx = px.index[keep]
    R = px[ASSETS].pct_change().loc[idx].values
    rf, e, P, me = rf_d.loc[idx].values, e.loc[idx].values, tp.loc[idx].values * pair_size, me[keep]

    w, prev, rows = np.zeros(len(ASSETS)), np.zeros(len(SECTORS)), []
    for i in range(len(idx)):
        if i == 0:
            gross, w_drift = 0.0, w.copy()
        else:
            cash = 1 - w.sum()
            gross = w @ R[i] + cash * (rf[i] + (p.fin_spread / 252 if cash < 0 else 0)) \
                    - np.abs(np.minimum(w, 0)).sum() * p.short_fee / 252
            w_drift = w * (1 + R[i]) / (1 + gross)
        tgt = w_drift.copy()
        if i == 0 or me[i]:
            tgt[0] = e[i]
        if not np.array_equal(P[i], prev):
            tgt[1:] = P[i]
            prev = P[i]
        turn = np.abs(tgt - w_drift).sum()
        rows.append((gross, gross - turn * p.cost, turn, tgt[0], np.abs(tgt).sum()))
        w = tgt
    out = pd.DataFrame(rows, index=idx, columns=['gross', 'net', 'turnover', 'w_spy', 'gross_exposure'])
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
    yearly = pd.DataFrame({'Strategy': (1 + bt.net).groupby(bt.index.year).prod() - 1,
                           'S&P 500 TR': (1 + bench_d).groupby(bench_d.index.year).prod() - 1})
    chosen = pair_targets(px, p)[1]
    yearly['Pair held'] = [('/'.join(chosen[y]) if p.pair_size > 0 else '–') for y in yearly.index]
    return dict(bt=bt, spy_only=spy_only, pair_only=pair_only, bench_d=bench_d, table=table, sleeves=sleeves,
                yearly=yearly, exposure_now=float(spy_exposure(px, p).loc[:p.end].iloc[-1]),
                pair_now=chosen[max(chosen)])

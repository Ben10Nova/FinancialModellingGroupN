import numpy as np, pandas as pd, statsmodels.api as sm
from scipy.optimize import minimize

PX = pd.read_pickle(__file__.replace('engine.py', 'px.pkl'))
START, END = '2006-01-01', '2025-12-31'
IS_END = '2015-12-31'
COST = 0.0010          # 10 bp per unit of notional traded
FIN_SPREAD = 0.005     # borrow at rf + 50 bp p.a.
SHORT_FEE = 0.0025     # 25 bp p.a. on short notional

RD = PX.pct_change(fill_method=None)                       # daily simple returns
PM = PX.resample('ME').last()
RM = PM.pct_change(fill_method=None)                       # monthly simple returns
RF = (PX['^IRX'].resample('ME').last() / 100 / 12).shift(1)  # T-bill yield at t-1 earned over t
BM = RM['^SP500TR']
MONTH_ENDS = RM.loc['2005-01-01':END].index


def run(weight_fn, assets, cost=COST):
    """weight_fn(t) -> pd.Series of weights decided at month-end t, held over month t+1."""
    W = pd.DataFrame({t: weight_fn(t) for t in MONTH_ENDS[:-1]}).T.reindex(columns=assets).fillna(0)
    W.index = MONTH_ENDS[1:]                               # shift: decided at t, earns t+1
    R = RM[assets].loc[W.index].fillna(0)
    rf = RF.loc[W.index]
    cash = 1 - W.sum(axis=1)
    cash_rate = np.where(cash < 0, rf + FIN_SPREAD / 12, rf)
    gross = (W * R).sum(axis=1) + cash * cash_rate - W.clip(upper=0).abs().sum(axis=1) * SHORT_FEE / 12
    drift = W * (1 + R)
    drift = drift.div((1 + gross), axis=0)
    turnover = (W - drift.shift(1).fillna(0)).abs().sum(axis=1)
    net = gross - turnover * cost
    return pd.DataFrame({'gross': gross, 'net': net, 'turnover': turnover})


def stats(r, bm=BM):
    r = r.dropna()
    rf, b = RF.loc[r.index], bm.loc[r.index]
    ex, bex = r - rf, b - rf
    ols = sm.OLS(ex, sm.add_constant(bex)).fit()
    alpha, beta = ols.params.iloc[0], ols.params.iloc[1]
    wealth = (1 + r).cumprod()
    return pd.Series({
        'ret': r.mean() * 12, 'vol': r.std() * np.sqrt(12),
        'sharpe': ex.mean() / ex.std() * np.sqrt(12),
        'alpha': alpha * 12, 'beta': beta,
        'IR': alpha / ols.resid.std() * np.sqrt(12),
        'maxDD': (wealth / wealth.cummax() - 1).min(),
        't_alpha': ols.tvalues.iloc[0],
    })


# ---------- weight helpers (all use data up to and including t) ----------
def vol(assets, t, days=63):
    return RD[assets].loc[:t].tail(days).std() * np.sqrt(252)


def cov(assets, t, days=252):
    return RD[assets].loc[:t].tail(days).cov() * 252


def inv_vol(assets, t, days=63):
    iv = 1 / vol(assets, t, days)
    return iv / iv.sum()


def erc(assets, t, days=252):
    # equal risk contribution: argmin 0.5 w'Sw - mean(log w), then normalise (Spinu 2013)
    S = cov(assets, t, days).values
    n = len(assets)
    res = minimize(lambda w: 0.5 * w @ S @ w - np.log(w).mean(), np.ones(n) / n,
                   jac=lambda w: S @ w - 1 / (n * w), bounds=[(1e-6, None)] * n)
    return pd.Series(res.x / res.x.sum(), index=assets)


def min_var(assets, t, days=252):
    S = cov(assets, t, days).values
    n = len(assets)
    res = minimize(lambda w: w @ S @ w, np.ones(n) / n, bounds=[(0, 1)] * n,
                   constraints={'type': 'eq', 'fun': lambda w: w.sum() - 1})
    return pd.Series(res.x, index=assets)


def target_vol(w, t, target, cap=3.0, days=63):
    a = list(w.index)
    S = RD[a].loc[:t].tail(days).cov() * 252
    pv = np.sqrt(w @ S @ w)
    return w * min(target / pv, cap)


def beta_to_spy(assets, t, days=252):
    d = RD[assets + ['SPY']].loc[:t].tail(days)
    return d.cov()['SPY'][assets] / d['SPY'].var()

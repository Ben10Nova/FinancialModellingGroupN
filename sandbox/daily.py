from engine import *

RFD = (PX['^IRX'] / 100 / 252).shift(1)


def run_daily(P, cost=COST):
    """P: DataFrame of weights decided at close t. Earns return t+1."""
    P = P.loc['2005-01-01':END]
    W = P.shift(1).fillna(0)
    R = RD[P.columns].loc[W.index].fillna(0)
    rf = RFD.loc[W.index]
    cash = 1 - W.sum(axis=1)
    gross = (W * R).sum(axis=1) + cash * np.where(cash < 0, rf + FIN_SPREAD / 252, rf) \
        - W.clip(upper=0).abs().sum(axis=1) * SHORT_FEE / 252
    turn = W.diff().abs().sum(axis=1)
    net = gross - turn * cost
    m = lambda x: (1 + x).resample('ME').prod() - 1
    return pd.DataFrame({'gross': m(gross), 'net': m(net), 'turnover': turn.resample('ME').sum()}).loc[START:END]


def pair(a, b, win=60, z_in=2.0, z_out=0.5):
    s = np.log(PX[a] / PX[b])
    z = (s - s.rolling(win).mean()) / s.rolling(win).std()
    pos, p = [], 0
    for zt in z.values:
        if np.isnan(zt): p = 0
        elif p == 0 and zt > z_in: p = -1
        elif p == 0 and zt < -z_in: p = 1
        elif p != 0 and abs(zt) < z_out: p = 0
        pos.append(p)
    pos = pd.Series(pos, index=z.index)
    return pd.DataFrame({a: pos, b: -pos})


def turn_of_month(asset='SPY', alt=None, n_first=3):
    idx = RD.index
    ym = idx.to_period('M')
    rank = pd.Series(1, index=idx).groupby(ym).cumsum()
    last = pd.Series(idx, index=idx).groupby(ym).transform('max') == idx
    in_window = (rank <= n_first) | last                 # return days to be invested
    hold = pd.Series(in_window.values, index=idx).shift(-1).fillna(False).astype(float)  # decided day before
    P = pd.DataFrame({asset: hold})
    if alt: P[alt] = 1 - hold
    return P


if __name__ == '__main__':
    tests = {
        'Pair KO/PEP': pair('KO', 'PEP'), 'Pair XOM/CVX': pair('XOM', 'CVX'),
        'Pair HD/LOW': pair('HD', 'LOW'), 'Pair EWA/EWC': pair('EWA', 'EWC'),
        'Pair XLU/XLP': pair('XLU', 'XLP'), 'Pair XLK/XLY': pair('XLK', 'XLY'),
        'TOM SPY else cash': turn_of_month(), 'TOM SPY else IEF': turn_of_month(alt='IEF'),
    }
    rows = {}
    for k, P in tests.items():
        res = run_daily(P)
        rows[k] = pd.concat([stats(res.net)[['ret', 'vol', 'sharpe', 'alpha', 'beta', 'IR', 'maxDD']],
                             pd.Series({'SR_gross': stats(res.gross).sharpe, 'turn/yr': res.turnover.mean() * 12,
                                        'SR_IS': stats(res.net.loc[:IS_END]).sharpe,
                                        'SR_OOS': stats(res.net.loc[IS_END:]).sharpe})])
    pd.set_option('display.width', 250)
    print(pd.DataFrame(rows).T.round(3).to_string())

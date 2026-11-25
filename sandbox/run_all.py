import sys, pandas as pd, numpy as np
from engine import *

MA = ['SPY', 'EFA', 'EEM', 'IWM', 'TLT', 'IEF', 'LQD', 'TIP', 'GLD', 'VNQ']   # multi-asset
RP4 = ['SPY', 'EFA', 'IEF', 'GLD']                                            # stocks/intl/bonds/gold
SEC = ['XLB', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLU', 'XLV', 'XLY']
fix = lambda d: (lambda t: pd.Series(d))


def low_vol_sectors(t, k=3):
    v = vol(SEC, t, 252)
    return pd.Series(1 / k, index=v.nsmallest(k).index)


def bab_sectors(t, k=3):
    b = beta_to_spy(SEC, t)
    lo, hi = b.nsmallest(k), b.nlargest(k)
    w = pd.Series(0.0, index=SEC)
    w[lo.index] = (1 / lo.mean()) / k           # long low-beta, levered to beta 1
    w[hi.index] = -(1 / hi.mean()) / k          # short high-beta, scaled to beta 1
    return w


def halloween(t, risk_on='SPY', risk_off='IEF'):
    # decided at end of month t for month t+1: hold equities Nov-Apr
    nxt = (t + pd.offsets.MonthEnd(1)).month
    return pd.Series({risk_on: 1.0}) if nxt in (11, 12, 1, 2, 3, 4) else pd.Series({risk_off: 1.0})


def vol_managed_spy(t, target=0.15, cap=2.0):
    v = RD['SPY'].loc[:t].tail(21).std() * np.sqrt(252)
    return pd.Series({'SPY': min(target / v, cap)})


S = {
    'SPY buy&hold':           (fix({'SPY': 1}), ['SPY']),
    '60/40 SPY/IEF':          (fix({'SPY': .6, 'IEF': .4}), ['SPY', 'IEF']),
    'Permanent 25x4':         (fix({'SPY': .25, 'TLT': .25, 'GLD': .25, 'SHY': .25}), ['SPY', 'TLT', 'GLD', 'SHY']),
    '1/N multi-asset':        (fix({a: 1 / len(MA) for a in MA}), MA),
    '1/N sectors':            (fix({a: 1 / len(SEC) for a in SEC}), SEC),
    'InvVol multi-asset':     (lambda t: inv_vol(MA, t), MA),
    'ERC multi-asset':        (lambda t: erc(MA, t), MA),
    'MinVar multi-asset':     (lambda t: min_var(MA, t), MA),
    'InvVol SPY/TLT':         (lambda t: inv_vol(['SPY', 'TLT'], t), ['SPY', 'TLT']),
    'InvVol SPY/EFA/IEF/GLD': (lambda t: inv_vol(RP4, t), RP4),
    'ERC SPY/EFA/IEF/GLD':    (lambda t: erc(RP4, t), RP4),
    'LevRP MA tv10':          (lambda t: target_vol(erc(MA, t), t, .10), MA),
    'LevRP MA tv15':          (lambda t: target_vol(erc(MA, t), t, .15), MA),
    'LevRP 4 tv10':           (lambda t: target_vol(erc(RP4, t), t, .10), RP4),
    'LevRP 4 tv15':           (lambda t: target_vol(erc(RP4, t), t, .15), RP4),
    'InvVol sectors':         (lambda t: inv_vol(SEC, t), SEC),
    'LowVol 3 sectors':       (low_vol_sectors, SEC),
    'BAB sectors L/S':        (bab_sectors, SEC),
    'VolManaged SPY tv15':    (vol_managed_spy, ['SPY']),
    'Halloween SPY/IEF':      (halloween, ['SPY', 'IEF']),
    'MinVar sectors':         (lambda t: min_var(SEC, t), SEC),
}

if __name__ == '__main__':
    rows = {}
    for name, (fn, a) in S.items():
        res = run(fn, a).loc[START:END]
        full, ins, oos = stats(res.net), stats(res.net.loc[:IS_END]), stats(res.net.loc[IS_END:])
        rows[name] = pd.concat([full[['ret', 'vol', 'sharpe', 'alpha', 'beta', 'IR', 'maxDD']],
                                pd.Series({'SR_gross': stats(res.gross).sharpe, 'turn/yr': res.turnover.mean() * 12,
                                           'SR_IS': ins.sharpe, 'SR_OOS': oos.sharpe})])
    rows['^SP500TR (bench)'] = stats(BM.loc[START:END])[['ret', 'vol', 'sharpe', 'alpha', 'beta', 'IR', 'maxDD']]
    out = pd.DataFrame(rows).T.sort_values('SR_IS', ascending=False)
    pd.set_option('display.width', 250)
    print(out.round(3).to_string())

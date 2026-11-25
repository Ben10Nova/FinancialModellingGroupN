from run_all import *
from daily import run_daily, pair

cores = {k: run(*S[k]).loc[START:END] for k in
         ['Permanent 25x4', 'InvVol SPY/EFA/IEF/GLD', 'ERC SPY/EFA/IEF/GLD', 'LevRP 4 tv10', 'LevRP 4 tv15',
          'LowVol 3 sectors', 'VolManaged SPY tv15', '60/40 SPY/IEF']}
pr = run_daily(pair('XLU', 'XLP'))
rf = RF.loc[pr.index]
print('corr of net streams:\n', pd.DataFrame({**{k: v.net for k, v in cores.items()}, 'XLU/XLP': pr.net}).corr().round(2).iloc[:, -1])

rows = {}
for name, c in cores.items():
    for k in [0, 0.5, 1.0]:
        r = c.net + k * (pr.net - rf)                     # self-financing overlay
        f, i, o = stats(r), stats(r.loc[:IS_END]), stats(r.loc[IS_END:])
        rows[f'{name} + {k}x pair'] = pd.concat([f[['ret', 'vol', 'sharpe', 'alpha', 'beta', 'IR', 'maxDD']],
                                                pd.Series({'SR_IS': i.sharpe, 'SR_OOS': o.sharpe})])
pd.set_option('display.width', 250)
print(pd.DataFrame(rows).T.sort_values('SR_IS', ascending=False).round(3).to_string())

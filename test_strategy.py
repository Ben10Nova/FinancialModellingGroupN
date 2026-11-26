"""Run: python test_strategy.py  (needs internet). Fails if the app logic drifts from the notebook."""
import numpy as np
from strategy import Params, load_prices, run, backtest, pair_targets

px = load_prices()
res = run(px)
t = res['table']['Strategy (net)']
notebook = {'Ann. avg return': 0.1736, 'Ann. volatility': 0.1434, 'Sharpe ratio': 1.0973,
            'Alpha (ann.)': 0.0966, 'Beta': 0.6074, 'Information ratio': 0.8757, 'Max drawdown (monthly)': -0.1476}
for k, v in notebook.items():
    assert abs(t[k] - v) < 1e-3, f'{k}: app {t[k]:.4f} vs notebook {v:.4f}'

risk = {'Excess kurtosis': 2.3559, 'VaR 95%, historical': 0.0568, 'VaR 99%, Cornish-Fisher': 0.1049,      # notebook: risk profile
        'CVaR 95% (expected shortfall)': 0.0799, 'Sortino ratio': 1.9366, 'Calmar ratio': 1.1940,
        'Downside capture': 0.6113, 'Alpha t-stat, Newey-West': 3.0953}
for k, v in risk.items():
    assert abs(res['risk'].loc[k, 'Strategy (net)'] - v) < 1e-3, f'{k}: app {res["risk"].loc[k, "Strategy (net)"]:.4f} vs notebook {v:.4f}'
mc, head = res['mc']                                                                              # notebook: monte carlo
assert abs(mc.loc['Wealth of $1: median', 'Strategy (net)'] - 5.1298) < 1e-3 and abs(head['beats_sp'] - 0.9316) < 1e-3

for cut in ['2010-06-30', '2015-12-31', '2020-03-31']:     # no look-ahead: deleting the future changes nothing
    assert np.allclose(backtest(px, Params()).loc[:cut].values, backtest(px.loc[:cut], Params()).values), cut

tgt, _, z = pair_targets(px, Params())                    # every new pair position needs |z| > z_in that day
nz = tgt.ne(0)                                            # new set of open legs = an entry (hedge-ratio resets are not)
opened = nz.ne(nz.shift(fill_value=False)).any(axis=1) & nz.any(axis=1) & z.notna()
assert opened.sum() > 50 and (z[opened].abs() > Params().z_in).all(), z[opened][z[opened].abs() <= Params().z_in]
print(f'ok: app matches notebook (performance, risk profile, monte carlo), no look-ahead, all {opened.sum()} pair entries at |z| > {Params().z_in}')

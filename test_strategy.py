"""Run: python test_strategy.py  (needs internet). Fails if the app logic drifts from the notebook."""
import numpy as np
from strategy import Params, load_prices, run, backtest

px = load_prices()
t = run(px)['table']['Strategy (net)']
notebook = {'Ann. avg return': 0.1747, 'Ann. volatility': 0.1566, 'Sharpe ratio': 1.0121,
            'Alpha (ann.)': 0.0741, 'Beta': 0.8434, 'Information ratio': 0.8124, 'Max drawdown (monthly)': -0.2678}
for k, v in notebook.items():
    assert abs(t[k] - v) < 2e-3, f'{k}: app {t[k]:.4f} vs notebook {v:.4f}'

for cut in ['2010-06-30', '2015-12-31', '2020-03-31']:     # no look-ahead: deleting the future changes nothing
    assert np.allclose(backtest(px, Params()).loc[:cut].values, backtest(px.loc[:cut], Params()).values), cut
print('ok: app matches notebook, no look-ahead')

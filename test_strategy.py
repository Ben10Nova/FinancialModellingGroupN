"""Run: python test_strategy.py  (needs internet). Fails if the app logic drifts from the notebook."""
import numpy as np
from strategy import Params, load_prices, run, backtest, pair_targets

px = load_prices()
t = run(px)['table']['Strategy (net)']
notebook = {'Ann. avg return': 0.1746, 'Ann. volatility': 0.1566, 'Sharpe ratio': 1.0115,
            'Alpha (ann.)': 0.0739, 'Beta': 0.8435, 'Information ratio': 0.8115, 'Max drawdown (monthly)': -0.2678}
for k, v in notebook.items():
    assert abs(t[k] - v) < 2e-3, f'{k}: app {t[k]:.4f} vs notebook {v:.4f}'

for cut in ['2010-06-30', '2015-12-31', '2020-03-31']:     # no look-ahead: deleting the future changes nothing
    assert np.allclose(backtest(px, Params()).loc[:cut].values, backtest(px.loc[:cut], Params()).values), cut

tgt, _, z = pair_targets(px, Params())                    # every new pair position needs |z| > z_in that day
opened = (tgt != tgt.shift()).any(axis=1) & (tgt.abs().sum(axis=1) > 0) & z.notna()
assert opened.sum() > 50 and (z[opened].abs() > Params().z_in).all(), z[opened][z[opened].abs() <= Params().z_in]
print(f'ok: app matches notebook, no look-ahead, all {opened.sum()} pair entries at |z| > {Params().z_in}')

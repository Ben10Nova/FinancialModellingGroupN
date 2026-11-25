"""Run: python test_strategy.py  (needs internet). Fails if the app logic drifts from the notebook."""
import numpy as np
from strategy import Params, load_prices, run, backtest, pair_targets

px = load_prices()
t = run(px)['table']['Strategy (net)']
notebook = {'Ann. avg return': 0.1736, 'Ann. volatility': 0.1434, 'Sharpe ratio': 1.0973,
            'Alpha (ann.)': 0.0966, 'Beta': 0.6074, 'Information ratio': 0.8757, 'Max drawdown (monthly)': -0.1476}
for k, v in notebook.items():
    assert abs(t[k] - v) < 1e-3, f'{k}: app {t[k]:.4f} vs notebook {v:.4f}'

for cut in ['2010-06-30', '2015-12-31', '2020-03-31']:     # no look-ahead: deleting the future changes nothing
    assert np.allclose(backtest(px, Params()).loc[:cut].values, backtest(px.loc[:cut], Params()).values), cut

tgt, _, z = pair_targets(px, Params())                    # every new pair position needs |z| > z_in that day
nz = tgt.ne(0)                                            # new set of open legs = an entry (hedge-ratio resets are not)
opened = nz.ne(nz.shift(fill_value=False)).any(axis=1) & nz.any(axis=1) & z.notna()
assert opened.sum() > 50 and (z[opened].abs() > Params().z_in).all(), z[opened][z[opened].abs() <= Params().z_in]
print(f'ok: app matches notebook, no look-ahead, all {opened.sum()} pair entries at |z| > {Params().z_in}')

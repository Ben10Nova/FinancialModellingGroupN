"""Run: python test_strategy.py  (needs internet). Fails if the app logic drifts from the notebook."""
from dataclasses import replace

import numpy as np
import pandas as pd
from strategy import (Params, funding, funding_summary, intraday_value, load_intraday, load_live, load_prices, monthly,
                      monte_carlo, pension_daily, pension_mc, pension_mix, run, backtest, pair_targets, stats)

px = load_prices()
res = run(px)
t = res['table']['Strategy (net)']
notebook = {'Ann. avg return': 0.1718, 'Ann. volatility': 0.1433, 'Sharpe ratio': 1.0862,
            'Alpha (ann.)': 0.0952, 'Beta': 0.6036, 'Information ratio': 0.8611, 'Max drawdown (monthly)': -0.1476}
for k, v in notebook.items():
    assert abs(t[k] - v) < 1e-3, f'{k}: app {t[k]:.4f} vs notebook {v:.4f}'

risk = {'Excess kurtosis': 2.3722, 'VaR 95%, historical': 0.0573, 'VaR 99%, Cornish-Fisher': 0.1048,      # notebook: risk profile
        'CVaR 95% (expected shortfall)': 0.0799, 'Sortino ratio': 1.9143, 'Calmar ratio': 1.1809,
        'Downside capture': 0.6105, 'Alpha t-stat, Newey-West': 3.0381}
for k, v in risk.items():
    assert abs(res['risk'].loc[k, 'Strategy (net)'] - v) < 1e-3, f'{k}: app {res["risk"].loc[k, "Strategy (net)"]:.4f} vs notebook {v:.4f}'
mc, head, _ = res['mc']                                                                              # notebook: monte carlo
assert abs(mc.loc['Wealth of $1: median', 'Strategy (net)'] - 5.0576) < 1e-3 and abs(head['beats_sp'] - 0.9243) < 1e-3

# The opening fee is charged in addition to any trading cost on the first return day.
bt = res['bt']
opening_turnover = np.abs(bt.attrs['opening_weights']).sum()
opening_fee = opening_turnover * Params().cost
first = bt.iloc[0]
first_day_cost = (first.turnover - opening_turnover) * Params().cost
assert opening_fee > 0
assert np.isclose(first.net, (1 - opening_fee) * (1 + first.gross - first_day_cost) - 1)

# A first-month loss is a drawdown from the initial balance.
dates = pd.date_range('2020-01-31', periods=3, freq='ME')
sample = pd.Series([-0.10, 0.02, 0.01], index=dates)
assert np.isclose(stats(sample, sample * 0, sample)['Max drawdown (monthly)'], -0.10)

# Pension page: replacing 0% is the S&P 500, replacing 100% without a fee is the strategy itself.
r_m, b_m = monthly(res['bt'].net), monthly(res['bench_d'])
_, none = pension_mix(r_m, res['rf_m'], b_m, 0.0, 0.0)
assert np.allclose(none['With the strategy'], none['All in the S&P 500 TR'], equal_nan=True)
_, full = pension_mix(r_m, res['rf_m'], b_m, 1.0, 0.0)
assert np.allclose(full.loc[['Ann. avg return', 'Sharpe ratio', 'Beta', 'Max drawdown (monthly)'], 'With the strategy'],
                   res['table'].loc[['Ann. avg return', 'Sharpe ratio', 'Beta', 'Max drawdown (monthly)'], 'Strategy (net)'])
mix, _ = pension_mix(r_m, res['rf_m'], b_m)
assert np.allclose(monthly(pension_daily(res['bt'].net, res['bench_d'])), mix)        # daily sleeve lands on the monthly one
flat = funding(r_m, equity=0.0)                                                        # no equities: hedged, stays at 100%
assert np.allclose(flat.funding, 1.0) and flat.top_up.sum() == 0
short = funding(b_m * 0 - 0.01, equity=1.0, start=1.0, liab=0.0)                       # losing 1% a month: deficit, top-ups
assert (short.top_up > 0).sum() == len(short) // 12 and (short.funding < 1).all()
assert funding_summary(funding(b_m), 1.0)['Funding level at the end of 2008'] < 0.95   # 2008 pushed an all-S&P scheme into deficit
tab, ph, _ = pension_mc(mix, b_m)
mc_mix = monte_carlo(mix, res['rf_m'], b_m)
assert np.isclose(tab.loc['Wealth of $1: median', 'With the strategy'], mc_mix[0].loc['Wealth of $1: median', 'Strategy (net)'])
assert np.isclose(ph['beats_sp'], mc_mix[1]['beats_sp'])                                # same draws as the Monte Carlo page

early = run(px, replace(Params(), end='2020-12-31'))
assert (early['pair_year'], early['pair_now']) == (2021, ('XLP', 'XLV'))

for cut in ['2010-06-30', '2015-12-31', '2020-03-31']:     # no look-ahead: deleting the future changes nothing
    assert np.allclose(backtest(px, Params()).loc[:cut].values, backtest(px.loc[:cut], Params()).values), cut

tgt, _, z = pair_targets(px, Params())                    # every new pair position needs |z| > z_in that day
nz = tgt.ne(0)                                            # new set of open legs = an entry (hedge-ratio resets are not)
opened = nz.ne(nz.shift(fill_value=False)).any(axis=1) & nz.any(axis=1) & z.notna()
assert opened.sum() > 50 and (z[opened].abs() > Params().z_in).all(), z[opened][z[opened].abs() <= Params().z_in]
live = load_live()                                                    # live 2026 (11 months) must run too
lr = run(live, Params(start='2026-01-01', end=str(live.index[-1].date())))
assert len(lr['bt']) > 100
done = [s for s in intraday_value(lr['bt'], live, lr['bench_d'], load_intraday())[:-1]]   # completed sessions
for s in done:                       # 5-minute revaluation lands on the backtest's daily return (accruals aside)
    day = s.index[-1].normalize()
    assert abs(s.pf.iloc[-1] / s.pf.iloc[0] - 1 - lr['bt'].gross.loc[day]) < 3e-4, day

print(f'ok: app matches notebook (performance, risk profile, monte carlo), no look-ahead, all {opened.sum()} pair entries at |z| > {Params().z_in}, '
      f'live intraday matches daily on {len(done)} sessions')

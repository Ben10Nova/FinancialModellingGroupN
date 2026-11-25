# Strategy sandbox (research only, not the graded notebook)

Screens ~30 non-momentum strategies, 2006-01 to 2025-12, monthly evaluation.
Conventions: yfinance `auto_adjust=True`, ^SP500TR benchmark, rf = ^IRX, weights decided at t earn t+1,
10 bp cost per unit traded, net results ranked on in-sample (2006-2015) and checked out-of-sample (2016-2025).

```sh
pip install yfinance pandas numpy scipy statsmodels
cd sandbox
python fetch_data.py   # caches prices to px.pkl (git-ignored)
python run_all.py      # long-only / risk parity / sector / calendar strategies
python daily.py        # pair trades, turn-of-month
python combos.py       # core portfolios + XLU/XLP pair overlay
python pair_select.py  # ex-ante pair-selection rules over all 36 sector pairs
```

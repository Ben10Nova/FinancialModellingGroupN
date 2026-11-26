# FinancialModelling

Student number: 70689

Lucas Strobel – Student number: 78177

Noah van Raay – Student number: 81173

## Backtest notebook

`vol-control_pair_v1.ipynb` reproduces the backtest and simulation figures for the strategy. Open it in Google Colab and choose *Runtime → Run all*; data is pulled from the Yahoo Finance API.

## Run the Streamlit app locally

From the repository root, install the dependencies and start the app.

```sh
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

`strategy.py` holds the strategy logic (same as the notebook). `python3 test_strategy.py` checks that the
app reproduces the notebook's numbers and has no look-ahead.

## Deploy on Streamlit Community Cloud

In Streamlit Community Cloud, select `Ben10Nova/FinancialModellingGroupN`,
choose the GitHub branch that contains the app, and set the main file path to
`app.py`. Streamlit installs the dependencies from `requirements.txt`.

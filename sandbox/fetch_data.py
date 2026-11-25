import yfinance as yf
T = 'SPY EFA EEM IWM TLT IEF SHY LQD HYG TIP GLD VNQ DBC XLB XLE XLF XLI XLK XLP XLU XLV XLY KO PEP XOM CVX GDX EWA EWC HD LOW ^SP500TR ^IRX'.split()
yf.download(T, start='2004-01-01', end='2026-01-01', auto_adjust=True, progress=False)['Close'].to_pickle(__file__.replace('fetch_data.py', 'px.pkl'))

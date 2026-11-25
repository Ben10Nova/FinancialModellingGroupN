from dataclasses import asdict
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.dates import MonthLocator, num2date
from matplotlib.ticker import FuncFormatter, NullLocator
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from strategy import ASSETS, Params, load_live, load_prices, monthly, pair_returns, pair_targets, run, spy_exposure, wealth

FUND, FUND_LONG = 'MVP Strategies', 'Managed Volatility Portfolio'
ADDRESS = 'Rua da Holanda 1 &middot; 2775-405 Carcavelos &middot; Portugal'
REPO = 'https://github.com/Ben10Nova/FinancialModellingGroupN'
COLAB = 'https://colab.research.google.com/github/Ben10Nova/FinancialModellingGroupN/blob/main/vol-control_pair_v1.ipynb'
DEFAULTS = Params()
DEMO_DEPOSIT, DEMO_START = 1000.0, '2026-01-01'
CRISES = [('global financial crisis', '2007-10-09', '2009-03-09'), ('euro debt crisis', '2011-04-29', '2011-10-03'),
          ('q4 2018 selloff', '2018-09-20', '2018-12-24'), ('covid crash', '2020-02-19', '2020-03-23'),
          ('2022 rate shock', '2022-01-03', '2022-10-12')]          # s&p 500 peak and trough closes
TEAM = [('lucas s', '[title]'), ('ben s', '[title]'), ('katha g', '[title]'), ('noah vr', '[title]'),
        ('henrik t', '[title]'), ('chris w', '[title]')]
BIO = '[short bio: background, role at mvp strategies and areas of focus. two to three sentences.]'
LOADER = ('M0,134.8 5,134.4 10,137.7 15,132.2 20,128.2 25,128.8 30,127.6 35,126.4 41,127.5 46,129.3 51,131.2 56,130.3 61,129.5 66,129.5 71,124.2 76,123.9 81,124.0 86,120.1 91,123.6 96,119.8 101,115.4 106,112.6 111,114.6 116,115.9 122,113.9 127,110.9 132,110.7 137,109.9 142,107.3 147,104.5 152,103.1 157,98.8 162,100.2 167,97.1 172,94.1 177,90.5 182,89.7 187,87.2 192,84.7 197,84.4 203,85.2 208,84.5 213,83.0 218,83.1 223,77.8 228,72.6 233,68.5 238,67.4 243,63.9 248,67.8 253,63.8 258,67.2 263,65.0 268,62.8 273,66.0 278,64.7 284,60.9 289,48.8 294,48.8 299,48.5 304,51.0 309,46.0 314,44.0 319,42.5 324,42.8 329,44.4 334,42.5 339,42.7 344,39.2 349,36.9 354,31.3 359,33.5 365,27.2 370,27.0 375,21.6 380,18.8 385,14.9 390,14.7 395,12.6 400,10.0',                # all-time growth of $1, log scale, quarterly: portfolio
          'M0,135.2 5,134.1 10,134.9 15,131.7 20,129.9 25,128.5 30,129.0 35,126.4 41,130.8 46,130.4 51,133.7 56,144.0 61,150.0 66,147.5 71,142.4 76,140.3 81,138.7 86,134.6 91,137.3 96,134.3 101,130.8 106,128.4 111,130.3 116,131.3 122,129.2 127,126.5 132,126.8 137,125.7 142,123.1 147,120.4 152,118.0 157,116.2 162,115.4 167,113.1 172,111.9 177,109.9 182,110.2 187,108.3 192,107.7 197,108.0 203,110.5 208,107.8 213,105.6 218,106.2 223,103.3 228,101.3 233,99.7 238,97.9 243,94.0 248,96.4 253,93.8 258,95.1 263,95.0 268,91.4 273,90.7 278,89.8 284,87.2 289,91.1 294,86.3 299,86.2 304,81.0 309,76.2 314,74.1 319,72.1 324,72.7 329,76.1 334,75.9 339,78.3 344,76.1 349,75.1 354,71.1 359,74.5 365,68.7 370,67.0 375,63.2 380,61.8 385,59.4 390,62.5 395,57.3 400,54.2')                   # and s&p 500 tr
INK, MUTED, HAIR = '#101924', '#555b63', '#d7d7d7'
S1, S2, S3 = '#0b2648', '#848a90', '#a36d34'                   # portfolio, s&p / equity sleeve, spread sleeve

for f in (Path(__file__).parent / 'fonts').glob('*.ttf'):
    font_manager.fontManager.addfont(str(f))
plt.rcParams.update({
    'figure.facecolor': 'white', 'axes.facecolor': 'white', 'figure.dpi': 200,
    'font.family': 'monospace', 'font.monospace': ['IBM Plex Mono', 'DejaVu Sans Mono'], 'font.size': 8,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False, 'axes.spines.bottom': False,
    'axes.grid': False,
    'xtick.color': MUTED, 'ytick.color': MUTED, 'xtick.major.size': 0, 'ytick.major.size': 0,
    'lines.solid_joinstyle': 'round', 'text.parse_math': False})   # '$' in labels is a dollar sign, never math

st.set_page_config(page_title='MVP Strategies', layout='centered', initial_sidebar_state='collapsed')
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap');
:root { --paper:#ffffff; --ink:#101924; --muted:#555b63; --hairline:#d7d7d7; --panel:#f5f5f5; --inputline:#7c8186;
  --negative:#8c2d2b; --serif:"Newsreader",Georgia,serif; --sans:"IBM Plex Sans",system-ui,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,monospace; }
html, body, .stApp, .stApp *:where(:not([data-testid="stIconMaterial"])), [role="dialog"] *:where(:not([data-testid="stIconMaterial"])) { font-family: var(--sans) !important; color: var(--ink); }
.stApp { background: var(--paper); }
.stApp * { transition: none !important; animation: none !important; }
[data-testid="stToolbarActions"], [data-testid="stMainMenu"], [data-testid="stAppDeployButton"],
[data-testid="stDecoration"], footer, #MainMenu, [data-testid="stHeaderActionElements"], [data-testid="stElementToolbar"],
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stHeader"] { background: transparent !important; }
.block-container { max-width: 860px; padding: 6rem 1.25rem 6rem; }
p, li, label { font-size: 15px !important; line-height: 1.6; }

/* menu = sidebar; the expand control becomes three bars */
[data-testid="stSidebar"] { background: var(--paper) !important; border-right: 1px solid var(--ink); box-shadow: none !important; }
[data-testid="stSidebar"] > div:first-child { background: var(--paper) !important; }
[data-testid="stSidebarNav"] a { background: none !important; border-radius: 0 !important; padding: 5px 0 !important;
  min-height: 0 !important; height: auto !important; }
[data-testid="stSidebarNavSeparator"] { display: none !important; }
[data-testid="stSidebarNav"] a, [data-testid="stSidebarNav"] a * { font-size: 15px !important; color: var(--ink) !important;
  text-decoration: none !important; font-weight: 400; }
[data-testid="stSidebarNav"] a[aria-current="page"] * { font-weight: 600 !important; }
[data-testid="stSidebar"] p.ext { border-top: 1px solid var(--hairline); margin-top: 10px; padding-top: 14px; line-height: 2.2; }
[data-testid="stSidebar"] p.ext a { font-size: 13px !important; color: var(--muted) !important; text-decoration: none !important; }
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] button {
  width: 40px !important; height: 40px !important; min-width: 40px !important; min-height: 40px !important;
  border-radius: 0 !important; box-shadow: none !important; border: 0 !important;
  background-color: var(--paper) !important;
  background-image: linear-gradient(var(--ink),var(--ink)), linear-gradient(var(--ink),var(--ink)), linear-gradient(var(--ink),var(--ink)) !important;
  background-size: 22px 2px !important; background-repeat: no-repeat !important;
  background-position: center 12px, center 19px, center 26px !important; }
[data-testid="stExpandSidebarButton"] *, [data-testid="stSidebarCollapsedControl"] button * { visibility: hidden; }

.stElementContainer:has(> iframe[height="0"]), [data-testid="stElementContainer"]:has(> iframe[height="0"]) { margin: 0; }

/* home */
.home { min-height: calc(100vh - 14rem); display: flex; flex-direction: column; text-align: center; }
.home .mid { flex: 1 1 auto; display: flex; flex-direction: column; justify-content: center; }
.home p.fine { max-width: 90ch; margin: 0 auto 6px; }
h1.bh { font-family: var(--serif) !important; font-weight: 500; font-size: 84px !important; line-height: 1; letter-spacing: .01em;
  text-align: center; margin: 0; padding: 0 !important; }
p.long { font-family: var(--serif) !important; font-size: 21px !important; text-align: center; margin: 10px 0 0; }
p.addr { text-align: center; color: var(--muted) !important; margin: 10px 0 0; }

/* page heading */
.stApp h3 { font-family: var(--serif) !important; font-size: 36px !important; font-weight: 500 !important;
  line-height: 1.15; letter-spacing: -.01em; margin: 0 0 24px !important; padding: 0 0 14px !important;
  border-bottom: 1px solid var(--ink); }
.stApp h4 { font-family: var(--serif) !important; font-size: 22px !important; font-weight: 500 !important;
  margin: 34px 0 10px !important; padding: 0 !important; }

/* text */
a, a * { color: var(--ink) !important; text-decoration: underline !important; text-underline-offset: 3px; }
p.note, p.note * { font-size: 12.5px !important; color: var(--muted) !important; }
p.lede { font-family: var(--serif) !important; font-size: 19px !important; line-height: 1.45; max-width: 60ch; }
p.lede strong, .fig { font-family: var(--mono) !important; font-weight: 500; font-size: .92em !important; }
.stApp p.fine, .stApp p.fine * { font-size: 11.5px !important; line-height: 1.55; color: var(--muted) !important; }
.items { list-style: none; margin: 0 0 16px; padding: 0; max-width: 72ch; }
.items > li { display: grid; grid-template-columns: 28px 1fr; margin: 0; padding: 9px 0; }
.items .mk { font-family: var(--mono) !important; font-size: 12px !important; line-height: 24px; color: var(--muted) !important; }

/* tables */
table.plain { width: 100%; border-collapse: collapse; margin: 6px 0 10px; }
table.plain, table.plain tr, table.plain td, table.plain th { border: 0 !important; background: none !important; }
table.plain th { font-size: 11px !important; font-weight: 500; letter-spacing: .04em; color: var(--muted) !important;
  text-align: right; vertical-align: bottom; padding: 0 0 6px 14px; border-bottom: 1px solid var(--ink) !important; }
table.plain td { font-family: var(--mono) !important; font-size: 12.5px !important; font-variant-numeric: tabular-nums;
  text-align: right; white-space: nowrap; padding: 6px 0 6px 14px; border-bottom: 1px solid var(--hairline) !important; }
table.plain th:first-child, table.plain td:first-child { text-align: left; padding-left: 0; }
table.plain td.label { font-family: var(--sans) !important; font-size: 13.5px !important; white-space: normal; }
table.plain td.em, table.plain tr.em td { font-weight: 600; }
table.plain td.neg { color: var(--negative) !important; }
table.plain td.dim { color: var(--muted) !important; }
table.plain tr.total td { font-weight: 600; border-bottom: 0 !important; }
table.plain tr.first td { border-top: 1px solid var(--ink) !important; }
table.plain.compact td { padding-top: 4px; padding-bottom: 4px; }

/* form */
[class*="st-key-inv_"] button * { text-decoration: none !important; color: var(--muted) !important; }
.st-key-knobs { padding: 16px; gap: 10px !important; }
.st-key-knobs, [data-testid="stForm"] { background: var(--panel); border: 1px solid var(--hairline); border-top: 1px solid var(--ink);
  border-radius: 0; padding: 16px; }
[data-testid="stWidgetLabel"] p { font-size: 12px !important; color: var(--muted) !important; }
[data-baseweb="input"], [data-baseweb="select"] > div, [data-testid="stNumberInputContainer"] {
  border-radius: 0 !important; background: var(--paper) !important; box-shadow: none !important; }
[data-testid="stNumberInputContainer"], [data-baseweb="select"] > div, [data-testid="stTextInputRootElement"] {
  border: 1px solid var(--inputline) !important; min-height: 36px; border-radius: 0 !important; }
[data-baseweb="input"] { border: 0 !important; }
input, [data-baseweb="select"] * { font-family: var(--mono) !important; font-size: 13px !important; background: transparent !important; }
[data-testid="stNumberInputStepDown"], [data-testid="stNumberInputStepUp"] { border-radius: 0 !important;
  background: var(--paper) !important; border-left: 1px solid var(--hairline) !important; color: var(--muted) !important; }
button[kind="primaryFormSubmit"], button[kind="primary"] { border-radius: 0 !important; background: var(--ink) !important;
  border: 1px solid var(--ink) !important; min-height: 36px !important; padding: 0 28px !important; box-shadow: none !important; }
button[kind="primaryFormSubmit"] *, button[kind="primary"] * { color: var(--paper) !important; font-size: 13.5px !important; font-weight: 500; }
button[kind="tertiaryFormSubmit"], button[kind="tertiary"], .stDownloadButton button { background: none !important;
  border: 0 !important; padding: 0 !important; min-height: 0 !important; box-shadow: none !important; border-radius: 0 !important; }
button[kind="tertiaryFormSubmit"] *, button[kind="tertiary"] *, .stDownloadButton button * { font-size: 12.5px !important;
  text-decoration: underline; text-underline-offset: 3px; color: var(--ink) !important; }
[data-testid="stCheckbox"] span { border-radius: 0 !important; }

.st-key-knobs [data-testid="stColumn"] [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 12px !important; }
.st-key-knobs [data-testid="stColumn"] [data-testid="stColumn"] { min-width: 0 !important; }
[data-testid="stSliderThumbValue"], [data-testid="stSliderTickBarMin"], [data-testid="stSliderTickBarMax"] {
  font-family: var(--mono) !important; font-size: 11px !important; }
p.status i { display: inline-block; width: 9px; height: 9px; margin-right: 10px; border-radius: 50%; border: 1.5px solid var(--muted); }
p.status.on i { background: var(--ink); border-color: var(--ink); }

/* charts */
p.chart-head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; gap: 4px 16px;
  margin: 24px 0 0; padding-bottom: 6px; border-bottom: 1px solid var(--ink); }
p.chart-head b { font-size: 12px !important; font-weight: 500; margin-right: auto; }
p.chart-head span { display: inline-flex; align-items: center; gap: 6px; font-size: 11.5px !important; color: var(--muted) !important; }
p.chart-head i { display: inline-block; width: 14px; height: 2px; }

/* team: horizontal scroll, the card in the middle is in focus, the others fade */
.team-row { display: flex; gap: 28px; overflow-x: auto; scroll-snap-type: x mandatory; scrollbar-width: thin;
  padding: 6px calc(50% - 150px) 22px; }
.team-row .card { flex: 0 0 300px; scroll-snap-align: center; }
.stApp .team-row .card { animation: fade linear both !important; animation-timeline: view(inline) !important; }
@keyframes fade { 0%, 32% { opacity: .4; } 50% { opacity: 1; } 68%, 100% { opacity: .4; } }
div.ph { width: 100%; aspect-ratio: 4/5; margin: 0 0 14px; background: var(--panel); border: 1px solid var(--hairline);
  display: grid; place-items: center; font-family: var(--mono) !important; font-size: 18px; letter-spacing: .08em; color: var(--muted) !important; }
p.mname { font-family: var(--serif) !important; font-size: 26px !important; line-height: 1.2; margin: 0; }
.team-row p.note { margin: 2px 0 10px; }
p.bio { font-size: 14px !important; margin: 0; }

/* clickable lists, episodes and their deep-dive pop-up */
[class*="st-key-dv_"] { gap: 0 !important; max-width: 72ch; counter-reset: it; margin-bottom: 16px; }
[class*="st-key-dv_"] .stButton { counter-increment: it; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"] { width: 100%; display: block; position: relative; text-align: left;
  padding: 9px 0 9px 28px !important; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"]::before { content: counter(it); position: absolute; left: 0; top: 9px;
  font-family: var(--mono); font-size: 12px; line-height: 24px; color: var(--muted); }
.stApp [class*="st-key-dv_"] button[kind="tertiary"] * { font-size: 15px !important; line-height: 1.6; text-decoration: none !important;
  text-align: left; white-space: normal; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"] p::after, .stApp .st-key-stress button[kind="tertiary"] p::after {
  content: "↗"; margin-left: 6px; font-family: var(--mono); font-size: 12px; color: var(--muted); }
.stApp [class*="st-key-dv_"] button[kind="tertiary"]:hover *, .stApp .st-key-stress button[kind="tertiary"]:hover * { color: var(--muted) !important; }
.st-key-stress { gap: 0 !important; }
.st-key-stress [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 14px !important; padding: 6px 0;
  border-bottom: 1px solid var(--hairline); }
.st-key-stress [data-testid="stHorizontalBlock"]:has(p.th) { border-bottom-color: var(--ink); padding-top: 0; align-items: flex-end; }
.st-key-stress [data-testid="stColumn"] { min-width: 0 !important; }
.st-key-stress [data-testid="stColumn"] [data-testid="stVerticalBlock"] { gap: 0 !important; }
.st-key-stress p { margin: 0 !important; }
.st-key-stress [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
.st-key-stress p.th { font-size: 11px !important; font-weight: 500; letter-spacing: .04em; color: var(--muted) !important; text-align: right; }
.st-key-stress p.c { font-family: var(--mono) !important; font-size: 12.5px !important; font-variant-numeric: tabular-nums; text-align: right; }
.st-key-stress p.c.em { font-weight: 600; } .st-key-stress p.c.neg { color: var(--negative) !important; }
.st-key-stress p.dim { font-size: 12.5px !important; color: var(--muted) !important; text-align: left; } .st-key-stress p.th.l { text-align: left; }
.stApp .st-key-stress button[kind="tertiary"] * { font-size: 13.5px !important; text-decoration: none !important; text-align: left; }
.st-key-stress p.win { display: none; }
[role="dialog"] { border-radius: 0 !important; }
[role="dialog"] :not([data-testid="stMarkdown"]) > [data-testid="stMarkdownContainer"] p { font-family: var(--serif) !important; font-weight: 500 !important; font-size: 28px !important; }
[role="dialog"] [data-testid="stImage"], [role="dialog"] [data-testid="stImage"] img { width: 100% !important; height: auto !important; }

/* investor account */
table.kpi { width: 100%; border-collapse: collapse; table-layout: fixed; margin: 0 0 8px; }
table.kpi, table.kpi tr, table.kpi td { border: 0 !important; background: none !important; }
table.kpi td { padding: 0 16px 0 0; vertical-align: top; }
table.kpi span.k { display: block; font-size: 11px !important; letter-spacing: .04em; color: var(--muted) !important; }
table.kpi span.v { display: block; font-family: var(--mono) !important; font-size: 22px !important; font-weight: 500; }
table.kpi span.v.neg { color: var(--negative) !important; }

@media (max-width: 640px) {
  h1.bh { font-size: 46px !important; } p.long { font-size: 17px !important; } .stApp h3 { font-size: 28px !important; }
  .team-row { padding: 6px 14vw 22px; gap: 18px; } .team-row .card { flex-basis: 72vw; }
  .st-key-stress [data-testid="stColumn"]:has(p.dim), .st-key-stress [data-testid="stColumn"]:has(p.wh) { display: none !important; }
  .stApp .st-key-stress button[kind="tertiary"] * { font-size: 12.5px !important; line-height: 1.35; }
  .st-key-stress p.c { font-size: 11.5px !important; } .st-key-stress p.th { font-size: 10px !important; }
  .st-key-stress p.win { display: block; white-space: nowrap; font-size: 10px !important; font-family: var(--mono) !important; color: var(--muted) !important; }
  table.kpi tr { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
  table.kpi span.v { font-size: 18px !important; }
}
</style>
""", unsafe_allow_html=True)

html = lambda s: st.markdown(s, unsafe_allow_html=True)
heading = lambda t: html(f'<h3>{t}</h3>')
note = lambda t: html(f'<p class="note">{t}</p>')
ROWS = {'Ann. avg return': 'ann. return', 'Ann. volatility': 'ann. volatility', 'Sharpe ratio': 'sharpe ratio',
        'Alpha (ann.)': 'alpha (ann.)', 'Alpha t-stat': 'alpha t-stat', 'Beta': 'beta',
        'Information ratio': 'information ratio', 'Max drawdown (monthly)': 'max drawdown (monthly)'}
PCT_ROWS = {'ann. return', 'ann. volatility', 'alpha (ann.)', 'max drawdown (monthly)'}


def num(v, kind='pct'):
    """formatted text and css class; true minus sign for negatives"""
    if pd.isna(v):
        return '–', ''
    v = round(float(v), 8) + 0.0
    s = {'pct': f'{v:.1%}', 'x': f'{v:.2f}', 'usd': f'${abs(v):,.2f}'}[kind]
    return ('−' + s.lstrip('-') if v < 0 else s), ('neg' if v < 0 else '')


def td(v, kind='pct', cls=''):
    s, neg = num(v, kind)
    return f'<td class="{cls} {neg}">{s}</td>'


def metrics_table(df, bold):
    df = df.rename(index=ROWS)
    head = '<tr><th></th>' + ''.join(f'<th>{c}</th>' for c in df.columns) + '</tr>'
    body = ''.join(f'<tr><td class="label">{i}</td>' + ''.join(
        td(v, 'pct' if i in PCT_ROWS else 'x', 'em' if c == bold else '') for c, v in row.items()) + '</tr>'
        for i, row in df.iterrows())
    html(f'<table class="plain">{head}{body}</table>')


def chart(title, series, kind='growth', h=2.9, bands=()):
    legend = ''.join(f'<span><i style="background:{c}"></i>{n}</span>' for n, _, c in series)
    html(f'<p class="chart-head"><b>{title}</b>{legend}</p>')
    fig, ax = plt.subplots(figsize=(8, h))
    for k, (_, s, c) in enumerate(series):
        y = s / s.cummax() - 1 if kind == 'drawdown' else s
        ax.plot(y.index, y.values, color=c, lw=1.8 if k == 0 else 1.3, zorder=3 - k)
        if kind == 'drawdown':
            ax.fill_between(y.index, y.values, 0, color=c, alpha=.18, lw=0)
    if kind == 'growth':
        lo, hi = min(s.min() for _, s, _ in series), max(s.max() for _, s, _ in series)
        ticks = [t for t in [0.5, 1, 2, 5, 10, 20, 30, 50, 100] if lo / 1.3 <= t <= hi * 1.3]
        ax.set_yscale('log'); ax.set_yticks(ticks); ax.yaxis.set_minor_locator(NullLocator())
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'${v:g}'))
        ax.axhline(1, color=INK, lw=.8)
    elif kind == 'drawdown':
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:.0%}'.replace('-', '−')))
        ax.axhline(0, color=INK, lw=.8)
    else:                                                          # one year, linear: dollar values or z-scores
        if kind == 'z':
            for b, ls in bands:
                ax.axhline(b, color=MUTED, lw=.8, ls=ls); ax.axhline(-b, color=MUTED, lw=.8, ls=ls)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:g}'.replace('-', '−')))
        else:
            dec = 2 if max(s.max() for _, s, _ in series) < 10 else 0
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'${v:,.{dec}f}'))
        ax.xaxis.set_major_locator(MonthLocator())
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: num2date(v).strftime('%b').lower()))
    fig.tight_layout(pad=.3)
    st.pyplot(fig)
    plt.close(fig)


def items(rows, ordered=True):
    tag = 'ol' if ordered else 'ul'
    html(f'<{tag} class="items">' + ''.join(
        f'<li><span class="mk">{i + 1 if ordered else "–"}</span><span>{f"<b>{lead}</b> " if lead else ""}{text}</span></li>'
        for i, (lead, text) in enumerate(rows)) + f'</{tag}>')


def dive(title, body):
    """pop-up over the current page; body draws its content"""
    st.dialog(title, width='medium')(body)()


def placeholder(what):
    note(f'[deep dive placeholder: {what}]')


def clickable(key, rows):
    """numbered list, each item opens its deep dive. plain markdown labels: write '&', '>' not entities"""
    with st.container(key=f'dv_{key}'):
        for i, (lead, text) in enumerate(rows):
            if st.button(f'**{lead}** {text}', key=f'{key}{i}', type='tertiary'):
                dive(lead.rstrip('.'), lambda: (html(f'<p class="lede">{text}</p>'),
                                                placeholder('the reasoning behind this point, evidence from the backtest '
                                                            'and supporting charts.')))


@st.cache_data(ttl=86400, show_spinner=False)
def get_prices():
    return load_prices()


@st.cache_data(show_spinner=False)
def get_results(**kw):
    return run(get_prices(), Params(**kw))


@st.cache_data(ttl=3600, show_spinner='loading live prices ...')
def get_live(target_vol=DEFAULTS.target_vol):
    px = load_live()
    return run(px, Params(start=DEMO_START, end=str(px.index[-1].date()), target_vol=target_vol)), px


def results():
    p = st.session_state.get('params', DEFAULTS)
    try:
        return p, get_results(**asdict(p))
    except RuntimeError as e:
        note(str(e))
        st.stop()


# ================================================================ pages
def home():
    html(f'<div class="home"><div class="mid"><h1 class="bh">{FUND}</h1><p class="long">{FUND_LONG}</p>'
         f'<p class="addr">{ADDRESS}</p></div>'
         f'<p class="fine">data: yahoo finance (split/dividend adjusted), ^SP500TR, ^IRX. statistics on monthly returns; '
         f'means &times;12, volatility &times;&radic;12, beta not annualized. method: <a href="{COLAB}">notebook</a> &middot; '
         f'<a href="{REPO}">source code</a>.</p>'
         f'<p class="fine">hypothetical backtest, 2270 financial modeling, nova sbe. not investment advice.</p></div>')


def thesis():
    heading('thesis')
    html('<p>two return streams, built to be uncorrelated, sharing one 15% risk budget:</p>')
    clickable('thesis', [('volatility-targeted equity.', 'we hold the s&p 500 and scale exposure with realized volatility: more in '
            'calm markets, less in stressed ones. it gets whatever risk budget the spread sleeve does not use.'),
           ('defensive sector spread.', 'a beta-neutral relative-value position between the two most defensive us '
            'equity sectors, which trades the mean reversion of temporary dislocations.')])
    html('<p>the two sleeves earn their returns from different sources, so the combined portfolio has outperformed '
         'either one on its own, with lower volatility and drawdowns than the s&amp;p 500.</p>')


KNOBS = [  # params field, label, min, max, step, shown as field x scale, format
    ('target_vol', 'volatility target (% p.a.)', 5.0, 30.0, 0.5, 100, '%.1f'),
    ('max_lev', 'max equity exposure (x)', 1.0, 3.0, 0.05, 1, '%.2f'),
    ('pair_size', 'spread size per leg, avg (x)', 0.25, 2.0, 0.05, 1, '%.2f'),
    ('z_in', 'spread entry threshold (|z|)', 1.0, 4.0, 0.1, 1, '%.1f'),
    ('cost', 'trading cost (bp per unit traded)', 0.0, 100.0, 1.0, 1e4, '%.0f'),
    ('fin_spread', 'financing spread over t-bills (bp p.a.)', 0.0, 500.0, 5.0, 1e4, '%.0f'),
    ('short_fee', 'borrow fee on shorts (bp p.a.)', 0.0, 500.0, 5.0, 1e4, '%.0f')]


def sync(src, dst):
    st.session_state[dst] = st.session_state[src]


def load_knobs(p, apply=False):
    ss = st.session_state
    for f, *_, k, _ in KNOBS:
        ss[f's_{f}'] = ss[f'n_{f}'] = round((getattr(p, f) or getattr(DEFAULTS, f)) * k, 6)
    ss['years'], ss['pair_on'] = (int(p.start[:4]), int(p.end[:4])), p.pair_size > 0
    if apply:
        ss['params'] = p


def apply_knobs():
    ss = st.session_state
    (y0, y1), v = ss['years'], {f: round(ss[f's_{f}'] / k, 8) for f, *_, k, _ in KNOBS}
    if y1 <= y0:
        ss['bad_years'] = True
        return
    v['pair_size'] = v['pair_size'] if ss['pair_on'] else 0.0
    ss['params'] = Params(start=f'{y0}-01-01', end=f'{y1}-12-31', **v)


def performance():
    heading('performance')
    ss = st.session_state
    if 's_target_vol' not in ss:                                   # widget state is dropped when the page is left
        load_knobs(ss.get('params', DEFAULTS))
    with st.container(key='knobs'):
        for pair in (KNOBS[i:i + 2] for i in range(0, len(KNOBS), 2)):
            for col, (f, label, lo, hi, step, _, fmt) in zip(st.columns(2, gap='large'), pair):
                a, b = col.columns([3, 1.2], vertical_alignment='bottom')
                a.slider(label, lo, hi, step=step, format=fmt, key=f's_{f}', on_change=sync, args=(f's_{f}', f'n_{f}'))
                b.number_input(label, lo, hi, step=step, format=fmt, key=f'n_{f}', label_visibility='collapsed',
                               on_change=sync, args=(f'n_{f}', f's_{f}'))
        st.slider('years', 2006, 2025, key='years')
        b = st.columns([4, 2, 1], vertical_alignment='center')
        b[0].checkbox('include sector spread', key='pair_on')
        b[1].button('reset to notebook defaults', type='tertiary', on_click=load_knobs, args=(DEFAULTS, True))
        b[2].button('run', type='primary', on_click=apply_knobs)
    if ss.pop('bad_years', False):
        note('end year must be after start year.')
    p, res = results()
    note('notebook defaults: matches the prospectus.' if p == DEFAULTS else
         'modified assumptions: differs from the prospectus. all pages use these settings.')

    bt, bench = res['bt'], res['bench_d']
    w_s, w_b = wealth(bt.net), wealth(bench)
    html(f'<p class="lede">$1 invested in january {p.start[:4]}: <strong>${w_s.iloc[-1]:,.2f}</strong> '
         f'(s&amp;p 500 tr: <strong>${w_b.iloc[-1]:,.2f}</strong>). net of trading, financing and borrow costs.</p>')
    metrics_table(res['table'].rename(columns={'Strategy (net)': 'portfolio (net)', 'S&P 500 TR': 's&amp;p 500 tr'}),
                  'portfolio (net)')
    chart('growth of $1, log scale', [('portfolio (net)', w_s, S1), ('s&amp;p 500 tr', w_b, S2)])
    chart('drawdown', [('portfolio (net)', w_s, S1), ('s&amp;p 500 tr', w_b, S2)], kind='drawdown', h=2.2)
    rf_d = (get_prices()['^IRX'] / 100 / 252).shift(1).loc[bt.index]
    csv = monthly(pd.DataFrame({'portfolio_net': bt.net, 'portfolio_gross': bt.gross, 'equity_sleeve': res['spy_only'].net,
                                'spread_sleeve': res['pair_only'].net, 'sp500_tr': bench, 'rf': rf_d}))
    st.download_button('download monthly returns (csv)', csv.to_csv(index_label='month', float_format='%.6f'),
                       file_name=f'monthly_returns_{p.start[:4]}_{p.end[:4]}.csv', mime='text/csv', type='tertiary')


def annual_returns():
    heading('annual returns')
    p, res = results()
    yr = res['yearly']
    cagr = lambda r: (1 + r).prod() ** (1 / len(yr)) - 1
    rows = ''.join(f'<tr><td>{y}</td>{td(r.Strategy, cls="em")}{td(r["S&P 500 TR"])}<td class="dim">{r["Pair held"].lower()}</td></tr>'
                   for y, r in yr.iterrows())
    html(f'<table class="plain compact"><tr><th>year</th><th>portfolio</th><th>s&amp;p 500 tr</th><th>spread pair</th></tr>{rows}'
         f'<tr class="total first"><td>cagr</td>{td(cagr(yr.Strategy))}{td(cagr(yr["S&P 500 TR"]))}<td></td></tr>'
         f'<tr class="total"><td>cumulative</td>{td((1 + yr.Strategy).prod() - 1)}{td((1 + yr["S&P 500 TR"]).prod() - 1)}<td></td></tr></table>')


def stress_tests():
    heading('stress tests')
    p, res = results()
    bt, bench = res['bt'], res['bench_d']
    note('s&amp;p 500 peak-to-trough episodes, total return over each window. click an episode for the deep dive.')
    cut = lambda r, a, b: r.loc[a:b].iloc[1:]
    span = lambda a, b: f'{pd.Timestamp(a):%b %Y} &rarr; {pd.Timestamp(b):%b %Y}'.lower()
    eps = [e for e in CRISES if pd.Timestamp(e[1]) >= bt.index[0] and pd.Timestamp(e[2]) <= bt.index[-1]]
    if not eps:
        note('no episode falls inside the selected years.')
        return
    streams = [('s&amp;p 500 tr', bench), ('portfolio', bt.net), ('equity sleeve', res['spy_only'].net),
               ('spread sleeve', res['pair_only'].net)]
    cell = lambda col, v, cls='': col.markdown(f'<p class="c {cls} {num(v)[1]}">{num(v)[0]}</p>', unsafe_allow_html=True)
    W = [3, 2.2, 1.3, 1.3, 1.3, 1.3]
    with st.container(key='stress'):
        for col, t in zip(st.columns(W), ['episode', 'window'] + [n for n, _ in streams]):
            col.markdown(f'<p class="th {"l" if t == "episode" else "wh" if t == "window" else ""}">{t}</p>', unsafe_allow_html=True)
        for k, (name, a, b) in enumerate(eps):
            c = st.columns(W, vertical_alignment='center')
            clicked = c[0].button(name, key=f'ep{k}', type='tertiary')
            c[0].markdown(f'<p class="win">{span(a, b)}</p>', unsafe_allow_html=True)
            c[1].markdown(f'<p class="dim">{span(a, b)}</p>', unsafe_allow_html=True)
            for col, (n, r) in zip(c[2:], streams):
                cell(col, (1 + cut(r, a, b)).prod() - 1, 'em' if n == 'portfolio' else '')
            if clicked:
                def body(a=a, b=b):
                    note(span(a, b))
                    html('<table class="plain"><tr>' + ''.join(f'<th>{n}</th>' for n, _ in streams) + '</tr><tr>'
                         + ''.join(td((1 + cut(r, a, b)).prod() - 1) for _, r in streams) + '</tr></table>')
                    chart('growth of $1 over the episode', [('portfolio (net)', wealth(cut(bt.net, a, b)), S1),
                                                            ('s&amp;p 500 tr', wealth(cut(bench, a, b)), S2)], kind='line')
                    placeholder('what happened in markets, how each sleeve was positioned going in, and what drove the result.')
                dive(name, body)


def attribution():
    heading('attribution')
    p, res = results()
    note('each sleeve run in isolation, idle capital in t-bills.')
    metrics_table(res['sleeves'].rename(columns={'Vol-managed SPY only': 'equity sleeve', 'Pair only (+ T-bills)': 'spread sleeve',
                                                 'Combined strategy': 'combined'}), 'combined')
    chart('growth of $1, log scale', [('combined', wealth(res['bt'].net), S1), ('equity sleeve', wealth(res['spy_only'].net), S2),
                                      ('spread sleeve', wealth(res['pair_only'].net), S3)])
    html(f'<p>positioning at the {p.end[:4]} close: equity exposure <span class="fig">{res["exposure_now"]:.2f}x</span>, '
         f'spread pair for {int(p.end[:4]) + 1}: <span class="fig">{"/".join(res["pair_now"]).lower()}</span>.</p>')


def live_2026():
    heading('live: 2026')
    html('<p>the rules were frozen at the 31 dec 2025 close. this page runs them, with notebook defaults, on data the '
         'strategy was never fitted on: a true out-of-sample check, separate from the prospectus numbers.</p>')
    try:
        live = get_live()[0]
    except Exception:
        note('live data unavailable right now (yahoo rate limit). reload in a minute.')
        return
    lb, lbench = live['bt'], live['bench_d']
    note(f'1 jan 2026 &rarr; {lb.index[-1]:%d %b %Y}'.lower())
    row = lambda name, r, cls: (f'<tr class="{cls}"><td class="label">{name}</td>{td((1 + r).prod() - 1)}'
                                f'{td(r.std() * 252 ** .5)}{td((wealth(r) / wealth(r).cummax() - 1).min())}</tr>')
    html('<table class="plain"><tr><th></th><th>return</th><th>volatility (ann.)</th><th>max drawdown</th></tr>'
         + row('portfolio (net)', lb.net, 'em') + row('s&amp;p 500 tr', lbench, '') + '</table>')
    chart('growth of $1', [('portfolio (net)', wealth(lb.net), S1), ('s&amp;p 500 tr', wealth(lbench), S2)], kind='line')
    html(f'<p>current positioning: equity exposure <span class="fig">{lb.w_spy.iloc[-1]:.2f}x</span>, spread pair '
         f'<span class="fig">{"/".join(live["pair_now"]).lower()}</span>.</p>')


def rules():
    heading('rules')
    p, _ = results()
    clickable('rules', [('risk budget.', f'one {p.target_vol:.0%} volatility budget for the whole portfolio. the spread sleeve\'s realized '
            'volatility (63 trading days) is taken out first; the equity sleeve gets the rest.'),
           ('equity sleeve.', f'at each month-end, exposure = remaining budget / spy realized volatility (21 trading days, '
            f'annualized), capped at {p.max_lev:.2f}x. idle cash earns the t-bill rate; leverage is financed at t-bill + '
            f'{p.fin_spread * 1e4:.0f} bp.'),
           ('spread sleeve.', f'at each year-end, select the two lowest-beta sector etfs vs spy (trailing 1y). daily z-score '
            f'of the log price ratio vs its 60-day mean: enter at |z| > {p.z_in:g} (long cheap, short rich), exit at '
            f'|z| < {p.z_out:g}. legs are sized beta-neutral from the same prior-year betas, {2 * p.pair_size:.2f}x gross. '
            'a newly selected pair starts flat.'),
           ('execution.', 'signals use closes up to day t; positions earn from t+1.'),
           ('costs.', f'{p.cost * 1e4:.0f} bp per unit traded, {p.short_fee * 1e4:.0f} bp p.a. borrow fee on shorts.')])


def risks():
    heading('risks')
    p, res = results()
    mdd = num(res['table'].loc['Max drawdown (monthly)', 'Strategy (net)'])[0]
    items([(None, 'leverage and shorting required; gross exposure can exceed 4x.'),
           (None, f'max drawdown {mdd} on monthly data.'),
           (None, 'selection bias: the low-beta pair rule was formulated after observing defensive-sector pairs; '
                  'alternative selection rules did not add value.'),
           (None, 'monthly rebalancing lags sudden volatility spikes; low exposure after crashes misses sharp rebounds.'),
           (None, 'realized daily volatility can exceed the budget in sudden spikes, because exposure is reset monthly.'),
           (None, 'yahoo finance data, fixed cost assumptions, no taxes.')], ordered=False)


def team():
    heading('team')
    initials = lambda n: ''.join(w[0] for w in n.split())
    html('<div class="team-row">' + ''.join(
        f'<div class="card"><div class="ph">{initials(n)}</div><p class="mname">{n}</p><p class="note">{t}</p>'
        f'<p class="bio">{BIO}</p></div>' for n, t in TEAM) + '</div>')


def investor():
    heading('investor login')
    if not st.session_state.get('investor'):
        note('draft: accounts are not connected yet. any details open a demo account.')
        with st.form('login'):
            st.text_input('email')
            st.text_input('password', type='password')
            if st.form_submit_button('log in', type='primary'):
                st.session_state['investor'] = True
                st.rerun()
        return
    ss = st.session_state
    dep, tv = ss.get('inv_dep', DEMO_DEPOSIT), ss.get('inv_tv', DEFAULTS.target_vol)
    html(f'<style>.st-key-inv_{ss.get("inv_view") or "account"} button * {{ color: var(--ink) !important; font-weight: 600; }}</style>')
    menu = st.columns([1, 1, 1, 5])
    for col, (label, view) in zip(menu, [('account', 'account'), ('settings', 'settings'), ('log out', None)]):
        if col.button(label, key=f'inv_{view or "logout"}', type='tertiary'):
            ss['investor'], ss['inv_view'] = view is not None, view
            st.rerun()
    if ss.get('inv_view') == 'settings':
        with st.form('inv_settings'):
            new_dep = st.number_input('deposit at the 31 dec 2025 close ($)', 100.0, 10_000_000.0, dep, 100.0, format='%.0f')
            new_tv = st.select_slider('risk budget: volatility target (% p.a.)', list(range(5, 31)), round(tv * 100))
            note('the whole account is recalculated from 1 jan 2026 with these settings.')
            if st.form_submit_button('save', type='primary'):
                ss['inv_dep'], ss['inv_tv'], ss['inv_view'] = new_dep, new_tv / 100, 'account'
                st.rerun()
        return
    try:
        live, px = get_live(tv)
    except Exception:
        note('live data unavailable right now (yahoo rate limit). reload in a minute.')
        return
    lb, lbench = live['bt'], live['bench_d']
    value = dep * (1 + lb.net).cumprod()
    bench_value = dep * (1 + lbench).cumprod()
    profit = value.iloc[-1] - dep
    note(f'demo account &middot; ${dep:,.0f} invested at the 31 dec 2025 close, {tv:.0%} risk budget &middot; '
         f'as of the {lb.index[-1]:%d %b %Y} close'.lower())
    kpi = lambda k, v, cls='': f'<td><span class="k">{k}</span><span class="v {cls}">{v}</span></td>'
    pr, neg = num(profit, 'usd')
    html('<table class="kpi"><tr>' + kpi('balance', num(value.iloc[-1], 'usd')[0]) + kpi('profit', pr, neg)
         + kpi('return', num(value.iloc[-1] / dep - 1)[0], neg)
         + kpi('s&amp;p 500 tr, same deposit', num(bench_value.iloc[-1], 'usd')[0]) + '</tr></table>')
    chart('account value', [('portfolio (net)', pd.concat([pd.Series(dep, index=[pd.Timestamp('2025-12-31')]), value]), S1),
                            ('s&amp;p 500 tr', pd.concat([pd.Series(dep, index=[pd.Timestamp('2025-12-31')]), bench_value]), S2)],
          kind='line')

    p0 = Params(start=DEMO_START, end=str(lb.index[-1].date()), target_vol=tv)
    tgt, chosen, z = pair_targets(px, p0)
    a, b = chosen[int(DEMO_START[:4])]
    legs, zt = tgt.iloc[-1][[a, b]] * p0.pair_size, z.iloc[-1]
    if legs.abs().sum() > 0:
        lng, sht = legs.idxmax(), legs.idxmin()
        status = (f'<b>spread open</b> &middot; long {lng.lower()} {legs[lng]:.2f}x, short {sht.lower()} {-legs[sht]:.2f}x '
                  f'&middot; z-score {num(zt, "x")[0]} &middot; closes when |z| &lt; {p0.z_out:g}')
    else:
        status = (f'<b>spread flat</b> &middot; {a.lower()}/{b.lower()} &middot; z-score {num(zt, "x")[0]} '
                  f'&middot; opens when |z| &gt; {p0.z_in:g}')
    html('<h4>sector spread</h4>')
    html(f'<p class="status {"on" if legs.abs().sum() > 0 else ""}"><i></i>{status}</p>')
    chart(f'z-score, log {a.lower()}/{b.lower()}', [('z-score', z.loc[DEMO_START:], S1)], kind='z', h=2.2,
          bands=((p0.z_in, '--'), (p0.z_out, ':')))
    note(f'dashed: entry at |z| &gt; {p0.z_in:g} (short the rich leg, buy the cheap one). dotted: exit at |z| &lt; {p0.z_out:g}.')

    W = lb[[f'w_{a}' for a in ASSETS]].set_axis(ASSETS, axis=1)
    html('<h4>positions</h4>')
    eq = value.iloc[-1]
    pos = W.iloc[-1]
    rows = ''.join(f'<tr><td class="label">{a.lower()}</td>{td(w, "x")}{td(w * eq, "usd")}</tr>' for a, w in pos.items() if abs(w) > 1e-9)
    cash = 1 - pos.sum()
    rows += f'<tr><td class="label">{"cash (t-bills)" if cash >= 0 else "borrowing"}</td>{td(cash, "x")}{td(cash * eq, "usd")}</tr>'
    html(f'<table class="plain"><tr><th>holding</th><th>weight (x equity)</th><th>value</th></tr>{rows}'
         f'<tr class="total first"><td>account value</td><td></td>{td(eq, "usd")}</tr></table>')

    html('<h4>trades</h4>')
    d0 = px.index[px.index.get_loc(lb.index[0]) - 1]                # initial purchase at the last close of 2025
    P = tgt * p0.pair_size
    w0 = pd.Series([spy_exposure(px, p0, pair_returns(px, P)).loc[d0], *P.loc[d0]], index=ASSETS)
    W = pd.concat([w0.to_frame(d0).T, W])
    gross = pd.concat([pd.Series(0.0, index=[d0]), lb.gross])
    V = pd.concat([pd.Series(dep, index=[d0]), value])
    eq_before = V.shift(1).fillna(dep) * (1 + gross)          # equity at each close, before that day's costs
    drift = W.shift(1).fillna(0) * (1 + px[ASSETS].pct_change().loc[W.index]) / (1 + gross).values[:, None]
    trades = ((W - drift) * eq_before.values[:, None]).stack()
    trades = trades[trades.abs() > 0.005].iloc[::-1]
    note(f'{len(trades)} trades, newest first, including the initial purchase; '
         f'costs of {p0.cost * 1e4:.0f} bp per unit traded are deducted from the account.')
    rows = ''.join(f'<tr><td>{d:%d %b %Y}'.lower() + f'</td><td class="label">{a.lower()}</td><td class="dim">'
                   f'{"buy" if v > 0 else "sell"}</td>{td(abs(v), "usd")}</tr>' for (d, a), v in trades.items())
    html(f'<table class="plain compact"><tr><th>date</th><th>asset</th><th>side</th><th>amount</th></tr>{rows}</table>')


def loader(key):
    """on a new page: close the menu and cover the page while the performance curve draws itself, until the run is done.
    the iframe only reloads when key changes, so widget reruns on the same page show nothing."""
    path = lambda d, c, w, t: (f'<path d="{d}" pathLength="1" style="stroke:{c};stroke-width:{w};'
                               f'animation:draw 1.3s cubic-bezier(.4,0,.2,1) {t}s forwards"/>')
    components.html(f"""<!-- {key} -->
<style>html,body{{margin:0;height:100%;background:#fff;display:grid;place-items:center;overflow:hidden}}
svg{{width:min(520px,78vw);overflow:visible}} path{{fill:none;stroke-linejoin:round;stroke-linecap:round;
stroke-dasharray:1;stroke-dashoffset:1}} @keyframes draw{{to{{stroke-dashoffset:0}}}}</style>
<svg viewBox="0 0 400 160">{path(LOADER[1], S2, 1.4, 0)}{path(LOADER[0], S1, 2.2, .15)}</svg>
<script>
const f = frameElement, d = parent.document, t0 = Date.now();
d.querySelector('[data-testid="stSidebar"][aria-expanded="true"] [data-testid="stSidebarCollapseButton"] button')?.click();
Object.assign(f.style, {{display: 'block', opacity: 1, position: 'fixed', inset: 0, width: '100vw', height: '100vh', zIndex: 999990, border: 0, transition: 'opacity .4s'}});
(function wait() {{
  if (Date.now() - t0 < 1600 || d.querySelector('.stApp')?.dataset.testScriptState === 'running') return setTimeout(wait, 100);
  f.style.opacity = 0; setTimeout(() => f.style.display = 'none', 450);
}})();
</script>""", height=0)


pages = [st.Page(home, title='home', url_path='home', default=True), st.Page(thesis, title='thesis', url_path='thesis'),
         st.Page(performance, title='performance', url_path='performance'),
         st.Page(annual_returns, title='annual returns', url_path='annual-returns'),
         st.Page(stress_tests, title='stress tests', url_path='stress-tests'),
         st.Page(attribution, title='attribution', url_path='attribution'),
         st.Page(live_2026, title='live: 2026', url_path='live-2026'), st.Page(rules, title='rules', url_path='rules'),
         st.Page(risks, title='risks', url_path='risks'), st.Page(team, title='team', url_path='team'),
         st.Page(investor, title='investor login', url_path='investor-login')]
nav = st.navigation(pages, position='sidebar')
st.sidebar.markdown(f'<p class="ext"><a href="{REPO}">source code</a><br><a href="{COLAB}">notebook</a></p>',
                    unsafe_allow_html=True)
loader(f"{nav.url_path}|{st.session_state.get('params', DEFAULTS)}")
nav.run()

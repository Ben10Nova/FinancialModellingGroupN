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
INK, MUTED, HAIR = '#101924', '#555b63', '#d7d7d7'
S1, S2, S3 = '#0b2648', '#848a90', '#a36d34'                   # portfolio, s&p / equity sleeve, spread sleeve

for f in (Path(__file__).parent / 'fonts').glob('*.ttf'):
    font_manager.fontManager.addfont(str(f))
plt.rcParams.update({
    'figure.facecolor': 'white', 'axes.facecolor': 'white', 'figure.dpi': 200,
    'font.family': 'monospace', 'font.monospace': ['IBM Plex Mono', 'DejaVu Sans Mono'], 'font.size': 8,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False, 'axes.spines.bottom': False,
    'axes.grid': True, 'axes.grid.axis': 'y', 'grid.color': HAIR, 'grid.linewidth': 0.8, 'axes.axisbelow': True,
    'xtick.color': MUTED, 'ytick.color': MUTED, 'xtick.major.size': 0, 'ytick.major.size': 0,
    'lines.solid_joinstyle': 'round', 'text.parse_math': False})   # '$' in labels is a dollar sign, never math

st.set_page_config(page_title='MVP Strategies', layout='centered', initial_sidebar_state='collapsed')
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap');
:root { --paper:#ffffff; --ink:#101924; --muted:#555b63; --hairline:#d7d7d7; --panel:#f5f5f5; --inputline:#7c8186;
  --negative:#8c2d2b; --serif:"Newsreader",Georgia,serif; --sans:"IBM Plex Sans",system-ui,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,monospace; }
html, body, .stApp, .stApp *:where(:not([data-testid="stIconMaterial"])) { font-family: var(--sans) !important; color: var(--ink); }
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
.items > li { display: grid; grid-template-columns: 28px 1fr; margin: 0; padding: 9px 0; border-top: 1px solid var(--hairline); }
.items > li:last-child { border-bottom: 1px solid var(--hairline); }
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
table.plain span.win { display: none; }

/* form */
[data-testid="stForm"] { background: var(--panel); border: 1px solid var(--hairline); border-top: 1px solid var(--ink);
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

/* charts */
p.chart-head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; gap: 4px 16px;
  margin: 24px 0 0; padding-bottom: 6px; border-bottom: 1px solid var(--ink); }
p.chart-head b { font-size: 12px !important; font-weight: 500; margin-right: auto; }
p.chart-head span { display: inline-flex; align-items: center; gap: 6px; font-size: 11.5px !important; color: var(--muted) !important; }
p.chart-head i { display: inline-block; width: 14px; height: 2px; }

/* team */
table.team, table.team tr, table.team td { border: 0 !important; background: none !important; }
table.team { width: calc(100% + 32px); table-layout: fixed; border-collapse: separate !important; border-spacing: 16px 0;
  margin: 6px -16px; }
table.team td { text-align: left; vertical-align: top; padding: 0 !important; white-space: normal; }
div.ph { width: 100%; aspect-ratio: 4/5; margin: 0 0 8px; background: var(--panel); border: 1px solid var(--hairline);
  display: grid; place-items: center; font-family: var(--mono) !important; font-size: 12px; letter-spacing: .08em; color: var(--muted) !important; }
table.team b { font-size: 13.5px; font-weight: 600; }
div.ph.sm { width: 64px; aspect-ratio: 4/5; margin: 0; }
div.ph.off, p.off { opacity: .35; }
div.ph.big { aspect-ratio: 4/5; max-width: 320px; font-size: 18px; margin-bottom: 14px; }
p.mname { font-family: var(--serif) !important; font-size: 28px !important; line-height: 1.2; margin: 0; }
.st-key-teamlist [data-testid="stVerticalBlock"] { gap: 0 !important; }
.st-key-teamlist p.note { margin: 0 !important; }
p.bio { max-width: 52ch; border-top: 1px solid var(--hairline); padding-top: 12px; margin-top: 14px; }
table.team i { font-style: normal; font-size: 12px !important; color: var(--muted) !important; display: block; }

/* investor account */
table.kpi { width: 100%; border-collapse: collapse; table-layout: fixed; margin: 0 0 8px; }
table.kpi, table.kpi tr, table.kpi td { border: 0 !important; background: none !important; }
table.kpi td { padding: 0 16px 0 0; vertical-align: top; }
table.kpi span.k { display: block; font-size: 11px !important; letter-spacing: .04em; color: var(--muted) !important; }
table.kpi span.v { display: block; font-family: var(--mono) !important; font-size: 22px !important; font-weight: 500; }
table.kpi span.v.neg { color: var(--negative) !important; }

@media (max-width: 640px) {
  h1.bh { font-size: 46px !important; } p.long { font-size: 17px !important; } .stApp h3 { font-size: 28px !important; }
  table.team { display: block; width: 100%; margin: 6px 0; } table.team tbody, table.team tr { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px 12px; }
  table.team td { padding: 0; }
  table.plain th.wcol, table.plain td.wcol { display: none; }
  table.plain span.win { display: block; font-family: var(--mono) !important; font-size: 11px !important; color: var(--muted) !important; }
  [data-testid="stColumn"]:has(.st-key-teamlist) { display: none !important; }
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


def chart(title, series, kind='growth', h=2.9):
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
    else:                                                          # dollar values, linear
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


@st.cache_data(ttl=86400, show_spinner='loading prices from yahoo finance ...')
def get_prices():
    return load_prices()


@st.cache_data(show_spinner='running backtest ...')
def get_results(**kw):
    return run(get_prices(), Params(**kw))


@st.cache_data(ttl=3600, show_spinner='loading live prices ...')
def get_live():
    px = load_live()
    return run(px, Params(start='2026-01-01', end=str(px.index[-1].date()))), px


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
    items([('volatility-targeted equity.', 'we hold the s&amp;p 500 and scale exposure with realized volatility: more in '
            'calm markets, less in stressed ones. it gets whatever risk budget the spread sleeve does not use.'),
           ('defensive sector spread.', 'a beta-neutral relative-value position between the two most defensive us '
            'equity sectors, which trades the mean reversion of temporary dislocations.')])
    html('<p>the two sleeves earn their returns from different sources, so the combined portfolio has outperformed '
         'either one on its own, with lower volatility and drawdowns than the s&amp;p 500.</p>')


def performance():
    heading('performance')
    p = st.session_state.get('params', DEFAULTS)
    with st.form('assumptions'):
        c = st.columns(3)
        tv = c[0].number_input('volatility target (% p.a.)', 5.0, 30.0, p.target_vol * 100, 1.0, format='%.0f')
        lev = c[1].number_input('max equity exposure (x)', 1.0, 3.0, p.max_lev, 0.25)
        cost = c[2].number_input('trading cost (bp per unit traded)', 0, 100, round(p.cost * 1e4), 5)
        size = c[0].number_input('spread size per leg, avg (x)', 0.25, 2.0, p.pair_size or DEFAULTS.pair_size, 0.25)
        fin = c[1].number_input('financing spread over t-bills (bp p.a.)', 0, 500, round(p.fin_spread * 1e4), 25)
        fee = c[2].number_input('borrow fee on shorts (bp p.a.)', 0, 500, round(p.short_fee * 1e4), 25)
        z_in = c[0].number_input('spread entry threshold (|z|)', 1.0, 4.0, p.z_in, 0.5, format='%.1f')
        years = list(range(2006, 2026))
        y0 = c[1].selectbox('start year', years[:-1], years.index(int(p.start[:4])))
        y1 = c[2].selectbox('end year', years[1:], years[1:].index(int(p.end[:4])))
        b = st.columns([4, 2, 1], vertical_alignment='center')
        pair_on = b[0].checkbox('include sector spread', p.pair_size > 0)
        reset = b[1].form_submit_button('reset to notebook defaults', type='tertiary')
        go = b[2].form_submit_button('run', type='primary')
    if reset:
        st.session_state['params'] = DEFAULTS
        st.rerun()
    if go:
        if y1 <= y0:
            note('end year must be after start year.')
            st.stop()
        st.session_state['params'] = Params(start=f'{y0}-01-01', end=f'{y1}-12-31', target_vol=tv / 100, max_lev=lev,
                                            cost=cost / 1e4, fin_spread=fin / 1e4, short_fee=fee / 1e4, z_in=z_in,
                                            pair_size=size if pair_on else 0.0)
        st.rerun()
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
    note('s&amp;p 500 peak-to-trough episodes, total return over each window.')
    window = lambda r, a, b: (1 + r.loc[a:b].iloc[1:]).prod() - 1
    span = lambda a, b: f'{pd.Timestamp(a):%b %Y} &rarr; {pd.Timestamp(b):%b %Y}'.lower()
    rows = ''.join(f'<tr><td class="label">{name}<span class="win">{span(a, b)}</span></td><td class="dim wcol">{span(a, b)}</td>'
                   f'{td(window(bench, a, b))}{td(window(bt.net, a, b), cls="em")}{td(window(res["spy_only"].net, a, b))}'
                   f'{td(window(res["pair_only"].net, a, b))}</tr>'
                   for name, a, b in CRISES if pd.Timestamp(a) >= bt.index[0] and pd.Timestamp(b) <= bt.index[-1])
    if not rows:
        note('no episode falls inside the selected years.')
        return
    html(f'<table class="plain"><tr><th>episode</th><th class="wcol">window</th><th>s&amp;p 500 tr</th><th>portfolio</th>'
         f'<th>equity sleeve</th><th>spread sleeve</th></tr>{rows}</table>')


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
    items([('risk budget.', f'one {p.target_vol:.0%} volatility budget for the whole portfolio. the spread sleeve\'s realized '
            'volatility (63 trading days) is taken out first; the equity sleeve gets the rest.'),
           ('equity sleeve.', f'at each month-end, exposure = remaining budget / spy realized volatility (21 trading days, '
            f'annualized), capped at {p.max_lev:.2f}x. idle cash earns the t-bill rate; leverage is financed at t-bill + '
            f'{p.fin_spread * 1e4:.0f} bp.'),
           ('spread sleeve.', f'at each year-end, select the two lowest-beta sector etfs vs spy (trailing 1y). daily z-score '
            f'of the log price ratio vs its 60-day mean: enter at |z| &gt; {p.z_in:g} (long cheap, short rich), exit at '
            f'|z| &lt; {p.z_out:g}. legs are sized beta-neutral from the same prior-year betas, {2 * p.pair_size:.2f}x gross. '
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
    sel = st.session_state.get('member', 0)
    html(f'<style>.st-key-m{sel} button * {{ font-weight: 600 !important; color: var(--ink) !important; }}'
         f'[class*="st-key-m"]:not(.st-key-m{sel}) button * {{ color: var(--muted) !important; }}'
         '[class*="st-key-m"] button * { text-decoration: none !important; font-size: 15px !important; }</style>')
    left, right = st.columns([2, 3], gap='large')
    with left, st.container(height=520, border=False, key='teamlist'):
        for k, (n, t) in enumerate(TEAM):
            c1, c2 = st.columns([1, 2], vertical_alignment='center')
            c1.markdown(f'<div class="ph sm {"" if k == sel else "off"}">{initials(n)}</div>', unsafe_allow_html=True)
            if c2.button(n, key=f'm{k}', type='tertiary'):
                st.session_state['member'] = k
                st.rerun()
            c2.markdown(f'<p class="note {"" if k == sel else "off"}">{t}</p>', unsafe_allow_html=True)
    with right:
        n, t = TEAM[sel]
        html(f'<div class="ph big">{initials(n)}</div><p class="mname">{n}</p><p class="note">{t}</p><p class="bio">{BIO}</p>')
        prev, nxt = st.columns(2)
        if prev.button('← previous', key='prev', type='tertiary'):
            st.session_state['member'] = (sel - 1) % len(TEAM); st.rerun()
        if nxt.button('next →', key='next', type='tertiary'):
            st.session_state['member'] = (sel + 1) % len(TEAM); st.rerun()


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
    try:
        live, px = get_live()
    except Exception:
        note('live data unavailable right now (yahoo rate limit). reload in a minute.')
        return
    lb, lbench = live['bt'], live['bench_d']
    value = DEMO_DEPOSIT * (1 + lb.net).cumprod()
    bench_value = DEMO_DEPOSIT * (1 + lbench).cumprod()
    profit = value.iloc[-1] - DEMO_DEPOSIT
    note(f'demo account &middot; ${DEMO_DEPOSIT:,.0f} invested at the 31 dec 2025 close &middot; '
         f'as of the {lb.index[-1]:%d %b %Y} close'.lower())
    kpi = lambda k, v, cls='': f'<td><span class="k">{k}</span><span class="v {cls}">{v}</span></td>'
    pr, neg = num(profit, 'usd')
    html('<table class="kpi"><tr>' + kpi('balance', num(value.iloc[-1], 'usd')[0]) + kpi('profit', pr, neg)
         + kpi('return', num(value.iloc[-1] / DEMO_DEPOSIT - 1)[0], neg)
         + kpi('s&amp;p 500 tr, same deposit', num(bench_value.iloc[-1], 'usd')[0]) + '</tr></table>')
    chart('account value', [('portfolio (net)', pd.concat([pd.Series(DEMO_DEPOSIT, index=[pd.Timestamp('2025-12-31')]), value]), S1),
                            ('s&amp;p 500 tr', pd.concat([pd.Series(DEMO_DEPOSIT, index=[pd.Timestamp('2025-12-31')]), bench_value]), S2)],
          kind='line')

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
    p0 = Params(start=DEMO_START, end=str(lb.index[-1].date()))
    d0 = px.index[px.index.get_loc(lb.index[0]) - 1]                # initial purchase at the last close of 2025
    P = pair_targets(px, p0)[0] * p0.pair_size
    w0 = pd.Series([spy_exposure(px, p0, pair_returns(px, P)).loc[d0], *P.loc[d0]], index=ASSETS)
    W = pd.concat([w0.to_frame(d0).T, W])
    gross = pd.concat([pd.Series(0.0, index=[d0]), lb.gross])
    V = pd.concat([pd.Series(DEMO_DEPOSIT, index=[d0]), value])
    eq_before = V.shift(1).fillna(DEMO_DEPOSIT) * (1 + gross)          # equity at each close, before that day's costs
    drift = W.shift(1).fillna(0) * (1 + px[ASSETS].pct_change().loc[W.index]) / (1 + gross).values[:, None]
    trades = ((W - drift) * eq_before.values[:, None]).stack()
    trades = trades[trades.abs() > 0.005].iloc[::-1]
    note(f'{len(trades)} trades, newest first, including the initial purchase; '
         f'costs of {DEFAULTS.cost * 1e4:.0f} bp per unit traded are deducted from the account.')
    rows = ''.join(f'<tr><td>{d:%d %b %Y}'.lower() + f'</td><td class="label">{a.lower()}</td><td class="dim">'
                   f'{"buy" if v > 0 else "sell"}</td>{td(abs(v), "usd")}</tr>' for (d, a), v in trades.items())
    html(f'<table class="plain compact"><tr><th>date</th><th>asset</th><th>side</th><th>amount</th></tr>{rows}</table>')
    if st.button('log out', type='tertiary'):
        st.session_state['investor'] = False
        st.rerun()


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
nav.run()

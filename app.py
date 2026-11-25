from dataclasses import asdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from strategy import Params, load_prices, run, wealth

REPO = 'https://github.com/Ben10Nova/FinancialModellingGroupN'
COLAB = 'https://colab.research.google.com/github/Ben10Nova/FinancialModellingGroupN/blob/main/vol-control_pair_v1.ipynb'
DEFAULTS = Params()

st.set_page_config(page_title='Group N Capital - Official Home Page', layout='centered')
st.markdown("""
<style>
html, body, .stApp, .stApp * { font-family: "Times New Roman", Times, serif !important; color: #000; }
.stApp { background: #fff; }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], footer, #MainMenu { display: none !important; }
.block-container { max-width: 780px; padding-top: 2rem; }
a, a * { color: #0000EE !important; text-decoration: underline !important; }
a:visited, a:visited * { color: #551A8B !important; }
h1.bh { text-align: center; font-size: 30px; font-weight: bold; margin: 0; letter-spacing: .5px; }
p.addr { text-align: center; margin: 2px 0; font-size: 17px; }
h2.bh { font-size: 21px; font-weight: bold; margin: 28px 0 6px 0; padding: 0; }
p, li, td, th, label { font-size: 17px !important; line-height: 1.35; }
.stApp hr { border: 0 !important; border-top: 1px solid #000 !important; background: none !important; margin: 18px 0 !important; }
table.plain { border-collapse: collapse; margin: 6px 0 10px 0; }
table.plain td, table.plain th { border: 1px solid #000; padding: 2px 10px; text-align: right; font-weight: normal; }
table.plain th { font-weight: bold; text-align: center; }
table.plain td:first-child { text-align: left; }
table.links, table.links tr, table.links td { border: 0 !important; background: none !important; }
table.links td { vertical-align: top; padding: 0 30px 0 0; }
table.links ul { margin: 0; padding-left: 22px; }
[data-baseweb="input"], [data-baseweb="select"] > div, input { border-radius: 0 !important; background: #fff !important; }
[data-baseweb="input"] { border: 2px inset #c0c0c0 !important; }
[data-testid="stNumberInputStepDown"], [data-testid="stNumberInputStepUp"] { border-radius: 0 !important; background: #e0e0e0 !important; }
.stButton button, .stFormSubmitButton button {
  border-radius: 0 !important; background: #e0e0e0 !important; border: 2px outset #f5f5f5 !important;
  padding: 1px 14px !important; min-height: 0 !important; box-shadow: none !important; }
[data-testid="stForm"] { border: 1px solid #000; border-radius: 0; padding: 14px 16px; }
.stApp p.fine, .stApp p.fine * { font-size: 14px !important; }
</style>
""", unsafe_allow_html=True)

html = lambda s: st.markdown(s, unsafe_allow_html=True)
h2 = lambda anchor, text: html(f'<h2 class="bh" id="{anchor}">{text}</h2>')
pct = lambda x: f'{x + 0.0:.1%}'.replace('-0.0%', '0.0%')
FMT = {'Ann. avg return': pct, 'Ann. volatility': pct, 'Alpha (ann.)': pct, 'Max drawdown (monthly)': pct}


def table_html(df, fmt=lambda row, v: v):
    head = ''.join(f'<th>{c}</th>' for c in [df.index.name or ''] + list(df.columns))
    body = ''.join('<tr><td>{}</td>{}</tr>'.format(i, ''.join(f'<td>{fmt(i, v)}</td>' for v in row))
                   for i, row in zip(df.index, df.values))
    return f'<table class="plain"><tr>{head}</tr>{body}</table>'


def metric_fmt(row, v):
    if pd.isna(v): return '–'
    return FMT.get(row, lambda x: f'{x:.2f}')(v)


def chart(series, ylabel, log=False, h=3.2, legend_loc='upper left'):
    plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'Liberation Serif', 'DejaVu Serif'],
                         'font.size': 10})
    fig, ax = plt.subplots(figsize=(7.6, h), dpi=150)
    styles = [dict(c='black', lw=1.4), dict(c='black', lw=1, ls='--'), dict(c='grey', lw=1), dict(c='grey', lw=1, ls=':')]
    for (name, s), style in zip(series.items(), styles):
        ax.plot(s.index, s.values, label=name, **style)
    if log: ax.set_yscale('log')
    ax.set_ylabel(ylabel)
    for side in ['top', 'right']: ax.spines[side].set_visible(False)
    ax.legend(frameon=False, loc=legend_loc)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


@st.cache_data(ttl=86400, show_spinner='Fetching prices from Yahoo Finance ...')
def get_prices():
    return load_prices()


@st.cache_data(show_spinner='Running the backtest ...')
def get_results(**kw):
    return run(get_prices(), Params(**kw))


# ---------------------------------------------------------------- masthead
html('<h1 class="bh">GROUP N CAPITAL</h1>')
html('<p class="addr">Nova School of Business and Economics &middot; Carcavelos, Portugal</p>')
html('<p class="addr">Official Home Page</p><hr>')
html(f"""<table class="links"><tr>
<td><ul><li><a href="#message">A Message to Investors</a></li><li><a href="#assumptions">Change the Assumptions</a></li>
<li><a href="#performance">Performance vs. the S&amp;P 500</a></li><li><a href="#annual">Annual Results, 2006 to 2025</a></li></ul></td>
<td><ul><li><a href="#sources">Where the Return Comes From</a></li><li><a href="#rules">The Rules</a></li>
<li><a href="#risks">Risks and Limitations</a></li><li><a href="{REPO}">Source Code</a> and <a href="{COLAB}">Notebook</a></li></ul></td>
</tr></table><hr>""")

# ---------------------------------------------------------------- message
h2('message', 'A Message to Investors')
html("""<p>Our portfolio does two simple things. First, it owns the S&amp;P 500, but holds more of it when markets
are calm and less when they are stormy. Second, it runs a small market-neutral trade between the two most
defensive sectors of the stock market, betting that temporary gaps between them close. The two parts earn their
money in different ways, which is why together they have done better than either alone.</p>
<p>All figures below are a backtest from January 2006 to December 2025, net of trading, borrowing and shorting
costs. A backtest is not a promise.</p>""")

# ---------------------------------------------------------------- assumptions
h2('assumptions', 'Change the Assumptions')
if st.button('Restore notebook defaults'):
    for k in list(st.session_state): del st.session_state[k]
    st.rerun()
with st.form('assumptions'):
    c1, c2 = st.columns(2)
    tv = c1.number_input('Volatility target (% per year)', 5.0, 30.0, DEFAULTS.target_vol * 100, 1.0, format='%.0f', key='tv')
    lev = c1.number_input('Maximum S&P 500 exposure (x capital)', 1.0, 3.0, DEFAULTS.max_lev, 0.25, key='lev')
    cost = c1.number_input('Trading cost (basis points per trade)', 0, 100, int(DEFAULTS.cost * 1e4), 5, key='cost')
    y0 = c1.selectbox('First year', list(range(2006, 2025)), 0, key='y0')
    pair_on = c2.checkbox('Include the sector pair trade', True, key='pair_on')
    size = c2.number_input('Pair size per leg (x capital)', 0.25, 2.0, DEFAULTS.pair_size, 0.25, key='size')
    fin = c2.number_input('Borrowing cost over T-bills (bp per year)', 0, 500, int(DEFAULTS.fin_spread * 1e4), 25, key='fin')
    y1 = c2.selectbox('Last year', list(range(2007, 2026)), 18, key='y1')
    st.form_submit_button('Submit')

if y1 <= y0:
    html('<p><b>The last year must come after the first year.</b></p>')
    st.stop()

params = dict(asdict(DEFAULTS), start=f'{y0}-01-01', end=f'{y1}-12-31', target_vol=tv / 100, max_lev=lev,
              cost=cost / 1e4, fin_spread=fin / 1e4, pair_size=size if pair_on else 0.0)
is_default = Params(**params) == DEFAULTS
try:
    res = get_results(**params)
except RuntimeError as e:
    html(f'<p><b>{e}</b></p>')
    st.stop()

html('<p><i>These are the notebook defaults. Every number matches the prospectus.</i></p>' if is_default else
     '<p><i>Modified assumptions. Numbers differ from the prospectus.</i></p>')

# ---------------------------------------------------------------- performance
bt, bench = res['bt'], res['bench_d']
w_s, w_b = wealth(bt.net), wealth(bench)
h2('performance', 'Performance vs. the S&amp;P 500')
html(f'<p>One dollar invested on 1 January {y0} grew to <b>${w_s.iloc[-1]:,.2f}</b> in our portfolio, against '
     f'<b>${w_b.iloc[-1]:,.2f}</b> in the S&amp;P 500 with dividends reinvested.</p>')
html(table_html(res['table'].rename(columns={'Strategy (net)': 'Group N (net)', 'S&P 500 TR': 'S&amp;P 500'}), metric_fmt))
chart({'Group N (net of costs)': w_s, 'S&P 500 total return': w_b}, 'Growth of $1 (log scale)', log=True)
chart({'Group N': w_s / w_s.cummax() - 1, 'S&P 500': w_b / w_b.cummax() - 1}, 'Fall from previous peak', h=2.4, legend_loc='lower right')

# ---------------------------------------------------------------- annual table (Buffett letter style)
h2('annual', f'Annual Results, {y0} to {y1}')
yr = res['yearly']
n = len(yr)
cagr = lambda r: (1 + r).prod() ** (1 / n) - 1
rows = ''.join(f'<tr><td>{y}</td><td>{r.Strategy:.1%}</td><td>{r["S&P 500 TR"]:.1%}</td><td>{r["Pair held"]}</td></tr>'
               for y, r in yr.iterrows())
html(f"""<table class="plain"><tr><th>Year</th><th>Annual Percentage Change<br>in Group N</th>
<th>Annual Percentage Change<br>in S&amp;P 500<br>with Dividends Included</th><th>Pair Held</th></tr>{rows}
<tr><td>Compounded Annual Gain</td><td>{cagr(yr.Strategy):.1%}</td><td>{cagr(yr['S&P 500 TR']):.1%}</td><td></td></tr>
<tr><td>Overall Gain</td><td>{(1 + yr.Strategy).prod() - 1:,.0%}</td><td>{(1 + yr['S&P 500 TR']).prod() - 1:,.0%}</td><td></td></tr>
</table>""")

# ---------------------------------------------------------------- attribution
h2('sources', 'Where the Return Comes From')
html('<p>The same backtest run three ways: the S&amp;P 500 part alone, the pair trade alone (spare cash in '
     'T-bills), and both together.</p>')
html(table_html(res['sleeves'], metric_fmt))
chart({'Both together': wealth(bt.net), 'S&P 500 part alone': wealth(res['spy_only'].net),
       'Pair trade alone': wealth(res['pair_only'].net)}, 'Growth of $1 (log scale)', log=True)
html(f'<p>At the end of {y1} the rule would hold <b>{res["exposure_now"]:.2f}x</b> capital in the S&amp;P 500, '
     f'and the pair for {y1 + 1} is <b>{"/".join(res["pair_now"])}</b>.</p>')

# ---------------------------------------------------------------- rules, risks
h2('rules', 'The Rules')
html(f"""<ol>
<li><b>S&amp;P 500 part.</b> On the last trading day of each month, measure how much SPY moved over the past 21
trading days (annualised volatility). Hold {tv:.0f}% divided by that volatility in SPY, at most {lev:.2f}x capital.
Spare cash earns the T-bill rate; borrowed cash costs the T-bill rate plus {fin} bp.</li>
<li><b>Pair trade.</b> On the last trading day of each year, pick the two sector funds with the lowest beta to the
S&amp;P 500 over that year. Each day, compare their price ratio with its 60-day average. When the gap exceeds two
standard deviations, buy the cheap fund and short the expensive one ({size:.2f}x capital each). Close when the gap
falls below half a standard deviation.</li>
<li><b>No peeking.</b> Every decision uses closing prices of that day or earlier and starts earning the next day.</li>
<li><b>Costs.</b> {cost} bp per unit traded, plus 0.25% per year on short positions.</li></ol>""")

h2('risks', 'Risks and Limitations')
html("""<ul>
<li>Leverage and short selling are required; total positions can exceed four times capital.</li>
<li>The worst fall from a peak was about a third of the portfolio's value.</li>
<li>The pair rule was formulated after we saw that defensive-sector pairs had worked; picking pairs any other way
did not make money in our tests.</li>
<li>Monthly resizing reacts slowly to sudden crashes, and the strategy holds little stock during sharp rebounds.</li>
<li>Results rely on Yahoo Finance data and fixed cost assumptions. Taxes are ignored.</li></ul><hr>""")

# ---------------------------------------------------------------- footer
html(f"""<p class="fine">Data: Yahoo Finance (prices adjusted for dividends and splits; S&amp;P 500 total-return
index ^SP500TR; 13-week T-bill ^IRX). Statistics use monthly returns; means &times;12, volatilities &times;&radic;12;
beta is not annualised. Full method and every number: <a href="{COLAB}">the notebook</a> and
<a href="{REPO}">the source code</a>.</p>
<p class="fine">If you have comments about our web page, you may write to us at the address above. Our
corporate office consists of a handful of students and one laptop, so please do not expect a reply.</p>
<p class="fine">This page describes a hypothetical backtest prepared for a university course. It is not
investment advice. Copyright &copy; 2026 Group N.</p>""")

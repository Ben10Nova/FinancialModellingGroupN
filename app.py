from dataclasses import asdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from strategy import Params, load_live, load_prices, monthly, run, wealth

FUND = '[fund name]'
REPO = 'https://github.com/Ben10Nova/FinancialModellingGroupN'
COLAB = 'https://colab.research.google.com/github/Ben10Nova/FinancialModellingGroupN/blob/main/vol-control_pair_v1.ipynb'
DEFAULTS = Params()
CRISES = [('global financial crisis', '2007-10-09', '2009-03-09'), ('euro debt crisis', '2011-04-29', '2011-10-03'),
          ('q4 2018 selloff', '2018-09-20', '2018-12-24'), ('covid crash', '2020-02-19', '2020-03-23'),
          ('2022 rate shock', '2022-01-03', '2022-10-12')]          # s&p 500 peak and trough closes
TEAM = [('lucas s', '[title]'), ('ben s', '[title]'), ('katha g', '[title]'), ('noah vr', '[title]'), ('henrik t', '[title]'),
        ('chris w', '[title]')]

st.set_page_config(page_title=FUND, layout='centered')
st.markdown("""
<style>
html, body, .stApp, .stApp * { font-family: "Times New Roman", Times, serif !important; color: #000; }
.stApp { background: #fff; }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], footer, #MainMenu { display: none !important; }
[data-testid="stHeaderActionElements"] { display: none !important; }
.block-container { max-width: 780px; padding-top: 2rem; }
a, a * { color: #0000EE !important; text-decoration: underline !important; }
a:visited, a:visited * { color: #551A8B !important; }
h1.bh { text-align: center; font-size: 30px; font-weight: bold; margin: 0; }
p.addr { text-align: center; margin: 2px 0; }
.stApp h3 { font-size: 21px !important; font-weight: bold !important; text-decoration: underline; padding: 22px 0 2px 0 !important; }
p, li, td, th, label { font-size: 17px !important; line-height: 1.35; }
.stApp hr { border: 0 !important; border-top: 1px solid #000 !important; background: none !important; margin: 18px 0 !important; }
table.plain { border-collapse: collapse; margin: 6px 0 10px 0; }
table.plain td, table.plain th { border: 1px solid #000; padding: 2px 10px; text-align: right; font-weight: normal; }
table.plain th { font-weight: bold; text-align: center; }
table.plain td:first-child { text-align: left; }
table.links, table.links tr, table.links td { border: 0 !important; background: none !important; }
table.links td { vertical-align: top; padding: 0 30px 0 0; }
table.links ul { margin: 0; padding-left: 22px; }
table.stress td { white-space: nowrap; }
table.team, table.team tr { border: 0 !important; background: none !important; } table.team { width: 100%; table-layout: fixed; margin: 6px 0; }
table.team td { border: 0 !important; text-align: center; padding: 0 4px; vertical-align: top; white-space: nowrap; }
@media (max-width: 500px) { table.team td, table.team td * { font-size: 13px !important; } }
div.ph { width: 100%; max-width: 90px; aspect-ratio: 1; margin: 0 auto 4px auto; background: #e0e0e0; border: 1px solid #000; }
[data-baseweb="input"], [data-baseweb="select"] > div, input { border-radius: 0 !important; background: #fff !important; }
[data-baseweb="input"] { border: 2px inset #c0c0c0 !important; }
[data-testid="stNumberInputStepDown"], [data-testid="stNumberInputStepUp"] { border-radius: 0 !important; background: #e0e0e0 !important; }
.stButton button, .stFormSubmitButton button, .stDownloadButton button {
  border-radius: 0 !important; background: #e0e0e0 !important; border: 2px outset #f5f5f5 !important;
  padding: 1px 14px !important; min-height: 0 !important; box-shadow: none !important; }
[data-testid="stForm"] { border: 1px solid #000; border-radius: 0; padding: 14px 16px; }
.stApp p.fine, .stApp p.fine * { font-size: 14px !important; }
</style>
""", unsafe_allow_html=True)

html = lambda s: st.markdown(s, unsafe_allow_html=True)
pct = lambda x: f'{x + 0.0:.1%}'.replace('-0.0%', '0.0%')
ROWS = {'Ann. avg return': 'ann. return', 'Ann. volatility': 'ann. volatility', 'Sharpe ratio': 'sharpe ratio',
        'Alpha (ann.)': 'alpha (ann.)', 'Alpha t-stat': 'alpha t-stat', 'Beta': 'beta',
        'Information ratio': 'information ratio', 'Max drawdown (monthly)': 'max drawdown (monthly)'}
PCT_ROWS = {'ann. return', 'ann. volatility', 'alpha (ann.)', 'max drawdown (monthly)'}


def section(anchor, title):
    st.subheader(f'{title}:', anchor=anchor)


def table_html(df):
    df = df.rename(index=ROWS)
    fmt = lambda row, v: '–' if pd.isna(v) else (pct(v) if row in PCT_ROWS else f'{v:.2f}')
    head = ''.join(f'<th>{c}</th>' for c in [''] + list(df.columns))
    body = ''.join('<tr><td>{}</td>{}</tr>'.format(i, ''.join(f'<td>{fmt(i, v)}</td>' for v in row))
                   for i, row in zip(df.index, df.values))
    return f'<table class="plain"><tr>{head}</tr>{body}</table>'


def chart(series, ylabel, log=False, h=3.2, legend_loc='upper left'):
    plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'Liberation Serif', 'DejaVu Serif'],
                         'font.size': 10})
    fig, ax = plt.subplots(figsize=(7.6, h), dpi=150)
    styles = [dict(c='black', lw=1.4), dict(c='black', lw=1, ls='--'), dict(c='grey', lw=1)]
    for (name, s), style in zip(series.items(), styles):
        ax.plot(s.index, s.values, label=name, **style)
    if log: ax.set_yscale('log')
    ax.set_ylabel(ylabel)
    for side in ['top', 'right']: ax.spines[side].set_visible(False)
    ax.legend(frameon=False, loc=legend_loc)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


@st.cache_data(ttl=86400, show_spinner='loading prices from yahoo finance ...')
def get_prices():
    return load_prices()


@st.cache_data(ttl=3600, show_spinner='loading live prices ...')
def get_live():
    px = load_live()
    return run(px, Params(start='2026-01-01', end=str(px.index[-1].date())))


@st.cache_data(show_spinner='running backtest ...')
def get_results(**kw):
    return run(get_prices(), Params(**kw))


# ---------------------------------------------------------------- masthead
html(f'<h1 class="bh">{FUND}</h1>')
html('<p class="addr">2270 financial modeling &middot; nova sbe</p><hr>')
html(f"""<table class="links"><tr>
<td><ul><li><a href="#thesis">thesis</a></li><li><a href="#assumptions">assumptions</a></li>
<li><a href="#performance">performance</a></li><li><a href="#annual-returns">annual returns</a></li>
<li><a href="#stress-tests">stress tests</a></li></ul></td>
<td><ul><li><a href="#attribution">attribution</a></li><li><a href="#live-2026">live: 2026</a></li>
<li><a href="#rules">rules</a></li><li><a href="#risks">risks</a></li><li><a href="#team">team</a></li>
<li><a href="{REPO}">source code</a> &middot; <a href="{COLAB}">notebook</a></li></ul></td>
</tr></table><hr>""")

# ---------------------------------------------------------------- thesis
section('thesis', 'thesis')
html("""<p>two return streams, built to be uncorrelated, sharing one 15% risk budget:</p>
<p>1: volatility-targeted equity. we hold the s&amp;p 500 and scale exposure with realized volatility: more in calm
markets, less in stressed ones. it gets whatever risk budget the spread sleeve does not use.</p>
<p>2: defensive sector spread. a beta-neutral relative-value position between the two most defensive us equity
sectors, which trades the mean reversion of temporary dislocations.</p>
<p>the two sleeves earn their returns from different sources, so the combined portfolio has outperformed either one
on its own, with lower volatility and drawdowns than the s&amp;p 500.</p>""")

# ---------------------------------------------------------------- assumptions
section('assumptions', 'assumptions')
if st.button('reset to notebook defaults'):
    for k in list(st.session_state): del st.session_state[k]
    st.rerun()
with st.form('assumptions'):
    c1, c2 = st.columns(2)
    tv = c1.number_input('volatility target (% p.a.)', 5.0, 30.0, DEFAULTS.target_vol * 100, 1.0, format='%.0f', key='tv')
    lev = c1.number_input('max equity exposure (x)', 1.0, 3.0, DEFAULTS.max_lev, 0.25, key='lev')
    cost = c1.number_input('trading cost (bp per unit traded)', 0, 100, int(DEFAULTS.cost * 1e4), 5, key='cost')
    y0 = c1.selectbox('start year', list(range(2006, 2025)), 0, key='y0')
    pair_on = c2.checkbox('include sector spread', True, key='pair_on')
    size = c2.number_input('spread size per leg, avg (x)', 0.25, 2.0, DEFAULTS.pair_size, 0.25, key='size')
    fin = c2.number_input('financing spread over t-bills (bp p.a.)', 0, 500, int(DEFAULTS.fin_spread * 1e4), 25, key='fin')
    y1 = c2.selectbox('end year', list(range(2007, 2026)), 18, key='y1')
    st.form_submit_button('run')

if y1 <= y0:
    html('<p><b>end year must be after start year.</b></p>')
    st.stop()

params = dict(asdict(DEFAULTS), start=f'{y0}-01-01', end=f'{y1}-12-31', target_vol=tv / 100, max_lev=lev,
              cost=cost / 1e4, fin_spread=fin / 1e4, pair_size=size if pair_on else 0.0)
try:
    res = get_results(**params)
except RuntimeError as e:
    html(f'<p><b>{e}</b></p>')
    st.stop()

html('<p><i>notebook defaults: matches the prospectus.</i></p>' if Params(**params) == DEFAULTS else
     '<p><i>modified assumptions: differs from the prospectus.</i></p>')

# ---------------------------------------------------------------- performance
bt, bench = res['bt'], res['bench_d']
w_s, w_b = wealth(bt.net), wealth(bench)
section('performance', 'performance')
html(f'<p>$1 invested in january {y0}: <b>${w_s.iloc[-1]:,.2f}</b> (s&amp;p 500 tr: <b>${w_b.iloc[-1]:,.2f}</b>). '
     f'net of trading, financing and borrow costs.</p>')
html(table_html(res['table'].rename(columns={'Strategy (net)': 'portfolio (net)', 'S&P 500 TR': 's&amp;p 500 tr'})))
chart({'portfolio (net)': w_s, 's&p 500 tr': w_b}, 'growth of $1 (log)', log=True)
chart({'portfolio': w_s / w_s.cummax() - 1, 's&p 500 tr': w_b / w_b.cummax() - 1}, 'drawdown', h=2.4,
      legend_loc='lower right')
rf_d = (get_prices()['^IRX'] / 100 / 252).shift(1).loc[bt.index]
csv = monthly(pd.DataFrame({'portfolio_net': bt.net, 'portfolio_gross': bt.gross, 'equity_sleeve': res['spy_only'].net,
                            'spread_sleeve': res['pair_only'].net, 'sp500_tr': bench, 'rf': rf_d}))
st.download_button('download monthly returns (csv)', csv.to_csv(index_label='month', float_format='%.6f'),
                   file_name=f'monthly_returns_{y0}_{y1}.csv', mime='text/csv')

# ---------------------------------------------------------------- annual returns
section('annual-returns', 'annual returns')
yr = res['yearly']
cagr = lambda r: (1 + r).prod() ** (1 / len(yr)) - 1
rows = ''.join(f'<tr><td>{y}</td><td>{r.Strategy:.1%}</td><td>{r["S&P 500 TR"]:.1%}</td><td>{r["Pair held"].lower()}</td></tr>'
               for y, r in yr.iterrows())
html(f"""<table class="plain"><tr><th>year</th><th>portfolio</th><th>s&amp;p 500 tr</th><th>spread pair</th></tr>{rows}
<tr><td>cagr</td><td>{cagr(yr.Strategy):.1%}</td><td>{cagr(yr['S&P 500 TR']):.1%}</td><td></td></tr>
<tr><td>cumulative</td><td>{(1 + yr.Strategy).prod() - 1:,.0%}</td><td>{(1 + yr['S&P 500 TR']).prod() - 1:,.0%}</td><td></td></tr>
</table>""")

# ---------------------------------------------------------------- stress tests
section('stress-tests', 'stress tests')
html('<p>s&amp;p 500 peak-to-trough episodes, total return over each window.</p>')
window = lambda r, a, b: (1 + r.loc[a:b].iloc[1:]).prod() - 1
span = lambda a, b: f'{pd.Timestamp(a):%b %Y} &rarr; {pd.Timestamp(b):%b %Y}'.lower()
rows = ''.join(f'<tr><td>{name}</td><td>{span(a, b)}</td>' + ''.join(f'<td>{window(r, a, b):.1%}</td>' for r in
               [bench, bt.net, res['spy_only'].net, res['pair_only'].net]) + '</tr>'
               for name, a, b in CRISES if pd.Timestamp(a) >= bt.index[0] and pd.Timestamp(b) <= bt.index[-1])
html(f'<table class="plain stress"><tr><th>episode</th><th>window</th><th>s&amp;p 500 tr</th><th>portfolio</th>'
     f'<th>equity sleeve</th><th>spread sleeve</th></tr>{rows}</table>' if rows else
     '<p>no episode falls inside the selected years.</p>')

# ---------------------------------------------------------------- attribution
section('attribution', 'attribution')
html('<p>each sleeve run in isolation, idle capital in t-bills.</p>')
html(table_html(res['sleeves'].rename(columns={'Vol-managed SPY only': 'equity sleeve',
                                               'Pair only (+ T-bills)': 'spread sleeve',
                                               'Combined strategy': 'combined'})))
chart({'combined': wealth(bt.net), 'equity sleeve': wealth(res['spy_only'].net),
       'spread sleeve': wealth(res['pair_only'].net)}, 'growth of $1 (log)', log=True)
html(f'<p>positioning at the {y1} close: equity exposure <b>{res["exposure_now"]:.2f}x</b>, '
     f'spread pair for {y1 + 1}: <b>{"/".join(res["pair_now"]).lower()}</b>.</p>')

# ---------------------------------------------------------------- live out-of-sample
section('live-2026', 'live: 2026')
html('<p>the rules were frozen at the 31 dec 2025 close. this section runs them, with notebook defaults, on data the '
     'strategy was never fitted on: a true out-of-sample check, separate from the prospectus numbers.</p>')
try:
    live = get_live()
    lb, lbench = live['bt'], live['bench_d']
    lw_s, lw_b = wealth(lb.net), wealth(lbench)
    stats_live = lambda r: (f'{(1 + r).prod() - 1:.1%}', f'{r.std() * 252 ** .5:.1%}',
                            f'{(wealth(r) / wealth(r).cummax() - 1).min():.1%}')
    rows = ''.join(f'<tr><td>{n}</td>' + ''.join(f'<td>{v}</td>' for v in stats_live(r)) + '</tr>'
                   for n, r in [('portfolio (net)', lb.net), ('s&amp;p 500 tr', lbench)])
    html(f'<p>1 jan 2026 &rarr; {lb.index[-1]:%d %b %Y}'.lower() + '</p>')
    html(f'<table class="plain"><tr><th></th><th>return</th><th>volatility (ann.)</th><th>max drawdown</th></tr>{rows}</table>')
    chart({'portfolio (net)': lw_s, 's&p 500 tr': lw_b}, 'growth of $1')
    html(f'<p>current positioning: equity exposure <b>{lb.w_spy.iloc[-1]:.2f}x</b>, spread pair '
         f'<b>{"/".join(live["pair_now"]).lower()}</b>.</p>')
except Exception:
    html('<p><i>live data unavailable right now (yahoo rate limit). reload in a minute.</i></p>')

# ---------------------------------------------------------------- rules, risks
section('rules', 'rules')
html(f"""<p>1: risk budget. one {tv:.0f}% volatility budget for the whole portfolio. the spread sleeve's realized
volatility (63 trading days) is taken out first; the equity sleeve gets the rest.</p>
<p>2: equity sleeve. at each month-end, exposure = remaining budget / spy realized volatility (21 trading days,
annualized), capped at {lev:.2f}x. idle cash earns the t-bill rate; leverage is financed at t-bill + {fin} bp.</p>
<p>3: spread sleeve. at each year-end, select the two lowest-beta sector etfs vs spy (trailing 1y). daily z-score of
the log price ratio vs its 60-day mean: enter at |z| &gt; 2 (long cheap, short rich), exit at |z| &lt; 0.5. legs are
sized beta-neutral from the same prior-year betas, {2 * size:.2f}x gross. a newly selected pair starts flat.</p>
<p>4: execution. signals use closes up to day t; positions earn from t+1.</p>
<p>5: costs. {cost} bp per unit traded, 25 bp p.a. borrow fee on shorts.</p>""")

mdd = res['table'].loc['Max drawdown (monthly)', 'Strategy (net)']
section('risks', 'risks')
html(f"""<p>- leverage and shorting required; gross exposure can exceed 4x.</p>
<p>- max drawdown {pct(mdd)} on monthly data.</p>
<p>- selection bias: the low-beta pair rule was formulated after observing defensive-sector pairs; alternative
selection rules did not add value.</p>
<p>- monthly rebalancing lags sudden volatility spikes; low exposure after crashes misses sharp rebounds.</p>
<p>- realized daily volatility can exceed the budget in sudden spikes, because exposure is reset monthly.</p>
<p>- yahoo finance data, fixed cost assumptions, no taxes.</p>""")

# ---------------------------------------------------------------- team
section('team', 'team')
html('<table class="team"><tr>' + ''.join(f'<td><div class="ph"></div>{n}<br><i>{r}</i></td>' for n, r in TEAM) + '</tr></table><hr>')

# ---------------------------------------------------------------- footer
html(f"""<p class="fine">data: yahoo finance (split/dividend adjusted), ^SP500TR, ^IRX. statistics on monthly returns;
means &times;12, volatility &times;&radic;12, beta not annualized. method: <a href="{COLAB}">notebook</a> &middot;
<a href="{REPO}">source code</a>.</p>
<p class="fine">hypothetical backtest, 2270 financial modeling, nova sbe. not investment advice.</p>""")

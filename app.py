import base64
import hashlib
from dataclasses import asdict
from io import BytesIO
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.dates import MonthLocator, num2date
from matplotlib.ticker import FuncFormatter, NullLocator
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from strategy import ASSETS, Params, var_es, load_live, load_prices, monthly, pair_returns, pair_targets, run, spy_exposure, wealth
from replay import replay

FUND, FUND_LONG = 'MVP Strategies', 'Managed Volatility Portfolio'
ADDRESS = 'Rua da Holanda 1 &middot; 2775-405 Carcavelos &middot; Portugal'
REPO = 'https://github.com/Ben10Nova/FinancialModellingGroupN'
COLAB = 'https://colab.research.google.com/github/Ben10Nova/FinancialModellingGroupN/blob/main/vol-control_pair_v1.ipynb'
DEFAULTS = Params()
CODE = hashlib.md5((Path(__file__).parent / 'strategy.py').read_bytes()).hexdigest()   # cache key: new code = new results
DEMO_DEPOSIT, DEMO_START = 1000.0, '2026-01-01'
CRISES = [  # s&p 500 peak and trough closes, what happened, what it shows
    ('global financial crisis', '2007-10-09', '2009-03-09',
     'the us housing bust turned into a banking crisis. lehman brothers failed in september 2008 and the s&amp;p 500 lost more than half its value.',
     'the fall built up over many months, so the monthly reset had time to cut exposure before the worst of it.'),
    ('euro debt crisis', '2011-04-29', '2011-10-03',
     'markets feared that greece, italy and spain could not pay their debts, and the us lost its aaa rating in august.',
     'markets were calm going in, so exposure was high when it hit. most of the drop came within a few weeks, faster than a monthly reset can react.'),
    ('q4 2018 selloff', '2018-09-20', '2018-12-24',
     'the fed kept raising rates while the trade war with china escalated. stocks fell almost 20% into christmas eve.',
     'a calm summer meant exposure was close to the cap going in.'),
    ('covid crash', '2020-02-19', '2020-03-23',
     'the pandemic shut down economies and the s&amp;p 500 fell a third in about a month, the fastest crash on record.',
     'the first leg down in late february hit at full exposure. the february month-end reset then cut it hard, which spared most of the march crash.'),
    ('2022 rate shock', '2022-01-03', '2022-10-12',
     'inflation hit a 40-year high and the fed raised rates faster than in decades. stocks and bonds fell together.',
     'a slow grind lower, so exposure came down month by month as volatility picked up.')]
UNSPLASH = 'https://images.unsplash.com/photo-{}?w=480&h=600&fit=crop&crop=faces&q=75'
# photo: a file in assets/, a full image url, or an unsplash id (stock placeholder until the real photo is in)
# bio: education, internships, focus within the fund. rendered as html (innerHTML), not plain text
BIO_LUCAS = ('<p>BSc in International Business from Maastricht University, now completing an MSc in Finance at Nova SBE.</p>'
             '<p>Internships at KPMG, PradoNeo and Montag &amp; Montag.</p>'
             '<ul><li>Works on the defensive sector spread: pair selection and the mean-reversion rules behind it.</li></ul>')
BIO_BEN = ('<p>BSc from Maastricht University, now completing an MSc in Finance at Nova SBE.</p>'
           '<p>Internships at Simon-Kucher, DZ Bank and H.C.F. Hanse Corporate Finance.</p>'
           '<ul><li>Covers trade execution mechanics and the financing/borrow cost assumptions behind the strategy.</li></ul>')
BIO_KATHA = ('<p>BBA from WHU &ndash; Otto Beisheim School of Management, now completing an MSc in Finance at Nova SBE.</p>'
             '<p>Internships at BlackFin Capital Partners, Roland Berger and PwC.</p>'
             '<ul><li>Focuses on the volatility-targeted equity sleeve and how exposure scales with realized volatility.</li></ul>')
BIO_NOAH = ('<p>BSc from the University of Münster, now completing an MSc in Finance at Nova SBE.</p>'
            '<p>Internships at Triton Partners, UBS and BNP Paribas CIB.</p>'
            '<ul><li>Leads the risk framework: volatility targeting, drawdowns and the stress-test scenarios.</li>'
            '<li>Reviews capital allocation between the equity and spread sleeves each month.</li></ul>')
BIO_HENRIK = ('<p>BSc in International Business from Maastricht University, now completing an MSc in Finance at Nova SBE.</p>'
              '<p>Internships at Liberta Partners, REIA Capital and Deloitte.</p>'
              '<ul><li>Oversees portfolio construction across both sleeves and the fund&rsquo;s overall risk budget.</li>'
              '<li>Main point of contact for investor reporting.</li></ul>')
BIO_CHRIS = ('<p>BBA in International Finance from the University of Augsburg, now completing an MSc in Finance at Nova SBE.</p>'
             '<p>Internships at EY and Salesfive.</p>'
             '<ul><li>Maintains performance tracking and the monthly return attribution between sleeves.</li></ul>')
TEAM = [  # name, title, photo, bio (html), linkedin url ('' hides the icon)
    ('lucas s', 'investor', 'assets/lucas_strobel.jpg', BIO_LUCAS, ''),
    ('ben s', 'investor', 'assets/ben_s.jpg', BIO_BEN, ''),
    ('katha g', 'investor', 'assets/katha_g.jpg', BIO_KATHA, ''),
    ('noah vr', 'investor', 'assets/noah_vr.jpg', BIO_NOAH, ''),
    ('henrik t', 'investor', 'assets/henrik_trillhaas.jpg', BIO_HENRIK, ''),
    ('chris w', 'investor', 'assets/chris_w.jpg', BIO_CHRIS, '')]
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
  --negative:#8c2d2b; --soft:#f5f5f7; --line:#d2d2d7; --r:18px; --serif:"Newsreader",Georgia,serif; --sans:"IBM Plex Sans",system-ui,sans-serif;
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


/* clickable lists, episodes and their deep-dive pop-up */
[class*="st-key-dv_"] { gap: 0 !important; max-width: 72ch; counter-reset: it; margin-bottom: 16px; }
[class*="st-key-dv_"] .stButton { counter-increment: it; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"] { width: 100%; display: block; position: relative; text-align: left;
  padding: 9px 0 9px 28px !important; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"]::before { content: counter(it); position: absolute; left: 0; top: 9px;
  font-family: var(--mono); font-size: 12px; line-height: 24px; color: var(--muted); }
.stApp [class*="st-key-dv_"] button[kind="tertiary"] * { font-size: 15px !important; line-height: 1.6; text-decoration: none !important;
  text-align: left; white-space: normal; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"] strong, .stApp .st-key-stress button[kind="tertiary"] p {
  text-decoration: underline !important; text-decoration-thickness: 1px !important; text-underline-offset: 3px; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"]:hover, .stApp .st-key-stress button[kind="tertiary"]:hover { background: var(--panel) !important; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"] p::after, .stApp .st-key-stress button[kind="tertiary"] p::after {
  content: "↗"; margin-left: 6px; font-family: var(--mono); font-size: 13px; color: var(--ink); display: inline-block; text-decoration: none; }
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
.stApp .st-key-stress button[kind="tertiary"] * { font-size: 13.5px !important; text-align: left; }
.st-key-stress p.win { display: none; }
[role="dialog"] :not([data-testid="stMarkdown"]) > [data-testid="stMarkdownContainer"] p { font-family: var(--serif) !important; font-weight: 500 !important; font-size: 28px !important; }
img.chart { display: block; width: 100%; height: auto; margin: 6px 0 0; }

/* soft ios layer: rounded grey panels, pill buttons, segmented control, frosted pop-up backdrop. tables and charts stay plain */
.stApp .st-key-knobs, .stApp [data-testid="stForm"] { background: var(--soft) !important; border: 0 !important; border-radius: var(--r) !important;
  padding: 20px !important; }
.stApp [data-testid="stNumberInputContainer"], .stApp [data-baseweb="select"] > div, .stApp [data-testid="stTextInputRootElement"] {
  border: 1px solid var(--line) !important; border-radius: 10px !important; overflow: hidden; }
.stApp [data-testid="stNumberInputStepDown"], .stApp [data-testid="stNumberInputStepUp"] { border-left: 1px solid var(--line) !important; }
.stApp button[kind="primaryFormSubmit"], .stApp button[kind="primary"] { border-radius: 980px !important; padding: 0 26px !important; }
.stApp [data-testid="stCheckbox"] span { border-radius: 6px !important; }
[data-testid="stButtonGroup"] > div { background: #e8e8ed; border-radius: 10px; padding: 2px; gap: 0 !important; display: inline-flex !important; }
.stApp [data-testid="stButtonGroup"] button { border: 0 !important; border-radius: 8px !important; background: transparent !important;
  min-height: 30px !important; padding: 0 22px !important; box-shadow: none !important; }
.stApp [data-testid="stButtonGroup"] button[kind*="Active"] { background: #fff !important; box-shadow: 0 1px 3px rgba(0,0,0,.12), 0 0 0 .5px rgba(0,0,0,.04) !important; }
.stApp [data-testid="stButtonGroup"] button * { font-size: 13px !important; color: var(--ink) !important; font-weight: 500; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"] { margin: 0 -12px; width: calc(100% + 24px); padding: 10px 12px 10px 40px !important;
  border-radius: 14px !important; transition: background .2s !important; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"]::before { left: 12px; top: 10px; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"]:hover { background: var(--soft) !important; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"]:hover * { color: var(--ink) !important; }
.stApp .st-key-stress [data-testid="stHorizontalBlock"]:has(button) { border-radius: 12px; transition: background .2s !important; }
.stApp .st-key-stress [data-testid="stHorizontalBlock"]:has(button):hover { background: var(--soft); }
.stApp .st-key-stress button[kind="tertiary"]:hover { background: none !important; }
.stApp .st-key-stress button[kind="tertiary"]:hover * { color: var(--ink) !important; }
[data-testid="stDialog"] > div { background: rgba(250,250,252,.45) !important; backdrop-filter: blur(16px) saturate(160%); -webkit-backdrop-filter: blur(16px) saturate(160%); }
[role="dialog"] { border-radius: 22px !important; border: 0 !important; box-shadow: 0 24px 70px rgba(0,0,0,.16), 0 0 0 .5px rgba(0,0,0,.06) !important; }
.stApp [data-testid="stSidebar"] { border-right: 1px solid rgba(0,0,0,.08) !important; }
[data-testid="stHorizontalBlock"]:has([data-testid="stButtonGroup"]) { flex-wrap: nowrap !important; }
[data-testid="stHorizontalBlock"]:has([data-testid="stButtonGroup"]) > [data-testid="stColumn"] { min-width: 0 !important; }
[data-testid="stHorizontalBlock"]:has([data-testid="stButtonGroup"]) .stButton { display: flex; justify-content: flex-end; }

/* risk profile: paired bars */
.rg { margin: 18px 0 8px; }
.rg p.rt { font-size: 13px !important; font-weight: 600; margin: 0 0 6px !important; }
.rg p.rt span { font-weight: 400; color: var(--muted) !important; font-size: 12px !important; margin-left: 6px; }
.rr { display: grid; grid-template-columns: 190px 1fr; align-items: center; gap: 14px; padding: 7px 0; }
.rr span.rl { font-size: 13.5px !important; }
.rb { display: flex; align-items: center; gap: 10px; height: 18px; }
.rb i { display: block; height: 12px; border-radius: 6px; background: #0b2648; min-width: 2px; }
.rb.s i { background: #c9ccd0; }
.rb em { font-style: normal; font-family: var(--mono) !important; font-size: 12px !important; white-space: nowrap; }
.rb.s em { color: var(--muted) !important; }
.stApp [data-testid="stExpander"] details { border: 0 !important; border-radius: 14px !important; background: var(--soft); }
.stApp [data-testid="stExpander"] summary p { font-size: 13px !important; }

/* investor account */
.hero { margin: 28px 0 8px; }
.hero p { margin: 0 !important; }
.hero p.k { font-size: 12.5px !important; color: var(--muted) !important; }
.hero p.big { font-family: var(--serif) !important; font-size: 64px !important; font-weight: 400; line-height: 1.1;
  letter-spacing: -.02em; font-variant-numeric: tabular-nums lining-nums; margin: 2px 0 6px !important; }
.hero p.chg, .hero p.chg span { font-size: 14px !important; }
.hero p.chg span:first-child { font-family: var(--mono) !important; font-weight: 500; }
.hero span.neg { color: var(--negative) !important; } .hero span.dim { color: var(--muted) !important; }

@media (max-width: 640px) {
  .rr { grid-template-columns: 1fr; gap: 4px; }
  h1.bh { font-size: 46px !important; } p.long { font-size: 17px !important; } .stApp h3 { font-size: 28px !important; }
  .st-key-stress [data-testid="stColumn"]:has(p.dim), .st-key-stress [data-testid="stColumn"]:has(p.wh) { display: none !important; }
  .stApp .st-key-stress button[kind="tertiary"] * { font-size: 12.5px !important; line-height: 1.35; }
  .st-key-stress p.c { font-size: 11.5px !important; } .st-key-stress p.th { font-size: 10px !important; }
  .st-key-stress p.win { display: block; white-space: nowrap; font-size: 10px !important; font-family: var(--mono) !important; color: var(--muted) !important; }
  .hero p.big { font-size: 46px !important; }
}
</style>
""", unsafe_allow_html=True)

html = lambda s: st.markdown(s, unsafe_allow_html=True)
heading = lambda t: html(f'<h3>{t}</h3>')
note = lambda t: html(f'<p class="note">{t}</p>')
ROWS = {'Ann. avg return': 'ann. return', 'Ann. volatility': 'ann. volatility', 'Sharpe ratio': 'sharpe ratio',
        'Alpha (ann.)': 'alpha (ann.)', 'Alpha t-stat': 'alpha t-stat', 'Beta': 'beta',
        'Information ratio': 'information ratio', 'Max drawdown (monthly)': 'max drawdown (monthly)'}
ROWS |= {'Skewness': 'skewness', 'Excess kurtosis': 'excess kurtosis', 'VaR 95%, historical': 'value at risk 95%, historical',
         'VaR 95%, normal': 'value at risk 95%, normal', 'VaR 99%, normal': 'value at risk 99%, normal',
         'VaR 99%, Cornish-Fisher': 'value at risk 99%, cornish-fisher', 'CVaR 95% (expected shortfall)': 'expected shortfall 95%',
         'Worst month': 'worst month', 'Positive months': 'positive months', 'Sortino ratio': 'sortino ratio',
         'Calmar ratio': 'calmar ratio', 'Upside capture': 'upside capture', 'Downside capture': 'downside capture',
         'Tracking error': 'tracking error', 'Active IR (vs S&P 500 TR)': 'active information ratio',
         'Alpha t-stat, Newey-West': 'alpha t-stat, newey-west'}
PCT_ROWS = {'ann. return', 'ann. volatility', 'alpha (ann.)', 'max drawdown (monthly)', 'value at risk 95%, historical',
            'value at risk 95%, normal', 'value at risk 99%, normal', 'value at risk 99%, cornish-fisher',
            'expected shortfall 95%', 'worst month', 'positive months', 'upside capture', 'downside capture', 'tracking error'}


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


def show(fig):
    fig.tight_layout(pad=.3)
    buf = BytesIO()                            # inline png: no separate media file that a redeploy or reload can lose
    fig.savefig(buf, format='png')
    html(f'<img class="chart" alt="" src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}">')
    plt.close(fig)


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
    show(fig)


def items(rows, ordered=True):
    tag = 'ol' if ordered else 'ul'
    html(f'<{tag} class="items">' + ''.join(
        f'<li><span class="mk">{i + 1 if ordered else "–"}</span><span>{f"<b>{lead}</b> " if lead else ""}{text}</span></li>'
        for i, (lead, text) in enumerate(rows)) + f'</{tag}>')


def dive(title, body):
    """pop-up over the current page; body draws its content"""
    st.dialog(title, width='medium')(body)()


def clickable(key, rows):
    """numbered list, each item opens its deep dive. plain markdown labels: write '&', '>' not entities"""
    with st.container(key=f'dv_{key}'):
        for i, (lead, text, more) in enumerate(rows):
            if st.button(f'**{lead}** {text}', key=f'{key}{i}', type='tertiary'):
                dive(lead.rstrip('.'), lambda: html(''.join(f'<p>{t}</p>' for t in more())))


@st.cache_data(ttl=86400, show_spinner=False)
def get_prices():
    return load_prices()


@st.cache_data(show_spinner=False)
def get_results(code, **kw):
    return run(get_prices(), Params(**kw))


@st.cache_data(ttl=3600, show_spinner='loading live prices ...')
def get_live(target_vol=DEFAULTS.target_vol, code=CODE):
    px = load_live()
    return run(px, Params(start=DEMO_START, end=str(px.index[-1].date()), target_vol=target_vol)), px


def results():
    p = st.session_state.get('params', DEFAULTS)
    try:
        return p, get_results(CODE, **asdict(p))
    except RuntimeError as e:
        note(str(e))
        st.stop()


# ================================================================ pages
def home():
    html(f'<div class="home"><div class="mid"><h1 class="bh">{FUND}</h1><p class="long">{FUND_LONG}<br>Strategies</p>'
         f'<p class="addr">{ADDRESS}</p></div></div>')
    with st.container(key='foot', horizontal=True, horizontal_alignment='center', gap='medium'):
        if st.button('imprint', type='tertiary'):
            dive('imprint', lambda: html(
                f'<p>{FUND} &middot; {FUND_LONG}<br>{ADDRESS}</p>'
                '<p class="note">student project, 2270 financial modeling, nova sbe. hypothetical backtest, '
                'not investment advice.</p>'))
        if st.button('data & method', type='tertiary'):
            dive('data & method', lambda: html(
                '<p>data: yahoo finance (split/dividend adjusted), ^SP500TR, ^IRX.<br>statistics on monthly returns; '
                'means &times;12, volatility &times;&radic;12, beta not annualized.</p>'
                f'<p><a href="{COLAB}">notebook</a> &middot; <a href="{REPO}">source code</a></p>'))


def sleeve_facts():
    p, res = results()
    sl = res['sleeves']
    corr = monthly(res['spy_only'].net).corr(monthly(res['pair_only'].net))
    sp_dd = res['table'].loc['Max drawdown (monthly)', 'S&P 500 TR']
    return p, sl, corr, sp_dd


def thesis_equity():
    p, sl, _, sp_dd = sleeve_facts()
    e = sl['Vol-managed SPY only']
    return ['volatility comes in clusters. a wild week is usually followed by another wild week, a calm month by another '
            'calm month. and markets tend to fall hardest when they are already nervous.',
            f'so we don\'t hold a fixed amount of the s&amp;p 500. at each month-end we check how much spy moved over the last '
            f'21 trading days and size the position so its risk lands on target. calm market: bigger position, up to '
            f'{p.max_lev:.2f}x. nervous market: smaller position, the rest sits in t-bills.',
            f'on its own this sleeve made <span class="fig">{num(e["Ann. avg return"])[0]}</span> a year with a worst drawdown '
            f'of <span class="fig">{num(e["Max drawdown (monthly)"])[0]}</span>. the s&amp;p 500: '
            f'<span class="fig">{num(sp_dd)[0]}</span>.',
            'the catch: after a crash exposure is low, right when markets bounce back. so it misses part of the rebound.']


def thesis_spread():
    p, sl, corr, _ = sleeve_facts()
    s = sl['Pair only (+ T-bills)']
    return ['utilities, consumer staples and health care sell things people buy in good times and bad: power, food, '
            'medicine. so these sectors react little to the market, and they tend to move together.',
            f'sometimes one runs ahead of the other for a few weeks for no lasting reason. we measure the gap as a z-score: how '
            f'far the price ratio is from its 60-day average, in standard deviations. past {p.z_in:g} we buy the one that fell '
            f'behind and short the one that ran ahead. once the gap is back under {p.z_out:g}, we close both.',
            f'one leg is long, one is short, so the direction of the market mostly cancels out. beta of this sleeve: '
            f'<span class="fig">{num(s["Beta"], "x")[0]}</span>. return on its own: '
            f'<span class="fig">{num(s["Ann. avg return"])[0]}</span> a year. '
            f'correlation with the equity sleeve: <span class="fig">{num(corr, "x")[0]}</span>.']


def thesis():
    heading('thesis')
    html('<p>two return streams, built to be uncorrelated, sharing one 15% risk budget:</p>')
    clickable('thesis', [('volatility-targeted equity.', 'we hold the s&p 500 and scale exposure with realized volatility: more in '
            'calm markets, less in stressed ones. it gets whatever risk budget the spread sleeve does not use.', thesis_equity),
           ('defensive sector spread.', 'a beta-neutral relative-value position between the two most defensive us '
            'equity sectors, which trades the mean reversion of temporary dislocations.', thesis_spread)])
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


RISK_GROUPS = [  # title, hint, rows: (label, table, row, format, sign)
    ('a bad month', 'one-month loss, shorter is better', [
        ('value at risk 95%', 'risk', 'VaR 95%, historical', 'pct', 1), ('expected shortfall 95%', 'risk', 'CVaR 95% (expected shortfall)', 'pct', 1),
        ('worst month', 'risk', 'Worst month', 'pct', -1)]),
    ('reward per unit of risk', 'longer is better', [
        ('sharpe ratio', 'table', 'Sharpe ratio', 'x', 1), ('sortino ratio', 'risk', 'Sortino ratio', 'x', 1),
        ('calmar ratio', 'risk', 'Calmar ratio', 'x', 1)]),
    ('up and down markets', 'share of the s&amp;p&rsquo;s average month we went along with', [
        ('in up months', 'risk', 'Upside capture', 'pct', 1), ('in down months', 'risk', 'Downside capture', 'pct', 1)])]


def risk_profile(table, risk):
    """the risk numbers as paired bars, portfolio vs s&p; the full table sits in an expander"""
    html('<h4>risk profile</h4>')
    html(f'<p class="chart-head"><b>monthly returns, net of costs</b><span><i style="background:{S1}"></i>portfolio (net)</span>'
         f'<span><i style="background:#c9ccd0"></i>s&amp;p 500 tr</span></p>')
    out = ''
    for title, hint, rows in RISK_GROUPS:
        vals = [[sign * {'risk': risk, 'table': table}[t].loc[k, c] for c in ('Strategy (net)', 'S&P 500 TR')]
                for _, t, k, _, sign in rows]
        top = max(max(v) for v in vals)
        out += f'<div class="rg"><p class="rt">{title} <span>{hint}</span></p>'
        for (label, _, _, kind, _), (p, s) in zip(rows, vals):
            bar = lambda v, cls: (f'<div class="rb {cls}"><i style="width:calc((100% - 70px) * {max(v, 0) / top:.3f})"></i>'
                                  f'<em>{num(v, kind)[0]}</em></div>')
            out += f'<div class="rr"><span class="rl">{label}</span><div>{bar(p, "p")}{bar(s, "s")}</div></div>'
        out += '</div>'
    html(out)
    with st.expander('all risk numbers'):
        note('monthly returns. value at risk and expected shortfall are one-month losses. cornish-fisher adjusts the normal '
             'quantile for skew and fat tails. capture: our average return in the s&amp;p&rsquo;s up (down) months, relative to the s&amp;p.')
        metrics_table(risk[['Strategy (net)', 'S&P 500 TR']].rename(
            columns={'Strategy (net)': 'portfolio (net)', 'S&P 500 TR': 's&amp;p 500 tr'}), 'portfolio (net)')


def var_section(r, b):
    """value at risk and expected shortfall at a chosen confidence level, with the return distribution"""
    html('<h4>value at risk</h4>')
    lvl = st.slider('confidence level', 90.0, 99.5, 95.0, 0.5, format='%.1f%%', key='var_level') / 100
    v = pd.DataFrame({'portfolio (net)': var_es(r, lvl), 's&amp;p 500 tr': var_es(b, lvl)})
    p, s = v['portfolio (net)'], v['s&amp;p 500 tr']
    html(f'<p class="lede">in 1 month out of {1 / (1 - lvl):.0f}, the portfolio lost more than <strong>{num(p.iloc[0])[0]}</strong> '
         f'(s&amp;p 500: <strong>{num(s.iloc[0])[0]}</strong>). in those months the average loss was '
         f'<strong>{num(p.iloc[3])[0]}</strong> (s&amp;p 500: <strong>{num(s.iloc[3])[0]}</strong>).</p>')
    rows = ''.join(f'<tr><td class="label">{i.lower()}</td>{td(x, cls="em")}{td(y)}</tr>' for i, x, y in zip(v.index, p, s))
    html(f'<table class="plain"><tr><th>one-month loss at {lvl:.1%}</th><th>portfolio (net)</th><th>s&amp;p 500 tr</th></tr>'
         f'{rows}</table>')
    period = f'{r.index[0]:%Y}–{r.index[-1]:%Y}'
    note(f'historical: the loss exceeded in {1 - lvl:.1%} of the months {period}. normal: assumes a bell curve. cornish-fisher: bell curve '
         f'corrected for skew and fat tails. expected shortfall: average loss in the months beyond the historical var. '
         f'{(r <= -p.iloc[0]).sum()} of {len(r)} months are in the tail, so far-out levels rest on very few months.')
    html(f'<p class="chart-head"><b>monthly returns, {period}</b><span><i style="background:{S1}"></i>portfolio (net)</span>'
         f'<span><i style="background:{S2}"></i>s&amp;p 500 tr</span></p>')
    fig, ax = plt.subplots(figsize=(8, 2.9))
    lo, hi = min(r.min(), b.min()), max(r.max(), b.max())
    bins = np.arange(np.floor(lo * 100) - 1, np.ceil(hi * 100) + 2) / 100
    ax.hist(b, bins=bins, histtype='step', color=S2, lw=1.2)
    ax.hist(r, bins=bins, color=S1, alpha=.85, rwidth=.85)
    for x, c in ((p, S1), (s, S2)):
        ax.axvline(-x.iloc[0], color=c, lw=1.3)                               # value at risk
        ax.axvline(-x.iloc[3], color=c, lw=1.3, ls='--')                      # expected shortfall
    ax.axvspan(lo - .01, -p.iloc[0], color=S1, alpha=.06, lw=0)
    ax.set_xlim(lo - .01, hi + .01)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.0%}'.replace('-', '−')))
    ax.set_ylabel('months', color=MUTED)
    show(fig)
    note('solid line: value at risk (historical). dashed: expected shortfall. shaded: the portfolio&rsquo;s tail.')


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
    replay(res, p, DEFAULTS)                                       # lede + growth of $1 with year-by-year replay
    metrics_table(res['table'].rename(columns={'Strategy (net)': 'portfolio (net)', 'S&P 500 TR': 's&amp;p 500 tr'}),
                  'portfolio (net)')
    chart('drawdown', [('portfolio (net)', w_s, S1), ('s&amp;p 500 tr', w_b, S2)], kind='drawdown', h=2.2)
    risk_profile(res['table'], res['risk'])
    var_section(monthly(bt.net), monthly(bench))
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
        for k, (name, a, b, story, lesson) in enumerate(eps):
            c = st.columns(W, vertical_alignment='center')
            clicked = c[0].button(name, key=f'ep{k}', type='tertiary')
            c[0].markdown(f'<p class="win">{span(a, b)}</p>', unsafe_allow_html=True)
            c[1].markdown(f'<p class="dim">{span(a, b)}</p>', unsafe_allow_html=True)
            for col, (n, r) in zip(c[2:], streams):
                cell(col, (1 + cut(r, a, b)).prod() - 1, 'em' if n == 'portfolio' else '')
            if clicked:
                def body(a=a, b=b, story=story, lesson=lesson):
                    note(span(a, b))
                    w = bt.w_spy
                    pos = (f' spread pair: {res["yearly"].loc[int(a[:4]), "Pair held"].lower()}, open on '
                           f'{(res["pair_only"].gross_exposure.loc[a:b] > 0).mean():.0%} of days.' if p.pair_size > 0 else '')
                    html(f'<p>{story}</p><p>{lesson} equity exposure going in: <span class="fig">{w.loc[:a].iloc[-1]:.2f}x</span>, '
                         f'average during the episode: <span class="fig">{w.loc[a:b].mean():.2f}x</span>.{pos}</p>')
                    html('<table class="plain"><tr>' + ''.join(f'<th>{n}</th>' for n, _ in streams) + '</tr><tr>'
                         + ''.join(td((1 + cut(r, a, b)).prod() - 1) for _, r in streams) + '</tr></table>')
                    chart('growth of $1 over the episode', [('portfolio (net)', wealth(cut(bt.net, a, b)), S1),
                                                            ('s&amp;p 500 tr', wealth(cut(bench, a, b)), S2)], kind='line')
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
                                f'{td(monthly(r).std() * 12 ** .5)}{td((wealth(r) / wealth(r).cummax() - 1).min())}</tr>')
    html('<table class="plain"><tr><th></th><th>return</th><th>volatility (ann., monthly)</th><th>max drawdown</th></tr>'
         + row('portfolio (net)', lb.net, 'em') + row('s&amp;p 500 tr', lbench, '') + '</table>')
    chart('growth of $1', [('portfolio (net)', wealth(lb.net), S1), ('s&amp;p 500 tr', wealth(lbench), S2)], kind='line')
    html(f'<p>current positioning: equity exposure <span class="fig">{lb.w_spy.iloc[-1]:.2f}x</span>, spread pair '
         f'<span class="fig">{"/".join(live["pair_now"]).lower()}</span>.</p>')


def rule_budget():
    p, _ = results()
    left = max(p.target_vol ** 2 - 0.06 ** 2, 0) ** .5
    return [f'think of {p.target_vol:.0%} volatility as the total risk we are allowed to take. the spread sleeve goes first: we '
            'measure how much it moved over the last 63 trading days. the equity sleeve gets what is left.',
            f'risks don\'t add up in a straight line, because the two sleeves don\'t move together. if the spread uses 6%, the '
            f'equity sleeve still gets &radic;({p.target_vol * 100:g}&sup2; &minus; 6&sup2;) = <span class="fig">{left:.1%}</span>, '
            f'not {p.target_vol - .06:.0%}.']


def rule_equity():
    p, _ = results()
    return ['position = risk budget / how much spy moved lately (annualized).',
            f'example: budget 13%, spy moving at 20% a year: hold 13 / 20 = 0.65x, the other 0.35 sits in t-bills. spy moving at '
            f'8%: 1.6x, and the extra 0.6 is borrowed at the t-bill rate plus {p.fin_spread * 1e4:.0f} bp. never more than '
            f'{p.max_lev:.2f}x.',
            'we only reset at month-end. in between, the position just moves with the market.']


def rule_spread():
    p, _ = results()
    return ['on the last trading day of the year we measure each of the 9 sector etfs against spy over that year and pick the '
            'two that moved least with the market. that pair is traded all of next year.',
            'the legs are sized so both carry the same market exposure: the one that moves less with the market gets the bigger weight.',
            f'example with xlp and xlu: z hits +2.3, so xlp has run ahead of xlu. we short xlp and buy xlu. when z falls back '
            f'under {p.z_out:g}, we close both.',
            'when the pair changes at year-end, the old position is closed and the new pair starts flat.']


def rule_execution():
    return ['every decision uses closing prices up to today. we trade at today\'s close, so a new position earns from tomorrow. '
            'no peeking at prices we could not have known.',
            'we checked this by deleting all data after a date and rerunning. everything before that date came out exactly the '
            'same. the test is in the notebook.']


def rule_costs():
    p, res = results()
    bt = res['bt']
    turn = bt.turnover.sum() / (len(bt) / 252)
    return [f'every trade costs {p.cost * 1e4:.0f} bp of the amount traded: spread, commission, slippage. shorts cost '
            f'{p.short_fee * 1e4:.0f} bp a year to borrow, borrowed cash costs the t-bill rate plus {p.fin_spread * 1e4:.0f} bp.',
            'every return on this site is after these costs.',
            f'we trade about <span class="fig">{turn:.0f}x</span> our capital a year, mostly the spread legs, so costs matter. '
            'raise the cost slider on the performance page to see how much.']


def rules():
    heading('rules')
    p, _ = results()
    clickable('rules', [('risk budget.', f'one {p.target_vol:.0%} volatility budget for the whole portfolio. the spread sleeve\'s realized '
            'volatility (63 trading days) is taken out first; the equity sleeve gets the rest.', rule_budget),
           ('equity sleeve.', f'at each month-end, exposure = remaining budget / spy realized volatility (21 trading days, '
            f'annualized), capped at {p.max_lev:.2f}x. idle cash earns the t-bill rate; leverage is financed at t-bill + '
            f'{p.fin_spread * 1e4:.0f} bp.', rule_equity),
           ('spread sleeve.', f'at each year-end, select the two lowest-beta sector etfs vs spy (trailing 1y). daily z-score '
            f'of the log price ratio vs its 60-day mean: enter at |z| > {p.z_in:g} (long cheap, short rich), exit at '
            f'|z| < {p.z_out:g}. legs are sized beta-neutral from the same prior-year betas, {2 * p.pair_size:.2f}x gross. '
            'a newly selected pair starts flat.', rule_spread),
           ('execution.', 'signals use closes up to day t; positions earn from t+1.', rule_execution),
           ('costs.', f'{p.cost * 1e4:.0f} bp per unit traded, {p.short_fee * 1e4:.0f} bp p.a. borrow fee on shorts.', rule_costs)])


def fan_chart(fan):
    """monte carlo fan: a few single paths, 5-95% and 25-75% bands and the median, s&p median and 5/95% for comparison"""
    html(f'<p class="chart-head"><b>$1 over 10 years, 10,000 simulated paths (log scale)</b>'
         f'<span><i style="background:{S1}"></i>portfolio (net)</span><span><i style="background:{S2}"></i>s&amp;p 500 tr</span></p>')
    q = np.concatenate([np.ones((5, 1, 2)), fan['q']], axis=1)              # every path starts at $1
    t = np.arange(q.shape[1]) / 12
    fig, ax = plt.subplots(figsize=(8, 3.4))
    for path in fan['paths']:
        ax.plot(t, np.r_[1, path], color=S1, lw=.5, alpha=.12)
    ax.fill_between(t, q[0, :, 0], q[4, :, 0], color=S1, alpha=.10, lw=0)
    ax.fill_between(t, q[1, :, 0], q[3, :, 0], color=S1, alpha=.18, lw=0)
    ax.plot(t, q[2, :, 0], color=S1, lw=2)
    ax.plot(t, q[2, :, 1], color=S2, lw=1.5)
    for k in (0, 4):
        ax.plot(t, q[k, :, 1], color=S2, lw=1, ls='--')
    for k, lab in ((0, '5%'), (2, 'median'), (4, '95%')):
        ax.annotate(f'{lab} ${q[k, -1, 0]:.2f}', (t[-1], q[k, -1, 0]), xytext=(6, 0), textcoords='offset points',
                    va='center', fontsize=7.5, color=S1)
    ax.set_yscale('log'); ax.yaxis.set_minor_locator(NullLocator())
    ax.set_yticks([t_ for t_ in [0.5, 1, 2, 5, 10, 20] if q.min() / 1.3 <= t_ <= q.max() * 1.3])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'${v:g}'))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:.0f}y'))
    ax.axhline(1, color=INK, lw=.8); ax.set_xlim(0, t[-1] * 1.13)
    show(fig)
    note('shaded: the middle 50% and 90% of the portfolio&rsquo;s paths, thin lines: single paths, bold: median. '
         'grey: s&amp;p 500 median, dashed: its 5% and 95% levels.')


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
    mc, head, fan = res['mc']
    html('<h4>10-year outlook</h4>')
    note('monte carlo: 10,000 paths of 10 years, built from random 12-month blocks of the backtest (portfolio, s&amp;p and '
         't-bills from the same months). it resamples our own history, so it inherits its optimism: a range of outcomes '
         'if the next decade looks like the backtest, not a forecast.')
    kind = lambda i: 'usd' if i.startswith('Wealth') else 'x' if i.startswith('Sharpe') else 'pct'
    rows = ''.join(f'<tr><td class="label">{i.lower().replace("$1", "$1 invested")}</td>'
                   + ''.join(td(v, kind(i), 'em' if c == 'Strategy (net)' else '') for c, v in r.items()) + '</tr>'
                   for i, r in mc.iterrows())
    html(f'<table class="plain"><tr><th></th><th>portfolio (net)</th><th>s&amp;p 500 tr</th></tr>{rows}</table>')
    note(f'the portfolio ends ahead of the s&amp;p 500 in {head["beats_sp"]:.0%} of paths.')
    fan_chart(fan)


def photo(ph):
    if ph.startswith('assets/'):                                   # local file, inlined: the team iframe cannot load app files
        return f'data:image/jpeg;base64,{base64.b64encode((Path(__file__).parent / ph).read_bytes()).decode()}'
    return ph if ph.startswith('http') else UNSPLASH.format(ph)


def team():
    """wheel picker: spin the names, the one in the middle shows its photo and bio"""
    heading('team')
    people = json.dumps([dict(n=n, t=t, b=b, i=''.join(w[0] for w in n.split()),
                              u=photo(ph), li=li) for n, t, ph, b, li in TEAM])
    components.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono&family=IBM+Plex+Sans:wght@400;500&family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap');
* { box-sizing: border-box; margin: 0; }
body { font-family: "IBM Plex Sans", system-ui, sans-serif; color: #101924; background: #fff; }
.wrap { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.25fr); gap: 48px; align-items: center; }
.picker { position: relative; height: 420px; }
.wheel { height: 100%; overflow-y: scroll; scroll-snap-type: y mandatory; scrollbar-width: none; perspective: 900px;
  -webkit-mask-image: linear-gradient(transparent, #000 30%, #000 70%, transparent);
          mask-image: linear-gradient(transparent, #000 30%, #000 70%, transparent); }
.wheel::-webkit-scrollbar { display: none; }
.pad { height: 178px; }
.item { height: 64px; display: flex; align-items: center; justify-content: center; scroll-snap-align: center; cursor: pointer;
  font-family: "Newsreader", Georgia, serif; font-size: 30px; transform-origin: center; will-change: transform, opacity; user-select: none; }
.band { position: absolute; left: 0; right: 0; top: 178px; height: 64px; pointer-events: none;
  border-top: 1px solid #d7d7d7; border-bottom: 1px solid #d7d7d7; }
.card { transition: opacity .25s; }
.card.out { opacity: 0; }
.ph { position: relative; overflow: hidden; width: 180px; aspect-ratio: 4/5; background: #f5f5f5; border: 1px solid #d7d7d7; display: grid; place-items: center;
  font-family: "IBM Plex Mono", monospace; font-size: 18px; letter-spacing: .08em; color: #555b63; margin-bottom: 16px; }
.ph img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; filter: grayscale(1); }
.hd { display: flex; align-items: center; gap: 8px; }
.name { font-family: "Newsreader", Georgia, serif; font-size: 28px; line-height: 1.2; }
.li { display: inline-flex; color: #9aa1a8; transition: color .15s; }
.li.hide { display: none; }
.li:hover { color: #0b2648; }
.li svg { width: 18px; height: 18px; fill: currentColor; }
.title { font-size: 12.5px; color: #555b63; margin: 2px 0 14px; }
.bio { font-size: 15px; line-height: 1.6; max-width: 46ch; }
.bio p { margin: 0 0 10px; }
.bio ul { margin: 10px 0 0; padding-left: 1.1em; }
.bio li { margin: 0 0 4px; }
.bio p:last-child, .bio ul:last-child { margin-bottom: 0; }
@media (max-width: 600px) { .wrap { grid-template-columns: 1fr; gap: 28px; } .picker { height: 300px; } .pad { height: 118px; }
  .band { top: 118px; } .item { font-size: 26px; } }
</style>
<div class="wrap">
  <div class="picker"><div class="wheel" id="w"></div><div class="band"></div></div>
  <div class="card" id="c"><div class="ph"><span id="ph"></span><img id="im" alt=""></div><div class="hd"><p class="name" id="nm"></p><a class="li" id="li" target="_blank" rel="noopener" aria-label="LinkedIn"><svg viewBox="0 0 448 512"><path d="M416 32H31.9C14.3 32 0 46.5 0 64.3v383.4C0 465.5 14.3 480 31.9 480H416c17.6 0 32-14.5 32-32.3V64.3C448 46.5 433.6 32 416 32zM135.4 416H69V202.2h66.5V416zM102 172.2c-21.3 0-38.5-17.3-38.5-38.5S80.7 95.2 102 95.2c21.2 0 38.5 17.3 38.5 38.5s-17.2 38.5-38.5 38.5zm284.3 243.8h-66.4V312c0-24.8-.5-56.7-34.5-56.7-34.6 0-39.9 27-39.9 54.9V416h-66.4V202.2h63.7v29.2h.9c8.9-16.8 30.6-34.5 62.9-34.5 67.2 0 79.7 44.3 79.7 101.9V416z"/></svg></a></div><p class="title" id="tt"></p><div class="bio" id="bo"></div></div>
</div>
<script>
const P = PEOPLE, w = document.getElementById('w'), c = document.getElementById('c');
w.innerHTML = '<div class="pad"></div>' + P.map((p, i) => `<div class="item" data-i="${i}">${p.n}</div>`).join('') + '<div class="pad"></div>';
const items = [...w.querySelectorAll('.item')];
let cur = -1;
im.onerror = () => im.style.display = 'none';                      // no photo: the initials stay visible
P.forEach(p => new Image().src = p.u);                              // preload, so spinning does not flash
function show(i) {
  if (i === cur) return; cur = i; c.classList.add('out');
  setTimeout(() => { const p = P[i]; ph.textContent = p.i; im.style.display = ''; im.src = p.u; im.alt = p.n; nm.textContent = p.n; tt.textContent = p.t; bo.innerHTML = p.b;
                     li.href = p.li; li.classList.toggle('hide', !p.li);
                     c.classList.remove('out'); frameElement.style.height = document.body.scrollHeight + 'px'; }, cur === -1 ? 0 : 150);
}
function paint() {
  const mid = w.scrollTop + w.clientHeight / 2;
  let best = 0, bd = 1e9;
  items.forEach((el, i) => {
    const d = (el.offsetTop + el.offsetHeight / 2 - mid) / el.offsetHeight;
    const a = Math.abs(d);
    el.style.transform = `rotateX(${Math.max(-80, Math.min(80, -d * 22))}deg) scale(${Math.max(.6, 1 - a * .14)})`;
    el.style.opacity = Math.max(.08, 1 - a * .42);
    el.style.filter = `blur(${Math.min(a * 1.1, 3)}px)`;
    if (Math.abs(d) < bd) { bd = Math.abs(d); best = i; }
  });
  show(best);
}
w.addEventListener('scroll', () => requestAnimationFrame(paint), { passive: true });
items.forEach(el => el.addEventListener('click', () =>
  w.scrollTo({ top: el.offsetTop + el.offsetHeight / 2 - w.clientHeight / 2, behavior: 'smooth' })));
const fit = () => { frameElement.style.height = document.body.scrollHeight + 'px'; paint(); };
addEventListener('resize', fit); fit();
</script>""".replace('PEOPLE', people), height=440)


def save_settings():
    ss = st.session_state
    ss['inv_dep'], ss['inv_tv'], ss['inv_view'] = ss['f_dep'], ss['f_tv'] / 100, 'account'


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
    a, b = st.columns([4, 1], vertical_alignment='center')
    ss.setdefault('inv_view', 'account')                           # state, not default=: save_settings also sets it
    view = a.segmented_control('view', ['account', 'settings'], key='inv_view', label_visibility='collapsed',
                               on_change=lambda: ss.update(inv_view=ss['inv_view'] or 'account'))   # no empty selection
    if b.button('log out', key='inv_logout', type='tertiary'):
        ss['investor'] = False
        st.rerun()
    if view == 'settings':
        with st.form('inv_settings'):
            st.number_input('deposit at the 31 dec 2025 close ($)', 100.0, 10_000_000.0, dep, 100.0, format='%.0f', key='f_dep')
            st.select_slider('risk budget: volatility target (% p.a.)', list(range(5, 31)), round(tv * 100), key='f_tv')
            note('the whole account is recalculated from 1 jan 2026 with these settings.')
            st.form_submit_button('save', type='primary', on_click=save_settings)
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
    signed = lambda v, kind: ('+' if v >= 0 else '') + num(v, kind)[0]
    neg = num(profit)[1]
    html(f'<div class="hero"><p class="k">balance &middot; as of the {lb.index[-1]:%d %b %Y} close</p>'.lower()
         + f'<p class="big">{num(value.iloc[-1], "usd")[0]}</p>'
         f'<p class="chg"><span class="{neg}">{signed(profit, "usd")} &nbsp;{signed(value.iloc[-1] / dep - 1, "pct")}</span>'
         f'<span class="dim"> since your ${dep:,.0f} deposit &middot; the s&amp;p 500 tr would be at '
         f'{num(bench_value.iloc[-1], "usd")[0]} ({signed(bench_value.iloc[-1] / dep - 1, "pct")}) &middot; '
         f'{tv:.0%} risk budget</span></p></div>')
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

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

from live import board
from strategy import (ASSETS, Params, intraday_value, load_intraday, load_live, load_prices, monthly, pair_targets, pension_mix,
                      run, wealth)
from replay import replay
from landing import landing
from statement import statement_pdf

FUND, FUND_LONG = 'MVP Strategies', 'Managed Volatility Portfolio'
REPO = 'https://github.com/Ben10Nova/FinancialModellingGroupN'
RESPONSIBLE = ('Noah van Raay', 'c/o Nova School of Business and Economics', 'Rua da Holanda 1', '2775-405 Carcavelos, Portugal')   # imprint
COLAB = 'https://colab.research.google.com/github/Ben10Nova/FinancialModellingGroupN/blob/main/vol-control_pair_v1.ipynb'
DEFAULTS = Params()
CODE = hashlib.md5((Path(__file__).parent / 'strategy.py').read_bytes()).hexdigest()   # cache key: new code = new results
MANDATE, DEMO_START = 100e6, '2026-01-01'           # sample mandate report: $100m from the 31 Dec 2025 close
CRISES = [  # S&P 500 peak and trough closes, what happened, what it shows
    ('Global financial crisis', '2007-10-09', '2009-03-09',
     'The US housing bust turned into a banking crisis. Lehman Brothers failed in September 2008 and the S&amp;P 500 lost more than half its value.',
     'The fall built up over many months, so the monthly reset had time to cut exposure before the worst of it.'),
    ('Euro debt crisis', '2011-04-29', '2011-10-03',
     'Markets feared that Greece, Italy and Spain could not pay their debts, and the US lost its AAA rating in August.',
     'Markets were calm going in, so exposure was high when it hit. Most of the drop came within a few weeks, faster than a monthly reset can react.'),
    ('Q4 2018 selloff', '2018-09-20', '2018-12-24',
     'The Fed kept raising rates while the trade war with China escalated. Stocks fell almost 20% into Christmas Eve.',
     'A calm summer meant exposure was close to the cap going in.'),
    ('COVID crash', '2020-02-19', '2020-03-23',
     'The pandemic shut down economies and the S&amp;P 500 fell a third in about a month, the fastest crash on record.',
     'The first leg down in late February hit at full exposure. The February month-end reset then cut it hard, which spared most of the March crash.'),
    ('2022 rate shock', '2022-01-03', '2022-10-12',
     'Inflation hit a 40-year high and the Fed raised rates faster than in decades. Stocks and bonds fell together.',
     'A slow grind lower, so exposure came down month by month as volatility picked up.')]
# photo: a file in assets/ or a full image url
# bio: education, internships, focus within the fund. rendered as html (innerHTML), not plain text
BIO_LUCAS = ('<p>BSc in International Business from Maastricht University, now completing an MSc in Finance at Nova SBE.</p>'
             '<p>Internships at KPMG, PradoNeo and Montag &amp; Montag.</p>')
BIO_BEN = ('<p>BSc from Maastricht University, now completing an MSc in Finance at Nova SBE.</p>'
           '<p>Internships at Simon-Kucher, DZ Bank and H.C.F. Hanse Corporate Finance.</p>')
BIO_KATHA = ('<p>BBA from WHU &ndash; Otto Beisheim School of Management, now completing an MSc in Finance at Nova SBE.</p>'
             '<p>Internships at BlackFin Capital Partners, Roland Berger and PwC.</p>')
BIO_NOAH = ('<p>BSc from the University of Münster, now completing an MSc in Finance at Nova SBE.</p>'
            '<p>Internships at Triton Partners, UBS and BNP Paribas CIB.</p>')
BIO_HENRIK = ('<p>BSc in International Business from Maastricht University, now completing an MSc in Finance at Nova SBE.</p>'
              '<p>Internships at Liberta Partners, REIA Capital and Deloitte.</p>')
BIO_CHRIS = ('<p>BBA in International Finance from the University of Augsburg, now completing an MSc in Finance at Nova SBE.</p>'
             '<p>Internships at EY and Salesfive.</p>')
TEAM = [  # name, photo, bio (html), linkedin url ('' hides the icon)
    ('Lucas S.', 'assets/lucas_strobel.jpg', BIO_LUCAS, ''),
    ('Ben S.', 'assets/ben_s.jpg', BIO_BEN, ''),
    ('Katha G.', 'assets/katha_g.jpg', BIO_KATHA, ''),
    ('Noah v. R.', 'assets/noah_vr.jpg', BIO_NOAH, ''),
    ('Henrik T.', 'assets/henrik_trillhaas.jpg', BIO_HENRIK, ''),
    ('Chris W.', 'assets/chris_w.jpg', BIO_CHRIS, '')]
LOADER = ('M0,134.8 5,134.4 10,137.7 15,132.2 20,128.2 25,128.8 30,127.6 35,126.4 41,127.5 46,129.3 51,131.2 56,130.3 61,129.5 66,129.5 71,124.2 76,123.9 81,124.0 86,120.1 91,123.6 96,119.8 101,115.4 106,112.6 111,114.6 116,115.9 122,113.9 127,110.9 132,110.7 137,109.9 142,107.3 147,104.5 152,103.1 157,98.8 162,100.2 167,97.1 172,94.1 177,90.5 182,89.7 187,87.2 192,84.7 197,84.4 203,85.2 208,84.5 213,83.0 218,83.1 223,77.8 228,72.6 233,68.5 238,67.4 243,63.9 248,67.8 253,63.8 258,67.2 263,65.0 268,62.8 273,66.0 278,64.7 284,60.9 289,48.8 294,48.8 299,48.5 304,51.0 309,46.0 314,44.0 319,42.5 324,42.8 329,44.4 334,42.5 339,42.7 344,39.2 349,36.9 354,31.3 359,33.5 365,27.2 370,27.0 375,21.6 380,18.8 385,14.9 390,14.7 395,12.6 400,10.0',                # all-time growth of $1, log scale, quarterly: portfolio
          'M0,135.2 5,134.1 10,134.9 15,131.7 20,129.9 25,128.5 30,129.0 35,126.4 41,130.8 46,130.4 51,133.7 56,144.0 61,150.0 66,147.5 71,142.4 76,140.3 81,138.7 86,134.6 91,137.3 96,134.3 101,130.8 106,128.4 111,130.3 116,131.3 122,129.2 127,126.5 132,126.8 137,125.7 142,123.1 147,120.4 152,118.0 157,116.2 162,115.4 167,113.1 172,111.9 177,109.9 182,110.2 187,108.3 192,107.7 197,108.0 203,110.5 208,107.8 213,105.6 218,106.2 223,103.3 228,101.3 233,99.7 238,97.9 243,94.0 248,96.4 253,93.8 258,95.1 263,95.0 268,91.4 273,90.7 278,89.8 284,87.2 289,91.1 294,86.3 299,86.2 304,81.0 309,76.2 314,74.1 319,72.1 324,72.7 329,76.1 334,75.9 339,78.3 344,76.1 349,75.1 354,71.1 359,74.5 365,68.7 370,67.0 375,63.2 380,61.8 385,59.4 390,62.5 395,57.3 400,54.2')                   # and s&p 500 tr
INK, MUTED, HAIR, NIGHT = '#0e1a2b', '#4d5866', '#dde3ea', '#071a3a'   # night = the sky of the home page photo
S1, S2, S3 = '#0e7c70', '#8c95a0', '#0b2648'                   # portfolio (aurora teal), S&P / equity sleeve, spread sleeve / base case

for f in (Path(__file__).parent / 'fonts').glob('*.ttf'):
    font_manager.fontManager.addfont(str(f))
plt.rcParams.update({
    'figure.facecolor': 'white', 'axes.facecolor': 'white', 'figure.dpi': 200,
    'font.family': 'sans-serif', 'font.sans-serif': ['IBM Plex Sans', 'DejaVu Sans'], 'font.size': 8.5,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False, 'axes.spines.bottom': False,
    'axes.grid': False,
    'xtick.color': MUTED, 'ytick.color': MUTED, 'xtick.major.size': 0, 'ytick.major.size': 0,
    'lines.solid_joinstyle': 'round', 'text.parse_math': False})   # '$' in labels is a dollar sign, never math

st.set_page_config(page_title='MVP Strategies', layout='centered', initial_sidebar_state='collapsed')
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap');
:root { --paper:#ffffff; --ink:#0e1a2b; --muted:#4d5866; --hairline:#dde3ea; --panel:#f5f7fa; --inputline:#7c8794;
  --night:#071a3a; --accent:#0e7c70; --aurora:#5fd4c0; --negative:#a3342b; --soft:#f5f7fa; --line:#d2d2d7; --r:18px; --serif:"Newsreader",Georgia,serif; --sans:"IBM Plex Sans",system-ui,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,monospace; }
html, body, .stApp, .stApp *:where(:not([data-testid="stIconMaterial"])), [role="dialog"] *:where(:not([data-testid="stIconMaterial"])) { font-family: var(--sans) !important; color: var(--ink); }
.stApp { background: var(--paper); }
.stApp * { transition: none !important; animation: none !important; }
[data-testid="stToolbarActions"], [data-testid="stMainMenu"], [data-testid="stAppDeployButton"],
[data-testid="stDecoration"], footer, #MainMenu, [data-testid="stHeaderActionElements"], [data-testid="stElementToolbar"],
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stHeader"] { background: var(--night) !important; border-bottom: 0; }
.block-container { max-width: 860px; padding: 60px 1.25rem 0; }
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
  background-color: transparent !important;
  background-image: linear-gradient(#fff,#fff), linear-gradient(#fff,#fff), linear-gradient(#fff,#fff) !important;
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
.stApp h3 { font-family: var(--serif) !important; font-size: 40px !important; font-weight: 400 !important; color: #fff !important;
  line-height: 1.15; letter-spacing: -.01em; margin: 0 0 30px !important; padding: 18px 0 30px !important;
  background: var(--night); box-shadow: 0 0 0 100vmax var(--night); clip-path: inset(-100px -100vmax 0); }   /* reaches up under the header */
.stApp h4 { font-family: var(--serif) !important; font-size: 22px !important; font-weight: 500 !important;
  margin: 34px 0 10px !important; padding: 0 !important; }

/* text */
a, a * { color: var(--ink) !important; text-decoration: underline !important; text-underline-offset: 3px; }
.stApp a:hover, .stApp a:hover * { color: var(--accent) !important; }
p.note, p.note * { font-size: 12.5px !important; color: var(--muted) !important; }
p.lede { font-family: var(--serif) !important; font-size: 19px !important; line-height: 1.45; max-width: 60ch; }
p.lede strong, .fig { font-family: var(--sans) !important; font-variant-numeric: tabular-nums lining-nums; font-weight: 600; }
.stApp p.fine, .stApp p.fine * { font-size: 11.5px !important; line-height: 1.55; color: var(--muted) !important; }
.items { list-style: none; margin: 0 0 16px; padding: 0; max-width: 72ch; }
.items > li { display: grid; grid-template-columns: 28px 1fr; margin: 0; padding: 9px 0; }
.items .mk { font-family: var(--sans) !important; font-variant-numeric: tabular-nums lining-nums; font-size: 13px !important; line-height: 24px; color: var(--muted) !important; }

/* tables */
table.plain { width: 100%; border-collapse: collapse; margin: 6px 0 10px; }
table.plain, table.plain tr, table.plain td, table.plain th { border: 0 !important; background: none !important; }
table.plain th { font-size: 11px !important; font-weight: 500; letter-spacing: .04em; color: var(--muted) !important;
  text-align: right; vertical-align: bottom; padding: 0 0 6px 14px; border-bottom: 1px solid var(--ink) !important; }
table.plain td { font-family: var(--sans) !important; font-variant-numeric: tabular-nums lining-nums; font-size: 13.5px !important;
  text-align: right; white-space: nowrap; padding: 6px 0 6px 14px; border-bottom: 1px solid var(--hairline) !important; }
table.plain th:first-child, table.plain td:first-child { text-align: left; padding-left: 0; }
table.plain td.label { font-family: var(--sans) !important; font-size: 13.5px !important; white-space: normal; }
table.plain td.em, table.plain tr.em td { font-weight: 600; }
table.plain td.neg { color: var(--negative) !important; }
table.plain td.dim { color: var(--muted) !important; }
table.plain tr.total td { font-weight: 600; border-bottom: 0 !important; }
table.plain tr.first td { border-top: 1px solid var(--ink) !important; }
table.plain.compact td { padding-top: 4px; padding-bottom: 4px; }
.scroll { overflow-x: auto; }
table.plain.heat { min-width: 640px; }
table.plain.heat th, table.plain.heat td { font-size: 12px !important; padding: 5px 5px; text-align: right; border-bottom: 1px solid #fff !important; }
table.plain.heat th.sep, table.plain.heat td.sep { padding-left: 12px; }
table.plain.heat td.ext { font-weight: 600; box-shadow: inset 0 0 0 1.5px var(--ink); }
table.plain.heat tr.total td { border-top: 1px solid var(--ink) !important; }
table.plain.heat td.g1 { background: rgba(29,90,150,0.09) !important; }
table.plain.heat td.g2 { background: rgba(29,90,150,0.18) !important; }
table.plain.heat td.g3 { background: rgba(29,90,150,0.27) !important; }
table.plain.heat td.g4 { background: rgba(29,90,150,0.36) !important; }
table.plain.heat td.g5 { background: rgba(29,90,150,0.45) !important; }
table.plain.heat td.r1 { background: rgba(163,52,43,0.09) !important; }
table.plain.heat td.r2 { background: rgba(163,52,43,0.18) !important; }
table.plain.heat td.r3 { background: rgba(163,52,43,0.27) !important; }
table.plain.heat td.r4 { background: rgba(163,52,43,0.36) !important; }
table.plain.heat td.r5 { background: rgba(163,52,43,0.45) !important; }
table.plain.terms td { text-align: left; white-space: normal; font-size: 14px !important; padding: 9px 0 9px 14px; vertical-align: top; }
table.plain.terms td.label { width: 28%; font-weight: 500; padding-left: 0; }

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
input, [data-baseweb="select"] * { font-family: var(--sans) !important; font-variant-numeric: tabular-nums lining-nums; font-size: 14px !important; background: transparent !important; }
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
  font-family: var(--sans) !important; font-variant-numeric: tabular-nums lining-nums; font-size: 12px !important; }
p.status i { display: inline-block; width: 9px; height: 9px; margin-right: 10px; border-radius: 50%; border: 1.5px solid var(--muted); }
p.status.on i { background: var(--accent); border-color: var(--accent); }

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
  font-family: var(--sans); font-variant-numeric: tabular-nums; font-size: 13px; line-height: 24px; color: var(--muted); }
.stApp [class*="st-key-dv_"] button[kind="tertiary"] * { font-size: 15px !important; line-height: 1.6; text-decoration: none !important;
  text-align: left; white-space: normal; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"] strong, .stApp .st-key-stress button[kind="tertiary"] p {
  text-decoration: underline !important; text-decoration-thickness: 1px !important; text-underline-offset: 3px; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"]:hover, .stApp .st-key-stress button[kind="tertiary"]:hover { background: var(--panel) !important; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"] p::after, .stApp .st-key-stress button[kind="tertiary"] p::after {
  content: "↗"; margin-left: 6px; font-family: var(--sans); font-size: 13px; color: var(--ink); display: inline-block; text-decoration: none; }
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
.st-key-stress p.c { font-family: var(--sans) !important; font-variant-numeric: tabular-nums lining-nums; font-size: 13.5px !important; text-align: right; }
.st-key-stress p.c.em { font-weight: 600; } .st-key-stress p.c.neg { color: var(--negative) !important; }
.st-key-stress p.dim { font-size: 12.5px !important; color: var(--muted) !important; text-align: left; } .st-key-stress p.th.l { text-align: left; }
.stApp .st-key-stress button[kind="tertiary"] * { font-size: 13.5px !important; text-align: left; }
.st-key-stress p.win { display: none; }
[role="dialog"] :not([data-testid="stMarkdown"]) > [data-testid="stMarkdownContainer"] p { font-family: var(--serif) !important; font-weight: 500 !important; font-size: 28px !important; }
img.chart { display: block; width: 100%; height: auto; margin: 6px 0 18px; }
img.chart.m { display: none; }

/* plain layer: sections are marked by rules, not boxes */
.stApp .st-key-knobs, .stApp [data-testid="stForm"] { background: none !important; border: 0 !important; border-top: 1px solid var(--ink) !important;
  border-bottom: 1px solid var(--hairline) !important; border-radius: 0 !important; padding: 18px 0 !important; }
.stApp button[kind="primaryFormSubmit"], .stApp button[kind="primary"] { border-radius: 980px !important; padding: 0 26px !important; }
[data-testid="stButtonGroup"] > div { gap: 22px !important; display: inline-flex !important; }
.stApp [data-testid="stButtonGroup"] button { border: 0 !important; border-radius: 0 !important; background: transparent !important;
  min-height: 30px !important; padding: 0 0 4px !important; box-shadow: none !important; }
.stApp [data-testid="stButtonGroup"] button[kind*="Active"] { box-shadow: inset 0 -2px 0 var(--accent) !important; }
.stApp [data-testid="stButtonGroup"] button * { font-size: 14px !important; color: var(--muted) !important; font-weight: 500; }
.stApp [data-testid="stButtonGroup"] button[kind*="Active"] * { color: var(--ink) !important; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"]:hover, .stApp .st-key-stress button[kind="tertiary"]:hover { background: none !important; }
.stApp [class*="st-key-dv_"] button[kind="tertiary"]:hover *, .stApp .st-key-stress button[kind="tertiary"]:hover * { color: var(--accent) !important; }
[data-testid="stDialog"] > div { background: rgba(7,26,58,.45) !important; }
[role="dialog"] { border-radius: 4px !important; border: 0 !important; border-top: 3px solid var(--night) !important;
  box-shadow: 0 24px 60px rgba(7,26,58,.25) !important; }
.stApp [data-testid="stSidebar"] { border-right: 1px solid var(--hairline) !important; }
[data-testid="stHorizontalBlock"]:has([data-testid="stButtonGroup"]) { flex-wrap: nowrap !important; }
[data-testid="stHorizontalBlock"]:has([data-testid="stButtonGroup"]) > [data-testid="stColumn"] { min-width: 0 !important; }
[data-testid="stHorizontalBlock"]:has([data-testid="stButtonGroup"]) .stButton { display: flex; justify-content: flex-end; }
.stApp [data-testid="stExpander"] details { border: 0 !important; border-top: 1px solid var(--hairline) !important;
  border-bottom: 1px solid var(--hairline) !important; border-radius: 0 !important; background: none; }
.stApp [data-testid="stExpander"] summary { padding-left: 0 !important; padding-right: 0 !important; }
.stApp [data-testid="stExpander"] summary p { font-size: 13px !important; }

/* footer on every page */
.site-foot { margin: 72px 0 0; padding: 30px 0 44px; background: var(--night); box-shadow: 0 0 0 100vmax var(--night);
  clip-path: inset(0 -100vmax -100vmax); }
.site-foot p, .site-foot a { font-size: 12.5px !important; line-height: 1.55; color: #c9d3e0 !important; }
.site-foot p.links { margin-top: 8px; }

/* top navigation */
[data-testid="stTopNavLinkContainer"] a, [data-testid="stTopNavLink"] { text-decoration: none !important; }
[data-testid="stTopNavLink"] *, [data-testid="stTopNavSection"] * { font-size: 14px !important; color: #fff !important; text-decoration: none !important; }
[data-testid="stTopNavSection"] svg { fill: #fff !important; }
[data-testid="stTopNavLink"]:hover, [data-testid="stTopNavSection"]:hover { background: rgba(255,255,255,.1) !important; }
[data-testid="stTopNavLink"][aria-current="page"]:not([href$="/assumptions"]) { box-shadow: inset 0 -2px 0 var(--aurora); border-radius: 0 !important;
  background: none !important; }
[data-testid="stTopNavLink"][aria-current="page"] * { font-weight: 600 !important; }
[data-testid="stToolbar"] { padding: 0 clamp(20px, 4vw, 64px) 0 clamp(0px, 4vw - 24px, 40px) !important; }
div:has(> div > div > [data-testid="stTopNavLinkContainer"]) > :nth-child(1) { margin-right: auto !important; }
div:has(> div > div > [data-testid="stTopNavLinkContainer"]) > :nth-child(1) [data-testid="stTopNavLink"] { background: none !important; box-shadow: none !important; }
div:has(> div > div > [data-testid="stTopNavLinkContainer"]) > :nth-child(1) [data-testid="stTopNavLink"] span { font-size: 0 !important; }
div:has(> div > div > [data-testid="stTopNavLinkContainer"]) > :nth-child(1) [data-testid="stTopNavLink"] span::before {
  content: "MVP Strategies"; font-family: var(--serif) !important; font-size: 23px; font-weight: 500; letter-spacing: .005em; }
[data-baseweb="popover"]:has([data-testid="stTopNavPopover"]) { background: transparent !important; }
[data-baseweb="popover"]:has([data-testid="stTopNavPopover"]) > div { background: rgba(7,26,58,.82) !important; backdrop-filter: blur(18px) saturate(1.4);
  -webkit-backdrop-filter: blur(18px) saturate(1.4); border: 1px solid rgba(255,255,255,.14); border-radius: 12px !important;
  box-shadow: 0 12px 32px rgba(7,26,58,.25) !important; overflow: hidden; }
[data-baseweb="popover"]:has([data-testid="stTopNavPopover"]) a, [data-baseweb="popover"]:has([data-testid="stTopNavPopover"]) a * { color: #fff !important; }
[data-baseweb="popover"]:has([data-testid="stTopNavPopover"]) a:hover { background: rgba(255,255,255,.12) !important; }
[data-testid="stTopNavPopover"], [data-testid="stTopNavPopover"] * { background: transparent !important; }
[data-baseweb="popover"] a, [data-baseweb="popover"] a * { text-decoration: none !important; font-size: 14px !important; }

div:has(> div > div > [data-testid="stTopNavLinkContainer"]) > :nth-child(1) { order: 0 !important; }   /* Overview */
div:has(> div > div > [data-testid="stTopNavLinkContainer"]) > :nth-child(2) { order: 1 !important; }   /* Test your assumptions */
div:has(> div > div > [data-testid="stTopNavLinkContainer"]) > :nth-child(4) { order: 2 !important; }   /* Strategy */
div:has(> div > div > [data-testid="stTopNavLinkContainer"]) > :nth-child(5) { order: 3 !important; }   /* Results */
div:has(> div > div > [data-testid="stTopNavLinkContainer"]) > :nth-child(6) { order: 4 !important; }   /* Backtest & analysis */
[data-testid="stTopNavLink"][href$="/assumptions"] { background: #fff !important; border-radius: 980px !important; padding: 0 16px !important; }
[data-testid="stHeader"] [data-testid="stTopNavLink"][href$="/assumptions"] * { color: var(--night) !important; font-weight: 500 !important; }
[data-testid="stSidebarNav"] a[href$="/assumptions"] * { font-weight: 600 !important; }
div:has(> div > div > [data-testid="stTopNavLinkContainer"]) > :nth-child(3) { order: 5 !important; }   /* Team */
div:has(> div > div > [data-testid="stTopNavLinkContainer"]) > :nth-child(n+7) { order: 6 !important; }

/* sample mandate report */
.st-key-mr_pdf { display: flex; justify-content: flex-end; }
.stApp .st-key-mr_pdf button { background: var(--ink) !important; border-radius: 980px !important; padding: 0 22px !important;
  min-height: 36px !important; }
.stApp .st-key-mr_pdf button * { color: var(--paper) !important; text-decoration: none !important; font-size: 13.5px !important; font-weight: 500; }
.stApp .st-key-mr_pdf button p { white-space: nowrap; }
@media (max-width: 640px) { .stApp .st-key-mr_pdf button { padding: 0 14px !important; } .stApp .st-key-mr_pdf button * { font-size: 12.5px !important; } }
.hero { margin: 28px 0 8px; }
.hero p { margin: 0 !important; }
.hero p.k { font-size: 12.5px !important; color: var(--muted) !important; }
.hero p.big { font-family: var(--serif) !important; font-size: 64px !important; font-weight: 400; line-height: 1.1;
  letter-spacing: -.02em; font-variant-numeric: tabular-nums lining-nums; margin: 2px 0 6px !important; }
.hero p.chg, .hero p.chg span { font-size: 14px !important; }
.hero p.chg span:first-child { font-family: var(--sans) !important; font-variant-numeric: tabular-nums lining-nums; font-weight: 600; }
.hero span.neg { color: var(--negative) !important; } .hero span.dim { color: var(--muted) !important; }

@media (max-width: 640px) {
  img.chart.d { display: none; } img.chart.m { display: block; }
  input, textarea, [data-baseweb="select"] * { font-size: 16px !important; }
  h1.bh { font-size: 46px !important; } p.long { font-size: 17px !important; } .stApp h3 { font-size: 28px !important; }
  .st-key-stress [data-testid="stColumn"]:has(p.dim), .st-key-stress [data-testid="stColumn"]:has(p.wh) { display: none !important; }
  .stApp .st-key-stress button[kind="tertiary"] * { font-size: 12.5px !important; line-height: 1.35; }
  .st-key-stress p.c { font-size: 11.5px !important; } .st-key-stress p.th { font-size: 10px !important; }
  .st-key-stress p.win { display: block; white-space: nowrap; font-size: 11px !important; color: var(--muted) !important; }
  .hero p.big { font-size: 46px !important; }
}
</style>
""", unsafe_allow_html=True)

html = lambda s: st.markdown(s, unsafe_allow_html=True)
heading = lambda t: html(f'<h3>{t}</h3>')
note = lambda t: html(f'<p class="note">{t}</p>')
PF, SP = 'Portfolio (net)', 'S&amp;P 500 TR'                          # column labels
ROWS = {  # table row labels; the keys are strategy.py's row names
    'Ann. avg return': 'Average annual return (arithmetic)', 'Ann. volatility': 'Volatility (annualised)',
    'Sharpe ratio': 'Sharpe ratio', 'Alpha (ann.)': 'Alpha (annualised)', 'Alpha t-stat': 'Alpha t-statistic', 'Beta': 'Beta',
    'Information ratio': 'Information ratio', 'Max drawdown (monthly)': 'Max drawdown (month-end)',
    'Max drawdown (daily)': 'Max drawdown (daily)',
    'Skewness': 'Skewness', 'Excess kurtosis': 'Excess kurtosis', 'VaR 95%, historical': 'Value at risk 95%, historical',
    'VaR 95%, normal': 'Value at risk 95%, normal', 'VaR 99%, normal': 'Value at risk 99%, normal',
    'VaR 99%, Cornish-Fisher': 'Value at risk 99%, Cornish-Fisher', 'CVaR 95% (expected shortfall)': 'Expected shortfall 95%',
    'Worst month': 'Worst month', 'Positive months': 'Share of positive months', 'Sortino ratio': 'Sortino ratio',
    'Calmar ratio': 'Calmar ratio', 'Upside capture': 'Upside capture', 'Downside capture': 'Downside capture',
    'Tracking error': 'Tracking error', 'Active IR (vs S&P 500 TR)': 'Information ratio against the S&amp;P 500 TR',
    'Alpha t-stat, Newey-West': 'Alpha t-statistic, Newey-West'}
PCT_ROWS = {'Ann. avg return', 'Ann. volatility', 'Alpha (ann.)', 'Max drawdown (monthly)', 'Max drawdown (daily)',
            'VaR 95%, historical', 'VaR 95%, normal', 'VaR 99%, normal', 'VaR 99%, Cornish-Fisher',
            'CVaR 95% (expected shortfall)', 'Worst month', 'Positive months', 'Upside capture', 'Downside capture', 'Tracking error'}


def num(v, kind='pct'):
    """formatted text and css class; true minus sign for negatives"""
    if pd.isna(v):
        return '–', ''
    v = round(float(v), 8) + 0.0
    s = {'pct': f'{v:.1%}', 'x': f'{v:.2f}', 'usd': f'${abs(v):,.2f}', 'm': f'${abs(v) / 1e6:,.2f}m'}[kind]
    return ('−' + s.lstrip('-') if v < 0 else s), ('neg' if v < 0 else '')


def td(v, kind='pct', cls=''):
    s, neg = num(v, kind)
    return f'<td class="{cls} {neg}">{s}</td>'


def metrics_table(df, bold):
    head = '<tr><th></th>' + ''.join(f'<th>{c}</th>' for c in df.columns) + '</tr>'
    body = ''.join(f'<tr><td class="label">{ROWS.get(i, i)}</td>' + ''.join(
        td(v, 'pct' if i in PCT_ROWS else 'x', 'em' if c == bold else '') for c, v in row.items()) + '</tr>'
        for i, row in df.iterrows())
    html(f'<table class="plain">{head}{body}</table>')


def show(fig):
    """inline png (no media file a redeploy can lose), drawn twice: full width for desktop and narrower for phones,
    so phone labels stay readable instead of shrinking with the picture"""
    imgs = []
    for cls, w in (('d', None), ('m', 4.2)):
        if w:
            wd, ht = fig.get_size_inches()
            fig.set_size_inches(w, ht * 1.3)
        fig.tight_layout(pad=.3)
        buf = BytesIO()
        fig.savefig(buf, format='png')
        imgs.append(f'<img class="chart {cls}" alt="" src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}">')
    html(''.join(imgs))
    plt.close(fig)


def chart(title, series, kind='growth', h=2.9, bands=()):
    legend = ''.join(f'<span><i style="background:{c}"></i>{n}</span>' for n, _, c in series) if len(series) > 1 else ''
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
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: num2date(v).strftime('%b')))
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


@st.cache_data(persist='disk', show_spinner=False)          # 2006-2025 never changes: one download per container
def get_prices():
    return load_prices()


@st.cache_data(show_spinner=False)
def get_results(code, **kw):
    return run(get_prices(), Params(**kw))


@st.cache_data(ttl=3600, show_spinner='loading live prices ...')   # one live download per hour, whatever the settings
def live_prices():
    return load_live()


@st.cache_data(ttl=60, show_spinner=False)                         # one download a minute, shared by all visitors
def get_intraday(code=CODE):
    return load_intraday()


@st.cache_data(ttl=3600, show_spinner=False)
def get_live(target_vol=DEFAULTS.target_vol, code=CODE):
    px = live_prices()
    return run(px, Params(start=DEMO_START, end=str(px.index[-1].date()), target_vol=target_vol)), px


def results(custom=False):
    """the base case on every page; only Your assumptions uses the visitor's settings"""
    p = st.session_state.get('params', DEFAULTS) if custom else DEFAULTS
    try:
        return p, get_results(CODE, **asdict(p))
    except RuntimeError as e:
        note(str(e))
        st.stop()


# ================================================================ pages
HOME_CSS = """
.st-key-hero iframe { position: fixed !important; inset: 0; width: 100vw !important; height: 100vh !important; height: 100dvh !important;
  z-index: 0; border: 0; }
.stApp, [data-testid="stMain"] { background: #06122e !important; overflow: hidden !important; }
.site-foot { display: none; }
[data-testid="stHeader"] { background: transparent !important; border-bottom: 0 !important; }
[data-testid="stHeader"] [data-testid="stTopNavLink"] *, [data-testid="stHeader"] [data-testid="stTopNavSection"] *,
[data-testid="stHeader"] button * { color: #fff !important; }
[data-testid="stHeader"] [data-testid="stTopNavSection"] svg { fill: #fff !important; }
[data-testid="stTopNavLink"][href$="/assumptions"] { background: rgba(255,255,255,.16) !important; box-shadow: inset 0 0 0 1px rgba(255,255,255,.5); }
[data-testid="stHeader"] [data-testid="stTopNavLink"][href$="/assumptions"] * { color: #fff !important; }
[data-baseweb="popover"]:has([data-testid="stTopNavPopover"]) > div { background: rgba(8,22,56,.42) !important; border-color: rgba(255,255,255,.18) !important; }
.st-key-hero > div, .st-key-hero { height: 0 !important; min-height: 0 !important; }
.st-key-foot { position: fixed; left: 0; right: 0; bottom: 12px; width: auto !important; z-index: 2; }   /* centred: streamlit's own badge sits bottom right */
.st-key-foot button * { color: rgba(255,255,255,.75) !important; font-size: 12.5px !important; }
"""


def home():
    html(f'<style>{HOME_CSS}</style>')                             # only while this page shows: header over the photo
    with st.container(key='hero'):
        try:                                                       # hero at the base case
            landing(get_results(CODE, **asdict(DEFAULTS)), FUND, FUND_LONG)
        except RuntimeError:                                       # no prices (Yahoo limit): plain name
            html(f'<div class="home"><div class="mid"><h1 class="bh">{FUND}</h1><p class="long">{FUND_LONG}</p></div></div>')
    with st.container(key='foot', horizontal=True, horizontal_alignment='center', gap='medium'):
        if st.button('Imprint', type='tertiary'):
            dive('Imprint', lambda: html(
                f'<p>{FUND} is a student project for the course 2270 Financial Modeling at Nova SBE. It is not a company '
                'or a registered investment firm and offers no financial services.</p>'
                f'<p>Responsible for this website:<br>{"<br>".join(RESPONSIBLE)}</p>'
                '<p>All figures are hypothetical backtests on historical data. Nothing on this site is investment advice or '
                'an offer to buy or sell any security. Past performance does not predict future results.</p>'
                '<p>We check our content carefully but give no guarantee that it is complete, correct or up to date. We are '
                'not responsible for the content of external sites we link to.</p>'
                '<p>Privacy: we don\'t set cookies or collect personal data ourselves. The sample mandate report stores nothing '
                'you enter. The site runs on Streamlit Community Cloud, and fonts load from Google Fonts, which receives your '
                'IP address when you visit.</p>'
                '<p>Market data: Yahoo Finance.</p>'))
        if st.button('Data and method', type='tertiary'):
            dive('Data and method', lambda: html(
                '<p>Data from Yahoo Finance, adjusted for splits and dividends: SPY, the nine original Select Sector SPDR ETFs, '
                'the S&amp;P 500 total return index (^SP500TR) and the 13-week T-bill yield (^IRX).</p>'
                '<p>Statistics use monthly returns. Means are multiplied by 12, volatilities by &radic;12, and beta is not '
                'annualised.</p>'
                f'<p><a href="{COLAB}">Notebook</a> &middot; <a href="{REPO}">Source code</a></p>'))


def sleeve_facts():
    p, res = results()
    sl = res['sleeves']
    corr = monthly(res['spy_only'].net).corr(monthly(res['pair_only'].net))
    sp_dd = res['table'].loc['Max drawdown (monthly)', 'S&P 500 TR']
    return p, sl, corr, sp_dd


def thesis_equity():
    p, sl, _, sp_dd = sleeve_facts()
    e = sl['Vol-managed SPY only']
    return ['Volatility comes in clusters. A wild week is usually followed by another wild week, and a calm month by another '
            'calm month. Markets also tend to fall hardest when they are already nervous.',
            f'So we don\'t hold a fixed amount of the S&amp;P 500. At each month-end we check how much SPY moved over the last '
            f'21 trading days and size the position so that its risk lands on target. In a calm market the position is bigger, '
            f'up to {p.max_lev:.2f}x. In a nervous market it is smaller, and the rest sits in T-bills.',
            f'On its own this sleeve returned <span class="fig">{num(e["Ann. avg return"])[0]}</span> a year, with a largest '
            f'month-end drawdown of <span class="fig">{num(e["Max drawdown (monthly)"])[0]}</span>. The S&amp;P 500 fell '
            f'<span class="fig">{num(sp_dd)[0]}</span>.',
            'The cost: after a crash exposure is low, just when markets bounce back, so the sleeve misses part of the rebound.']


def thesis_spread():
    p, sl, corr, _ = sleeve_facts()
    s = sl['Pair only (+ T-bills)']
    return ['Utilities, consumer staples and health care sell things people buy in good times and bad: power, food and '
            'medicine. These sectors react little to the market, and they tend to move together.',
            f'Sometimes one runs ahead of the other for a few weeks for no lasting reason. We measure the gap as a z-score, '
            f'which says how far the price ratio is from its 60-day average in standard deviations. Beyond {p.z_in:g} we buy the '
            f'sector that fell behind and short the one that ran ahead. Once the gap is back under {p.z_out:g}, we close both.',
            f'One leg is long and one is short, so the direction of the market mostly cancels out. The beta of this sleeve is '
            f'<span class="fig">{num(s["Beta"], "x")[0]}</span>, its return on its own '
            f'<span class="fig">{num(s["Ann. avg return"])[0]}</span> a year, and its correlation with the equity sleeve '
            f'<span class="fig">{num(corr, "x")[0]}</span>.']


def term_sheet():
    """the strategy as a pension consultant would read it: one row per question"""
    res = get_results(CODE, **asdict(DEFAULTS))
    d = DEFAULTS
    rows = [
        ('Objective', 'Equity-like long-run growth with much smaller drawdowns than the S&amp;P 500, for the '
                      'return-seeking part of a pension scheme.'),
        ('Comparator', 'S&amp;P 500 total return index.'),
        ('Risk budget', f'{d.target_vol:.0%} annualised volatility for the whole portfolio.'),
        ('Instruments', 'SPY and the nine original Select Sector SPDR ETFs. Uninvested cash earns the 3-month T-bill rate.'),
        ('Exposure', f'Equity up to {d.max_lev:.1f}x at each monthly reset. Gross exposure including the sector spread '
                     f'reached {res["bt"].gross_exposure.max():.1f}x in the backtest.'),
        ('Implementation', 'Needs short selling and leverage. EU schemes may borrow only temporarily for liquidity '
                           '(IORP II, Art. 19), so they would hold the strategy through an investment fund or use futures '
                           'and swaps instead of borrowed cash.'),
        ('Liquidity', 'All positions are daily-liquid ETFs. Equity is rebalanced monthly; the spread trades on its signal.'),
        ('Currency', 'US dollars, not hedged.'),
        ('Costs assumed', f'{d.cost * 1e4:.0f} bp per unit traded, T-bill rate plus {d.fin_spread * 1e4:.0f} bp on borrowed '
                          f'cash, {d.short_fee * 1e4:.0f} bp a year to borrow the short leg.'),
        ('Track record', 'Backtest from January 2006 to December 2025. The rules were then frozen and have run live since '
                         '1 January 2026.')]
    html('<table class="plain terms">' + ''.join(f'<tr><td class="label">{k}</td><td>{v}</td></tr>' for k, v in rows) + '</table>')


def thesis():
    heading('Investment approach')
    html('<p>The portfolio has two parts that share one 15% volatility budget.</p>')
    clickable('thesis', [('Volatility-targeted equity.', 'We hold the S&P 500 and scale exposure with realised volatility: more '
                          'in calm markets, less in stressed ones. This sleeve gets whatever risk budget the spread sleeve '
                          'does not use.', thesis_equity),
                         ('Defensive sector spread.', 'A beta-neutral position between the two most defensive US equity '
                          'sectors, which trades the reversal of temporary gaps between them.', thesis_spread)])
    html('<p>The two sleeves earn their returns from different sources. In the backtest the combined portfolio did better '
         'than either sleeve on its own, with lower volatility and much smaller drawdowns than the S&amp;P 500.</p>')
    html('<h4>For pension schemes</h4>')
    term_sheet()


PENSION_ROWS = [('Ann. avg return', 'pct'), ('Ann. volatility', 'pct'), ('Sharpe ratio', 'x'), ('Beta', 'x'),
                ('Max drawdown (monthly)', 'pct'), ('Return in 2008', 'pct'), ('Upside capture', 'pct'),
                ('Downside capture', 'pct'), ('Tracking error', 'pct'), ('Value at the end ($)', 'm'),
                ('Change in 2008 ($)', 'm'), ('Largest fall from a peak ($)', 'm')]


SLEEVES = [10, 25, 50, 100, 250, 500, 1_000, 2_500, 5_000, 10_000]   # $m, choices for the equity sleeve


def save_pension():
    ss = st.session_state
    ss['pm'] = (ss['f_pm_size'] * 1e6, ss['f_pm_share'] / 100, ss['f_pm_fee'] / 100)


def pension():
    heading('In a pension portfolio')
    html('<p class="lede">The strategy is built to replace part of a pension scheme&rsquo;s US equities, not to sit on top of '
         'them. It runs at about the volatility of the S&amp;P 500, so the swap leaves total risk roughly where it was, while '
         'market exposure and crash losses come down.</p>')
    ss = st.session_state
    size, share, fee = ss.setdefault('pm', (MANDATE, .20, .005))
    with st.container(key='knobs'):                                # same panel as Test your assumptions; updates as you drag
        c = st.columns(3, gap='large', vertical_alignment='bottom')
        c[0].select_slider('US equity sleeve', SLEEVES, round(size / 1e6), key='f_pm_size', on_change=save_pension,
                           format_func=lambda v: f'${v:,}m' if v < 1000 else f'${v / 1000:g}bn')
        c[1].slider('Share moved into the strategy', 0, 100, round(share * 100), 5, format='%d%%', key='f_pm_share',
                    on_change=save_pension)
        c[2].slider('Management fee, a year', 0.0, 2.0, round(fee * 100, 2), 0.05, format='%.2f%%', key='f_pm_fee',
                    on_change=save_pension)
    p, res = results()
    mix, t = pension_mix(monthly(res['bt'].net), res['rf_m'], monthly(res['bench_d']), share, fee, size)
    w, b = t['With the strategy'], t['All in the S&P 500 TR']
    mixed = f'{1 - share:.0%} S&amp;P 500 + {share:.0%} strategy'
    dollars = lambda v: ('−' if v < 0 else '') + f'${abs(v) / 1e6:,.1f}m'          # one decimal, as on the mandate report
    html(f'<div class="hero"><p class="k">A ${size / 1e6:,.0f}m US equity sleeve from January {p.start[:4]} to the '
         f'{mix.index[-1]:%b %Y} month-end</p><p class="big">{dollars(w["Value at the end ($)"])}</p>'
         f'<p class="chg"><span class="{num(w["Value at the end ($)"] - b["Value at the end ($)"])[1]}">'
         f'{("+" if w["Value at the end ($)"] >= b["Value at the end ($)"] else "") + dollars(w["Value at the end ($)"] - b["Value at the end ($)"])}</span><span class="dim"> against '
         f'{dollars(b["Value at the end ($)"])} all in the S&amp;P 500 TR &middot; 2008: '
         f'{("+" if w["Change in 2008 ($)"] >= 0 else "") + dollars(w["Change in 2008 ($)"])} instead of '
         f'{("+" if b["Change in 2008 ($)"] >= 0 else "") + dollars(b["Change in 2008 ($)"])}</span></p></div>')
    if share > 0:
        fig = lambda s: f'<span class="fig">{s}</span>'
        d_ret = w['Ann. avg return'] - b['Ann. avg return']
        html(f'<p>Moving {fig(f"{share:.0%}")} of the sleeve into the strategy takes its beta from {fig("1.00")} to '
             f'{fig(num(w["Beta"], "x")[0])} and its largest month-end drawdown from {fig(num(b["Max drawdown (monthly)"])[0])} '
             f'to {fig(num(w["Max drawdown (monthly)"])[0])}, with volatility at {fig(num(w["Ann. volatility"])[0])} against '
             f'{fig(num(b["Ann. volatility"])[0])}. The average return changes by '
             f'{fig(("+" if d_ret >= 0 else "−") + f"{abs(d_ret) * 100:.1f} pp")} a year after the fee.</p>')
    head = f'<tr><th></th><th>{mixed}</th><th>{SP}</th></tr>'
    body = ''.join(f'<tr><td class="label">{ROWS.get(k, k)}</td>{td(w[k], kind, "em")}{td(b[k], kind)}</tr>'
                   for k, kind in PENSION_ROWS)
    html(f'<table class="plain">{head}{body}</table>')
    chart('Growth of $1, log scale', [(mixed, wealth(mix), S1), (SP, wealth(monthly(res['bench_d'])), S2)])
    chart('Drawdown, month-end', [(mixed, wealth(mix), S1), (SP, wealth(monthly(res['bench_d'])), S2)], kind='drawdown', h=2.2)
    note(f'Backtest {p.start[:4]}&ndash;{p.end[:4]}, monthly returns. The strategy slice is net of the modelled trading, '
         'financing and borrow costs and of the management fee set above, charged monthly. The S&amp;P 500 slice is held at no '
         'cost. The split goes back to target at each month-end. Interest-rate risk on the liabilities stays with the '
         'scheme&rsquo;s liability-hedging portfolio and is not part of this view.')


KNOBS = [  # params field, label, min, max, step, shown as field x scale, format
    ('target_vol', 'Volatility target (% a year)', 5.0, 30.0, 0.5, 100, '%.1f'),
    ('max_lev', 'Maximum equity exposure (x)', 1.0, 3.0, 0.05, 1, '%.2f'),
    ('pair_size', 'Spread size per leg, average (x)', 0.25, 2.0, 0.05, 1, '%.2f'),
    ('z_in', 'Spread entry threshold (|z|)', 1.0, 4.0, 0.1, 1, '%.1f'),
    ('cost', 'Trading cost (bp per unit traded)', 0.0, 100.0, 1.0, 1e4, '%.0f'),
    ('fin_spread', 'Financing spread over T-bills (bp a year)', 0.0, 500.0, 5.0, 1e4, '%.0f'),
    ('short_fee', 'Borrow fee on shorts (bp a year)', 0.0, 500.0, 5.0, 1e4, '%.0f')]


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


def daily_dd(r):
    w = wealth(r)
    return (w / w.cummax() - 1).min()


def with_daily_dd(table, bt, bench):
    """add the daily max drawdown under the month-end one: the drawdown chart is daily, so both belong in the table"""
    t = table.copy()
    t.loc['Max drawdown (daily)'] = [daily_dd(bt.net), daily_dd(bench)]
    return t


def performance_view(p, res):
    bt, bench = res['bt'], res['bench_d']
    w_s, w_b = wealth(bt.net), wealth(bench)
    replay(res, p, DEFAULTS)                                       # lede + growth of $1 with year-by-year replay
    metrics_table(with_daily_dd(res['table'], bt, bench).rename(columns={'Strategy (net)': PF, 'S&P 500 TR': SP}), PF)
    chart('Drawdown, daily', [(PF, w_s, S1), (SP, w_b, S2)], kind='drawdown', h=2.2)
    rf_d = (get_prices()['^IRX'] / 100 / 252).shift(1).loc[bt.index]
    csv = monthly(pd.DataFrame({'portfolio_net': bt.net, 'portfolio_gross': bt.gross, 'equity_sleeve': res['spy_only'].net,
                                'spread_sleeve': res['pair_only'].net, 'sp500_tr': bench, 'rf': rf_d}))
    st.download_button('Download monthly returns (CSV)', csv.to_csv(index_label='month', float_format='%.6f'),
                       file_name=f'monthly_returns_{p.start[:4]}_{p.end[:4]}.csv', mime='text/csv', type='tertiary')


def performance():
    heading('Performance')
    p, res = results()
    performance_view(p, res)
    html('<p style="margin-top:18px"><a href="/assumptions" target="_self">Test your own assumptions &rarr;</a></p>')


def assumptions():
    heading('Test your assumptions')
    html('<p class="lede">Change any assumption, press Run, and see how the result compares with the base case and the '
         'S&amp;P 500.</p>')
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
        st.slider('Years', 2006, 2025, key='years')
        b = st.columns([4, 2, 1], vertical_alignment='center')
        b[0].checkbox('Include the sector spread', key='pair_on')
        b[1].button('Reset to the base case', type='tertiary', on_click=load_knobs, args=(DEFAULTS, True))
        b[2].button('Run', type='primary', on_click=apply_knobs)
    if ss.pop('bad_years', False):
        note('The end year must be after the start year.')
    p, res = results(custom=True)
    bt, bench = res['bt'], res['bench_d']
    mine = with_daily_dd(res['table'], bt, bench)
    if p == DEFAULTS:
        note('These are the base-case figures shown on every other page. Change a setting above and press Run.')
        table = mine.rename(columns={'Strategy (net)': PF, 'S&P 500 TR': SP})
        lines = [(PF, wealth(bt.net), S1), (SP, wealth(bench), S2)]
    else:                                                          # base case over the same years, so only the rules differ
        base = get_results(CODE, **{**asdict(DEFAULTS), 'start': p.start, 'end': p.end})
        table = pd.DataFrame({'Your assumptions': mine['Strategy (net)'],
                              'Base case': with_daily_dd(base['table'], base['bt'], base['bench_d'])['Strategy (net)'],
                              SP: mine['S&P 500 TR']})
        lines = [('Your assumptions', wealth(bt.net), S1), ('Base case', wealth(base['bt'].net), S3), (SP, wealth(bench), S2)]
        note(f'Your assumptions against the base case over the same years ({p.start[:4]}&ndash;{p.end[:4]}). Every other page '
             'shows the base case.')
    metrics_table(table, table.columns[0])
    chart('Growth of $1, log scale', lines)


def shade(v, full):
    """css class for a return cell: g1-g5 up, r1-r5 down, darker the bigger (full = return at the darkest shade).
    classes, not inline styles: streamlit strips style attributes"""
    return ('g' if v >= 0 else 'r') + str(min(int(abs(v) / full * 5) + 1, 5))


def month_grid(r, rf_m):
    """month-by-year returns as a heat map, with each year's return, volatility, sharpe and share of positive months"""
    m = monthly(r)
    y = m.index.year
    grid = m.groupby([y, m.index.month]).first().unstack()
    ex = m - rf_m.loc[m.index]
    year = pd.DataFrame({'ret': (1 + m).groupby(y).prod() - 1, 'vol': m.groupby(y).std() * 12 ** .5,
                         'sharpe': ex.groupby(y).mean() / ex.groupby(y).std() * 12 ** .5, 'up': (m > 0).groupby(y).mean()})
    pc = lambda v: '' if pd.isna(v) else num(round(v, 3))[0].rstrip('%')            # round first: no "−0.0"
    cell = lambda v, full, cls='': f'<td class="{cls} {shade(v, full)}">{pc(v)}</td>' if pd.notna(v) else '<td></td>'
    best, worst = year.ret.idxmax(), year.ret.idxmin()
    head = ('<tr><th>Year</th>' + ''.join(f'<th>{pd.Timestamp(2000, k, 1):%b}</th>' for k in range(1, 13))
            + '<th class="sep">Total</th><th>Vol</th><th>Sharpe</th><th>Up</th></tr>')
    rows = ''.join(f'<tr><td>{t}</td>' + ''.join(cell(grid.loc[t].get(k), .08) for k in range(1, 13))
                   + cell(o.ret, .3, 'sep ext' if t in (best, worst) else 'sep')
                   + f'<td>{pc(o.vol)}</td><td>{num(o.sharpe, "x")[0]}</td><td>{o.up:.0%}</td></tr>' for t, o in year.iterrows())
    avg = ('<tr class="total"><td>Average</td>' + ''.join(cell(grid[k].mean(), .08) if k in grid else '<td></td>' for k in range(1, 13))
           + cell(year.ret.mean(), .3, 'sep') + f'<td>{pc(m.std() * 12 ** .5)}</td>'
           + f'<td>{num(ex.mean() / ex.std() * 12 ** .5, "x")[0]}</td><td>{(m > 0).mean():.0%}</td></tr>')
    html(f'<div class="scroll"><table class="plain heat">{head}{rows}{avg}</table></div>')


def hit_rates(r, bench):
    """how often and by how much the portfolio wins, next to the S&P 500"""
    def col(d):
        m, y = monthly(d), (1 + d).groupby(d.index.year).prod() - 1
        return {'Positive months': (m > 0).mean(), 'Positive days': (d > 0).sum() / (d != 0).sum(),
                'Average up month': m[m > 0].mean(), 'Average down month': m[m < 0].mean(),
                'Best month': m.max(), 'Worst month': m.min(), 'Best year': y.max(), 'Worst year': y.min()}
    a, b = col(r), col(bench)
    rows = ''.join(f'<tr><td class="label">{k}</td>{td(a[k], cls="em")}{td(b[k])}</tr>' for k in a)
    html(f'<table class="plain"><tr><th></th><th>{PF}</th><th>{SP}</th></tr>{rows}</table>')


def annual_returns():
    heading('Annual returns')
    p, res = results()
    yr = res['yearly']
    cagr = lambda r: (1 + r).prod() ** (1 / len(yr)) - 1
    rows = ''.join(f'<tr><td>{y}</td>{td(r.Strategy, cls="em")}{td(r["S&P 500 TR"])}<td class="dim">{r["Pair held"]}</td></tr>'
                   for y, r in yr.iterrows())
    html(f'<table class="plain compact"><tr><th>Year</th><th>Portfolio</th><th>{SP}</th><th>Spread pair</th></tr>{rows}'
         f'<tr class="total first"><td>Compound annual growth (CAGR)</td>{td(cagr(yr.Strategy))}{td(cagr(yr["S&P 500 TR"]))}<td></td></tr>'
         f'<tr class="total"><td>Cumulative</td>{td((1 + yr.Strategy).prod() - 1)}{td((1 + yr["S&P 500 TR"]).prod() - 1)}<td></td></tr></table>')
    note('Compound growth is lower than the arithmetic average return on the Performance page, because losses and gains '
         'compound unevenly.')
    html('<h4>Month by month, net of costs (%)</h4>')
    month_grid(res['bt'].net, res['rf_m'])
    note('Green months gained, red months lost; the darker, the bigger the move. Total is the compounded return for the year, framed for '
         'the best and the worst year. Vol and Sharpe are annualised from that year&rsquo;s monthly returns, and Up is the '
         'share of months with a gain. The last row averages each column over all years.')
    html('<h4>Hit rates</h4>')
    hit_rates(res['bt'].net, res['bench_d'])


def stress_tests():
    heading('Stress tests')
    p, res = results()
    bt, bench = res['bt'], res['bench_d']
    note('The five S&amp;P 500 peak-to-trough episodes since 2007. Each figure is the total return over the S&amp;P 500&rsquo;s '
         'own window, which is not the same as each line&rsquo;s drawdown. Click an episode for what happened.')
    cut = lambda r, a, b: r.loc[a:b].iloc[1:]
    span = lambda a, b: f'{pd.Timestamp(a):%b %Y} &rarr; {pd.Timestamp(b):%b %Y}'
    eps = [e for e in CRISES if pd.Timestamp(e[1]) >= bt.index[0] and pd.Timestamp(e[2]) <= bt.index[-1]]
    if not eps:
        note('No episode falls inside the selected years.')
        return
    streams = [(SP, bench), ('Portfolio', bt.net), ('Equity sleeve', res['spy_only'].net), ('Spread sleeve', res['pair_only'].net)]
    cell = lambda col, v, cls='': col.markdown(f'<p class="c {cls} {num(v)[1]}">{num(v)[0]}</p>', unsafe_allow_html=True)
    W = [3, 2.2, 1.3, 1.3, 1.3, 1.3]
    with st.container(key='stress'):
        for col, t in zip(st.columns(W), ['Episode', 'Window'] + [n for n, _ in streams]):
            col.markdown(f'<p class="th {"l" if t == "Episode" else "wh" if t == "Window" else ""}">{t}</p>', unsafe_allow_html=True)
        for k, (name, a, b, story, lesson) in enumerate(eps):
            c = st.columns(W, vertical_alignment='center')
            clicked = c[0].button(name, key=f'ep{k}', type='tertiary')
            c[0].markdown(f'<p class="win">{span(a, b)}</p>', unsafe_allow_html=True)
            c[1].markdown(f'<p class="dim">{span(a, b)}</p>', unsafe_allow_html=True)
            for col, (n, r) in zip(c[2:], streams):
                cell(col, (1 + cut(r, a, b)).prod() - 1, 'em' if n == 'Portfolio' else '')
            if clicked:
                def body(a=a, b=b, story=story, lesson=lesson):
                    note(span(a, b))
                    w = bt.w_spy
                    pos = (f' Spread pair: {res["yearly"].loc[int(a[:4]), "Pair held"]}, open on '
                           f'{(res["pair_only"].gross_exposure.loc[a:b] > 0).mean():.0%} of days.' if p.pair_size > 0 else '')
                    html(f'<p>{story}</p><p>{lesson} Equity exposure going in was <span class="fig">{w.loc[:a].iloc[-1]:.2f}x</span>, '
                         f'and <span class="fig">{w.loc[a:b].mean():.2f}x</span> on average during the episode.{pos}</p>')
                    html('<table class="plain"><tr>' + ''.join(f'<th>{n}</th>' for n, _ in streams) + '</tr><tr>'
                         + ''.join(td((1 + cut(r, a, b)).prod() - 1) for _, r in streams) + '</tr></table>')
                    chart('Growth of $1 over the episode', [(PF, wealth(cut(bt.net, a, b)), S1),
                                                            (SP, wealth(cut(bench, a, b)), S2)], kind='line')
                dive(name, body)


def attribution():
    heading('Attribution')
    p, res = results()
    note('Each sleeve run on its own, with idle capital in T-bills.')
    metrics_table(res['sleeves'].rename(columns={'Vol-managed SPY only': 'Equity sleeve', 'Pair only (+ T-bills)': 'Spread sleeve',
                                                 'Combined strategy': 'Combined'}), 'Combined')
    chart('Growth of $1, log scale', [('Combined', wealth(res['bt'].net), S1), ('Equity sleeve', wealth(res['spy_only'].net), S2),
                                      ('Spread sleeve', wealth(res['pair_only'].net), S3)])
    pair = (f'the spread pair for {res["pair_year"]} is <span class="fig">{"/".join(res["pair_now"])}</span>'
            if res['pair_now'] else 'the spread sleeve is off')
    html(f'<p>At the {res["bt"].index[-1]:%d %b %Y} close, equity exposure is '
         f'<span class="fig">{res["exposure_now"]:.2f}x</span> and {pair}.</p>')


def live_ranges(live, px):
    """1D and 1W from 5-minute prices, 1M and YTD from daily closes plus the latest price. None if no intraday prices"""
    lb, bench = live['bt'], live['bench_d']
    try:
        sessions = intraday_value(lb, px, bench, get_intraday())
    except RuntimeError:
        sessions = []
    t0 = pd.Timestamp(DEMO_START) - pd.Timedelta(days=1)
    daily = pd.DataFrame({'pf': (1 + lb.net).cumprod(), 'sp': (1 + bench).cumprod()})
    daily = pd.concat([pd.DataFrame({'pf': 1.0, 'sp': 1.0}, index=[t0]), daily])
    if sessions:
        daily = pd.concat([daily.loc[:sessions[-1].attrs['prev']], sessions[-1].iloc[[-1]]])   # completed closes, then now
    iso = lambda df: [f'{t:%Y-%m-%dT%H:%M}' if (t.hour or t.minute) else f'{t:%Y-%m-%d}' for t in df.index]
    pack = lambda df: dict(t=iso(df), p=df.pf.round(6).tolist(), s=df.sp.round(6).tolist())
    ranges = {}
    if sessions:
        ranges['1D'] = pack(sessions[-1])
        ranges['1W'] = pack(pd.concat([sessions[0]] + [s.iloc[1:] for s in sessions[1:]]))
    month = daily.loc[:daily.index[-1] - pd.DateOffset(months=1)]
    ranges['1M'] = pack(daily.loc[month.index[-1]:] if len(month) else daily)
    ranges['YTD'] = pack(daily)
    last = sessions[-1].index[-1] if sessions else None
    return ranges, last


@st.fragment(run_every=60)
def live_board():
    """reruns on its own every minute; the rest of the page stays put"""
    try:
        live, px = get_live()
    except RuntimeError as e:                                   # download failed; real bugs still surface
        note(str(e))
        return
    ranges, last = live_ranges(live, px)
    now = pd.Timestamp.now(tz='America/New_York').tz_localize(None)
    is_live = last is not None and now - last < pd.Timedelta(minutes=15)
    status = (f'Live · {now:%H:%M} New York · 5-minute prices from Yahoo Finance, refreshed every minute' if is_live else
              f'Market closed · last price {last:%a %d %b, %H:%M} New York' if last is not None else
              f'Intraday prices unavailable right now · closes up to {live["bt"].index[-1]:%d %b %Y}')
    board(ranges, status, bool(is_live))


def live_2026():
    heading('Live 2026')
    html('<p>We fixed the rules at the 31 Dec 2025 close and have not changed them since. This page runs them on 2026 data, '
         'which played no part in designing the strategy, with the base-case assumptions.</p>')
    live_board()
    try:
        live = get_live()[0]
    except RuntimeError:
        return
    lb, lbench = live['bt'], live['bench_d']
    note('During the day the portfolio is revalued every five minutes with the weights it held at the previous close; '
         'SPY stands in for the S&amp;P 500 total return index until the close.')
    html('<h4>Since 1 January</h4>')
    row = lambda name, r, cls: (f'<tr class="{cls}"><td class="label">{name}</td>{td((1 + r).prod() - 1)}'
                                f'{td(monthly(r).std() * 12 ** .5)}{td(daily_dd(r))}</tr>')
    html('<table class="plain"><tr><th></th><th>Return since 1 Jan</th><th>Volatility (annualised, monthly)</th>'
         '<th>Max drawdown (daily)</th></tr>' + row(PF, lb.net, 'em') + row(SP, lbench, '') + '</table>')
    note(f'Daily closes from 1 Jan 2026 to {lb.index[-1]:%d %b %Y}.')
    html(f'<p>Equity exposure today is <span class="fig">{lb.w_spy.iloc[-1]:.2f}x</span>, and the spread pair is '
         f'<span class="fig">{"/".join(live["pair_now"])}</span>.</p>')


def rule_budget():
    p, _ = results()
    left = max(p.target_vol ** 2 - 0.06 ** 2, 0) ** .5
    return [f'Think of {p.target_vol:.0%} volatility as the total risk we are allowed to take. The spread sleeve goes first: we '
            'measure how much the positions actually held moved over the last 63 trading days. The equity sleeve gets what is left.',
            f'Risks don\'t add up in a straight line, because the two sleeves don\'t move together. If the spread uses 6%, the '
            f'equity sleeve still gets &radic;({p.target_vol * 100:g}&sup2; &minus; 6&sup2;) = <span class="fig">{left:.1%}</span>, '
            f'not {p.target_vol - .06:.0%}.']


def rule_equity():
    p, _ = results()
    return ['Position = risk budget / how much SPY moved lately (annualised).',
            f'For example, with a budget of 13% and SPY moving at 20% a year, we hold 13 / 20 = 0.65x and the other 0.35 sits in '
            f'T-bills. With SPY moving at 8% we would hold 1.6x, and the extra 0.6 is borrowed at the T-bill rate plus '
            f'{p.fin_spread * 1e4:.0f} bp. Exposure never goes above {p.max_lev:.2f}x.',
            'We only reset at month-end. In between, the position moves with the market.']


def rule_spread():
    p, _ = results()
    return ['On the last trading day of the year we measure each of the nine sector ETFs against SPY over that year and pick the '
            'two that moved least with the market. That pair is traded for the whole of the next year.',
            'The legs are sized so both carry the same market exposure, so the one that moves less with the market gets the '
            'bigger weight.',
            f'An example with XLP and XLU: z reaches +2.3, so XLP has run ahead of XLU. We short XLP and buy XLU. When z falls '
            f'back under {p.z_out:g}, we close both.',
            'When the pair changes at year-end, the old position is closed and the new pair starts flat.']


def rule_execution():
    return ['Every decision uses closing prices up to today. We trade at today\'s close, so a new position earns from tomorrow, '
            'and no decision uses a price we could not have known.',
            'We checked this by deleting all data after a date and running the backtest again. Everything before that date '
            'came out exactly the same. The test is in the notebook.']


def rule_costs():
    p, res = results()
    bt = res['bt']
    turn = bt.turnover.sum() / (len(bt) / 252)
    return [f'Every trade costs {p.cost * 1e4:.0f} bp of the amount traded, covering the spread, commission and slippage. '
            f'Shorts cost {p.short_fee * 1e4:.0f} bp a year to borrow, and borrowed cash costs the T-bill rate plus '
            f'{p.fin_spread * 1e4:.0f} bp.',
            'Every return on this site is after these costs.',
            f'We trade about <span class="fig">{turn:.0f}x</span> our capital a year, mostly in the spread legs, so costs matter. '
            'Raise the trading cost under Test your assumptions to see how much.']


def rules():
    heading('Rules')
    p, _ = results()
    clickable('rules', [('Risk budget.', f'One {p.target_vol:.0%} volatility budget for the whole portfolio. The spread sleeve\'s '
                         'realised volatility over 63 trading days is taken out first, and the equity sleeve gets the rest.', rule_budget),
                        ('Equity sleeve.', f'At each month-end, exposure = remaining budget / SPY realised volatility over 21 trading '
                         f'days (annualised), capped at {p.max_lev:.2f}x. Idle cash earns the T-bill rate; leverage is financed at '
                         f'the T-bill rate plus {p.fin_spread * 1e4:.0f} bp.', rule_equity),
                        ('Spread sleeve.', f'At each year-end, select the two sector ETFs with the lowest beta to SPY over the past '
                         f'year. Compute a daily z-score of their log price ratio against its 60-day mean: enter at |z| > {p.z_in:g} '
                         f'(long the cheap leg, short the rich one) and exit at |z| < {p.z_out:g}. The legs are sized to be '
                         f'beta-neutral from the same prior-year betas, {2 * p.pair_size:.2f}x gross. A newly selected pair starts '
                         'flat.', rule_spread),
                        ('Execution.', 'Signals use closing prices up to day t; positions earn from day t+1.', rule_execution),
                        ('Costs.', f'{p.cost * 1e4:.0f} bp per unit traded and a {p.short_fee * 1e4:.0f} bp a year borrow fee on '
                         'shorts.', rule_costs)])


def fan_chart(fan):
    """monte carlo fan: a few single paths, 5-95% and 25-75% bands and the median, S&P median and 5/95% for comparison"""
    html(f'<p class="chart-head"><b>$1 over 10 years, 10,000 simulated paths (log scale)</b>'
         f'<span><i style="background:{S1}"></i>{PF}</span><span><i style="background:{S2}"></i>{SP}</span></p>')
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
    for k, lab in ((0, '5%'), (2, 'Median'), (4, '95%')):
        ax.annotate(f'{lab} ${q[k, -1, 0]:.2f}', (t[-1], q[k, -1, 0]), xytext=(6, 0), textcoords='offset points',
                    va='center', fontsize=8, color=S1)
    ax.set_yscale('log'); ax.yaxis.set_minor_locator(NullLocator())
    ax.set_yticks([t_ for t_ in [0.5, 1, 2, 5, 10, 20] if q.min() / 1.3 <= t_ <= q.max() * 1.3])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'${v:g}'))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:.0f}y'))
    ax.axhline(1, color=INK, lw=.8); ax.set_xlim(0, t[-1] * 1.16)
    show(fig)
    note('The shaded bands hold the middle 50% and 90% of the portfolio&rsquo;s paths, thin lines are single paths and the '
         'bold line is the median. Grey: the S&amp;P 500 median, dashed: its 5% and 95% levels.')


def risk():
    heading('Risk')
    p, res = results()
    t = with_daily_dd(res['table'], res['bt'], res['bench_d'])
    mdd_m, mdd_d = (num(t.loc[k, 'Strategy (net)'])[0] for k in ('Max drawdown (monthly)', 'Max drawdown (daily)'))
    html('<h4>Main risks</h4>')
    items([(None, f'Leverage and short selling are required. Gross exposure reached {res["bt"].gross_exposure.max():.1f}x in '
                  'the backtest, and a scheme&rsquo;s rules may not allow this directly (see the term sheet under Investment approach).'),
           (None, f'The largest fall was {mdd_m} measured at month-ends and {mdd_d} measured daily.'),
           (None, 'Selection bias: the rule for choosing the pair was written after we had seen defensive-sector pairs work. '
                  'Other selection rules did not add value.'),
           (None, 'Exposure is reset once a month, so it reacts late to sudden volatility spikes, and low exposure after a crash '
                  'misses part of the rebound. For the same reason, realised daily volatility can run above the budget in spikes.'),
           (None, f'Short positions can be recalled, and the borrow fee is assumed fixed at {p.short_fee * 1e4:.0f} bp a year.'),
           (None, 'The portfolio is in US dollars and not hedged, which matters for a euro or sterling scheme.'),
           (None, 'Data from Yahoo Finance, fixed cost assumptions, no taxes and no management fee.')], ordered=False)

    html('<h4>Risk in numbers</h4>')
    note('Monthly returns, net of costs. Value at risk and expected shortfall are one-month losses. Cornish-Fisher adjusts the '
         'normal estimate for skew and fat tails. Capture compares our average return in the S&amp;P 500&rsquo;s rising (falling) '
         'months with the S&amp;P 500&rsquo;s own.')
    metrics_table(res['risk'][['Strategy (net)', 'S&P 500 TR']].rename(columns={'Strategy (net)': PF, 'S&P 500 TR': SP}), PF)


def monte_carlo():
    heading('Monte Carlo simulation')
    p, res = results()
    if res['mc'] is None:
        return
    mc, head, fan = res['mc']
    html('<p>We built 10,000 ten-year paths from random 12-month blocks of the backtest, taking the portfolio, the S&amp;P 500 '
         'and T-bills from the same months. Because it resamples our own history, the simulation inherits its optimism. Read it '
         'as the range of outcomes if the next decade looks like the backtest, not as a forecast.</p>')
    mc = mc.drop(index='Probability of a loss', errors='ignore')
    kind = lambda i: 'usd' if i.startswith('Wealth') else 'x' if i.startswith('Sharpe') else 'pct'
    rows = ''.join(f'<tr><td class="label">{i.replace("$1", "$1 invested")}</td>'
                   + ''.join(td(v, kind(i), 'em' if c == 'Strategy (net)' else '') for c, v in r.items()) + '</tr>'
                   for i, r in mc.iterrows())
    html(f'<table class="plain"><tr><th></th><th>{PF}</th><th>{SP}</th></tr>{rows}</table>')
    note(f'The portfolio ends ahead of the S&amp;P 500 in {head["beats_sp"]:.0%} of paths.')
    fan_chart(fan)



def photo(ph):
    if ph.startswith('assets/'):                                   # local file, inlined: the team iframe cannot load app files
        return f'data:image/jpeg;base64,{base64.b64encode((Path(__file__).parent / ph).read_bytes()).decode()}'
    return ph


def team():
    """wheel picker: spin the names, the one in the middle shows its photo and bio"""
    heading('Team')
    people = json.dumps([dict(n=n, b=b, i=''.join(w[0] for w in n.split()),
                              u=photo(ph), li=li) for n, ph, b, li in TEAM])
    components.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500&family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap');
* { box-sizing: border-box; margin: 0; }
body { font-family: "IBM Plex Sans", system-ui, sans-serif; color: #0e1a2b; background: #fff; }
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
  border-top: 1px solid #dde3ea; border-bottom: 1px solid #dde3ea; }
.card { transition: opacity .25s; }
.card.out { opacity: 0; }
.ph { position: relative; overflow: hidden; width: 180px; aspect-ratio: 4/5; background: #f5f7fa; border: 1px solid #dde3ea; display: grid; place-items: center;
  font-size: 18px; color: #4d5866; margin-bottom: 16px; }
.ph img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; filter: grayscale(1); }
.hd { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.name { font-family: "Newsreader", Georgia, serif; font-size: 28px; line-height: 1.2; }
.li { display: inline-flex; color: #9aa1a8; transition: color .15s; }
.li.hide { display: none; }
.li:hover { color: #0e7c70; }
.li svg { width: 18px; height: 18px; fill: currentColor; }
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
  <div class="card" id="c"><div class="ph"><span id="ph"></span><img id="im" alt=""></div><div class="hd"><p class="name" id="nm"></p><a class="li" id="li" target="_blank" rel="noopener" aria-label="LinkedIn"><svg viewBox="0 0 448 512"><path d="M416 32H31.9C14.3 32 0 46.5 0 64.3v383.4C0 465.5 14.3 480 31.9 480H416c17.6 0 32-14.5 32-32.3V64.3C448 46.5 433.6 32 416 32zM135.4 416H69V202.2h66.5V416zM102 172.2c-21.3 0-38.5-17.3-38.5-38.5S80.7 95.2 102 95.2c21.2 0 38.5 17.3 38.5 38.5s-17.2 38.5-38.5 38.5zm284.3 243.8h-66.4V312c0-24.8-.5-56.7-34.5-56.7-34.6 0-39.9 27-39.9 54.9V416h-66.4V202.2h63.7v29.2h.9c8.9-16.8 30.6-34.5 62.9-34.5 67.2 0 79.7 44.3 79.7 101.9V416z"/></svg></a></div><div class="bio" id="bo"></div></div>
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
  setTimeout(() => { const p = P[i]; ph.textContent = p.i; im.style.display = ''; im.src = p.u; im.alt = p.n; nm.textContent = p.n; bo.innerHTML = p.b;
                     li.href = p.li; li.classList.toggle('hide', !p.li);
                     c.classList.remove('out'); size(); }, cur === -1 ? 0 : 150);
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
function size() {                     // the streamlit wrapper keeps the height passed from python: resize it too
  const h = document.body.scrollHeight + 'px', box = frameElement.parentElement;
  frameElement.style.height = h; if (box) { box.style.height = h; box.style.minHeight = h; box.style.flex = '0 0 ' + h; } }
addEventListener('pagehide', () => { const box = frameElement.parentElement; if (box) box.style.height = box.style.minHeight = box.style.flex = ''; });
const fit = () => { size(); paint(); };
addEventListener('resize', fit);
const mid = items[Math.floor(items.length / 2) - 1];               // start in the middle: names above and below
w.scrollTop = mid.offsetTop + mid.offsetHeight / 2 - w.clientHeight / 2; fit();
</script>""".replace('PEOPLE', people), height=440)


def save_settings():
    ss = st.session_state
    ss['mr_size'], ss['mr_tv'], ss['mr_view'] = ss['f_size'] * 1e6, ss['f_tv'] / 100, 'Report'


@st.cache_data(ttl=3600, show_spinner=False)
def mandate_data(size, tv, code=CODE):
    """everything the mandate report and its pdf statement show, for a mandate of `size` dollars at volatility target tv"""
    live, px = get_live(tv)
    lb, lbench = live['bt'], live['bench_d']
    value, bench_value = size * (1 + lb.net).cumprod(), size * (1 + lbench).cumprod()
    W = lb[[f'w_{a}' for a in ASSETS]].set_axis(ASSETS, axis=1)
    d0 = px.index[px.index.get_loc(lb.index[0]) - 1]                # initial purchase at the last close of 2025
    Wt = pd.concat([pd.Series(lb.attrs['opening_weights'], index=ASSETS).to_frame(d0).T, W])
    gross = pd.concat([pd.Series(0.0, index=[d0]), lb.gross])
    V = pd.concat([pd.Series(size * (1 - lb.attrs['opening_cost']), index=[d0]), value])
    eq_before = V.shift(1).fillna(size) * (1 + gross)               # value at each close, before that day's costs
    drift = Wt.shift(1).fillna(0) * (1 + px[ASSETS].pct_change().loc[Wt.index]) / (1 + gross).values[:, None]
    trades = ((Wt - drift) * eq_before.values[:, None]).stack()
    limits = [('Realised volatility since 1 Jan (annualised, monthly)', num(monthly(lb.net).std() * 12 ** .5)[0], f'{tv:.0%} budget'),
              ('Equity exposure today', f'{lb.w_spy.iloc[-1]:.2f}x', f'{DEFAULTS.max_lev:.2f}x cap'),
              ('Gross exposure today', f'{lb.gross_exposure.iloc[-1]:.2f}x', ''),
              ('Max drawdown since 1 Jan (daily)', num(daily_dd(lb.net))[0], '')]
    return dict(size=size, tv=tv, lb=lb, px=px, value=value, bench_value=bench_value, pos=W.iloc[-1],
                trades=trades[trades.abs() > 0.005 * size / 1000], monthly=monthly(lb.net), monthly_bench=monthly(lbench),
                limits=[(k, v, l.replace('&nbsp;', ' ')) for k, v, l in limits])


@st.cache_data(ttl=3600, show_spinner='Preparing the statement ...')
def mandate_pdf(size, tv, code=CODE):
    return statement_pdf(mandate_data(size, tv))


def mandate_report():
    heading('Sample mandate report')
    note('Illustrative only: a simulated pension mandate, no capital is invested. The rules were frozen at the 31 Dec 2025 close.')
    ss = st.session_state
    size, tv = ss.get('mr_size', MANDATE), ss.get('mr_tv', DEFAULTS.target_vol)
    ss.setdefault('mr_view', 'Report')                             # state, not default=: save_settings also sets it
    top, pdf = st.columns([3, 2], vertical_alignment='center')
    view = top.segmented_control('view', ['Report', 'Settings'], key='mr_view', label_visibility='collapsed',
                                 on_change=lambda: ss.update(mr_view=ss['mr_view'] or 'Report'))   # no empty selection
    if view == 'Settings':
        with st.form('mr_settings'):
            st.number_input('Mandate size at the 31 Dec 2025 close ($m)', 1.0, 10_000.0, size / 1e6, 10.0, format='%.0f', key='f_size')
            st.select_slider('Risk budget: volatility target (% a year)', list(range(5, 31)), round(tv * 100), key='f_tv')
            note('The whole report and the PDF statement are recalculated from 1 Jan 2026 with these settings.')
            st.form_submit_button('Save', type='primary', on_click=save_settings)
        return
    try:
        d = mandate_data(size, tv)
    except RuntimeError as e:                                   # download failed; real bugs still surface
        note(str(e))
        return
    lb, px, value, bench_value = d['lb'], d['px'], d['value'], d['bench_value']
    pdf.download_button('Download PDF statement', mandate_pdf(size, tv), key='mr_pdf', type='primary',
                        file_name=f'mvp_mandate_statement_{lb.index[-1]:%Y%m%d}.pdf', mime='application/pdf')
    gain = value.iloc[-1] - size
    signed = lambda v, kind: ('+' if v >= 0 else '') + num(v, kind)[0]
    html(f'<div class="hero"><p class="k">Mandate value at the {lb.index[-1]:%d %b %Y} close</p>'
         f'<p class="big">${value.iloc[-1] / 1e6:,.1f}m</p>'
         f'<p class="chg"><span class="{num(gain)[1]}">{signed(gain, "m")} &nbsp;{signed(value.iloc[-1] / size - 1, "pct")}</span>'
         f'<span class="dim"> since 31 Dec 2025 &middot; S&amp;P 500 TR {signed(bench_value.iloc[-1] / size - 1, "pct")} '
         f'&middot; {tv:.0%} risk budget</span></p></div>')

    html('<h4>Risk against limits</h4>')
    html('<table class="plain"><tr><th></th><th>Current</th><th>Limit</th></tr>'
         + ''.join(f'<tr><td class="label">{k}</td><td class="em">{v}</td><td class="dim">{l}</td></tr>' for k, v, l in d['limits'])
         + '</table>')
    start = pd.Series(size / 1e6, index=[pd.Timestamp('2025-12-31')])
    chart('Mandate value ($m)', [(PF, pd.concat([start, value / 1e6]), S1), (SP, pd.concat([start, bench_value / 1e6]), S2)],
          kind='line')

    p0 = Params(start=DEMO_START, end=str(lb.index[-1].date()), target_vol=tv)
    tgt, chosen, z = pair_targets(px, p0)
    a, b = chosen[int(DEMO_START[:4])]
    legs, zt = tgt.iloc[-1][[a, b]] * p0.pair_size, z.iloc[-1]
    if legs.abs().sum() > 0:
        lng, sht = legs.idxmax(), legs.idxmin()
        status = (f'<b>Spread open</b> &middot; long {lng} {legs[lng]:.2f}x, short {sht} {-legs[sht]:.2f}x '
                  f'&middot; z-score {num(zt, "x")[0]} &middot; closes when |z| &lt; {p0.z_out:g}')
    else:
        status = f'<b>Spread flat</b> &middot; {a}/{b} &middot; z-score {num(zt, "x")[0]} &middot; opens when |z| &gt; {p0.z_in:g}'
    html('<h4>Sector spread</h4>')
    html(f'<p class="status {"on" if legs.abs().sum() > 0 else ""}"><i></i>{status}</p>')
    chart(f'Z-score of log {a}/{b}', [('z-score', z.loc[DEMO_START:], S1)], kind='z', h=2.2,
          bands=((p0.z_in, '--'), (p0.z_out, ':')))
    note(f'Dashed lines: entry at |z| &gt; {p0.z_in:g}, short the rich leg and buy the cheap one. Dotted lines: exit at '
         f'|z| &lt; {p0.z_out:g}.')

    html('<h4>Positions</h4>')
    eq, pos = value.iloc[-1], d['pos']
    rows = ''.join(f'<tr><td class="label">{a}</td>{td(w, "x")}{td(w * eq, "m")}</tr>' for a, w in pos.items() if abs(w) > 1e-9)
    cash = 1 - pos.sum()
    rows += f'<tr><td class="label">{"Cash (T-bills)" if cash >= 0 else "Borrowing"}</td>{td(cash, "x")}{td(cash * eq, "m")}</tr>'
    html(f'<table class="plain"><tr><th>Holding</th><th>Weight (x mandate)</th><th>Value</th></tr>{rows}'
         f'<tr class="total first"><td>Mandate value</td><td></td>{td(eq, "m")}</tr></table>')

    trades = d['trades'].iloc[::-1]
    with st.expander(f'Trades since 31 Dec 2025 ({len(trades)}, newest first)'):
        note(f'Including the initial purchase. Costs of {p0.cost * 1e4:.0f} bp per unit traded are deducted from the mandate.')
        rows = ''.join(f'<tr><td>{t:%d %b %Y}</td><td class="label">{a}</td><td class="dim">'
                       f'{"Buy" if v > 0 else "Sell"}</td>{td(abs(v), "m")}</tr>' for (t, a), v in trades.items())
        html(f'<table class="plain compact"><tr><th>Date</th><th>Asset</th><th>Side</th><th>Amount</th></tr>{rows}</table>')


def loader(key):
    """on a new page: close the menu and cover the page while the performance curve draws itself, until the run is done.
    the iframe only reloads when key changes, so widget reruns on the same page show nothing."""
    path = lambda d, c, w, t: (f'<path d="{d}" pathLength="1" style="stroke:{c};stroke-width:{w};'
                               f'animation:draw 1.3s cubic-bezier(.4,0,.2,1) {t}s forwards"/>')
    components.html(f"""<!-- {key} -->
<style>html,body{{margin:0;height:100%;background:{NIGHT};display:grid;place-items:center;overflow:hidden}}
svg{{width:min(520px,78vw);overflow:visible}} path{{fill:none;stroke-linejoin:round;stroke-linecap:round;
stroke-dasharray:1;stroke-dashoffset:1}} @keyframes draw{{to{{stroke-dashoffset:0}}}}</style>
<svg viewBox="0 0 400 160">{path(LOADER[1], '#8c95a0', 1.4, 0)}{path(LOADER[0], '#5fd4c0', 2.2, .15)}</svg>
<script>
const f = frameElement, d = parent.document, t0 = Date.now();
d.querySelector('[data-testid="stSidebar"][aria-expanded="true"] [data-testid="stSidebarCollapseButton"] button')?.click();
Object.assign(f.style, {{display: 'block', opacity: 1, position: 'fixed', inset: 0, width: '100vw', height: '100vh', zIndex: 999990, border: 0, transition: 'opacity .4s'}});
(function wait() {{
  if (Date.now() - t0 < 1600 || d.querySelector('.stApp')?.dataset.testScriptState === 'running') return setTimeout(wait, 100);
  f.style.opacity = 0; setTimeout(() => f.style.display = 'none', 450);
}})();
</script>""", height=0)


page = lambda f, t, u: st.Page(f, title=t, url_path=u)
nav = st.navigation({'': [st.Page(home, title='Home', default=True), page(assumptions, 'Test your assumptions', 'assumptions'),
                          page(team, 'Team', 'team')],              # shown after the groups, see the css order rules
                     'Strategy': [page(thesis, 'Investment approach', 'thesis'), page(rules, 'Rules', 'rules'),
                                  page(pension, 'In a pension portfolio', 'pension')],
                     'Results': [page(performance, 'Performance', 'performance'), page(live_2026, 'Live 2026', 'live-2026'),
                                 page(mandate_report, 'Sample mandate report', 'mandate-report')],
                     'Backtest & analysis': [page(annual_returns, 'Annual returns', 'annual-returns'),
                                             page(attribution, 'Attribution', 'attribution'), page(risk, 'Risk', 'risk'),
                                             page(stress_tests, 'Stress tests', 'stress-tests'),
                                             page(monte_carlo, 'Monte Carlo', 'monte-carlo')]},
                    position='top')
loader(f"{nav.url_path}|{st.session_state.get('params', DEFAULTS)}")
nav.run()
html(f'<div class="site-foot"><p>{FUND} is a student project for the course 2270 Financial Modeling at Nova SBE. It is not an '
     'investment firm and offers no investment services. All performance figures are simulated: a backtest from January 2006 '
     'to December 2025, and the frozen rules run live since 1 January 2026, in US dollars, net of modelled trading, financing '
     'and borrow costs, before management fees and taxes. Past performance does not predict future results.</p>'
     f'<p class="links"><a href="{COLAB}">Notebook</a> &middot; <a href="{REPO}">Source code</a></p></div>')

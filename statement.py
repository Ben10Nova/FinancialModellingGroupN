"""printable mandate statement: an A4 pdf drawn with matplotlib (already a dependency), page 1 the overview,
then the transactions. placeholders in [brackets] mark what a real statement would fill in."""
from io import BytesIO

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D

W, H, L, R = 8.27, 11.69, 0.8, 7.47                    # a4 in inches, left and right margin
INK, MUTED, RULE = '#111111', '#5a5a5a', '#c4c4c4'
NAMES = {'SPY': 'SPDR S&P 500 ETF Trust', 'XLB': 'Materials Select Sector SPDR Fund',
         'XLE': 'Energy Select Sector SPDR Fund', 'XLF': 'Financial Select Sector SPDR Fund',
         'XLI': 'Industrial Select Sector SPDR Fund', 'XLK': 'Technology Select Sector SPDR Fund',
         'XLP': 'Consumer Staples Select Sector SPDR Fund', 'XLU': 'Utilities Select Sector SPDR Fund',
         'XLV': 'Health Care Select Sector SPDR Fund', 'XLY': 'Consumer Discretionary Select Sector SPDR Fund'}
CLIENT = ['[Client name]', '[Pension scheme]', '[Street and number]', '[Postcode] [City]', '[Country]']
FOOT = ('Illustrative statement of a simulated mandate. No capital is invested. Figures are net of modelled costs.',
        'MVP Strategies is a student project (2270 Financial Modeling, Nova SBE) and offers no investment services.')
ROWS_PER_PAGE = 42

usd = lambda v: ('-' if v < -0.005 else '') + f'{abs(v):,.2f}'
pct = lambda v, sign=False: (f'{v:+.2%}' if sign else f'{v:.2%}').replace('-', '-')


class Page:
    def __init__(self, pdf, n, total, date):
        self.pdf, self.fig = pdf, plt.figure(figsize=(W, H))
        self.text(L, 11.15, FOOT[0], size=6.5, color=MUTED)
        self.text(L, 11.28, FOOT[1], size=6.5, color=MUTED)
        self.text(R, 11.15, f'Page {n} of {total}', size=6.5, color=MUTED, ha='right')
        self.rule(11.0, RULE)
        self.date = date

    def text(self, x, y, s, size=8.5, color=INK, ha='left', weight='normal'):
        self.fig.text(x / W, 1 - y / H, s, size=size, color=color, ha=ha, va='baseline', weight=weight)

    def rule(self, y, color=INK, lw=0.5, x0=L, x1=R):
        self.fig.add_artist(Line2D([x0 / W, x1 / W], [1 - y / H] * 2, color=color, lw=lw))

    def letterhead(self, title):
        self.text(L, 0.85, 'MVP Strategies', size=15, weight='bold')
        self.text(L, 1.05, 'Managed Volatility Portfolio', size=8.5, color=MUTED)
        self.text(L, 1.21, 'c/o Nova SBE, Rua da Holanda 1, 2775-405 Carcavelos, Portugal', size=7.5, color=MUTED)
        self.text(R, 0.85, title, size=12, weight='bold', ha='right')
        self.text(R, 1.05, f'Statement date  {self.date}', size=8.5, ha='right')
        self.text(R, 1.21, f'Period  1 Jan 2026 - {self.date}', size=8.5, ha='right')
        self.rule(1.4, lw=1)

    def section(self, y, title):
        self.text(L, y, title, size=10, weight='bold')
        return y + 0.12

    def table(self, y, cols, rows, xs, aligns, bold_last=False, size=8.5, step=0.215):
        """cols: header labels; xs: x position per column (right edge for right-aligned columns)"""
        for c, x, a in zip(cols, xs, aligns):
            self.text(x, y + 0.14, c, size=7.5, color=MUTED, ha=a)
        y += 0.2
        self.rule(y)
        for k, row in enumerate(rows):
            y += step
            last = bold_last and k == len(rows) - 1
            if last:
                self.rule(y - step + 0.06)
            for v, x, a in zip(row, xs, aligns):
                self.text(x, y, v, size=size, ha=a, weight='bold' if last else 'normal')
            if not last:
                self.rule(y + 0.07, RULE, lw=0.4)
        return y + 0.42

    def save(self):
        self.pdf.savefig(self.fig)
        plt.close(self.fig)


def statement_pdf(d):
    """d: dict from the app's mandate_data(): size, tv, value, bench_value, lb, pos, trades, monthly, monthly_bench, limits"""
    date = f'{d["value"].index[-1]:%d %b %Y}'
    trades = list(d['trades'].items())
    pages = 1 + max(1, -(-len(trades) // ROWS_PER_PAGE))
    buf = BytesIO()
    with plt.rc_context({'font.family': 'sans-serif', 'font.sans-serif': ['IBM Plex Sans', 'DejaVu Sans'], 'pdf.fonttype': 42}), \
            PdfPages(buf, metadata={'Title': 'MVP Strategies mandate statement', 'Author': 'MVP Strategies'}) as pdf:
        p = Page(pdf, 1, pages, date)
        p.letterhead('Mandate statement')
        for i, line in enumerate(CLIENT):
            p.text(L, 1.85 + i * 0.19, line, size=9.5)
        info = [('Mandate no.', '[000000]'), ('Base currency', 'USD'), ('Benchmark', 'S&P 500 Total Return'),
                ('Risk budget', f'{d["tv"]:.0%} volatility a year'), ('Inception', '31 Dec 2025')]
        for i, (k, v) in enumerate(info):
            p.text(4.55, 1.85 + i * 0.19, k, size=8.5, color=MUTED)
            p.text(R, 1.85 + i * 0.19, v, size=8.5, ha='right')

        value, bench, size = d['value'], d['bench_value'], d['size']
        y = p.section(3.05, 'Account summary')
        y = p.table(y, ['', 'USD'], [('Opening value, 31 Dec 2025', usd(size)), ('Contributions and withdrawals', usd(0)),
                                     ('Investment result, net of costs', usd(value.iloc[-1] - size)),
                                     (f'Closing value, {date}', usd(value.iloc[-1]))],
                    [L, R], ['left', 'right'], bold_last=True)

        r, b = value.iloc[-1] / size - 1, bench.iloc[-1] / size - 1
        y = p.section(y, 'Performance since inception')
        y = p.table(y, ['', 'Mandate', 'Benchmark', 'Difference'], [('Total return, net of costs', pct(r), pct(b), pct(r - b, True))],
                    [L, 5.0, 6.25, R], ['left', 'right', 'right', 'right'])

        y = p.section(y, 'Risk against limits')
        y = p.table(y, ['', 'Current', 'Limit'], d['limits'], [L, 6.0, R], ['left', 'right', 'right'])

        y = p.section(y, f'Holdings at {date}')
        eq = value.iloc[-1]
        rows = [(a, NAMES.get(a, ''), f'{w:.2f}x', usd(w * eq)) for a, w in d['pos'].items() if abs(w) > 1e-9]
        cash = 1 - d['pos'].sum()
        rows.append(('Cash' if cash >= 0 else 'Borrowing', 'US Treasury bills, 3 months' if cash >= 0 else 'Financing at T-bill + 50 bp',
                     f'{cash:.2f}x', usd(cash * eq)))
        rows.append(('Total', '', '', usd(eq)))
        y = p.table(y, ['Asset', 'Description', 'Weight', 'Market value (USD)'], rows, [L, 1.55, 5.5, R],
                    ['left', 'left', 'right', 'right'], bold_last=True)

        y = p.section(y, 'Monthly returns, net of costs (%)')
        m, mb = d['monthly'], d['monthly_bench']
        cols = [''] + [f'{t:%b}' for t in m.index]
        xs = [L] + [2.2 + i * (R - 2.2) / (len(m) - 1) for i in range(len(m))] if len(m) > 1 else [L, R]
        fmt = lambda v: f'{v * 100:.1f}'
        p.table(y, cols, [['Mandate'] + [fmt(v) for v in m], ['Benchmark'] + [fmt(v) for v in mb]], xs,
                ['left'] + ['right'] * len(m), size=8)
        p.save()

        for n, i in enumerate(range(0, max(len(trades), 1), ROWS_PER_PAGE), start=2):
            p = Page(pdf, n, pages, date)
            p.letterhead('Transactions')
            p.text(L, 1.75, '[Client name]', size=9.5)
            p.text(R, 1.75, 'Mandate no. [000000]', size=8.5, ha='right')
            y = p.section(2.2, 'Transactions since inception' + (' (continued)' if n > 2 else ''))
            rows = [(f'{t:%d %b %Y}', a, NAMES.get(a, ''), 'Buy' if v > 0 else 'Sell', usd(abs(v)))
                    for (t, a), v in trades[i:i + ROWS_PER_PAGE]]
            p.table(y, ['Date', 'Asset', 'Description', 'Side', 'Amount (USD)'], rows or [('', '', 'No transactions', '', '')],
                    [L, 1.75, 2.45, 6.0, R], ['left', 'left', 'left', 'left', 'right'], size=8, step=0.2)
            p.save()
    return buf.getvalue()

"""Ex-ante pair selection over all 36 sector-SPDR pairs. Rules fixed before looking at results."""
import itertools, numpy as np, pandas as pd, statsmodels.api as sm
PX = pd.read_pickle('px99.pkl')
PX['^IRX'] = PX['^IRX'].ffill()
SEC = 'XLB XLE XLF XLI XLK XLP XLU XLV XLY'.split()
PAIRS = list(itertools.combinations(SEC, 2))
RD = PX.pct_change(fill_method=None)
RFD = (PX['^IRX'] / 100 / 252).shift(1)
START, END, COST, SHORT_FEE = '2006-01-01', '2025-12-31', 0.001, 0.0025


def score(a, b, lo, hi, how):
    p = PX[[a, b]].loc[lo:hi]
    if how == 'ssd':                                       # Gatev et al. (2006) distance
        n = p / p.iloc[0]
        return ((n[a] - n[b]) ** 2).sum()
    return -RD[[a, b]].loc[lo:hi].corr().iloc[0, 1]        # lower is better


def signal(a, b, win=60, z_in=2.0, z_out=0.5):
    s = np.log(PX[a] / PX[b])
    z = (s - s.rolling(win).mean()) / s.rolling(win).std()
    out, p = [], 0
    for zt in z.values:
        if np.isnan(zt): p = 0
        elif p == 0 and zt > z_in: p = -1
        elif p == 0 and zt < -z_in: p = 1
        elif p != 0 and abs(zt) < z_out: p = 0
        out.append(p)
    return pd.Series(out, index=z.index)


SIG = {pr: signal(*pr) for pr in PAIRS}


def run(picks):
    """picks: {year: [pairs]} -> monthly net returns; each pair gets 1/k notional per leg."""
    P = pd.DataFrame(0.0, index=PX.index, columns=SEC)
    for y, prs in picks.items():
        m = P.index.year == y
        for a, b in prs:
            P.loc[m, a] += SIG[(a, b)][m] / len(prs)
            P.loc[m, b] -= SIG[(a, b)][m] / len(prs)
    W = P.shift(1).fillna(0).loc[START:END]
    R = RD[SEC].loc[W.index].fillna(0)
    gross = (W * R).sum(1) + (1 - W.sum(1)) * RFD.loc[W.index] - W.clip(upper=0).abs().sum(1) * SHORT_FEE / 252
    net = gross - W.diff().abs().sum(1) * COST
    return (1 + net).resample('ME').prod() - 1


def sharpe(r):
    rf = (1 + RFD.loc[START:END]).resample('ME').prod() - 1
    ex = r - rf.loc[r.index]
    return ex.mean() / ex.std() * np.sqrt(12)


years = range(2006, 2026)
rules = {}
for how in ['ssd', 'corr']:
    ranked = sorted(PAIRS, key=lambda pr: score(*pr, '1999-01-01', '2005-12-31', how))
    for k in [1, 3, 5]:
        rules[f'A static 1999-2005 {how} top{k}'] = {y: ranked[:k] for y in years}
    for lb in [1, 3]:
        for k in [1, 3, 5]:
            rules[f'B rolling {lb}y {how} top{k}'] = {
                y: sorted(PAIRS, key=lambda pr: score(*pr, f'{y - lb}-01-01', f'{y - 1}-12-31', how))[:k] for y in years}

rows = {}
for name, picks in rules.items():
    r = run(picks)
    allp = [pr for prs in picks.values() for pr in prs]
    rows[name] = {'SR_net': sharpe(r), 'SR_06-15': sharpe(r.loc[:'2015']), 'SR_16-25': sharpe(r.loc['2016':]),
                  'XLP/XLU share': sum(pr == ('XLP', 'XLU') for pr in allp) / len(allp),
                  'most picked': pd.Series([f'{a}/{b}' for a, b in allp]).value_counts().index[0]}
rows['(hindsight) XLU/XLP fixed'] = {'SR_net': sharpe(run({y: [('XLP', 'XLU')] for y in years}))}
rows['all 36 pairs, 1/36 each'] = {'SR_net': sharpe(run({y: PAIRS for y in years}))}
pd.set_option('display.width', 200)
print(pd.DataFrame(rows).T.round(2).to_string())
print('\nstatic ranking 1999-2005 (ssd) top 5:', sorted(PAIRS, key=lambda pr: score(*pr, '1999-01-01', '2005-12-31', 'ssd'))[:5])
print('static ranking 1999-2005 (corr) top 5:', sorted(PAIRS, key=lambda pr: score(*pr, '1999-01-01', '2005-12-31', 'corr'))[:5])

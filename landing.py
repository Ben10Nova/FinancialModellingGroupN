"""home page hero: name, tagline, three key figures against the s&p 500, two buttons and the growth of $1 drawn below.
one iframe, so the curves can draw themselves and the figures can count up."""
import json

import streamlit.components.v1 as components

from strategy import wealth


def landing(res, fund, fund_long, address):
    """res: results at the notebook defaults, so the home page always shows the prospectus numbers"""
    t, bt = res['table'], res['bt']
    s, b = 'Strategy (net)', 'S&P 500 TR'
    month = lambda r: wealth(r).resample('ME').last()
    ws, wb = month(bt.net), month(res['bench_d'])
    fig = lambda k, c, m=100: round(float(t.loc[k, c]) * m, 1 if m == 100 else 2)
    data = dict(s=[round(v, 4) for v in ws], b=[round(v, 4) for v in wb], y0=int(ws.index[0].year), y1=int(ws.index[-1].year),
                ret=[fig('Ann. avg return', s), fig('Ann. avg return', b)], sharpe=[fig('Sharpe ratio', s, 1), fig('Sharpe ratio', b, 1)],
                dd=[fig('Max drawdown (monthly)', s), fig('Max drawdown (monthly)', b)])
    page = (PAGE.replace('__DATA__', json.dumps(data, separators=(',', ':'))).replace('__FUND__', fund)
            .replace('__LONG__', fund_long.upper()).replace('__ADDRESS__', address))
    components.html(page, height=760)


PAGE = r"""<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500&family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap');
html,body{margin:0;background:transparent}
#lp{color:#101924;font-family:'IBM Plex Sans',sans-serif;padding-bottom:6px}
#wm{display:block;width:100%;height:auto;margin-top:18px;overflow:visible}
#wm path{fill:none;stroke-linejoin:round;stroke-linecap:round}
.fade{opacity:0;transform:translateY(10px);transition:opacity .9s ease,transform .9s ease}
.fade.in{opacity:1;transform:none}
.kick{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.12em;color:#848a90;margin:0 0 14px}
h1{font-family:'Newsreader',serif;font-weight:500;font-size:84px;line-height:1;margin:0;letter-spacing:.01em}
.tag{font-family:'Newsreader',serif;font-size:21px;line-height:1.45;color:#3d444c;margin:16px auto 0;max-width:38ch}
.card{background:#fff;border:1px solid #e9e9e6;border-radius:16px;box-shadow:0 10px 34px rgba(16,25,36,.07),0 1px 3px rgba(16,25,36,.05);max-width:580px;margin:34px auto 0;display:grid;grid-template-columns:repeat(3,1fr);padding:22px 8px}
.card div{text-align:center;padding:0 12px}
.card div+div{border-left:1px solid #ececea}
.card b{display:block;font-family:'Newsreader',serif;font-weight:500;font-size:50px;line-height:1;color:#0b2648;font-variant-numeric:lining-nums tabular-nums;letter-spacing:-.01em}
.card .lb{display:block;font-family:'IBM Plex Mono',monospace;font-size:10.5px;letter-spacing:.08em;color:#101924;margin-top:10px}
.card .vs{display:block;font-family:'IBM Plex Mono',monospace;font-size:11px;color:#9aa0a6;margin-top:4px}
.btns{display:flex;justify-content:center;align-items:center;gap:12px;margin-top:28px;flex-wrap:wrap}
.cta{all:unset;cursor:pointer;font-size:14px;font-weight:500;background:#101924;color:#fff;border-radius:999px;padding:12px 30px;box-shadow:0 6px 18px rgba(16,25,36,.18)}
.cta:hover{background:#0b2648}
.sec{all:unset;cursor:pointer;font-size:14px;font-weight:500;background:#fff;color:#101924;border:1px solid #d7d7d7;border-radius:999px;padding:11px 26px}
.sec:hover{border-color:#101924}
.cta:focus-visible,.sec:focus-visible{outline:2px solid #0b2648;outline-offset:3px}
.ft{text-align:center;font-size:12px;color:#848a90;margin-top:8px}
@media (max-width:560px){h1{font-size:46px}.tag{font-size:17px}.card b{font-size:30px}.card div{padding:0 6px}.card .lb{font-size:9.5px}}
@media (prefers-reduced-motion:reduce){.fade{transition:none}}
</style>
<div id="lp">
  <div style="text-align:center;padding:40px 12px 0">
    <p class="kick fade">__LONG__</p>
    <h1 class="fade">__FUND__</h1>
    <p class="tag fade">perfectly suited for long-term investors who want stock-market growth without sitting through stock-market crashes.</p>
    <div class="card fade" id="card"></div>
    <div class="btns fade"><button class="cta" data-go="performance">see the performance &rarr;</button><button class="sec" data-go="thesis">read the thesis</button></div>
  </div>
  <svg id="wm" viewBox="0 0 680 220" role="img" aria-label="growth of $1, portfolio against the s&amp;p 500"></svg>
  <p class="ft fade" id="ft"></p>
</div>
<script>
const D=__DATA__,S=D.s,B=D.b,$=id=>document.getElementById(id);
const sg=s=>String(s).replace(/^-/,'−');                       // keeps trailing zeros: 1.10, not 1.1
const cell=(v,f,suf,lab,bv)=>`<div><b data-v="${v}" data-f="${f}" data-s="${suf}">${sg(v.toFixed(f))}${suf}</b><span class="lb">${lab}</span><span class="vs">s&amp;p 500: ${sg(bv.toFixed(f))}${suf}</span></div>`;
$('card').innerHTML=cell(D.ret[0],1,'%','A YEAR, NET',D.ret[1])+cell(D.sharpe[0],2,'','SHARPE RATIO',D.sharpe[1])+cell(D.dd[0],1,'%','MAX DRAWDOWN',D.dd[1]);
$('ft').textContent=`backtest ${D.y0}–${D.y1}, net of costs · __ADDRESS__`.replace(/&middot;/g,'·');
const W=680,H=220,R=70,n=S.length-1;let lo=1,hi=1;S.concat(B).forEach(v=>{lo=Math.min(lo,v);hi=Math.max(hi,v);});
const l0=Math.log(lo/1.15),l1=Math.log(hi*1.15),x=i=>i/n*(W-R),y=v=>H-8-(Math.log(v)-l0)/(l1-l0)*(H-24);
const d=a=>a.map((v,i)=>(i?'L':'M')+x(i).toFixed(1)+','+y(v).toFixed(1)).join('');
$('wm').innerHTML=`<line x1="0" x2="${W-R}" y1="${y(1)}" y2="${y(1)}" stroke="#ececea"/><path id="pb" d="${d(B)}" stroke="#848a90" stroke-width="1.4" opacity=".5" pathLength="1"/><path id="ps" d="${d(S)}" stroke="#0b2648" stroke-width="2" opacity=".6" pathLength="1"/>
<g id="ends" style="opacity:0;transition:opacity .6s"><circle cx="${x(n)}" cy="${y(S[n])}" r="3.5" fill="#0b2648"/><text x="${x(n)+8}" y="${y(S[n])+4}" font-family="IBM Plex Mono" font-size="12" font-weight="500" fill="#0b2648">$${S[n].toFixed(2)}</text><circle cx="${x(n)}" cy="${y(B[n])}" r="3" fill="#848a90"/><text x="${x(n)+8}" y="${y(B[n])+4}" font-family="IBM Plex Mono" font-size="12" fill="#848a90">$${B[n].toFixed(2)}</text><text x="4" y="${y(1)-6}" font-family="IBM Plex Mono" font-size="10.5" fill="#9aa0a6">$1 in ${D.y0}</text></g>`;
function count(el){const v=+el.dataset.v,f=+el.dataset.f,s=el.dataset.s,t0=performance.now(),dur=1400;
 (function tick(t){const p=Math.min(1,(t-t0)/dur),e=1-Math.pow(1-p,3);el.textContent=sg((v*e).toFixed(f))+s;if(p<1)requestAnimationFrame(tick);else el.textContent=sg(v.toFixed(f))+s;})(t0);}
function intro(){const els=[...document.querySelectorAll('.fade')];
 if(matchMedia('(prefers-reduced-motion: reduce)').matches){els.forEach(e=>e.classList.add('in'));$('ends').style.opacity=1;return;}
 ['pb','ps'].forEach((id,k)=>{const p=$(id);p.style.strokeDasharray=1;p.style.strokeDashoffset=1;p.getBoundingClientRect();p.style.transition=`stroke-dashoffset 2.8s cubic-bezier(.4,0,.2,1) ${0.6+k*.2}s`;p.style.strokeDashoffset=0;});
 els.forEach((e,i)=>setTimeout(()=>e.classList.add('in'),150+i*170));
 setTimeout(()=>document.querySelectorAll('.card b').forEach(count),150+3*170+200);
 setTimeout(()=>$('ends').style.opacity=1,3500);}
document.querySelectorAll('[data-go]').forEach(btn=>btn.onclick=()=>{const p=btn.dataset.go;
 try{const a=parent.document.querySelector(`[data-testid="stSidebarNav"] a[href$="/${p}"]`);if(a){a.click();return;}}catch(e){}
 try{parent.location.href=p;}catch(e){window.open(p,'_top');}});
const fit=()=>{try{frameElement.style.height=Math.ceil($('lp').getBoundingClientRect().height)+4+'px';}catch(e){}};
new ResizeObserver(fit).observe($('lp'));fit();
const t0=Date.now();(function ready(){let busy=false;try{busy=parent.document.querySelector('.stApp')?.dataset.testScriptState==='running';}catch(e){}
 if((busy||Date.now()-t0<1500)&&Date.now()-t0<6000)return setTimeout(ready,100);intro();})();
</script>"""

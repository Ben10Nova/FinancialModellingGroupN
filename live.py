"""live 2026 board, broker style: ranges 1D / 1W / 1M / YTD, a ticker with the change over the chosen range, and a chart
you can scrub with the mouse or a finger. the app rebuilds it every minute with new 5-minute prices; the chosen range
and the last shown figure survive the rebuild, so the ticker rolls to the new value instead of jumping."""
import json

import streamlit.components.v1 as components


def board(ranges, status, live):
    """ranges: {name: {'t': [iso time or date], 'p': [portfolio value], 's': [S&P 500 value]}}, oldest first"""
    data = dict(r=ranges, st=status, live=live)
    components.html(PAGE.replace('__DATA__', json.dumps(data, separators=(',', ':'))), height=470)


PAGE = r"""<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap');
html,body{margin:0;background:#fff;color:#0e1a2b;font-family:'IBM Plex Sans',sans-serif}
#tk{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
#chg{font-size:44px;font-weight:500;letter-spacing:-.02em;font-variant-numeric:tabular-nums;border-radius:6px;padding:0 6px;margin-left:-6px;transition:background-color 1.2s}
#chg.up{color:#13804f}#chg.dn{color:#a3342b}
#chg.fu{background:rgba(19,128,79,.14);transition:none}#chg.fd{background:rgba(163,52,43,.14);transition:none}
#sp{font-size:14px;color:#4d5866;font-variant-numeric:tabular-nums}
#when{font-size:13px;color:#4d5866;margin:2px 0 14px;font-variant-numeric:tabular-nums}
#tabs{display:flex;gap:6px;margin-bottom:6px}
#tabs button{all:unset;cursor:pointer;font-size:13px;font-weight:500;padding:5px 12px;border-radius:999px;color:#4d5866}
#tabs button:hover{color:#0e1a2b}
#tabs button.on{background:#071a3a;color:#fff}
#tabs button:focus-visible{outline:2px solid #0e7c70;outline-offset:2px}
svg{display:block;width:100%;height:270px;touch-action:pan-y;cursor:crosshair;user-select:none}
#st{font-size:12px;color:#4d5866;margin:8px 0 0;display:flex;align-items:center;gap:8px}
#st i{width:7px;height:7px;border-radius:50%;background:#8c95a0;flex:none}
#st.live i{background:#13804f;animation:pulse 2s ease-in-out infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(19,128,79,.5)}50%{box-shadow:0 0 0 5px rgba(19,128,79,0)}}
.lg{font-size:12px;color:#4d5866;display:flex;gap:16px;margin:0 0 4px}.lg span{display:flex;align-items:center;gap:6px}
.lg i{display:inline-block;width:14px;height:2px}
@media (prefers-reduced-motion:reduce){#st.live i{animation:none}}
</style>
<div id="tk"><span id="chg">&nbsp;</span><span id="sp"></span></div>
<p id="when">&nbsp;</p>
<div id="tabs" role="tablist"></div>
<p class="lg"><span><i style="background:#0e7c70"></i>Portfolio (net)</span><span><i style="background:#8c95a0"></i>S&amp;P 500</span></p>
<svg id="sv" aria-label="Portfolio and S&amp;P 500 over the chosen range"></svg>
<p id="st"><i></i><span id="stt"></span></p>
<script>
const D=__DATA__,R=D.r,$=id=>document.getElementById(id),sv=$('sv'),NAMES=['1D','1W','1M','YTD'].filter(k=>R[k]);
const store={get(k){try{return JSON.parse(localStorage.getItem('mvp_live_'+k))}catch(e){return null}},set(k,v){try{localStorage.setItem('mvp_live_'+k,JSON.stringify(v))}catch(e){}}};
let cur=store.get('range');if(!R[cur])cur=NAMES[0];
const MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],DAY=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
const dt=s=>new Date(s.length>10?s+':00':s+'T00:00:00');
const pct=v=>(v>=0?'+':'−')+Math.abs(v*100).toFixed(2)+'%';
function label(s,k,i){if(i===0&&(k==='1D'||k==='1W'))return 'Previous close';const d=dt(s);const dm=`${d.getDate()} ${MON[d.getMonth()]}`;
 if(s.length<=10)return `${DAY[d.getDay()]} ${dm}, close`;const hm=s.slice(11,16);return k==='1D'?`${DAY[d.getDay()]} ${dm}, ${hm}`:`${DAY[d.getDay()]} ${dm}, ${hm}`;}
function since(k){const r=R[k],s=r.t[0],d=dt(s);
 if(k==='1D'){const e=dt(r.t[r.t.length-1]);return (D.live?'Today':`${DAY[e.getDay()]} ${e.getDate()} ${MON[e.getMonth()]}`)+' · since the previous close';}
 return k==='YTD'?'Since 1 January 2026':`Since the close on ${d.getDate()} ${MON[d.getMonth()]}`;}
// ticker: rolls from the last shown figure; flashes green or red when a refresh moves it
let shown=null;
function setTicker(v,s,when,flash){const el=$('chg');el.className=v>=0?'up':'dn';
 if(flash&&shown!==null&&Math.abs(v-shown)>5e-6){el.classList.add(v>shown?'fu':'fd');requestAnimationFrame(()=>requestAnimationFrame(()=>el.classList.remove('fu','fd')));}
 const from=flash&&shown!==null?shown:v,t0=performance.now();shown=v;
 (function tick(t){const p=Math.min(1,(t-t0)/600),x=from+(v-from)*(1-Math.pow(1-p,3));el.textContent=pct(x);if(p<1)requestAnimationFrame(tick);})(t0);
 $('sp').textContent='S&P 500 '+pct(s);$('when').textContent=when;}
function rangeChange(k,i){const r=R[k];return [r.p[i]/r.p[0]-1,r.s[i]/r.s[0]-1];}
function rest(flash){const r=R[cur],n=r.t.length-1,[a,b]=rangeChange(cur,n);setTicker(a,b,since(cur),flash);store.set('last',{k:cur,v:a});}
// chart
let G=null;
function draw(){const r=R[cur],n=r.t.length,w=sv.clientWidth,h=270,L=4,RR=48,T=10,Bm=26,span=cur==='1D'?Math.max(n,79):n;
 const P=r.p.map(v=>v/r.p[0]-1),S=r.s.map(v=>v/r.s[0]-1);let lo=Math.min(0,...P,...S),hi=Math.max(0,...P,...S);const pad=(hi-lo)*.08||.002;lo-=pad;hi+=pad;
 const x=i=>L+(span<2?0:i/(span-1))*(w-L-RR),y=v=>T+(hi-v)/(hi-lo)*(h-T-Bm),path=a=>a.map((v,i)=>(i?'L':'M')+x(i).toFixed(1)+','+y(v).toFixed(1)).join('');
 let ax='';const fmt=v=>(v>=0?'+':'−')+Math.abs(v*100).toFixed(Math.abs(hi-lo)<.03?1:0)+'%';
 [hi-pad,0,lo+pad].forEach((v,j)=>{if(j!==1&&Math.abs(v)<(hi-lo)*.12)return;ax+=`<text x="${w-RR+8}" y="${y(v)+4}" font-size="11" fill="#8c95a0">${fmt(v)}</text>`;});
 // time labels: hours for one day, days for a week, dates otherwise
 let last='';const marks=[];
 if(cur==='1D')[10,12,14,16].forEach(hr=>marks.push([(hr*60-570)/5+1,hr+':00']));       // bar k starts at 9:30 + 5(k-1) min
 else r.t.forEach((s,i)=>{if(i===0)return;const d=dt(s);
  const m=cur==='1W'?DAY[d.getDay()]:cur==='1M'?`${d.getDate()} ${MON[d.getMonth()]}`:MON[d.getMonth()];
  if(m!==last){if(cur==='1M'&&marks.length&&i-marks[marks.length-1][0]<5)return;if(cur!=='YTD'||d.getMonth()>0)marks.push([i,m]);last=m;}});
 marks.forEach(([i,m])=>ax+=`<text x="${x(i)}" y="${h-6}" font-size="11" fill="#8c95a0" text-anchor="${i>=span-1?'end':'middle'}">${m}</text>`);
 sv.setAttribute('viewBox',`0 0 ${w} ${h}`);
 sv.innerHTML=`<line x1="${L}" x2="${w-RR}" y1="${y(0)}" y2="${y(0)}" stroke="#c4ccd6" stroke-dasharray="3 4"/>${ax}`+
  `<path d="${path(S)}" fill="none" stroke="#8c95a0" stroke-width="1.4" stroke-linejoin="round"/>`+
  `<path d="${path(P)}" fill="none" stroke="#0e7c70" stroke-width="2.2" stroke-linejoin="round"/>`+
  `<g id="cur" style="display:none"><line id="cl" y1="${T}" y2="${h-Bm}" stroke="#0e1a2b" stroke-width="1"/><circle id="cs" r="3.5" fill="#8c95a0"/><circle id="cp" r="4.5" fill="#0e7c70" stroke="#fff" stroke-width="1.5"/></g>`+
  `<circle cx="${x(n-1)}" cy="${y(P[n-1])}" r="4" fill="#0e7c70"/>`;
 G={x,y,P,S,n,L,RR,w,span};}
// scrub: the ticker follows the pointer, like a broker app
function scrub(e){if(!G)return;const b=sv.getBoundingClientRect(),px=(e.touches?e.touches[0].clientX:e.clientX)-b.left;
 const i=Math.max(0,Math.min(G.n-1,Math.round((px-G.L)/(G.w-G.L-G.RR)*(G.span-1))));
 $('cur').style.display='';$('cl').setAttribute('x1',G.x(i));$('cl').setAttribute('x2',G.x(i));
 $('cp').setAttribute('cx',G.x(i));$('cp').setAttribute('cy',G.y(G.P[i]));$('cs').setAttribute('cx',G.x(i));$('cs').setAttribute('cy',G.y(G.S[i]));
 const [a,s]=rangeChange(cur,i);setTicker(a,s,label(R[cur].t[i],cur,i),false);}
function leave(){if(G)$('cur').style.display='none';rest(false);}
sv.addEventListener('pointermove',scrub);sv.addEventListener('pointerdown',scrub);sv.addEventListener('pointerleave',leave);sv.addEventListener('pointerup',e=>{if(e.pointerType!=='mouse')leave();});
function tabs(){$('tabs').innerHTML=NAMES.map(k=>`<button role="tab" aria-selected="${k===cur}" class="${k===cur?'on':''}" data-k="${k}">${k}</button>`).join('');
 $('tabs').querySelectorAll('button').forEach(bt=>bt.onclick=()=>{cur=bt.dataset.k;store.set('range',cur);tabs();draw();shown=null;rest(false);});}
$('st').className=D.live?'live':'';$('stt').textContent=D.st;
tabs();draw();
const prev=store.get('last');if(prev&&prev.k===cur)shown=prev.v;            // a refresh: roll from what was on screen
rest(true);
new ResizeObserver(()=>draw()).observe(document.body);
</script>"""

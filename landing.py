"""home page hero: a night fjord filling the screen, with the key figures over it. one iframe, so the photo can move:
the aurora drifts and breathes, the stars in the photo twinkle and the water shimmers, while the mountains stay still."""
import base64
import json
from pathlib import Path

import streamlit.components.v1 as components

PHOTO = Path(__file__).parent / 'assets' / 'hero.webp'          # 1672 x 941
RIDGE = [(0, 335), (120, 315), (200, 292), (240, 298), (300, 350), (400, 410), (470, 440), (560, 475), (700, 505),
         (830, 570), (870, 580), (950, 560), (1020, 490), (1100, 470), (1200, 420), (1260, 408), (1330, 430), (1380, 390),
         (1440, 345), (1500, 370), (1560, 362), (1620, 338), (1672, 338)]   # skyline traced on the photo, in pixels
ROCKS = [(1672, 696), (1580, 712), (1520, 755), (1370, 780), (1270, 870), (1255, 941)]   # shore rocks, bottom right
# stars found once in the photo (bright points on smooth dark sky above the skyline): x %, y %, strength 0-1
STARS = [[5.62,10.52,1],[5.38,6.06,1],[14.53,7.12,1],[31.1,17.53,1],[65.07,0.43,1],[17.34,7.23,1],[64.0,6.8,1.0],[30.14,8.29,1.0],[48.8,8.4,0.97],[58.91,11.58,0.97],[20.16,14.98,0.96],[12.92,8.5,0.96],[62.32,15.2,0.88],[16.09,15.2,0.88],[0.78,19.02,0.87],[12.44,24.44,0.85],[74.7,10.84,0.85],[21.23,1.59,0.85],[26.38,6.38,0.83],[62.62,8.61,0.83],[23.44,27.74,0.83],[25.66,5.1,0.82],[22.55,23.06,0.8],[30.02,31.77,0.77],[57.48,5.74,0.74],[31.4,22.53,0.73],[16.21,15.94,0.72],[2.21,13.39,0.71],[14.06,27.63,0.71],[15.73,13.5,0.71],[17.05,18.07,0.7],[35.17,24.87,0.67],[11.72,19.34,0.67],[47.73,16.58,0.66],[57.36,4.99,0.66],[33.79,7.55,0.66],[18.9,31.67,0.66],[19.92,30.61,0.65],[29.31,11.58,0.65],[23.98,22.85,0.65],[73.27,14.88,0.64],[9.45,20.94,0.64],[32.95,1.59,0.64],[25.12,8.29,0.64],[4.61,23.59,0.63],[82.12,1.49,0.63],[31.28,1.81,0.62],[24.46,12.33,0.62],[85.23,8.4,0.62],[32.89,4.78,0.62],[90.91,13.82,0.6],[70.22,10.31,0.6],[32.12,8.18,0.6],[51.08,9.78,0.59],[26.14,6.59,0.59],[78.83,0.32,0.58],[78.89,2.55,0.58],[15.91,7.01,0.58],[20.57,22.95,0.57],[74.1,15.3,0.57],[51.56,2.66,0.56],[33.31,6.27,0.56],[54.84,40.6,0.55],[54.96,6.27,0.55],[45.93,18.38,0.55],[20.75,3.93,0.54],[86.42,6.16,0.54],[47.85,12.65,0.54],[66.99,13.07,0.54],[62.02,14.03,0.53],[48.21,0.11,0.53],[79.43,5.84,0.53],[15.25,11.69,0.52],[73.5,16.05,0.52],[48.56,13.82,0.52],[23.09,21.89,0.52],[44.38,4.25,0.51],[93.24,6.7,0.51],[14.95,29.33,0.51],[52.33,0.85,0.51],[34.27,3.08,0.5],[83.85,0.85,0.5],[91.21,12.43,0.49],[94.92,19.98,0.49],[36.66,13.18,0.49],[24.04,22.32,0.48],[21.29,2.13,0.48],[25.3,2.76,0.47],[52.87,3.72,0.47],[0.66,0.43,0.47],[83.43,1.17,0.46],[72.31,23.27,0.46],[24.22,27.95,0.46],[14.17,21.36,0.46],[49.16,3.72,0.46],[43.24,19.13,0.45],[44.74,5.31,0.45],[49.76,5.74,0.44],[3.29,6.8,0.44],[66.33,21.57,0.44],[35.71,14.88,0.44],[22.31,12.54,0.44],[86.0,29.22,0.44],[30.56,3.61,0.43],[72.19,5.74,0.43],[64.0,13.5,0.43],[61.12,9.88,0.43],[57.78,13.07,0.43],[23.8,21.47,0.43],[11.6,1.28,0.43],[12.14,12.54,0.42],[23.39,13.6,0.42],[36.0,12.75,0.42],[46.89,6.91,0.42],[37.8,8.71,0.42],[14.77,11.16,0.42],[33.07,17.43,0.42],[70.39,6.7,0.42],[18.96,7.23,0.42],[19.86,11.69,0.41],[44.2,1.38,0.41],[1.56,30.29,0.41],[18.24,8.61,0.4],[55.08,20.09,0.4],[72.01,1.49,0.4],[23.27,28.59,0.4],[73.5,18.92,0.4],[50.78,3.72,0.4],[28.77,10.84,0.4],[32.18,39.21,0.4],[91.51,28.8,0.4],[26.85,16.26,0.4],[22.73,37.94,0.39],[28.95,13.82,0.39],[22.73,3.61,0.39],[11.18,0.53,0.39],[52.99,2.23,0.39],[47.97,7.01,0.38],[53.53,11.37,0.38],[72.43,1.81,0.38]]


def landing(res, fund, fund_long):
    """res: results at the notebook defaults, so the home page always shows the prospectus numbers"""
    t = res['table']
    fig = lambda k, m=100: [round(float(t.loc[k, c]) * m, 1 if m == 100 else 2) for c in ('Strategy (net)', 'S&P 500 TR')]
    y0, y1 = res['bt'].index[0].year, res['bt'].index[-1].year
    pct = lambda pts: ','.join(f'{x / 16.72:.2f}% {y / 9.41:.2f}%' for x, y in pts)
    data = dict(kpi=[[*fig('Ann. avg return'), 1, '%', 'Average return a year'], [*fig('Ann. volatility'), 1, '%', 'Volatility a year'],
                     [*fig('Sharpe ratio', 1), 2, '', 'Sharpe ratio'], [*fig('Max drawdown (monthly)'), 1, '%', 'Largest fall, month-end']],
                stars=STARS, years=f'{y0}–{y1}')
    page = (PAGE.replace('__DATA__', json.dumps(data, separators=(',', ':'))).replace('__FUND__', fund).replace('__LONG__', fund_long)
            .replace('__IMG__', base64.b64encode(PHOTO.read_bytes()).decode())
            .replace('__SKY__', f'polygon(0 0,100% 0,{pct(RIDGE[::-1])})')
            .replace('__WATER__', f'polygon(0 66.5%,100% 66.5%,{pct(ROCKS)},0 100%)'))
    components.html(page, height=1)                                # the css on the home page makes the frame fill the screen


PAGE = r"""<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500&family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap');
html,body{margin:0;height:100%;overflow:hidden;background:#06122e}
#stage{position:absolute;background:0 0/100% 100% no-repeat}
#stage>*{position:absolute;inset:0;width:100%;height:100%}
.sky{clip-path:__SKY__}
#water{clip-path:__WATER__}
.aur{mix-blend-mode:screen;opacity:.15;transform-origin:50% 66.5%;animation:breathe 11s ease-in-out infinite,drift 23s ease-in-out infinite alternate}
.aur.g{filter:hue-rotate(-30deg) saturate(1.3);animation-duration:17s,31s;animation-delay:-6s,-9s;animation-direction:normal,alternate-reverse}
.aur.w{clip-path:__WATER__;animation-name:breathe,driftw}
@keyframes breathe{0%,100%{opacity:.12}50%{opacity:.75}}
@keyframes drift{from{transform:translateX(-1.3%) scaleY(1)}to{transform:translateX(1.3%) scaleY(1.05)}}
@keyframes driftw{from{transform:translateX(-1.3%) scaleY(1)}to{transform:translateX(1.3%) scaleY(1.03)}}
#shade{position:fixed;inset:0;background:linear-gradient(180deg,rgba(3,10,28,.55),rgba(3,10,28,0) 22%),
 linear-gradient(90deg,rgba(3,10,28,.62),rgba(3,10,28,.2) 55%,rgba(3,10,28,0) 80%)}
#txt{position:fixed;left:var(--pad);right:var(--pad);top:50%;transform:translateY(-38%);color:#fff;font-family:'IBM Plex Sans',sans-serif}
:root{--pad:clamp(20px,4vw,64px)}
.brand{display:none;font-family:'Newsreader',serif;font-weight:500;font-size:34px;margin:0 0 18px}
.eye{font-size:13px;letter-spacing:.04em;color:rgba(255,255,255,.78);margin:0 0 26px}
.nums{display:grid;grid-template-columns:repeat(4,max-content);gap:28px clamp(36px,5vw,76px)}
.nums b{display:block;font-family:'Newsreader',serif;font-weight:400;font-size:clamp(46px,5.6vw,82px);line-height:1;
 letter-spacing:-.015em;font-variant-numeric:lining-nums tabular-nums;text-shadow:0 2px 24px rgba(0,0,0,.25)}
.nums span{display:block;font-size:14px;margin-top:12px;color:rgba(255,255,255,.92)}
.nums i{display:block;font-style:normal;font-size:12.5px;margin-top:3px;color:rgba(255,255,255,.62);font-variant-numeric:tabular-nums}
#fine{position:fixed;left:var(--pad);bottom:20px;max-width:56ch;margin:0;font:12px/1.5 'IBM Plex Sans',sans-serif;color:rgba(255,255,255,.6)}
.fade{opacity:0;transform:translateY(10px);transition:opacity 1.1s ease,transform 1.1s ease}.fade.in{opacity:1;transform:none}
@media (max-width:760px){.brand{display:block}.nums{grid-template-columns:repeat(2,max-content)}#txt{transform:translateY(-45%)}
 .nums b{font-size:44px}.nums span{font-size:13px}#fine{bottom:64px;right:var(--pad)}}
@media (prefers-reduced-motion:reduce){.aur{animation:none}.fade{transition:none}}
</style>
<div id="stage"><canvas id="water"></canvas><canvas class="aur sky"></canvas><canvas class="aur sky g"></canvas><canvas class="aur w"></canvas><canvas id="stars" class="sky"></canvas></div>
<div id="shade"></div>
<div id="txt"><p class="brand fade">__FUND__</p><p class="eye fade">__LONG__ &middot; simulated backtest, <span id="yrs"></span>, net of costs</p><div class="nums fade" id="nums"></div></div>
<p id="fine" class="fade">Student project for 2270 Financial Modeling at Nova SBE. Simulated figures, not investment advice. Past performance does not predict future results.</p>
<script>
const D=__DATA__,$=id=>document.getElementById(id),still=matchMedia('(prefers-reduced-motion: reduce)').matches;
const sg=s=>String(s).replace(/^-/,'−');
$('yrs').textContent=D.years;
$('nums').innerHTML=D.kpi.map(([v,b,f,s,l])=>`<div><b data-v="${v}" data-f="${f}" data-s="${s}">${sg(v.toFixed(f))}${s}</b><span>${l}</span><i>S&amp;P 500: ${sg(b.toFixed(f))}${s}</i></div>`).join('');
const img=new Image(),st=$('stage'),wc=$('water'),sc=$('stars'),IW=1672,IH=941,TOP=.665;
let W=0,H=0,dpr=1;
function layout(){const vw=innerWidth,vh=innerHeight;W=Math.max(vw,vh*IW/IH);H=W*IH/IW;
 const left=Math.min(0,Math.max(vw-W,vw/2-W*.62));         // phones: keep the aurora, right of centre, in view
 Object.assign(st.style,{width:W+'px',height:H+'px',left:left+'px',top:(vh-H)/2+'px'});
 dpr=Math.min(devicePixelRatio||1,2);[wc,sc].forEach(c=>{c.width=W*dpr;c.height=H*dpr;});}
function aurora(){                                         // the aurora alone: pixels where green beats red and blue
 const w=836,h=470,c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');x.drawImage(img,0,0,w,h);
 const d=x.getImageData(0,0,w,h),p=d.data;
 for(let i=0;i<p.length;i+=4){const s=p[i+1]-.5*(p[i]+p[i+2]);p[i+3]=Math.max(0,Math.min(255,(s-4)*8.5));}
 x.putImageData(d,0,0);
 document.querySelectorAll('.aur').forEach(a=>{a.width=w;a.height=h;const y=a.getContext('2d');y.filter='blur(1.5px)';y.drawImage(c,0,0);});}
const S=D.stars.map(([x,y,a])=>({x:x/100,y:y/100,a,ph:Math.random()*6.28,sp:.6+Math.random()*1.4}));
function frame(ms){const t=ms/1000,g=wc.getContext('2d'),s=sc.getContext('2d'),w=W*dpr,h=H*dpr;
 // water: redraw the reflection in thin bands, each nudged sideways by a slow wave, a little more towards the viewer
 const y0=Math.round(h*TOP),band=2*dpr,sh=IH/h*band;g.clearRect(0,0,w,h);
 for(let y=y0;y<h;y+=band){const k=(y-y0)/(h-y0),dx=(.5+1.6*k)*dpr*Math.sin(y/(7*dpr)*.55+t*.9+Math.sin(t*.23+y/(60*dpr)));
  g.drawImage(img,0,y/h*IH,IW,sh,dx-4*dpr,y,w+8*dpr,band);}
 // stars: each fades in and out on its own slow rhythm, at most a soft glow
 s.clearRect(0,0,w,h);
 for(const o of S){const v=.5+.5*Math.sin(t*o.sp+o.ph);if(v<.35)continue;const r=(1+1.2*o.a)*dpr;
  const gr=s.createRadialGradient(o.x*w,o.y*h,0,o.x*w,o.y*h,r*2.4);gr.addColorStop(0,`rgba(235,245,255,${.75*o.a*(v-.35)/.65})`);gr.addColorStop(1,'rgba(235,245,255,0)');
  s.fillStyle=gr;s.fillRect(o.x*w-r*2.4,o.y*h-r*2.4,r*4.8,r*4.8);}}
let last=0;function loop(ms){if(ms-last>40){last=ms;frame(ms);}requestAnimationFrame(loop);}   // about 25 frames a second
function count(el){const v=+el.dataset.v,f=+el.dataset.f,s=el.dataset.s,t0=performance.now(),dur=1600;
 (function tick(t){const p=Math.min(1,(t-t0)/dur),e=1-Math.pow(1-p,3);el.textContent=sg((v*e).toFixed(f))+s;if(p<1)requestAnimationFrame(tick);else el.textContent=sg(v.toFixed(f))+s;})(t0);}
img.onload=()=>{st.style.backgroundImage=`url(${img.src})`;layout();aurora();addEventListener('resize',()=>{layout();if(still)frame(0);});
 if(still){frame(0);document.querySelectorAll('.fade').forEach(e=>e.classList.add('in'));return;}
 requestAnimationFrame(loop);
 document.querySelectorAll('.fade').forEach((e,i)=>setTimeout(()=>e.classList.add('in'),250+i*220));
 setTimeout(()=>document.querySelectorAll('.nums b').forEach(count),700);};
img.src='data:image/webp;base64,__IMG__';
</script>"""

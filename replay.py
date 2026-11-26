"""performance page: growth of $1 as a year-by-year replay with an equity exposure strip and one story per year.
everything runs client-side in one iframe, so the curve can redraw smoothly without streamlit reruns."""
import html
import json

import streamlit.components.v1 as components

from strategy import wealth

# one story per calendar year: title, what happened, what we did, result, crisis year (holds longer while playing).
# the numbers in these texts were checked against the combined backtest at the notebook defaults (Params()),
# so they are only shown when the page runs with those settings.
STORIES = {
    2006: ('a calm start',
           'quiet markets for most of the year, broken by an emerging-market selloff in may and june.',
           'volatility sat well below our 15% target, so exposure ran 1.3–1.8x, fell below 1x in june–july and was back at 2x from august.',
           "ahead for the year, all of it in the second half. the may–june selloff cost us 15%, twice the market's fall.", 0),
    2007: ('the first cracks',
           'subprime funds froze in august and the "quant quake" hit hedge funds. the market peaked in october.',
           'exposure fell from 1.8x in january to about 0.5x by summer, rose to 1x in the autumn and was near 0.5x in december.',
           'ahead of the market. in the second half the spread (+5%) offset the equity loss.', 0),
    2008: ('the financial crisis',
           'lehman brothers failed in september and the s&p 500 lost 37% over the year.',
           'exposure stayed between 0.4x and 0.7x, then went to zero at the end of september. the spread made 11%.',
           'from the october 2007 peak to the march 2009 low we lost 15%, the market 55%.', 1),
    2009: ('the rebound we missed',
           'stocks bottomed on march 9 and rallied 65% from the low.',
           'started from zero exposure and only added risk as volatility fell. the spread added 4%.',
           'behind the market. the price of a smoother ride: we buy back slowly.', 0),
    2010: ('flash crash',
           "the dow briefly fell almost 1,000 points on may 6, days after greece's first bailout.",
           'went into may at about 0.9x. the june reset cut to 0.44x, and exposure stayed below 1x until october.',
           'a decent year, but behind the index. the may drop hit us as hard as the market (−15%).', 0),
    2011: ('euro crisis',
           'fears over greek, italian and spanish debt peaked, and the us lost its aaa rating in august.',
           'exposure was about 0.9x going into august. the drop came within days, faster than a monthly reset. '
           'afterwards exposure stayed near 0.4x.',
           "slightly ahead. our drawdown was 17%, the market's 19%.", 1),
    2012: ('whatever it takes',
           'in july ecb president draghi promised to do "whatever it takes" to save the euro, and fear left the market.',
           'exposure a little above 1x. the spread was open on 61% of days, its busiest year, but lost 2%.',
           'slightly ahead of the market, all of it from the equity sleeve.', 0),
    2013: ('the taper tantrum',
           'bond yields jumped when the fed hinted at slowing its bond buying, but stocks gained 32%.',
           'calm stretches let the model lever up toward 2x.',
           'ahead for the year, but the taper scare cost us 12% (market −6%), because the spread fell with yields.', 0),
    2014: ('low volatility',
           'a calm year, until oil prices slumped in the second half.',
           'exposure averaged 1.36x. the end-october reset halved it for november, and it was back at 2x for december.',
           'well ahead. the spread (+13%) added as much as the equity sleeve.', 0),
    2015: ('china shakes markets',
           'china devalued the yuan on aug 11. a week later the s&p 500 fell 11% in six trading days.',
           'we went into august at about 1x and took the drop, then cut to 0.4x. '
           'spread volatility had kept us at zero in april and may.',
           'the market was flat. the spread made 22% and carried the year; the equity sleeve lost 4%.', 0),
    2016: ('brexit and the election',
           'two shocks that faded fast: the brexit vote in june and the us election in november.',
           'the january selloff cut exposure to 0.3–0.5x just as stocks rebounded. after brexit we cut to 0.7x for july.',
           'matched the market, but with more volatility and a 10% drop around the brexit vote.', 0),
    2017: ('the calmest year ever',
           'record-low volatility. with dividends, the s&p 500 rose in every month.',
           'exposure sat near the 2x cap all year and never fell below 1.28x.',
           'almost twice the market return, but fully exposed if volatility returned.', 0),
    2018: ('volmageddon',
           'the vix more than doubled in one day in february. rate hikes and the trade war hit stocks in q4.',
           'went into february at 0.44x and q4 at 2x, cutting each time at the next reset. the spread made 9% in q4.',
           'a small loss against a bigger market loss.', 1),
    2019: ('the fed pivots',
           'the fed paused in january and cut rates three times from july. stocks gained 31%.',
           'zero exposure in january and february, then back to 2x by april.',
           'behind the index all year. the spread made 14%, the equity sleeve 9%.', 0),
    2020: ('covid',
           'the s&p 500 fell a third in a month, the fastest crash on record.',
           'the end-of-february reset took exposure to zero until july. the spread carried the rebound (+46% by june).',
           'well ahead at 0.49x average exposure, but the spread swung hard: −22% in the week to march 23.', 1),
    2021: ('meme stocks',
           'gamestop grabbed the headlines while the index climbed with few setbacks.',
           'exposure dropped to 0.4x in february, then ran near 1.2x. costs (2%) and a flat spread added to the gap.',
           'behind the market in a strong year.', 0),
    2022: ('the rate shock',
           'inflation hit a 40-year high and the fed hiked faster than in decades. stocks and bonds fell together.',
           'exposure fell from 0.8x to about 0.4x by spring and stayed below 0.9x. the spread made 13%.',
           'almost flat while the market lost 18%.', 1),
    2023: ('banks wobble, ai takes off',
           'silicon valley bank failed in march, then the ai rally lifted the biggest tech stocks.',
           'rebuilt exposure to about 1x as volatility faded. both sleeves contributed: equity +18%, spread +19%.',
           'beat the market by 13 points.', 0),
    2024: ('the ai boom',
           'ai optimism kept stocks climbing. the yen carry trade unwound in august.',
           'trimmed risk after the august spike and rebuilt it as calm returned. the spread gained 4% in the unwind.',
           'ahead of the market.', 0),
    2025: ('tariffs',
           'tariffs announced on april 2 cut the s&p 500 12% in four days, 19% from its february peak.',
           'exposure had been low since january and was 0.44x when the drop hit.',
           'lost 5% from february to the april low, the market 19%. finished well ahead.', 1),
}


def replay(res, p, defaults):
    """growth of $1 chart for the performance page, with play button, start-year slider and one story per year"""
    bt, bench = res['bt'], res['bench_d']
    first = bt.index[0].to_period('M')
    month = lambda w: w[w.index.to_period('M') >= first].resample('ME').last()  # drop the start point wealth() prepends
    ws, wb = month(wealth(bt.net)), month(wealth(bench))
    expo = bt.w_spy.resample('ME').mean().reindex(ws.index).fillna(0)
    show = p == defaults
    years = []
    for y, r in res['yearly'].iterrows():
        title, happened, did, result, crisis = STORIES.get(int(y), ('', '', '', '', 0)) if show else ('', '', '', '', 0)
        years.append(dict(y=int(y), pf=round(float(r['Strategy']) * 100, 1), sp=round(float(r['S&P 500 TR']) * 100, 1),
                          ex=round(float(bt.w_spy.loc[str(y)].mean()), 2), t=html.escape(title), h=html.escape(happened),
                          d=html.escape(did), r=html.escape(result), c=crisis))
    data = dict(m=[d.strftime('%Y-%m') for d in ws.index], s=[round(v, 4) for v in ws], b=[round(v, 4) for v in wb],
                e=[round(v, 2) for v in expo], y=years, stories=show)
    components.html(PAGE.replace('__DATA__', json.dumps(data, separators=(',', ':'))), height=880)


PAGE = r"""<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap');
html,body{margin:0;background:transparent}
#app{color:#101924;font-family:'IBM Plex Sans',sans-serif;padding:2px 1px 8px}
.mono{font-family:'IBM Plex Mono',monospace;font-variant-numeric:tabular-nums}
.lede{font-family:'Newsreader',serif;font-size:19px;line-height:1.45;margin:0 0 22px;max-width:60ch}
.lede b{font-family:'IBM Plex Mono',monospace;font-weight:500;font-size:.92em}
.hd{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;padding-bottom:8px;border-bottom:1px solid #101924}
.lg{display:flex;gap:18px;font-size:13.5px;color:#555b63}.lg span{display:flex;align-items:center;gap:7px}
.lg i{width:20px;height:3px;border-radius:2px;display:inline-block}
.ctl{display:flex;align-items:center;gap:18px;margin:18px 0 26px;flex-wrap:wrap}
#pl{all:unset;cursor:pointer;font-size:13px;font-weight:500;background:#101924;color:#fff;border-radius:999px;padding:8px 24px}
#pl:hover{background:#0b2648}
#tg{all:unset;cursor:pointer;font-size:13px;color:#0b2648;font-weight:500;display:inline-flex;align-items:center;gap:6px;padding:2px 0}
#tg:hover{text-decoration:underline;text-underline-offset:3px}
.start{flex:1;min-width:210px;max-width:280px;display:flex;align-items:center;gap:12px;margin-left:auto;font-size:13.5px;color:#555b63}
#yr{-webkit-appearance:none;appearance:none;width:100%;height:2px;background:#101924;outline:none;margin:0}
#yr::-webkit-slider-thumb{-webkit-appearance:none;width:14px;height:14px;border-radius:50%;background:#101924;cursor:grab}
#yr::-moz-range-thumb{width:14px;height:14px;border:0;border-radius:50%;background:#101924;cursor:grab}
.r{display:grid;grid-template-columns:124px minmax(0,1fr);gap:16px;padding:10px 0;border-bottom:.5px solid #e4e4e1;font-size:14px;line-height:1.55}
.r .k{color:#0b2648;font-size:13.5px;font-weight:600}
@media (max-width:540px){.r{grid-template-columns:1fr;gap:2px}}
#body{overflow:hidden;transition:max-height .35s ease,opacity .3s;max-height:400px}
#body.closed{max-height:0;opacity:0}
#story{transition:opacity .3s}
.foot{margin:12px 0 0;font-size:12.5px;color:#848a90}
.yt{cursor:pointer}
</style>
<div id="app">
  <p class="lede">$1 invested in <span id="l0"></span>: <b id="ls"></b> (s&amp;p 500 tr: <b id="lb"></b>) by <span id="l1"></span>.</p>
  <div class="hd"><b style="font-weight:500;font-size:15px">growth of $1, log scale</b><div class="lg"><span style="color:#0b2648"><i style="background:#0b2648"></i>portfolio (net)</span><span><i style="background:#848a90"></i>s&amp;p 500 tr</span></div></div>
  <svg id="sv" viewBox="0 0 640 340" width="100%" style="display:block;margin-top:12px;overflow:visible" role="img" aria-label="growth of $1, equity exposure and years"></svg>
  <div class="ctl">
    <button id="pl">play</button>
    <div class="start" id="startbox"><span>start</span><input type="range" id="yr" step="1" aria-label="start year"><span id="yv" class="mono" style="font-size:12.5px;min-width:34px"></span></div>
  </div>
  <div id="story" aria-live="polite">
    <div class="hd"><b id="sh" style="font-weight:500;font-size:15px"></b><span id="sn" class="mono" style="font-size:12.5px;color:#555b63"></span></div>
    <div id="body"></div>
    <div id="tgbox" style="margin-top:10px"><button id="tg" aria-expanded="true"><span id="tgt">hide story</span><span id="tgi">&#8963;</span></button></div>
  </div>
  <p class="foot" id="foot">full calendar-year returns, net of trading, financing and borrow costs.</p>
</div>
<script>
const D=__DATA__,N=D.m.length,S=D.s,B=D.b,E=D.e,YS=D.y;
const INK='#101924',MUTED='#555b63',S1='#0b2648',S2='#848a90',$=id=>document.getElementById(id),sv=$('sv');
const MN=['january','february','march','april','may','june','july','august','september','october','november','december'];
const full=i=>MN[+D.m[i].slice(5,7)-1]+' '+D.m[i].slice(0,4);
const first=y=>D.m.findIndex(s=>+s.slice(0,4)===y);
const last=y=>{let j=-1;D.m.forEach((s,i)=>{if(+s.slice(0,4)===y)j=i;});return j;};
const yOf=i=>+D.m[i].slice(0,4),kOf=y=>YS.findIndex(o=>o.y===y);
const L=48,W=640,GT=6,GB=236,ET=262,EB=300,AX=322;
let yr=YS[0].y,st0=0,bs=1,bb=1,X,YY,cur=N-1,sel=0,tm=null,hd=null,on=false,open=true;
const vs=i=>i<st0?1:S[i]/bs,vb=i=>i<st0?1:B[i]/bb,EY=v=>EB-Math.min(v,2.2)/2.2*(EB-ET);
const many=()=>YS.length-kOf(yr)>10;
function init(){st0=first(yr);bs=st0?S[st0-1]:1;bb=st0?B[st0-1]:1;let lo=1,hi=1;for(let i=st0;i<N;i++){lo=Math.min(lo,vs(i),vb(i));hi=Math.max(hi,vs(i),vb(i));}
 const a=Math.log(lo/1.1),b=Math.log(hi*1.1);X=i=>L+(i-st0+1)/(N-st0)*(W-L-6);YY=v=>GT+(b-Math.log(v))/(b-a)*(GB-GT);
 let t='';[0.5,1,2,5,10,20,30,50,100].filter(v=>v>=lo/1.1&&v<=hi*1.1).forEach(v=>{t+=`<text x="${L-10}" y="${YY(v)+4}" text-anchor="end" font-family="IBM Plex Mono" font-size="11.5" fill="${MUTED}">$${v}</text>`;});
 t+=`<line x1="${L}" x2="${W}" y1="${YY(1)}" y2="${YY(1)}" stroke="${INK}"/>`;
 t+=`<text x="${L-10}" y="${ET+10}" text-anchor="end" font-family="IBM Plex Mono" font-size="11.5" fill="${MUTED}">2x</text><text x="${L-10}" y="${EB+3}" text-anchor="end" font-family="IBM Plex Mono" font-size="11.5" fill="${MUTED}">0x</text><text x="${L}" y="${ET-8}" font-family="IBM Plex Sans" font-size="12" fill="${MUTED}">equity exposure</text><line x1="${L}" x2="${W}" y1="${EB}" y2="${EB}" stroke="${INK}"/>`;
 const bw=(W-L-6)/(N-st0);let eb='';for(let i=st0;i<N;i++)eb+=`<rect class="eb" data-i="${i}" x="${X(i)-bw+.3}" y="${EY(E[i])}" width="${Math.max(bw-.6,.5)}" height="${EB-EY(E[i])}" fill="#d0d3d6" opacity="0"/>`;
 let ax='';YS.forEach((o,k)=>{if(o.y<yr)return;const x0=X(first(o.y)-1),x1=X(last(o.y));
  ax+=`<g class="yt" data-k="${k}"><rect x="${x0}" y="${GT}" width="${x1-x0}" height="${AX+10-GT}" fill="transparent"/><line id="u${k}" x1="${x0+1}" x2="${x1-1}" y1="${EB+5}" y2="${EB+5}" stroke="${INK}" stroke-width="2" opacity="0"/><text id="t${k}" x="${(x0+x1)/2}" y="${AX}" text-anchor="middle" font-family="IBM Plex Mono" font-size="11.5" fill="${MUTED}">${o.y}</text></g>`;});
 sv.innerHTML=`<rect id="hl" y="${GT}" height="${EB-GT}" fill="#f4f4f2" opacity="0"/>${t}${eb}<path id="pb" fill="none" stroke="${S2}" stroke-width="1.5" stroke-linejoin="round"/><path id="ps" fill="none" stroke="${S1}" stroke-width="2.2" stroke-linejoin="round"/>${ax}`;
 sv.querySelectorAll('.yt').forEach(g=>{g.onclick=()=>{stop();show(+g.dataset.k,true);};});
 $('l0').textContent=full(st0);}
function line(f,n){let d=`M${L},${YY(1)}`;for(let i=st0;i<=n;i++)d+=`L${X(i).toFixed(1)},${YY(f(i)).toFixed(1)}`;return d;}
function render(n){$('ps').setAttribute('d',line(vs,n));$('pb').setAttribute('d',line(vb,n));
 $('ls').textContent='$'+(n<st0?1:vs(n)).toFixed(2);$('lb').textContent='$'+(n<st0?1:vb(n)).toFixed(2);$('l1').textContent=full(Math.max(n,st0));
 const sy=YS[sel].y;sv.querySelectorAll('.eb').forEach(r=>{const i=+r.dataset.i;r.setAttribute('opacity',i>n?0:1);r.setAttribute('fill',yOf(i)===sy?S1:'#d0d3d6');});}
function mark(k){const y=YS[k].y,a=X(Math.max(first(y),st0)-1),b=X(last(y));$('hl').setAttribute('x',a);$('hl').setAttribute('width',b-a);$('hl').setAttribute('opacity',1);
 YS.forEach((o,j)=>{const u=$('u'+j),t=$('t'+j);if(!u)return;const s=j===k;u.setAttribute('opacity',s?1:0);t.setAttribute('fill',s?INK:MUTED);t.setAttribute('font-weight',s?500:400);t.setAttribute('opacity',s||((!many()||o.y%4===0)&&Math.abs(o.y-YS[k].y)>(many()?1:0))?1:0);});}
const pct=v=>(v>0?'+':v<0?'−':'')+Math.abs(v).toFixed(1)+'%';
function story(k){const e=YS[k],s=$('story');s.style.opacity=0;setTimeout(()=>{
 $('sh').innerHTML=`${e.y}${e.t?` &nbsp;<span style="font-weight:400">${e.t}</span>`:''}`;
 $('sn').innerHTML=`portfolio <b style="font-weight:500;color:${S1}">${pct(e.pf)}</b> &nbsp; s&amp;p 500 ${pct(e.sp)} &nbsp; exposure ${e.ex.toFixed(2)}x`;
 $('body').innerHTML=e.h?`<div class="r"><span class="k">what happened</span><span>${e.h}</span></div><div class="r"><span class="k">what we did</span><span>${e.d}</span></div><div class="r" style="border-bottom:0"><span class="k">result</span><span style="font-weight:500">${e.r}</span></div>`:'';
 s.style.opacity=1;},180);}
function toggle(){open=!open;$('body').classList.toggle('closed',!open);$('tgt').textContent=open?'hide story':'show story';$('tgi').innerHTML=open?'&#8963;':'&#8964;';$('tg').setAttribute('aria-expanded',open);setTimeout(fit,450);}
function show(k,jump){sel=k;if(jump)cur=last(YS[k].y);render(cur);mark(k);story(k);}
function playYear(){if(!on)return;const k=sel,end=last(YS[k].y);
 (function draw(){if(!on)return;if(cur<end){cur++;render(cur);tm=setTimeout(draw,180);return;}
  const wait=D.stories&&open?(YS[k].c?6000:4200):1100;
  hd=setTimeout(()=>{if(!on)return;if(k>=YS.length-1){stop();return;}sel=k+1;mark(sel);story(sel);render(cur);setTimeout(playYear,300);},wait);})();}
function play(){if(on){stop();return;}on=true;$('pl').textContent='pause';
 if(cur>=N-1){cur=st0-1;sel=kOf(yr);}else sel=kOf(yOf(Math.min(cur+1,N-1)));
 render(cur);mark(sel);story(sel);setTimeout(playYear,400);}
function stop(){on=false;clearTimeout(tm);clearTimeout(hd);$('pl').textContent='play';}
$('pl').onclick=play;$('tg').onclick=toggle;
const ys=$('yr');ys.min=YS[0].y;ys.max=YS[YS.length-1].y-(YS.length>1?1:0);ys.value=yr;$('yv').textContent=yr;
if(YS.length<2)$('startbox').style.display='none';
ys.oninput=e=>{yr=+e.target.value;$('yv').textContent=yr;stop();init();cur=N-1;sel=Math.max(sel,kOf(yr));render(cur);mark(sel);story(sel);};
if(!D.stories){$('tgbox').style.display='none';$('foot').textContent='full calendar-year returns, net of trading, financing and borrow costs. the year stories describe the notebook defaults: reset to see them.';}
document.addEventListener('keydown',e=>{if(e.target.tagName==='INPUT')return;if(e.code==='Space'){e.preventDefault();play();}
 if(e.key==='ArrowRight'){stop();show(Math.min(YS.length-1,sel+1),true);}if(e.key==='ArrowLeft'){stop();show(Math.max(kOf(yr),sel-1),true);}});
const fit=()=>{try{frameElement.style.height=Math.ceil($('app').getBoundingClientRect().height)+4+'px';}catch(err){}};
new ResizeObserver(fit).observe($('app'));$('body').addEventListener('transitionend',fit);
init();sel=Math.max(0,kOf(2008));if(sel<0)sel=0;render(cur);mark(sel);story(sel);fit();
</script>"""

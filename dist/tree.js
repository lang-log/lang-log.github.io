'use strict';
// The classification tree of Lang Log, drawn inside the top page (all roots,
// with search and filters) and inside every record page (the branch below that
// record). Every record has its own static page; this script only draws the
// outline and the zoomable tree, and choosing a record opens its page.
//
// Markup: an element #atlas with
//   data-base  path from the page to the site root ("" on the top page, "../" ...);
//   data-root  (record pages) the record whose branch is drawn;
//   data-src   (record pages) the source of that branch: glottolog, wals or a study id.
// The top page also has the search form #home-q, the filters #evidence and
// #category and the result list #results.
//
// URL state (query string): q (search), evidence, category, dialects=0,
// view=tree, x/y/z (tree centre and zoom).
(()=>{
const host=document.getElementById('atlas');if(!host)return;
// The page's font stack (--font in style.css, which follows the interface language), for the canvas and the SVG export.
const siteFont=()=>getComputedStyle(document.body).fontFamily;
const $=id=>document.getElementById(id),fmt=n=>n.toLocaleString(),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const base=host.dataset.base||'',rootId=host.dataset.root||null,rootSrc=host.dataset.src||'glottolog',branchPage=!!rootId;
let data,unified,nodes,sourcePaths={},display='list',positions=[],scale=1,tx=0,ty=0,width=800,height=500,dirty=false,customView=false,restoring=false,searchTimer=0,viewTimer=0,matches=[];
const bySource=new Map(),conflictAncestors=new Set(),canvas=$('tree'),ctx=canvas.getContext('2d');
const children=(sid,id)=>bySource.get(sid+'|'+id)||[],source=id=>unified.sources[id],title=id=>source(id)?.title||id;
const eligible=n=>n&&($('dialects').checked||n.level!=='dialect');
const tc={},tok=h=>tc[h]||(tc[h]=getComputedStyle(document.documentElement).getPropertyValue('--c-'+h).trim()||'#'+h);
// One colour for every node: all records are languoids, so the tree does not mark them by kind.
const col=()=>tok('397b7b');
const round=(v,d)=>{const f=10**d;return Math.round(v*f)/f};
const search=$('home-q'),evidence=$('evidence'),category=$('category');

// The page of a record, relative to this page.
function pageURL(id){if(data.nodes[id])return base+window.LineagePaths.url(id);if(sourcePaths[id])return base+sourcePaths[id];return base+'record.html?domain=language&id='+encodeURIComponent(id)}
function open(id){location.href=pageURL(id)}

function stateURL(){const p=new URLSearchParams(location.search);for(const k of ['q','evidence','category','dialects','view','x','y','z'])p.delete(k);
 const q=search?.value.trim();if(q)p.set('q',q);if(evidence&&evidence.value!=='all')p.set('evidence',evidence.value);if(category&&category.value!=='all')p.set('category',category.value);if(!$('dialects').checked)p.set('dialects','0');
 if(display==='chart'){p.set('view','tree');if(customView){p.set('x',String(round((width/2-tx)/scale,0)));p.set('y',String(round((height/2-ty)/scale,0)));p.set('z',String(Number(scale.toPrecision(4))))}}
 const u=new URL(location.href);u.search=p.toString();return u}
function saveURL(push){if(restoring||!data)return;const u=stateURL();if(u.href===location.href)return;try{history[push?'pushState':'replaceState'](null,'',u)}catch(e){}}
function viewMoved(){customView=true;requestDraw();clearTimeout(viewTimer);viewTimer=setTimeout(()=>saveURL(false),400)}
function setOption(el,v){if(el)el.value=[...el.options].some(o=>o.value===v)?v:'all'}
function applyURL(){const p=new URLSearchParams(location.search);restoring=true;try{
 if(search)search.value=p.get('q')||'';setOption(evidence,p.get('evidence'));setOption(category,p.get('category'));$('dialects').checked=p.get('dialects')!=='0';
 display=p.get('view')==='tree'?'chart':'list';showDisplay();
 updateResults();
 if(display==='list')renderOutline();else{resize();layout();const x=parseFloat(p.get('x')),y=parseFloat(p.get('y')),z=parseFloat(p.get('z'));if([x,y,z].every(Number.isFinite)&&z>0){scale=Math.max(.0001,Math.min(20,z));tx=width/2-x*scale;ty=height/2-y*scale;customView=true;requestDraw()}}
 syncButtons();
}finally{restoring=false}}
function ancestors(id){const a=[],seen=new Set();while(data.nodes[id]&&!seen.has(id)){seen.add(id);a.unshift(id);id=data.nodes[id].parent}return a}
function native(n){return [...new Set((n.nativeNames||[]).map(r=>r.text))]}
function rootsFiltered(){const c=category?.value||'all',f=evidence?.value||'all';return data.roots.filter(id=>{const n=nodes[id];return eligible(n)&&(c==='all'||(c==='isolates'?n.isolate:n.category===c))&&(f==='all'||(f==='conflicts'?conflictAncestors.has(id):unified.studyIndex[id]?.length))})}

// Search (top page): matching records are ranked (exact name, ISO code or
// Glottocode, then names that start with the query, then a word in the name,
// then any match; languages before families and dialects) and listed in place
// under the search box. Choosing one opens its page.
const rankLevel={language:0,family:1,genus:2,dialect:3};
function searchQuery(){const q0=(search?.value||'').trim().toLowerCase();return {q0,q:({'日本語族':'japonic','印欧':'indo-european','インドヨーロッパ':'indo-european','琉球':'ryukyuan','手話':'sign language'}[q0]||q0)}}
function matchRank(n,q){const nm=n.name.toLowerCase();if(nm===q||(n.iso||'').toLowerCase()===q||n.id.toLowerCase()===q)return 0;if(nm.startsWith(q))return 1;if(nm.split(/[\s\-‑'’()]+/).some(w=>w.startsWith(q)))return 2;return 3}
const kindRank=n=>n.isolate?0:rankLevel[n.level]??4;
function updateResults(){if(!data||branchPage)return;const {q}=searchQuery(),f=evidence.value,c=category.value;
 let all=[];if(q){all=Object.values(nodes).filter(n=>n.level!=='clade'&&n.searchText.includes(q));if(f==='conflicts')all=all.filter(n=>conflictAncestors.has(n.id));if(f==='studies')all=all.filter(n=>unified.studyIndex[n.id]?.length);if(c!=='all')all=all.filter(n=>c==='isolates'?n.isolate:n.category===c);const r=new Map(all.map(n=>[n.id,matchRank(n,q)]));all.sort((a,b)=>r.get(a.id)-r.get(b.id)||kindRank(a)-kindRank(b)||(data.nodes[a.id]?0:1)-(data.nodes[b.id]?0:1)||a.name.localeCompare(b.name))}
 matches=all;$('results').hidden=!q;if(q)renderSearch()}
function hitPath(n){if(data.nodes[n.id]){const a=ancestors(n.id).slice(0,-1);return a.length?a.map(id=>esc(nodes[id].name)).join(' › '):''}return esc(title(n.source))}
// Matches shown at once; the message below says the same number.
const SEARCH_LIMIT=150;
function renderSearch(){const {q0}=searchQuery(),shown=matches.slice(0,SEARCH_LIMIT);
 $('results').innerHTML=`<div class="search-head"><h2>Search results</h2><p class="hit-count">${matches.length===1?'1 matching record':fmt(matches.length)+' matching records'}</p><span class="hit-query notranslate" dir="auto">${esc(q0)}</span><span class="search-actions"><button type="button" data-search-clear>Clear search</button></span></div>`+
 (shown.length?`<ol class="hits">${shown.map(n=>{const path=hitPath(n);return `<li><a class="hit" href="${esc(pageURL(n.id))}"><span class="dot"></span><span class="hit-main"><span class="hit-name notranslate" dir="auto">${esc(n.name)}</span><span class="hit-meta"><code class="notranslate">${esc(n.iso||n.id)}</code>${unified.conflictIndex[n.id]?' · competing branches':''}</span>${path?`<span class="hit-path notranslate" dir="auto">${path}</span>`:''}</span></a></li>`}).join('')}</ol>`+(matches.length>150?'<p class="small">First '+SEARCH_LIMIT+' matches. Refine your search.</p>':''):'<p class="empty">No matching records.</p>')}

// Outline: each row links to the record's page; opening a row shows its members
// in the same source, and below a Glottolog record the other sources' trees
// attached there.
function makeNode(id,sid='glottolog',trail=new Set(),sample=''){const n=nodes[id],key=sid+'|'+id;if(trail.has(key)){const p=document.createElement('p');p.textContent='Shared reference: '+n.name;return p}const path=new Set(trail);path.add(key);
 const el=document.createElement('details');el.className='tree-node'+(id===rootId?' selected-node':'');
 const sum=document.createElement('summary'),own=native(n),ps=new Set((unified.placements[id]||[]).map(x=>x.source));
 sum.innerHTML=`<span class="rowname"><a href="${esc(pageURL(id))}">${esc(n.name)}</a>${sample&&sample!==n.name?`<small class="all-source-label">sample: ${esc(sample)}</small>`:''}</span>${own.length?`<span class="native-inline" dir="auto">${own.slice(0,2).map(esc).join(' / ')}</span>`:''}${(()=>{const m=[ps.size>1?ps.size+' sources':'',unified.conflictIndex[id]?'⚑':''].filter(Boolean).join(' · ');return m?`<span class="rowmeta">${m}</span>`:''})()}`;el.appendChild(sum);
 let populated=false;
 function populate(){if(populated)return;populated=true;const kids=document.createElement('div');kids.className='node-children';
  for(const e of children(sid,id))if(eligible(nodes[e.child]))kids.appendChild(makeNode(e.child,sid,path,e.sample));
  if(sid==='glottolog')for(const a of unified.anchors[id]||[])kids.appendChild(makeSourceBranch(a,path));
  if(!kids.childElementCount)kids.innerHTML='<p class="small-disclaimer">No members recorded here.</p>';el.appendChild(kids)}
 el.populate=populate;el.addEventListener('toggle',e=>{if(e.target===el&&el.open)populate()});return el}
function makeSourceBranch(a,trail=new Set()){const d=document.createElement('details');d.className='source-branch';
 const sum=document.createElement('summary');sum.innerHTML=`If following <strong>${esc(title(a.source))}</strong> → ${a.type==='catalog'?'catalog grouping':'sampled study tree'}`;d.appendChild(sum);
 let loaded=false;function load(){if(loaded)return;loaded=true;const wrap=document.createElement('div');wrap.innerHTML=`<p class="small-disclaimer">Alternative source-conditioned branch. This attachment is for navigation, not an additional ancestor.</p>`;wrap.appendChild(makeNode(a.root,a.source,trail));d.appendChild(wrap)}
 d.addEventListener('toggle',e=>{if(e.target===d&&d.open)load()});return d}
function renderOutline(){if(!data)return;const out=$('outline');out.replaceChildren();
 if(branchPage){const el=makeNode(rootId,rootSrc);out.appendChild(el);el.populate();el.open=true;return}
 for(const id of rootsFiltered())out.appendChild(makeNode(id));
 const intro=document.createElement('p');intro.className='root-context';intro.textContent='Cross-family / outgroup source trees · navigation only';out.appendChild(intro);
 for(const a of unified.anchors.__unplaced__||[])out.appendChild(makeSourceBranch(a))}
function syncButtons(){$('listview').classList.toggle('active',display==='list');$('chartview').classList.toggle('active',display==='chart')}
function showDisplay(){$('outline').hidden=display!=='list';$('viewport').hidden=display==='list';$('collapse').hidden=display!=='list'}

// Zoomable tree on a canvas.
function layout(){if(!data)return;positions=[];let leaf=0;
 function walk(id,sid,depth,parent,trail,attachment=false){if(!eligible(nodes[id])||trail.has(sid+'|'+id))return null;
  const p={id,sid,depth,parent,attachment,x:depth*290,y:0};positions.push(p);const path=new Set(trail);path.add(sid+'|'+id);
  const kids=[];for(const e of children(sid,id)){const c=walk(e.child,sid,depth+1,p,path);if(c)kids.push(c)}
  if(sid==='glottolog')for(const a of unified.anchors[id]||[]){const c=walk(a.root,a.source,depth+1,p,path,true);if(c)kids.push(c)}
  p.y=kids.length?kids.reduce((s,c)=>s+c.y,0)/kids.length:leaf++*29;return p}
 if(branchPage)walk(rootId,rootSrc,0,null,new Set());else{for(const id of rootsFiltered()){walk(id,'glottolog',0,null,new Set());leaf+=7}for(const a of unified.anchors.__unplaced__||[]){walk(a.root,a.source,0,null,new Set());leaf+=7}}
 $('view-title').textContent=branchPage?nodes[rootId].name:'Independent roots & alternatives';$('view-count').textContent=fmt(positions.length)+' displayed occurrences · shared IDs may appear in multiple hypotheses';fit()}
function bounds(){if(!positions.length)return{x:0,y:0,w:500,h:500};let minx=Infinity,miny=Infinity,maxx=-Infinity,maxy=-Infinity;for(const p of positions){minx=Math.min(minx,p.x);miny=Math.min(miny,p.y);maxx=Math.max(maxx,p.x);maxy=Math.max(maxy,p.y)}return{x:minx,y:miny,w:maxx-minx+280,h:maxy-miny+40}}
function fit(){customView=false;const b=bounds();scale=Math.max(.0001,Math.min((width-60)/Math.max(b.w,50),(height-140)/Math.max(b.h,50),1.2));tx=(width-b.w*scale)/2-b.x*scale;ty=100+(height-130-b.h*scale)/2-b.y*scale;requestDraw()}
function requestDraw(){if(display!=='chart'||dirty)return;dirty=true;requestAnimationFrame(draw)}
function draw(){dirty=false;ctx.clearRect(0,0,width,height);if(!nodes)return;
 for(const p of positions){const x=p.x*scale+tx,y=p.y*scale+ty,par=p.parent;
  if(par){const px=par.x*scale+tx,py=par.y*scale+ty;if(Math.max(px,x)<-20||Math.min(px,x)>width+20||Math.max(py,y)<-20||Math.min(py,y)>height+20)continue;ctx.beginPath();ctx.moveTo(px,py);ctx.bezierCurveTo((px+x)/2,py,(px+x)/2,y,x,y);ctx.strokeStyle=p.attachment?tok('976bb0'):p.sid==='glottolog'?col(nodes[p.id]):tok('bc9156');ctx.setLineDash(p.attachment?[4,4]:[]);ctx.globalAlpha=.5;ctx.lineWidth=p.id===rootId?2:.7;ctx.stroke();ctx.setLineDash([])}
  if(x< -250||x>width+30||y< -30||y>height+30)continue;ctx.globalAlpha=1;ctx.fillStyle=col(nodes[p.id]);ctx.beginPath();ctx.arc(x,y,p.id===rootId?4:Math.max(.4,Math.min(2.5,scale*2)),0,Math.PI*2);ctx.fill();
  if(scale>.55||p.id===rootId){ctx.font=(window.matchMedia('(max-width:700px)').matches?'16px ':'11px ')+siteFont();ctx.fillStyle=tok('2d463c');ctx.fillText(nodes[p.id].name+(p.attachment?' ['+title(p.sid)+']':''),x+7,y+3)}}
 ctx.globalAlpha=1}
function resize(){const box=$('viewport').getBoundingClientRect();if(!box.width||!box.height)return;const cx=(width/2-tx)/scale,cy=(height/2-ty)/scale;width=box.width;height=box.height;const dpr=Math.min(window.devicePixelRatio||1,2);canvas.width=width*dpr;canvas.height=height*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);if(!nodes)return;if(customView){tx=width/2-cx*scale;ty=height/2-cy*scale;requestDraw()}else fit()}
function zoom(f,x=width/2,y=height/2){const next=Math.max(.0001,Math.min(20,scale*f)),r=next/scale;tx=x-(x-tx)*r;ty=y-(y-ty)*r;scale=next;viewMoved()}
function nearest(x,y){let best=null,dist=100;for(const p of positions){const d=(x-p.x*scale-tx)**2+(y-p.y*scale-ty)**2;if(d<dist){dist=d;best=p}}return best}
function setDisplay(d){display=d;showDisplay();syncButtons();if(d==='chart'){resize();layout()}else renderOutline();saveURL(true)}
function exportSVG(){if(!positions.length)layout();const b=bounds(),pad=300,w=b.w+2*pad,h=b.h+2*pad;
 const out=[`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${b.x-pad} ${b.y-pad} ${w} ${h}"><title>Lang Log — source-conditioned branches</title><desc>Solid edges belong to the labeled source. Dashed edges attach alternative trees for navigation only; they do not assert ancestry. Repeated IDs are references to shared records. Full paper links and assertions are in the XML export.</desc><rect x="${b.x-pad}" y="${b.y-pad}" width="${w}" height="${h}" fill="#fafbf6"/>`];
 for(const p of positions){if(p.parent)out.push(`<path d="M${p.parent.x},${p.parent.y} L${p.x},${p.y}" fill="none" stroke="${p.attachment?'#976bb0':'#78917e'}" stroke-width="0.6" ${p.attachment?'stroke-dasharray="5 5"':''}/>`);out.push(`<g><title>${esc(p.id)} · according to ${esc(title(p.sid))}</title><circle cx="${p.x}" cy="${p.y}" r="2" fill="${col(nodes[p.id])}"/><text x="${p.x+5}" y="${p.y+3}" font-family="${esc(siteFont())}" font-size="9" fill="#243c3b">${esc(nodes[p.id].name)}${p.attachment?' ['+esc(title(p.sid))+']':''}</text></g>`)}
 out.push('</svg>');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob(out,{type:'image/svg+xml'}));a.download=(branchPage?(nodes[rootId].name.normalize('NFKD').replace(/[^\x00-\x7f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'')||'branch'):'language-families')+'.svg';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),10000)}

const pointers=new Map();let moved=false,down=null,pinch=0;
canvas.addEventListener('pointerdown',e=>{canvas.setPointerCapture(e.pointerId);pointers.set(e.pointerId,{x:e.offsetX,y:e.offsetY});down={x:e.offsetX,y:e.offsetY};moved=false;if(pointers.size===2){const[a,b]=[...pointers.values()];pinch=Math.hypot(a.x-b.x,a.y-b.y)}});
canvas.addEventListener('pointermove',e=>{if(pointers.has(e.pointerId)){const old=pointers.get(e.pointerId);pointers.set(e.pointerId,{x:e.offsetX,y:e.offsetY});if(pointers.size===2){const[a,b]=[...pointers.values()],d=Math.hypot(a.x-b.x,a.y-b.y);if(pinch)zoom(d/pinch,(a.x+b.x)/2,(a.y+b.y)/2);pinch=d;moved=true}else{tx+=e.offsetX-old.x;ty+=e.offsetY-old.y;if(Math.hypot(e.offsetX-down.x,e.offsetY-down.y)>4)moved=true;viewMoved()}$('tooltip').hidden=true;return}
 const p=nearest(e.offsetX,e.offsetY);if(p){$('tooltip').textContent=nodes[p.id].name+' · '+title(p.sid);$('tooltip').style.left=Math.max(5,Math.min(width-220,e.offsetX+12))+'px';$('tooltip').style.top=Math.max(5,e.offsetY-35)+'px';$('tooltip').hidden=false}else $('tooltip').hidden=true});
canvas.addEventListener('pointerup',e=>{pointers.delete(e.pointerId);if(!moved){const p=nearest(e.offsetX,e.offsetY);if(p)open(p.id)}pinch=0});
canvas.addEventListener('pointercancel',e=>{pointers.delete(e.pointerId);moved=true});
canvas.addEventListener('pointerleave',()=>{$('tooltip').hidden=true});
canvas.addEventListener('wheel',e=>{e.preventDefault();zoom(Math.exp(-e.deltaY*.0015),e.offsetX,e.offsetY)},{passive:false});

document.addEventListener('click',e=>{if(e.target.closest('[data-search-clear]')){search.value='';updateResults();saveURL(true);search.focus()}});
if(search){search.addEventListener('input',()=>{updateResults();clearTimeout(searchTimer);searchTimer=setTimeout(()=>saveURL(false),400)});
 search.form?.addEventListener('submit',e=>{e.preventDefault();updateResults();saveURL(true)})}
for(const el of [evidence,category])el?.addEventListener('change',()=>{updateResults();renderOutline();if(display==='chart')layout();saveURL(true)});
$('dialects').onchange=()=>{renderOutline();if(display==='chart')layout();saveURL(true)};
$('listview').onclick=()=>setDisplay('list');$('chartview').onclick=()=>setDisplay('chart');
$('collapse').onclick=()=>host.querySelectorAll('#outline details[open]').forEach(e=>e.open=false);
$('minus').onclick=()=>zoom(1/1.5);$('plus').onclick=()=>zoom(1.5);$('fit').onclick=()=>{fit();saveURL(false)};
$('export').onclick=()=>{if(display!=='chart')layout();exportSVG()};
window.addEventListener('popstate',applyURL);new ResizeObserver(resize).observe($('viewport'));
document.addEventListener('themechange',()=>{for(const k in tc)delete tc[k];requestDraw()});

// Record pages load the data only when the visitor asks for the tree (dist/record-page.js);
// the top page loads it at once for the search.
let started=false;
function start(){if(started)return;started=true;
host.hidden=false;$('outline').innerHTML='<p class="outline-empty">Loading records…</p>';
window.AtlasData.base=base+'data/';
Promise.all([window.AtlasData.load(),fetch(base+'source-paths.json').then(r=>r.ok?r.json():{}).catch(()=>({}))]).then(async([{d,u},sp])=>{
 data=d;unified=u;sourcePaths=sp;await window.LineagePaths.init(d.nodes,d.roots,base);nodes={...data.nodes,...unified.extraNodes};
 for(const n of Object.values(nodes))n.searchText=[n.name,n.id,n.iso,...(n.names||[]).map(r=>r.text)].join(' ').toLowerCase();
 for(const e of u.assertions){if(!e.parent)continue;const k=e.source+'|'+e.parent;if(!bySource.has(k))bySource.set(k,[]);bySource.get(k).push(e)}
 for(const id of Object.keys(u.conflictIndex))for(const a of ancestors(id))conflictAncestors.add(a);
 if(branchPage&&!nodes[rootId]){$('outline').innerHTML='<p class="load-error">This record is not in the tree data.</p>';return}
 applyURL();
 if(!branchPage)window.AtlasData.search().then(t=>{for(const [id,s] of Object.entries(t))if(nodes[id])nodes[id].searchText+=' '+s;if(search.value.trim())updateResults()}).catch(console.error);
}).catch(e=>{$('outline').innerHTML='<p class="load-error">'+esc(e.message)+'. Reload to retry.</p>';$('view-count').textContent=e.message;console.error(e)});
}
window.LangLogTree={start};
if(!branchPage)start();
})();

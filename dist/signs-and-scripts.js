'use strict';
(async()=>{
 const $=id=>document.getElementById(id),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const domain=new URLSearchParams(location.search).get('domain')==='scripts'?'scripts':'sign';
 let data;
 try{const r=await fetch('signs-and-scripts.json');if(!r.ok)throw Error('HTTP '+r.status);data=await r.json();}catch(e){$('visual-outline').textContent='The data could not be loaded. Please reload this page.';return;}
 const {nodes:N,assertions:E,sources:S}=data,out={},inc={},all=Object.values(N).filter(n=>n.domain===domain);const PAGE=100;let selected=null,limit=PAGE,focused=false,focusId=null,horizontal=false,hfTask='',restoring=false,pendingPush=null,searchTimer=0;
 const baseTitle=document.title,detailIntro=$('detail').innerHTML;
 // URL state: domain, id (selected record), branch (expanded branch), q (search),
 // view=tree, task (Hugging Face model task) and about=1 (Sources & scope dialog).
 function stateURL(){const p=new URLSearchParams({domain}),q=$('search').value.trim();if(selected)p.set('id',selected);if(focusId)p.set('branch',focusId);if(q)p.set('q',q);if(horizontal)p.set('view','tree');if(hfTask)p.set('task',hfTask);if($('sources').open)p.set('about','1');const u=new URL(location.href);u.search=p.toString();u.hash='';return u;}
 function saveURL(push){if(restoring)return;if(pendingPush!==null){pendingPush=pendingPush||push;return;}pendingPush=push;queueMicrotask(()=>{const doPush=pendingPush;pendingPush=null;const u=stateURL();if(u.href===location.href)return;try{history[doPush?'pushState':'replaceState'](null,'',u);}catch(e){}});}
 for(const e of E){(out[e.parent]??=[]).push(e);(inc[e.child]??=[]).push(e);}
 $('nav-'+domain).setAttribute('aria-current','page');
 const sl=s=>`<a href="${esc(S[s].url)}" target="_blank" rel="noopener noreferrer">${esc(S[s].title)}</a>`;
 const short=s=>s==='glottolog'?'Glottolog 5.3':s==='abner2024'?'Abner et al. 2024':s==='power2020'?'Power et al. 2020':/^u\d+$/.test(s)?'Unicode 17 · §'+s.slice(1):S[s].title;
 const badge=e=>`${esc(e.kind)} · according to <a href="${esc(S[e.source].url)}" target="_blank" rel="noopener noreferrer">${esc(short(e.source))}</a>${e.status!=='reported'?` · <span class="v-status">${esc(e.status)}</span>`:''}${e.run?' · '+esc(e.run):''}${e.posterior!=null?' · posterior '+e.posterior:''}`;
 const c=data.counts;
 if(domain==='scripts'){$('heading').textContent='Writing systems';$('domain-note').textContent='A script is not a language family. Historical descent, graphic influence and language usage are distinct; missing ancestry is unreviewed, not proof of independent invention.';$('search-hint').textContent='Try Brahmi · Hangul · Latin · SignWriting';}
 else{$('domain-note').textContent='Glottolog classifications, lexical-feature study trees and manual-alphabet groups share identities but keep their evidence separate. Navigation categories are not universal ancestors.';$('search-hint').textContent='Try Japanese · Czech · ASL · Lithuanian';}
 function row(id,path=new Set(),relation=null){
  const n=N[id],el=document.createElement('details');el.className='v-node';el.dataset.record=id;
  const s=document.createElement('summary');s.innerHTML=`<span class="v-name"><a href="record.html?domain=${domain}&id=${encodeURIComponent(id)}">${esc(n.name)}</a></span><button type="button">Details ↗</button>${relation?`<span class="v-evidence">${badge(relation)}</span>`:''}`;
  s.querySelector('button').onclick=e=>{e.preventDefault();e.stopPropagation();inspect(id,true);};s.querySelectorAll('a').forEach(a=>a.onclick=e=>e.stopPropagation());el.append(s);
  const children=document.createElement('div');children.className='v-children';el.append(children);let rendered=false;
  el.addEventListener('toggle',()=>{if(!el.open||rendered)return;rendered=true;
   if(path.has(id)){children.innerHTML='<p class="v-empty">Shared reference — see Details.</p>';return;}
   const next=new Set(path);next.add(id);const list=out[id]||[];
   if(!list.length)children.innerHTML='<p class="v-empty">No further imported branches. See Details for incoming placements and evidence.</p>';
   else for(const e of list)children.append(row(e.child,next,e));
  });return el;
 }
 function group(title,description,ids,open=false){const d=document.createElement('details');d.className='v-group';d.open=open;const s=document.createElement('summary');s.textContent=title+' · '+ids.length;d.append(s);const p=document.createElement('p');p.textContent=description;d.append(p);const holder=document.createElement('div');d.append(holder);let done=false;function fill(){if(d.open&&!done){done=true;for(const id of ids)holder.append(row(id));}}d.addEventListener('toggle',fill);fill();return d;}
 function forest(id=null){focused=!!id;focusId=id;saveURL(true);$('world').classList.toggle('active',!id);$('branch').classList.toggle('active',!!id);const host=$('visual-outline');host.replaceChildren();if(id){const r=row(id);host.append(r);r.open=true;return;}
  const roots=all.filter(n=>!inc[n.id]?.length).sort((a,b)=>a.name.localeCompare(b.name));
  if(domain==='sign'){
   host.append(group('Catalog classification',`All ${c.glottologSignRecords} records in the Glottolog Sign Language category, including family and dialect records. Categories are navigation.`, ['sign1238'],true));
   host.append(group('Lexical-feature hypotheses','Source-specific sampled clades share the same language identities. Two European runs are replicates of one study.',data.studies.map(t=>t.root),true));
   host.append(group('Manual-alphabet evidence',`All ${c.manualAlphabetSamples} CLDF samples, including historical forms. Published subgroup metadata, not an inferred whole-language tree.`,roots.filter(n=>n.kind==='sample grouping').map(n=>n.id)));
  }else{
   host.append(group('Histories with reviewed relationships','All imported historical and influence assertions appear together; each edge carries its source and uncertainty.',roots.filter(n=>out[n.id]?.length).map(n=>n.id),true));
   host.append(group('Catalog entries without reviewed ancestry','These records remain searchable and inspectable. No displayed connection is not a claim of independent origin.',roots.filter(n=>!out[n.id]?.length).map(n=>n.id)));
  }
 }
 const aliasText=a=>typeof a==='string'?a:a.text||a.name||'';
 function search(){const q=$('search').value.trim().toLocaleLowerCase(),found=all.filter(n=>[n.name,n.id,n.iso,n.code,...(n.aliases||[]).map(aliasText)].join(' ').toLocaleLowerCase().includes(q)).sort((a,b)=>a.name.localeCompare(b.name));$('searchcount').textContent=found.length.toLocaleString();$('results').replaceChildren();for(const n of found.slice(0,limit)){const b=document.createElement('button');b.innerHTML=`${esc(n.name)}<small>${esc(n.iso||n.code||n.id)}</small>`;b.onclick=()=>{inspect(n.id,false);forest(n.id);if(matchMedia('(max-width:900px)').matches){$('branch-search').classList.remove('mobile-open');$('branch-menu').setAttribute('aria-expanded','false');$('branch-menu').querySelector('.menu-status').textContent='Open';$('visual-outline').scrollIntoView({behavior:'smooth',block:'start'});}};$('results').append(b);}$('more').hidden=found.length<=limit;}
 function jumpButton(id){return `<button type="button" data-jump="${esc(id)}">${esc(N[id].name)} ↗</button>`;}
 // Classification path from the top of the family down to this record, following one source (Glottolog when it places the record).
 function lineageHTML(id){const ps=inc[id]||[];if(!ps.length)return '';const sid=(ps.find(e=>e.source==='glottolog')||ps[0]).source,ids=[],seen=new Set();let p=id;while(p&&N[p]&&!seen.has(p)){seen.add(p);ids.unshift(p);p=(inc[p]||[]).find(e=>e.source===sid)?.parent}
  return `<nav class="lineage" aria-label="Classification according to ${esc(S[sid]?.title||sid)}"><span class="lineage-source">${sl(sid)}</span><ol class="lineage-path">${ids.slice(0,-1).map(i=>`<li><button type="button" data-jump="${esc(i)}">${esc(N[i].name)}</button></li>`).join('')}</ol></nav>`}
 function inspect(id,scroll){selected=id;$('branch').disabled=false;const n=N[id],incoming=inc[id]||[],outgoing=out[id]||[],nn=n.nativeNames||[],aliases=n.aliases||[],notes=data.notes.filter(x=>x.nodes.includes(id)),used=data.usage.filter(x=>x.script===id);
  $('detail').innerHTML=`${lineageHTML(id)}<h2>${esc(n.name)}</h2><a class="node-detail-link" href="record.html?domain=${domain}&id=${encodeURIComponent(id)}">Open detail page ↗</a><p class="small">${esc(n.id)}${n.iso?' · ISO 639-3: '+esc(n.iso):''}${n.code?' · catalog code: '+esc(n.code):''}</p>${n.glyphSample?`<p class="v-glyphs" dir="auto">${esc(n.glyphSample)}</p><p class="small">Illustrative Unicode letters · not a native name. Glyphs depend on your device’s fonts. ${sl('ucd')}</p>`:''}${n.region?`<p>Region: ${esc(n.region)}<br>SIL-reported type: ${esc(n.silType)}<br>Direction: ${esc(n.direction)} · status: ${esc(n.silStatus)}</p>`:''}${n.area?`<p>Macroarea: ${esc(n.area)}</p>`:''}<button id="focus-record">Show this branch</button><h3>According to each source</h3>${incoming.length?incoming.map(e=>`<div class="v-card">${jumpButton(e.parent)}<small>${badge(e)}</small>${e.hypothesis?'<p>'+esc(e.hypothesis)+'</p>':''}${e.sample?'<small>Original sample: '+esc(e.sample)+'</small>':''}${e.branchLength?'<small>Stored branch length: '+esc(e.branchLength)+' (not shown as calendar time)</small>':''}</div>`).join(''):'<p>No incoming assertion imported. This does not certify an independent origin or scientific consensus.</p>'}${notes.map(x=>`<div class="note"><strong>${esc(x.title)}</strong><p>${esc(x.text)}</p>${x.sources.map(sl).join('<br>')}</div>`).join('')}<h3>Outgoing relationships · ${outgoing.length}</h3>${outgoing.length?outgoing.map(e=>`<div class="v-card">${jumpButton(e.child)}<small>${badge(e)}</small></div>`).join(''):'<p>No outgoing relationships imported.</p>'}<details><summary>Names & aliases · ${aliases.length}</summary><ul class="v-aliases">${aliases.map(a=>`<li>${esc(aliasText(a))}<small> ${esc(a.lang||'')} · ${esc(a.provider||a.source||'Glottolog name record')}</small></li>`).join('')}</ul><h3>Same-language labels</h3>${nn.length?nn.map(a=>'<p dir="auto">'+esc(aliasText(a))+'</p>').join(''):'<p>No verified same-language label imported. For sign languages, a written label is not a video or signed self-name.</p>'}</details>${domain==='scripts'?`<details><summary>Languages using this script · ${used.length}</summary><p>Explicit CLDR languageData entries; identifiers are language codes, not a genealogy. “Secondary” is CLDR’s designation.</p><ul class="v-usage">${used.map(u=>`<li><strong>${esc(u.language)}</strong> · ${esc(u.status)}${u.territories.length?' · '+esc(u.territories.join(', ')):''}</li>`).join('')}</ul>${sl('cldr')}</details>`:''}<h3>Record sources</h3>${(n.sources||[]).map(sl).join('<br>')}${n.domain==='sign'&&n.iso?'<div id="hf-visual"></div>':''}`;
  $('focus-record').onclick=()=>{forest(id);$('visual-outline').scrollIntoView({behavior:'smooth',block:'start'});};$('detail').querySelectorAll('[data-jump]').forEach(b=>b.onclick=()=>{inspect(b.dataset.jump,false);forest(b.dataset.jump);});
  if($('hf-visual')&&window.LanguageModels)window.LanguageModels.mount($('hf-visual'),{...n,level:n.kind},{task:hfTask,onTask:t=>{hfTask=t;saveURL(false);}});
  document.title=n.name+' · '+baseTitle;saveURL(true);
  if(scroll){$('detail').scrollIntoView({behavior:'smooth',block:'start'});$('detail').focus({preventScroll:true});}
 }
 $('search').oninput=()=>{limit=PAGE;search();clearTimeout(searchTimer);searchTimer=setTimeout(()=>saveURL(false),400);};$('more').textContent=`Show ${PAGE} more`;$('more').onclick=()=>{limit+=PAGE;search();};$('world').onclick=()=>forest();$('branch').onclick=()=>selected&&forest(selected);$('collapse').onclick=()=>{$('visual-outline').querySelectorAll('details').forEach(d=>d.open=false);};
 function view(h){horizontal=h;saveURL(true);$('visual-outline').classList.toggle('horizontal',horizontal);$('listview').classList.toggle('active',!horizontal);$('chartview').classList.toggle('active',horizontal);}
 $('listview').onclick=()=>view(false);$('chartview').onclick=()=>view(true);
 $('branch-menu').onclick=()=>{const on=$('branch-search').classList.toggle('mobile-open');$('branch-menu').setAttribute('aria-expanded',String(on));$('branch-menu').querySelector('.menu-status').textContent=on?'Close':'Open';if(on)$('search').focus();};
 $('about').onclick=()=>{$('sources').showModal();saveURL(false);};$('close').onclick=()=>$('sources').close();$('sources').addEventListener('close',()=>saveURL(false));
 $('coverage').innerHTML=`<p><strong>${c.glottologSignRecords} / ${c.glottologSignRecords}</strong> Glottolog sign-category records; <strong>${c.iso15924Rows} / ${c.iso15924Rows}</strong> downloaded ISO 15924 rows; <strong>${c.silRows} / ${c.silRows}</strong> SIL index rows. Exact ISO-code matches share records; SIL-local identifiers remain distinct.</p><p>${c.manualAlphabetSamples} manual-alphabet samples; ${c.consensusTrees} lexical consensus trees covering ${c.distinctLexicalSamples} distinct language samples; ${c.scriptRelationships} reviewed script relationships; ${c.usageAssertions} CLDR usage assertions. These are different units and should not be added as “languages.”</p>`;
 $('limitations').innerHTML=data.limitations.map(x=>'<li>'+esc(x)+'</li>').join('');$('source-register').innerHTML=Object.values(S).map(s=>`<div class="v-source">${sl(s.id)}<p>${esc(s.kind)}${s.license?' · '+esc(s.license):''}</p>${s.scope?'<p>'+esc(s.scope)+'</p>':''}${s.dataset?`<a href="${esc(s.dataset)}" target="_blank" rel="noopener noreferrer">Research data ↗</a>`:''}</div>`).join('');
 function applyURL(){const p=new URLSearchParams(location.search),legacy=decodeURIComponent(location.hash.slice(1)),valid=x=>N[x]?.domain===domain?x:null;restoring=true;try{
  $('search').value=p.get('q')||'';limit=PAGE;search();hfTask=p.get('task')||'';
  let id=valid(p.get('id')),branch=valid(p.get('branch'));if(!id&&!p.has('id')&&valid(legacy)){id=legacy;branch=legacy;}
  view(p.get('view')==='tree');forest(branch);
  if(id)inspect(id,false);else{selected=null;$('branch').disabled=true;$('detail').innerHTML=detailIntro;document.title=baseTitle;}
  const dlg=$('sources');if(p.get('about')==='1'&&!dlg.open)dlg.showModal();else if(p.get('about')!=='1'&&dlg.open)dlg.close();
 }finally{restoring=false;}}
 window.addEventListener('popstate',applyURL);applyURL();if(location.hash)history.replaceState(null,'',stateURL());
})();

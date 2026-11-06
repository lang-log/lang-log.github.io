'use strict';
// URL of each Glottolog record's own page, which follows its classification:
// <family>/<subgroup>/.../<language>/ below the atlas root. Same rules as build_paths.py:
// ASCII slugs of names, "-<glottocode>" on both siblings when slugs collide,
// and historical stages as a section of their modern language (#old, #middle ...).
window.LineagePaths=(()=>{
 let nodes={},roots=[],stages={};const seg=new Map(),cache=new Map();
 const slug=s=>String(s).normalize('NFKD').replace(/[^\x00-\x7f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
 function fill(ids){const base=new Map(ids.map(i=>[i,slug(nodes[i].name)||i])),count=new Map();for(const s of base.values())count.set(s,(count.get(s)||0)+1);for(const [i,s] of base)seg.set(i,count.get(s)===1?s:s+'-'+i)}
 function segment(i){if(!seg.has(i)){const p=nodes[i].parent;fill(p?nodes[p].children.filter(c=>!stages[c]):roots)}return seg.get(i)}
 function raw(i){if(cache.has(i))return cache.get(i);let p;const st=stages[i];if(st)p=raw(st.modern)+'/#'+st.anchor;else{const parent=nodes[i].parent;p=parent&&stages[parent]?raw(stages[parent].modern)+'/'+stages[parent].anchor+'/'+segment(i):(parent?raw(parent)+'/':'')+segment(i)}cache.set(i,p);return p}
 return{
  async init(n,r,base='./'){nodes=n;roots=r;try{const res=await fetch(base+'stages.json');if(res.ok){const s=await res.json();for(const [k,v] of Object.entries(s))if(nodes[k]&&nodes[v.modern])stages[k]=v}}catch{}},
  // Relative URL from the atlas root, or '' for records without a page.
  url(i){if(!nodes[i])return '';const p=raw(i);return p.includes('/#')?p:p+'/'}
 };
})();

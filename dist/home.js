'use strict';
// The Random row on the top page (the only page that has Random). Each
// button opens the record page of a record drawn from random.json, which
// tools/build_home.py writes: {language: [ids], sign: [ids], scripts: [ids]}.
// The row stays hidden without JavaScript.
(()=>{
 const row=document.querySelector('.home-random');if(!row)return;
 let pools=null;
 const load=()=>pools||(pools=fetch('random.json').then(r=>{if(!r.ok)throw Error('Could not load random.json');return r.json()}));
 row.hidden=false;
 for(const b of row.querySelectorAll('button[data-domain]')){
  b.addEventListener('click',async()=>{
   b.disabled=true;
   try{
    const ids=(await load())[b.dataset.domain]||[];
    if(!ids.length)return;
    const id=ids[Math.floor(Math.random()*ids.length)];
    location.href='record.html?domain='+encodeURIComponent(b.dataset.domain)+'&id='+encodeURIComponent(id);
   }catch(e){pools=null;}
   finally{b.disabled=false;}
  });
 }
})();

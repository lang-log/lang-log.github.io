'use strict';
// Random buttons on the top page (the only page that has them). Each button
// opens the record page of a record drawn from random.json, which
// tools/build_home.py writes: {language: [ids], sign: [ids], scripts: [ids]}.
// The buttons stay hidden without JavaScript.
(()=>{
 let pools=null;
 const load=()=>pools||(pools=fetch('random.json').then(r=>{if(!r.ok)throw Error('Could not load random.json');return r.json()}));
 for(const b of document.querySelectorAll('.home-random')){
  b.hidden=false;
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

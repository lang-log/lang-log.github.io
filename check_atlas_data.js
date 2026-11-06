// Checks that dist/atlas-data.js rebuilds exactly what dist/data.json and
// dist/integrated.json hold (record names come from dist/data/names/).
// Run after split_data.py: node check_atlas_data.js
const fs=require('fs'),path=require('path'),assert=require('assert'),dist=path.join(__dirname,'dist');
global.window={};global.fetch=async f=>({ok:true,json:async()=>JSON.parse(fs.readFileSync(path.join(dist,f),'utf8'))});
eval(fs.readFileSync(path.join(dist,'atlas-data.js'),'utf8'));
(async()=>{
 const {d,u}=await window.AtlasData.load();
 const D=JSON.parse(fs.readFileSync(path.join(dist,'data.json'))),U=JSON.parse(fs.readFileSync(path.join(dist,'integrated.json')));
 for(const k of Object.keys(D.nodes)){const w={...D.nodes[k]};delete w.wals;delete w.names;assert.deepStrictEqual(Object.keys(d.nodes[k]),Object.keys(w));assert.deepStrictEqual(d.nodes[k],w,k)}
 assert.deepStrictEqual(Object.keys(d.nodes),Object.keys(D.nodes));
 for(const k of ['roots','stats','retrieved','glottologVersion'])assert.deepStrictEqual(d[k],D[k]);
 for(const k of Object.keys(U))assert.deepStrictEqual(u[k],U[k],k);
 assert.deepStrictEqual(Object.keys(u.placements),Object.keys(U.placements));
 for(const id of ['stan1288','nucl1643','abkh1242','berb1260'])assert.deepStrictEqual(await window.AtlasData.names(id),D.nodes[id].names);
 assert.deepStrictEqual(d.nodes.stan1288.names,D.nodes.stan1288.names);
 const s=await window.AtlasData.search();assert(s.nucl1643.includes('日本語'));
 console.log('OK: rebuilt data equals data.json and integrated.json');
})().catch(e=>{console.error(e.message.slice(0,500));process.exit(1)});

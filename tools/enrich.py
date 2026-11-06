import csv,json,pathlib,collections,hashlib,xml.etree.ElementTree as ET
out=pathlib.Path('dist');data=json.load(open(out/'data.json'));nodes=data['nodes'];mapping=json.load(open('source-data/iso-map.json'));rows=list(csv.DictReader(open('source-data/names.csv')))
for n in nodes.values():n['names']=[];n['nativeNames']=[]
for r in rows:
 assert r['Language_ID'] in nodes
 n=nodes[r['Language_ID']];lang=r['lang'];record={'text':r['Name'],'provider':r['Provider'],'lang':lang,'record':r['ID']}
 if r['Name'].lower()=='not specified':record['placeholder']=True
 n['names'].append(record)
 if lang and n['iso'] and mapping.get(lang,lang)==n['iso'] and not record.get('placeholder'):
  n['nativeNames'].append(record)
for n in data['wals'].values():
 g=nodes.get(n['glottocode']);n['names']=g['names'] if g else [];n['nativeNames']=g['nativeNames'] if g else []
data['stats']['nameRecords']=len(rows);data['stats']['recordsWithNames']=sum(bool(n['names']) for n in nodes.values());data['stats']['recordsWithNativeNames']=sum(bool(n['nativeNames']) for n in nodes.values());data['stats']['nativeNameRecords']=sum(len(n['nativeNames']) for n in nodes.values())
(out/'data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
prov=json.load(open(out/'provenance.json'));prov['files']['names.csv']={'sha256':hashlib.sha256(pathlib.Path('source-data/names.csv').read_bytes()).hexdigest(),'source_blob_sha':'643f45dc3fa7acb3069f65d10a7450f35987666d','source':'https://github.com/glottolog/glottolog-cldf/blob/v5.3/cldf/names.csv','rows':len(rows)}
prov['names_method']='All Glottolog names.csv rows retained with provider, language tag and original record ID. Names in the language itself are labels whose language tag matches the target ISO 639-3 code, using exact 639-1 to 639-3 equivalences only. These are source labels, not independently verified community autonyms. No macrolanguage or dialect inheritance.'
prov['iso_mapping']={'source':'https://github.com/pycountry/pycountry/blob/3e9e69f1f5eafd71c12cb7b6464a39df53115e71/src/pycountry/databases/iso639-3.json','source_blob_sha':'3e9e69f1f5eafd71c12cb7b6464a39df53115e71','note':'184 two-letter/three-letter equivalences extracted; source_blob_sha is a blob, not a commit URL. Repository file: https://github.com/pycountry/pycountry/blob/main/src/pycountry/databases/iso639-3.json'}
prov['iso_mapping']['source']='https://github.com/pycountry/pycountry/blob/main/src/pycountry/databases/iso639-3.json'
prov['limitations']=[x for x in prov['limitations'] if not x.startswith('No complete multilingual')]+['All imported Glottolog alternate-name records retained, but name coverage is not exhaustive. Most records have no same-language label; no name was inferred to fill these gaps.','No reconstructed proto-languages or inferred macrofamilies.']
(out/'provenance.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2))
root=ET.Element('language-atlas',{'version':'2','retrieved':'2026-10-12','names-license':'CC BY 4.0'})
ET.SubElement(root,'method').text=prov['names_method']
for key,rs,label in [('nodes','roots','Glottolog 5.3'),('wals','walsRoots','WALS CLDF snapshot')]:
 ds=ET.SubElement(root,'classification',{'source':label});d=data[key]
 def node(id,container):
  n=d[id];attrs={k:str(n[k]) for k in ['id','name','level','iso','category','glottocode'] if k in n};el=ET.SubElement(container,'node',attrs)
  names=ET.SubElement(el,'names',{'same-language-status':'recorded' if n['nativeNames'] else 'not-recorded'})
  native={r['record'] for r in n['nativeNames']}
  for r in n['names']:
   attrs={'provider':r['provider'],'language-tag':r['lang'],'source-record':r['record'],'same-language':str(r['record'] in native).lower()}
   if r.get('placeholder'):attrs['placeholder']='true'
   ET.SubElement(names,'name',attrs).text=r['text']
  for c in n['children']:node(c,el)
 for id in data[rs]:node(id,ds)
ET.ElementTree(root).write(out/'language-families.xml',encoding='utf-8',xml_declaration=True)
op=ET.Element('opml',{'version':'2.0'});head=ET.SubElement(op,'head');ET.SubElement(head,'title').text='Lang Log — Glottolog 5.3 and WALS';body=ET.SubElement(op,'body')
for key,rs,label in [('nodes','roots','Glottolog 5.3'),('wals','walsRoots','WALS CLDF snapshot')]:
 ds=ET.SubElement(body,'outline',{'text':label});d=data[key]
 def outline(id,parent):
  n=d[id];native=list(dict.fromkeys(r['text'] for r in n['nativeNames']));attrs={'text':n['name']+(' · '+' / '.join(native) if native else ''),'id':id,'level':n['level']}
  alts=list(dict.fromkeys(r['text'] for r in n['names'] if not r.get('placeholder')))
  if alts:attrs['_note']='Recorded names: '+'; '.join(alts)
  el=ET.SubElement(parent,'outline',attrs)
  for c in n['children']:outline(c,el)
 for id in data[rs]:outline(id,ds)
ET.ElementTree(op).write(out/'language-families.opml',encoding='utf-8',xml_declaration=True)
print({k:v for k,v in data['stats'].items() if 'ame' in k});print([(p.name,p.stat().st_size) for p in out.glob('language-families.*')]);print('Japanese:',nodes['nucl1643']['nativeNames'])

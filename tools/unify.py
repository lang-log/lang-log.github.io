import json,csv,pathlib,re,collections,hashlib,itertools,xml.etree.ElementTree as ET,gzip
P=pathlib.Path('dist');data=json.load(open(P/'data.json'));base=data['nodes'];wals=data['wals'];extra={};edges=[];sources={};placements=collections.defaultdict(list);anchors=collections.defaultdict(list);coverage=[]
S=lambda id,title,url,kind,**kw:sources.setdefault(id,dict(id=id,title=title,url=url,kind=kind,**kw))
S('glottolog','Glottolog 5.3','https://doi.org/10.5281/zenodo.18840935','catalog',license='CC BY 4.0');S('wals','WALS Online / CLDF','https://wals.info','catalog',license='CC BY 4.0')
def blank(id,name,level,source):
 return dict(id=id,name=name,level=level,source=source,iso='',area='',names=[],nativeNames=[],children=[],parent=None,category='Source-specific grouping')
def add_edge(parent,child,source,sample=None):
 e={'parent':parent,'child':child,'source':source}
 if sample:e['sample']=sample
 edges.append(e)
 if parent is not None:placements[child].append(e)
 return e
for id,n in base.items():add_edge(n['parent'],id,'glottolog')
def ancestors(id):
 a=[]
 while id in base:a.append(id);id=base[id]['parent']
 return list(reversed(a))
def lca(ids):
 paths=[ancestors(x) for x in ids if x in base]
 if not paths:return None
 shared=None
 for level in zip(*paths):
  if len(set(level))!=1:break
  shared=level[0]
 return shared
wm={}
for id,n in wals.items():
 wm[id]=n['glottocode'] if n.get('glottocode') in base else 'wals:'+id
 if wm[id] not in base:extra[wm[id]]=blank(wm[id],n['name'],n['level'],'wals');extra[wm[id]]['iso']=n.get('iso','')
for id,n in wals.items():
 parent=wm.get(n['parent']);cid=wm[id]
 if parent!=cid:add_edge(parent,cid,'wals',n['name'])
 if cid in extra:extra[cid]['children']=[wm[c] for c in n['children'] if wm[c]!=cid];extra[cid]['parent']=parent
# Source trees kept separately by assertions; identical language identities are shared.
class Parser:
 def __init__(self,s):
  self.t=re.findall(r"'(?:[^']|'')*'|\"[^\"]*\"|[(),:;]|[^\s(),:;]+",re.sub(r'\[[^\]]*\]','',s));self.i=0
 def parse(self):
  kids=[];label='';length=''
  if self.t[self.i]=='(':
   self.i+=1
   while True:
    kids.append(self.parse())
    c=self.t[self.i];self.i+=1
    if c==')':break
    assert c==','
  if self.i<len(self.t) and self.t[self.i] not in [',',')',':',';']:
   label=self.t[self.i].strip("'\"").replace("''", "'");self.i+=1
  if self.i<len(self.t) and self.t[self.i]==':':self.i+=1;length=self.t[self.i];self.i+=1
  return {'label':label,'children':kids,'length':length}
study_trees={};study_tips={};all_trees={};hashes=[]
for folder in sorted(pathlib.Path('source-data/phlorest').iterdir()):
 if not folder.is_dir():continue
 sid=folder.name;m=json.load(open(folder/'metadata.json'));S(sid,m['author']+' ('+str(m['year'])+')',m['url'],'study',citation=m['citation'],paperTitle=m['name'],family=m['family'],license=m['license'],dataset='https://github.com/phlorest/'+sid,doi=m.get('zenodo_concept_doi'),summaryOnly=True)
 rows=list(csv.DictReader(open(folder/'languages.csv')));langs={r['ID']:r for r in rows};s=(folder/'summary.trees').read_text();matches=re.findall(r'(?im)^\s*(?:tree|utree)\s+([^=]+)=\s*(.*?);',s,re.S);assert len(matches)==1,(sid,len(matches));tree=Parser(matches[0][1]).parse();counter=[0];tip_counts=collections.Counter();tipnodes=[];clades=[]
 def walk(t,parent=None):
  counter[0]+=1;local='ph:'+sid+':'+str(counter[0]);children=t['children']
  if not children:
   label=t['label'];assert label in langs,(sid,label)
   row=langs[label];gc=row.get('Glottocode','');id=gc if gc in base else local
   if id not in base:extra[id]=blank(id,row.get('Name') or label,'sample',sid);extra[id]['unmatchedGlottocode']=gc;extra[id]['sampleID']=label
   tip_counts[id]+=1;tipnodes.append(id);members={id}
  else:
   id=local;extra[id]=blank(id,t['label'] or 'Unnamed sampled clade','clade',sid);members=set()
   for c in children:
    ci,cm=walk(c,id);extra[id]['children'].append(ci);members.update(cm)
   extra[id]['members']=sorted(members);extra[id]['name']=t['label'] or 'Clade: '+', '.join((base.get(x) or extra[x])['name'] for x in sorted(members)[:3])+(' …' if len(members)>3 else '')
   clades.append((id,members))
  if id in extra:extra[id]['parent']=parent;extra[id]['branchLength']=t['length']
  edge=add_edge(parent,id,sid,t['label'] if not children else None)
  if t['length']:edge['branchLength']=t['length']
  return id,members
 root,members=walk(tree);study_trees[sid]={'root':root,'members':sorted(members),'sampleCount':len(tipnodes)};study_tips[sid]=set(x for x in members if tip_counts[x]==1 and x in base);all_trees[sid]=clades
 anchor=lca(members);anchors[anchor or '__unplaced__'].append({'source':sid,'root':root,'type':'study'})
 coverage.append({'source':sid,'tips':len(tipnodes),'uniqueMatched':len(set(tipnodes)&set(base)),'unmatched':len([x for x in tipnodes if x not in base]),'ambiguousRepeatedGlottocodes':len([x for x,c in tip_counts.items() if c>1 and x in base]),'root':root,'anchor':anchor})
 for f in ['metadata.json','summary.trees','languages.csv','trees.csv']:hashes.append({'path':str(folder/f),'sha256':hashlib.sha256((folder/f).read_bytes()).hexdigest()})
# Attach WALS groupings at their common Glottolog ancestor, preserving source-specific grouping identity.
def wmembers(id):
 n=wals[id];return {wm[id]} if not n['children'] else set().union(*(wmembers(c) for c in n['children']))
for root in data['walsRoots']:
 ids=wmembers(root);anchor=lca(ids);anchors[anchor or '__unplaced__'].append({'source':'wals','root':wm[root],'type':'catalog'})
# Compare rooted study topologies on shared, unambiguously mapped tip IDs only.
# A crossing pair of clades (intersection and both differences non-empty) is incompatible.
conflicts=[];conflict_index=collections.defaultdict(list);pair_stats=[]
for a,b in itertools.combinations(sorted(study_trees),2):
 shared=study_tips[a]&study_tips[b]
 # Remove shared IDs which are ancestors of other shared tip IDs in Glottolog.
 anc=set(x for tip in shared for x in ancestors(tip)[:-1]);shared-=anc
 if len(shared)<3:continue
 ca=[(id,s&shared) for id,s in all_trees[a]];cb=[(id,s&shared) for id,s in all_trees[b]];ca=[(i,s) for i,s in ca if 1<len(s)<len(shared)];cb=[(i,s) for i,s in cb if 1<len(s)<len(shared)];count=0
 for ia,sa in ca:
  for ib,sb in cb:
   overlap=sa&sb
   if overlap and sa-sb and sb-sa:
    witness=[sorted(sa-sb)[0],sorted(overlap)[0],sorted(sb-sa)[0]];idx=len(conflicts);conflicts.append({'a':a,'b':b,'cladeA':ia,'cladeB':ib,'witness':witness,'sharedTips':len(shared)});count+=1
    for x in sa|sb:conflict_index[x].append(idx)
 pair_stats.append({'a':a,'b':b,'sharedTips':len(shared),'incompatibleCladePairs':count})
# Collapse repeated references without erasing separate source-tree sample edges.
for k,v in conflict_index.items():conflict_index[k]=list(dict.fromkeys(v))
result={'schemaVersion':3,'sources':sources,'extraNodes':extra,'assertions':edges,'placements':dict(placements),'anchors':dict(anchors),'studies':study_trees,'coverage':coverage,'conflicts':conflicts,'conflictIndex':dict(conflict_index),'pairComparisons':pair_stats,'hashes':hashes,'method':'Canonical IDs are exact Glottocodes; unknown samples and internal study clades retain source-specific IDs. Original sample labels remain on source-tagged edges. Tree hypotheses are never combined across sources as one asserted ancestry. Incompatibility is computed only between rooted summary topologies restricted to at least three shared, non-repeated, non-ancestor tip IDs. Sample absence and polytomies alone are not classified as conflict. Source-specific summary trees, not posterior samples, are imported.','catalogDiscovery':'All 30 data repositories returned by the Phlorest organization repository search on 2026-10-12, excluding phlorest software and .github; second page empty.'}
(P/'integrated.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')))
print('STUDIES',len(study_trees),'EXTRA NODES',len(extra),'ASSERTIONS',len(edges),'CONFLICTS',len(conflicts),'LANGUAGES WITH CONFLICTS',len(conflict_index));print('COVERAGE',json.dumps(coverage));print('FILE', (P/'integrated.json').stat().st_size)

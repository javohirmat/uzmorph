# SPDX-License-Identifier: GPL-3.0-only
"""Auto-verify regenerated batch-1 candidates against uz.wikipedia + Wikidata (read-only API calls).
Output: phase2/wiki/batch%s_wiki.json'%B+' (per lemma: exists, title, redirect, disambig, qid, P31 classes, gender)"""
import os,csv,json,urllib.request,urllib.parse,time,os
M='work/morph/phase2/'
B=os.environ.get('BATCH','01')
rows=list(csv.DictReader(open(M+'mining_v2/batch_%s.csv'%B+'',encoding='utf-8')))
H={'User-Agent':'uzmorph-lexicon-check/0.1 (research; contact via repo owner)'}
def get(url,params):
    u=url+'?'+urllib.parse.urlencode(params)
    for k in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60))
        except Exception as e: time.sleep(2+3*k)
    raise SystemExit('api failed')
cache=M+'wiki/batch%s_wiki.json'%B+''
res=json.load(open(cache,encoding='utf-8')) if os.path.exists(cache) else {}
todo=[r['lemma'] for r in rows if not r['proposed_pos'].startswith('V') and r['lemma'] not in res]
for b in range(0,len(todo),50):
    ch=todo[b:b+50];titles={l:(l[:1].upper()+l[1:]) for l in ch}
    d=get('https://uz.wikipedia.org/w/api.php',dict(action='query',titles='|'.join(titles.values()),redirects=1,prop='pageprops',ppprop='wikibase_item|disambiguation',format='json'))
    q=d['query'];norm={n['from']:n['to'] for n in q.get('normalized',[])};red={n['from']:n['to'] for n in q.get('redirects',[])}
    pages={p['title']:p for p in q['pages'].values()}
    for l,t in titles.items():
        t2=norm.get(t,t);t3=red.get(t2,t2);p=pages.get(t3,{})
        pp=p.get('pageprops',{})
        res[l]=dict(exists=('missing' not in p) and bool(p),title=t3,redirect=t3!=t2,disambig='disambiguation' in pp,qid=pp.get('wikibase_item'))
    time.sleep(0.3)
qids=sorted({v['qid'] for v in res.values() if v.get('qid') and 'p31' not in v})
cl={}
for b in range(0,len(qids),50):
    d=get('https://www.wikidata.org/w/api.php',dict(action='wbgetentities',ids='|'.join(qids[b:b+50]),props='claims',format='json'))
    for qid,e in d.get('entities',{}).items():
        c=e.get('claims',{})
        ids=lambda P:[x['mainsnak'].get('datavalue',{}).get('value',{}).get('id') for x in c.get(P,[])]
        cl[qid]=dict(p31=ids('P31'),p21=ids('P21'),p279=ids('P279'),p625='P625' in c,p17=ids('P17'))
    time.sleep(0.3)
for v in res.values():
    if v.get('qid') in cl: v.update(cl[v['qid']])
json.dump(res,open(cache,'w',encoding='utf-8'),ensure_ascii=False,indent=0)
print(len(res),sum(v['exists'] for v in res.values()),sum(v['exists'] and not v['disambig'] for v in res.values()))

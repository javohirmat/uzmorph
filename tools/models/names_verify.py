# SPDX-License-Identifier: GPL-3.0-only
"""Read-only uz.wikipedia + Wikidata check of mined name stems (same API calls as phase2/scripts/wiki_verify.py).
Accept: page exists, not a disambiguation page, not redirected to a title with a different stem, and the Wikidata item is a
human, a given/family name, or a geolocated place (P625) / item with a country (P17) that is not a creative work/common concept.
-> names_wiki.json (cache), names_list.tsv (accepted)"""
import csv,json,os,time,urllib.request,urllib.parse
H={'User-Agent':'uzmorph-lexicon-check/0.1 (research; contact via repo owner)'}
def get(url,params):
    u=url+'?'+urllib.parse.urlencode(params)
    for k in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60))
        except Exception as e: time.sleep(2+3*k)
    raise SystemExit('api failed')
rows=list(csv.DictReader(open('names_cand.tsv',encoding='utf-8'),delimiter='\t'))
cache='names_wiki.json'; res=json.load(open(cache,encoding='utf-8')) if os.path.exists(cache) else {}
todo=[r['stem'] for r in rows if r['stem'] not in res]
for b in range(0,len(todo),50):
    ch=todo[b:b+50]
    d=get('https://uz.wikipedia.org/w/api.php',dict(action='query',titles='|'.join(ch),redirects=1,prop='pageprops',ppprop='wikibase_item|disambiguation',format='json'))
    q=d['query'];norm={n['from']:n['to'] for n in q.get('normalized',[])};red={n['from']:n['to'] for n in q.get('redirects',[])}
    pages={p['title']:p for p in q['pages'].values()}
    for t in ch:
        t2=norm.get(t,t);t3=red.get(t2,t2);p=pages.get(t3,{}); pp=p.get('pageprops',{})
        res[t]=dict(exists=('missing' not in p) and bool(p),title=t3,redirect=t3!=t2,disambig='disambiguation' in pp,qid=pp.get('wikibase_item'))
    time.sleep(0.3)
qids=sorted({v['qid'] for v in res.values() if v.get('qid') and 'p31' not in v})
for b in range(0,len(qids),50):
    d=get('https://www.wikidata.org/w/api.php',dict(action='wbgetentities',ids='|'.join(qids[b:b+50]),props='claims',format='json'))
    for qid,e in d.get('entities',{}).items():
        c=e.get('claims',{}); ids=lambda P:[x['mainsnak'].get('datavalue',{}).get('value',{}).get('id') for x in c.get(P,[])]
        for v in res.values():
            if v.get('qid')==qid: v.update(p31=ids('P31'),p21=ids('P21'),p279=ids('P279'),p625='P625' in c,p17=ids('P17'))
    time.sleep(0.3)
json.dump(res,open(cache,'w',encoding='utf-8'),ensure_ascii=False,indent=0)
NAMES={'Q202444','Q12308941','Q11879590','Q3409032','Q101352'}
WORKS={'Q7725634','Q571','Q11424','Q482994','Q7366','Q134556','Q13442814','Q5398426','Q4167410','Q215380','Q1004','Q17537576','Q47461344','Q105543609','Q7889','Q9143','Q1002697','Q28640'}
acc=[];why={}
for r in rows:
    v=res.get(r['stem'],{}); p31=set(v.get('p31') or [])
    def rej(k): why[k]=why.get(k,0)+1
    if not v.get('exists'): rej('no uz.wiki page'); continue
    if v['disambig']: rej('disambiguation'); continue
    if v['redirect'] and not v['title'].lower().startswith(r['stem'].lower()[:max(3,len(r['stem'])-2)]): rej('redirect to other title'); continue
    if not v.get('qid'): rej('no Wikidata item'); continue
    if p31&WORKS: rej('work/concept'); continue
    if 'Q5' in p31: cls='NP-ANT'
    elif p31&NAMES: cls='NP-NAME'
    elif v.get('p625'): cls='NP-TOP'
    elif v.get('p17'): cls='NP-ORG'
    else: rej('not person/name/place/org'); continue
    acc.append((r['stem'],cls,r['tokens'],v['qid'],v['title']))
with open('names_list.tsv','w',encoding='utf-8') as f:
    f.write('stem\tclass\ttokens\tqid\twiki_title\n')
    for a in acc: f.write('\t'.join(map(str,a))+'\n')
print('candidates',len(rows),'accepted',len(acc),why)
from collections import Counter; print(Counter(a[1] for a in acc)); print(acc[:25])

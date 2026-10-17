# SPDX-License-Identifier: GPL-3.0-only
"""Run ZirhUzMorph 0.1.1 (git fd627db) on all eval word tokens in 3 scripts (its own normalisation) -> ../private/zirh.json"""
import json,os,sys
from zirhuzmorph import Analyzer
from zirhuzmorph.analyzer import Analysis
P=os.path.join(os.path.dirname(__file__),'..','private')
an=Analyzer()
def ana(w):
    lw=an._norm(w).lower()
    if '-' in lw:
        full=an.analyze(w,allow_unknown=False)
        if full: return [(a,'') for a in full]
        head,last=lw.rsplit('-',1)
        if last in ('u','yu','da','ku','chi','mi','a','ya','ov'):
            return [(a,'') for a in an.analyze(head)]
        return [(a,head+'-') for a in an.analyze(last)]
    return [(a,'') for a in an.analyze(w)]
S=[json.loads(l) for l in open(f'{P}/sentences.jsonl',encoding='utf-8')]
res={}
for script in ('lat','cyr','new'):
    R={}
    for s in S:
        for t in s['tokens']:
            if not t['word']: continue
            rs=ana(t[script])
            R[f"{s['id']}:{t['i']}"]=[dict(prefix=p,stem=a.stem,lemma=a.lemma,pos=a.pos,morphs=a.morphs,cost=round(a.cost,3),known=a.known,tagged=a.tagged()) for a,p in rs]
    res[script]=R
json.dump(res,open(f'{P}/zirh.json','w',encoding='utf-8'),ensure_ascii=False)
print({k:len(v) for k,v in res.items()})

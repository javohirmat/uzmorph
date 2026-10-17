#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""attribute.py NEW PREV RULESPEC.json OUT.json : gained types NEW vs PREV attributed to rules by analysis pattern; 50-sample per rule."""
import sys,json,random,re
sys.path.insert(0,'work/verify');import covlib
new,prev,spec,out=sys.argv[1:5];S=json.load(open(spec,encoding='utf-8'))
B=covlib.BASE;W=B['words'];C=B['cnt'];a=covlib.load(new);p=covlib.load(prev);K=('lower','title','upper')
gain=[i for i in range(len(W)) if covlib.known_any(a,i) and not covlib.known_any(p,i)]
G=set(gain);an={}
for k in K:
    with open(f'work/verify/{new}_{k}.txt',encoding='utf-8') as f:
        for j,l in enumerate(f):
            if j in G and j not in an and '/*' not in l: an[j]=l.strip()
res={r:[] for r in S};res['other']=[]
for i in gain:
    s=an.get(i,'')
    for r,pat in S.items():
        if re.search(pat,s): res[r].append(i);break
    else: res['other'].append(i)
o={}
for r,ix in res.items():
    random.seed(7);sm=random.sample(ix,min(50,len(ix)))
    o[r]=dict(types=len(ix),tokens=sum(C[i] for i in ix),top=[(W[i],C[i]) for i in sorted(ix,key=lambda i:-C[i])[:15]],
      sample=[(W[i],C[i],an[i][:160]) for i in sorted(sm,key=lambda i:-C[i])])
json.dump(o,open(out,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
for r,v in o.items(): print(r,v['types'],v['tokens'],v['top'][:8])

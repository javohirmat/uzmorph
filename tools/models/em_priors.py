# SPDX-License-Identifier: GPL-3.0-only
"""Unsupervised reading priors from the 1.47B-token corpus (type frequencies, top 400k types = 96.7% of tokens).
EM over readings: q(r|w) ∝ θ(tagseq r) · φ(lemma+pos r); counts weighted by corpus frequency. No gold data used.
-> priors.pkl {theta, phi, q (top types)}"""
import re,math,pickle,sys
from collections import defaultdict
LU=re.compile(r'\^((?:[^$\\]|\\.)*)\$')
def split_reads(lu):
    parts=re.split(r'(?<!\\)/',lu); return parts[0],parts[1:]
ZC=re.compile(r'\+e<cop><aor><p3>(?:<frm>)?<(?:sg|pl)>')
def norm(r): return ZC.sub('',r)
def key(r):
    k=r.find('<'); lem=r[:k]; tags=r[k:]
    m=re.match(r'<[^>]+>',tags); pos=m.group(0) if m else ''
    return lem.lower()+pos, tags
types=[]
for (line,fl) in zip(open('types.ap',encoding='utf-8'),open('types400k.tsv',encoding='utf-8')):
    w,n=fl.rstrip('\n').split('\t'); n=int(n)
    lus=LU.findall(line)
    if len(lus)!=1: continue
    s,reads=split_reads(lus[0])
    if not reads or reads[0].startswith('*'): continue
    reads=[r for r in dict.fromkeys(norm(x) for x in reads) if '<' in r]
    if reads: types.append((w,n,[key(r) for r in reads],reads))
print('analysed types',len(types),file=sys.stderr)
theta=defaultdict(lambda:1.0); phi=defaultdict(lambda:1.0)
for it in range(25):
    T=defaultdict(float); F=defaultdict(float)
    for w,n,ks,_ in types:
        sc=[theta[t]*phi[l] for l,t in ks]; z=sum(sc)
        for (l,t),s in zip(ks,sc): T[t]+=n*s/z; F[l]+=n*s/z
    zt=sum(T.values()); zf=sum(F.values())
    a=0.5
    theta=defaultdict(lambda:a/zt,{t:(v+a)/zt for t,v in T.items()})
    phi=defaultdict(lambda:a/zf,{l:(v+a)/zf for l,v in F.items()})
q={}
for w,n,ks,reads in types[:200000]:
    sc=[theta[t]*phi[l] for l,t in ks]; z=sum(sc); q[w]={r:s/z for r,s in zip(reads,sc)}
pickle.dump(dict(theta=dict(theta),phi=dict(phi),floor_t=0.5/zt,floor_f=0.5/zf,q=q),open('priors.pkl','wb'))
for w in ['odam','esa','yer','kuya','koʻra','davom','kishi','yangi','turli','keldi','boʻlgan','tanlovda','soʻzlar']:
    if w in q: print(w,sorted(q[w].items(),key=lambda x:-x[1])[:3])

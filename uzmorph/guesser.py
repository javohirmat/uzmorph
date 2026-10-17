# SPDX-License-Identifier: GPL-3.0-only
"""Ranking of the stem-placeholder guesser's readings for words the main analyzer does not know.
score = log P(tag sequence) + 1.5·log(corpus stem support) + stem-length bonus + stem-ending plausibility − penalties.
Only confident guesses are returned by default (support ≥ 2, stem ≥ 4 letters, no auxiliary, not a foreign-looking word)."""
import re,math,functools
from .models import load
COP0=re.compile(r'\+e<cop><aor><p3><(sg|pl)>')
SUFFIXY=('lar','lari','larin','ning','dagi','dan','ga','da','ni','si','miz','ingiz','im','lik')
FOREIGN=re.compile(r'w|c(?!h)|(ogo|ykh|aya|yye|skiy|skoy|skaya|tion|nnoy|ovna|ovich|evich|evna|iye)$')
def _norm(t): return COP0.sub('',t).replace('<iv>','<TD>').replace('<tv>','<TD>')
@functools.lru_cache(None)
def _m():
    M=load('guess_model.json.gz'); return M['prior'],M['tot'],M['S'],frozenset(M['bare']),M['E']
def rank(surf,readings,cap,n=1,all_=False):
    P,TOT,S,BARE,E=_m(); EN=E['_n']
    lp=lambda t:math.log((P.get(t,0)+1.0)/TOT)
    plaus=lambda stem,pos:math.log((E[pos].get(stem[-2:],0)+0.5)/(EN[pos]+200))-math.log(1/400)
    w=surf.lower(); best=[]
    for r in readings:
        if '<guess>' not in r: continue
        k=r.find('<'); stem=r[:k].lower(); t=_norm(r[k:].replace('<guess>','')); pos='v' if t.startswith('<v>') else 'n'
        if cap and pos=='v': continue
        if len(stem)>=len(w) or len(stem)<3: continue
        s=S.get(f'{stem}\t{pos}',0)+(1 if pos=='n' and stem in BARE else 0)
        if s<1: s=1
        best.append((lp(t)+1.5*math.log(s)+0.15*min(len(stem),10)+plaus(stem,pos)-(1.5 if stem.endswith(SUFFIXY) else 0)-(3 if '<vaux>' in t else 0),stem,t,s))
    sb=S.get(f'{w}\tn',0)
    if sb>=3 and not any(x[3]>=sb for x in best):
        best.append((lp('<n><nom>')+1.5*math.log(sb)+0.15*min(len(w),10)+plaus(w,'n')-(1.5 if w.endswith(SUFFIXY) else 0),w,'<n><nom>',sb))
    best.sort(reverse=True)
    if not best: return None
    conf=best[0][3]>=2 and len(best[0][1])>=4 and '<vaux>' not in best[0][2] and not FOREIGN.search(w)
    if not conf and not all_: return None
    out=[]
    for sc,stem,t,s in best[:n]:
        if cap: t=t.replace('<n>','<np>',1); stem=stem[:1].upper()+stem[1:]
        out.append(stem+t+'<guess>')
    return out

# SPDX-License-Identifier: GPL-3.0-only
"""P(suffix s is a real suffix | a proper noun ends in s), estimated from v8d's np analyses of corpus types (top-400k). -> name_sufprior.pkl"""
import re,pickle
from collections import Counter
import names as N
LU=re.compile(r'\^((?:[^$\\]|\\.)*)\$')
yes=Counter(); tot=Counter()
for line,fl in zip(open('types.ap',encoding='utf-8'),open('types400k.tsv',encoding='utf-8')):
    lus=LU.findall(line)
    if len(lus)!=1: continue
    parts=re.split(r'(?<!\\)/',lus[0]); np_=[x for x in parts[1:] if '<np>' in x]
    if not np_: continue
    w=parts[0].lower(); stem=np_[0][:np_[0].find('<')].lower()
    for s,pt,ct in N.SUF:
        if s and w.endswith(s):
            tot[s]+=1; yes[s]+= (stem==w[:len(w)-len(s)].rstrip("ʼ'ʻ`’-") or len(stem)<=len(w)-len(s))
P={s:(yes[s]+1)/(tot[s]+2) for s in tot}
pickle.dump(P,open('name_sufprior.pkl','wb'))
for s in sorted(P,key=lambda s:-tot[s])[:25]: print(s,tot[s],round(P[s],2))

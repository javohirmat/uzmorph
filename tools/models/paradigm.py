# SPDX-License-Identifier: GPL-3.0-only
"""Paradigm size per lemma+pos: number of distinct corpus types (top-400k) that have a reading of it. -> paradigm.pkl"""
import re,pickle
from collections import defaultdict
from rank_lib import norm,key
LU=re.compile(r'\^((?:[^$\\]|\\.)*)\$')
PS=defaultdict(int); PU=defaultdict(int)
for line in open('types.ap',encoding='utf-8'):
    lus=LU.findall(line)
    if len(lus)!=1: continue
    parts=re.split(r'(?<!\\)/',lus[0])
    ks={key(norm(x).split('+')[0])[0] for x in parts[1:] if '<' in x}
    for k in ks: PS[k]+=1
    lems={k[:k.find('<')] for k in ks}
    if len(lems)==1:
        for k in ks: PU[k]+=1
pickle.dump(dict(PS=dict(PS),PU=dict(PU)),open('paradigm.pkl','wb'))
for k in ['uning<n>','u<prn>','ichiga<n>','ich<n>','shahri<n>','shahar<n>','shahr<n>','usti<n>','ust<n>','mazmuni<n>','mazmun<n>','foydalanish<n>','foydalan<v>','odam<n>','oda<n>','talab<n>','tala<v>','ostida<n>','ost<n>','hal<n>','hali<adv>','jam<n>','jami<adv>','bor<n>','bor<v>','kam<adj>','sathi<n>','sath<n>']: print(k,PS.get(k),PU.get(k))

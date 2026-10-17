# SPDX-License-Identifier: GPL-3.0-only
"""Proper-noun guesser: capitalised word -> Stem<np><guess>+number/possessive/case. The stem split is chosen by corpus
evidence (capitalised sentence-medial counts of the stem's paradigm forms) times a suffix prior; no gold data used.
A small verified list (names_list.tsv, Wikidata-checked) gives readings without <guess>."""
import csv,functools
from .models import load,path
CASE=[('ning','gen'),('ni','acc'),('ga','dat'),('ka','dat'),('qa','dat'),('da','loc'),('ta','loc'),('dan','abl'),('tan','abl'),
      ('dagi','loc><attr'),('gacha','term'),('day','sim'),('dek','sim'),('','nom')]
PX=[('lari','<pl><px3sp>'),('lar','<pl>'),('si','<px3sp>'),('i','<px3sp>'),('','')]
SUF=sorted({(px+cs,pt,ct) for px,pt in PX for cs,ct in CASE},key=lambda x:-len(x[0]))
APOS="ʼ'ʻ`’"
@functools.lru_cache(None)
def _cs():
    d=load('capstats.json.gz'); return d['cap'],d['lo']
@functools.lru_cache(None)
def _nlist():
    with open(path('names_list.tsv'),encoding='utf-8') as f: return frozenset(r['stem'] for r in csv.DictReader(f,delimiter='\t'))
def evidence(stem):
    CAP,LO=_cs(); s=stem.lower(); e=0
    for x in SUF:
        f=s+x[0]; c=CAP.get(f,0)
        if c and c>=LO.get(f,0): e+=c
    return e
def candidates(w):
    base=w.rstrip(APOS); out=[]
    for s,pt,ct in SUF:
        if s and not base.lower().endswith(s): continue
        stem=(base[:len(base)-len(s)] if s else base).rstrip(APOS+'-')
        if len(stem)<2 or not stem[0].isupper(): continue
        if pt=='<px3sp>' and s.startswith('i') and stem[-1].lower() in 'aeiouoʻ': continue
        if pt=='<px3sp>' and s.startswith('si') and stem[-1].lower() not in 'aeiou': continue
        out.append((stem,pt,ct))
    return out
def guess(w):
    """-> Apertium-style readings, best first"""
    cs=candidates(w)
    if not cs: return []
    SP=load('name_sufprior.json')
    sufs=[w.rstrip(APOS)[len(c[0]):].lower().lstrip(APOS+'-') for c in cs]
    pmax=max([SP.get(x,0.5) for x in sufs if x] or [0])
    ps=lambda x:SP.get(x,0.5) if x else 1-pmax
    sc=sorted(zip(cs,sufs),key=lambda z:(-(evidence(z[0][0])+1)*ps(z[1]),-len(z[0][0])))
    return [f'{st}<np><guess>{pt}<{ct}>' for (st,pt,ct),_ in sc]
def guess_hyph(w):
    """hyphenated names: guess on the last segment, keep the rest as a prefix"""
    if '-' in w.strip('-'):
        pre,last=w.rsplit('-',1)
        if last[:1].isupper(): return [pre+'-'+g for g in guess(last)]
    return guess(w)
def listed(w):
    """verified-list lookup -> reading without <guess>, or None"""
    for g in guess_hyph(w):
        st=g[:g.find('<')]
        if st.rsplit('-',1)[-1] in _nlist(): return g.replace('<guess>','')
    return None
def capratio(w):
    CAP,LO=_cs(); s=w.lower(); c=CAP.get(s,0); l=LO.get(s,0); return c,(c/(c+l) if c+l else 0.0)

# SPDX-License-Identifier: GPL-3.0-only
"""Proper-noun guesser: capitalised word -> Stem<np><guess>+number/possessive/case, stem chosen by
corpus evidence (capitalised medial counts of the stem's paradigm, from capstats.pkl). No gold used."""
import pickle,os,re
D=os.path.dirname(os.path.abspath(__file__))
SP=pickle.load(open(f'{D}/name_sufprior.pkl','rb'))   # P(segmentation | name ends in s), from v8d np analyses of capitalised corpus types
CS=pickle.load(open(f'{D}/capstats.pkl','rb')); CAP=CS['cap']; LO=CS['lo']
CASE=[('ning','gen'),('ni','acc'),('ga','dat'),('ka','dat'),('qa','dat'),('da','loc'),('ta','loc'),('dan','abl'),('tan','abl'),
      ('dagi','loc><attr'),('gacha','term'),('day','sim'),('dek','sim'),('','nom')]
PX=[('lari','<pl><px3sp>'),('lar','<pl>'),('si','<px3sp>'),('i','<px3sp>'),('','')]
SUF=[]
for px,pt in PX:
    for cs,ct in CASE:
        s=px+cs
        if px in('lari','si','i') and cs=='ni': pass
        SUF.append((s,pt,ct))
SUF=sorted(set(SUF),key=lambda x:-len(x[0]))
APOS="ʼ'ʻ`’"
def evidence(stem):
    """capitalised-medial counts of the stem's paradigm forms that are mostly capitalised (name-like)"""
    s=stem.lower(); e=0
    for x in SUF:
        f=s+x[0]; c=CAP.get(f,0)
        if c and c>=LO.get(f,0): e+=c
    return e
def candidates(w):
    base=w.rstrip(APOS); out=[]
    for s,pt,ct in SUF:
        if s and not base.lower().endswith(s): continue
        stem=base[:len(base)-len(s)] if s else base
        stem=stem.rstrip(APOS+'-')
        if len(stem)<2 or not stem[0].isupper(): continue
        if pt=='<px3sp>' and s.startswith('i') and stem[-1].lower() in 'aeiouoʻ': continue   # -i after consonant only
        if pt=='<px3sp>' and s.startswith('si') and stem[-1].lower() not in 'aeiou': continue
        out.append((stem,pt,ct))
    return out
def guess_hyph(w):
    """hyphenated names: guess on the last segment, keep the rest as a prefix"""
    if '-' in w.strip('-'):
        pre,last=w.rsplit('-',1)
        if last[:1].isupper(): return [pre+'-'+g for g in guess(last)]
    return guess(w)
def guess(w):
    """-> list of apertium-style readings, best first"""
    cs=candidates(w)
    if not cs: return []
    sl=lambda c:len(w.rstrip(APOS))-len(c[0])
    sufs=[w.rstrip(APOS)[len(c[0]):].lower().lstrip(APOS+'-') for c in cs]
    pmax=max([SP.get(x,0.5) for x in sufs if x] or [0])
    ps=lambda x:SP.get(x,0.5) if x else 1-pmax
    sc=sorted(zip(cs,sufs),key=lambda z:(-(evidence(z[0][0])+1)*ps(z[1]),-len(z[0][0])))
    sc=[c for c,_ in sc]
    return [f'{st}<np><guess>{pt}<{ct}>' for st,pt,ct in sc]
import csv as _csv
NLIST={r['stem'] for r in _csv.DictReader(open(f'{D}/names_list.tsv',encoding='utf-8'),delimiter='\t')} if os.path.exists(f'{D}/names_list.tsv') else set()
def listed(w):
    """verified proper-noun list lookup: -> reading without <guess> or None"""
    for g in guess_hyph(w):
        st=g[:g.find('<')]; base=st.rsplit('-',1)[-1]
        if base in NLIST: return g.replace('<guess>','')
    return None
def capratio(w):
    s=w.lower(); c=CAP.get(s,0); l=LO.get(s,0); return c,(c/(c+l) if c+l else 0.0)
if __name__=='__main__':
    for w in ['Kamini','Garti','Yagoni','Trampning','Ilonning','Ilon','Tramplari','Maskdan','Qoraqalpogʻistonidagi']: print(w,guess(w)[:3],capratio(w))

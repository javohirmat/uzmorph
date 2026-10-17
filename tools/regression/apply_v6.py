#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""v6 changes on top of apply_v4 + apply_v5 output.
G1 OTM: lowercase analysis-only surface so Otm/otm/otmlar/OTMga all match (R30-style; lt-proc maps upper input to lower dictionary only).
G2 analysis-only spelling variants (Dir/LR, never generated): ustivor(lik)->ustuvor(lik), talofat->talafot (plain variants);
   tushin- -> tushun-, muloqat -> muloqot carry <mistake> (2-4% of uses), so they stay out of the no-mistake figures.
G3 R8: nari -roq (nariroq). G4 R3 extension: -(a)yotganlik / -mayotganlik (new tag <ger_prog>).
G5 analysis-only -(a)qol auxiliary written solid (qoʻyaqol, ketaqol, olaqol).
--lemmas TSV adds LEXICON V6-Additions (batch-2 auto-verified lemmas)."""
import sys,re,csv,argparse,os
ap=argparse.ArgumentParser();ap.add_argument('dst');ap.add_argument('--lemmas');a=ap.parse_args()
assert 'apertium-uzb-v4' in a.dst or 'scratch' in a.dst
L=os.path.join(a.dst,'apertium-uzb.uzb.lexc');t=open(L,encoding='utf-8').read()
def sub1(old,new,s):
    assert s.count(old)==1,(old,s.count(old));return s.replace(old,new)
# G4 tag + rules
t=sub1('%<ger_pres%>  ! -ayotgan\n','%<ger_pres%>  ! -ayotgan\n%<ger_prog%>  ! -ayotganlik (v6 G4, R3 extension)\n',t)
old='%<neg%>%<ger_perf%>:%>ma%>%{G%}anlik FULL-NOMINAL-INFLECTION ; ! test build R3: boʻlmaganligi\n'
n=t.count(old);assert n>=2,n
t=t.replace(old,old+'%<ger_prog%>:%>%{a%}yotganlik FULL-NOMINAL-INFLECTION ; ! v6 G4 R3 ext: kelayotganligi\n'
                    '%<neg%>%<ger_prog%>:%>ma%>yotganlik FULL-NOMINAL-INFLECTION ; ! v6 G4 R3 ext: kelmayotganligi\n')
# G5 -(a)qol
t=sub1('%<prc_impf%>+ol%<vaux%>:%>ol V-AUX ;\n','%<prc_impf%>+ol%<vaux%>:%>ol V-AUX ;\n%<prc_impf%>+qol:%>%{E%}qol V-AUX ; ! Dir/LR ! v6 G5 solid-written -(a)qol (qoʻyaqol, ketaqol); analysis only\n',t)
# G3 R8
t=sub1('LEXICON Comparatives   ! R8: lemmas whose -roq form is attested (make_lists.py)\n','LEXICON Comparatives   ! R8: lemmas whose -roq form is attested (make_lists.py)\nnari:nari COMP-ADV ; ! v6 G3 nariroq\n',t)
add=["","! v6: second-opinion decisions (second review + the native reviewer), appended to V5-Additions (all analysis-only)",
 "OTM:otm ABBR ; ! Dir/LR ! v6 G1 R30-style: Otm, otmlar, OTMga (lowercase dictionary side matches any case)",
 "ustuvor:ustivor A2 ; ! Dir/LR ! v6 G2 variant spelling (ustivor- ~19% of uses), never generated",
 "ustuvor:ustivor COMP-ADJ ; ! Dir/LR ! v6 G2",
 "ustuvorlik:ustivorlik N1 ; ! Dir/LR ! v6 G2",
 "talafot:talofat N1 ; ! Dir/LR ! v6 G2 variant spelling (talofat ~40% of uses), never generated",
 "tushun%<mistake%>:tushin V-IV ; ! Dir/LR ! v6 G2 misspelling (~2% of uses): reading carries <mistake>",
 "muloqot%<mistake%>:muloqat N1 ; ! Dir/LR ! v6 G2 misspelling (~4% of uses): reading carries <mistake>"]
if a.lemmas:
    add+=["","LEXICON V6-Additions   ! v6: batch-2 auto-verified lemmas (uz.wikipedia + Wikidata), see phase2/lemmas_v6_batch02.tsv",""]
    for r in csv.DictReader(open(a.lemmas,encoding='utf-8'),delimiter='\t'):
        add.append(f"{r['lemma']}:{r['surface']} {r['paradigm']} ; ! v6 add ! {r['category']} ! {r['flag']}")
if a.lemmas: t=sub1("V5-Additions ; ! v5\n","V5-Additions ; ! v5\nV6-Additions ; ! v6\n",t)
t=t.rstrip('\n')+'\n'+'\n'.join(add)+'\n'
open(L,'w',encoding='utf-8').write(t);print('v6 applied, additions',len(add)-3)

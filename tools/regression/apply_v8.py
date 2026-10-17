#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""v8 on top of v7 (+ batches): the native reviewer batch-2 adjudication + generation fixes.
P1 present continuous: generate -yap (ketyapti, oʻqiyapti, kelmayapti); -{a}yab (*ketayabdi, 87 corpus tokens) becomes analysis-only.
P2 -moq infinitive + possessive voices q>gʻ (bilmogʻi, qilmogʻi; generator gave *bilmoqi): own possessive lexicon carrying {ʻ}.
P3 -(a)r + -mish reported future (boʻlarmish, kelmasmish); analysis only.
P4 archaic infinitive -mak (qilmak, qutlamak); analysis only, <arch>.
Variants/forms (analysis only): takidla -> taʼkidla <mistake>; samoʻ -> samo; qoplagʻich -> qoplagich; temiryoʻl (solid); buyogʻi (buyoq px3); boya + case (boyadan).
Lemmas: phase2/lemmas_v8_batch02.tsv (via apply_batch.py)."""
import sys,os
dst=sys.argv[1];L=os.path.join(dst,'apertium-uzb.uzb.lexc');t=open(L,encoding='utf-8').read()
def sub(old,new,n=1):
    global t
    assert t.count(old)==n,(old,t.count(old));t=t.replace(old,new)
# P1
sub('%<prog%>:%>yap PERS ;       ! Dir/LR\n','%<prog%>:%>yap PERS ; ! v8 P1: generable form (ketyapti, oʻqiyapti)\n')
sub('%<prog%>:%>%{a%}yab PERS ;\n','%<prog%>:%>%{a%}yab PERS ; ! Dir/LR ! v8 P1: was generable, gave *ketayabdi\n')
# P2 + P4
sub('%<ger_inf%>:%>moq GER-INFL ;\n','%<ger_inf%>:%>moq GER-INF-INFL ; ! v8 P2\n%<ger_inf%>:%>moq GER-INFL ; ! Dir/LR ! v8 P2 keeps the old unvoiced -moqi analyses (no regression)\n%<ger_inf%>%<arch%>:%>mak GER-INFL ; ! Dir/LR ! v8 P4 archaic qilmak\n',2)
sub('LEXICON GER-INFL\n','''LEXICON GER-INF-INFL   ! v8 P2: -moq; possessives carry {ʻ} so q>gʻ (bilmogʻi)
GER-CASE-ETC ;
%<pl%>:%>lar GER-POSSESSIVES ;
%<pl%>:%>lar GER-CASE-ETC ;
GER-ABE-ETC ;
INF-POSSESSIVES ;

LEXICON INF-POSSESSIVES   ! v8 P2
%<px1sg%>:%>%{ʻ%}%{i%}m GER-CASE-ETC ;
%<px2sg%>:%>%{ʻ%}%{i%}ng GER-CASE-ETC ;
%<px3sp%>:%>%{ʻ%}%{s%}i GER-CASE-ETC ;
%<px1pl%>:%>%{ʻ%}%{i%}miz GER-CASE-ETC ;
%<px2pl%>:%>%{ʻ%}%{i%}nglar GER-CASE-ETC ;
%<px3pl%>:%>lari GER-CASE-ETC ;
%<px2sg%>%<frm%>:%>%{ʻ%}%{i%}ngiz GER-CASE-ETC ;
%<px2pl%>%<frm%>:%>%{ʻ%}%{i%}ngizlar GER-CASE-ETC ;

LEXICON GER-INFL
''')
# P3
sub('%<neg%>%<fut2%>+e%<cop%>%<aor%>%<evid%>:%>mas%>kan V-PERS-S1 ;\n','%<neg%>%<fut2%>+e%<cop%>%<aor%>%<evid%>:%>mas%>kan V-PERS-S1 ;\n%<fut2%>+e%<cop%>%<past%>%<evid%>:%>%{a%}r%>mish PERS ; ! Dir/LR ! v8 P3 boʻlarmish\n%<neg%>%<fut2%>+e%<cop%>%<past%>%<evid%>:%>mas%>mish PERS ; ! Dir/LR ! v8 P3 kelmasmish\n')
# P5 optative 1st person after vowel stems: {E}y gave *qarayy / *qarayylik (qaraylik 7,499 unknown); {a} drops after a vowel
sub('%<opt%>%<p1%>%<sg%>:%>%{E%}y # ;\n','%<opt%>%<p1%>%<sg%>:%>%{a%}y # ; ! v8 P5 (was {E}y: *qarayy)\n')
sub('%<opt%>%<p1%>%<sg%>:%>%{E%}yin # ; !Dir/LR\n','%<opt%>%<p1%>%<sg%>:%>%{a%}yin # ; !Dir/LR ! v8 P5\n')
sub('%<opt%>%<p1%>%<pl%>:%>%{E%}ylik # ;\n','%<opt%>%<p1%>%<pl%>:%>%{a%}ylik # ; ! v8 P5 (was {E}ylik: *qarayylik)\n')
# P6 -{G}uncha 'until' (tag <gna_until> was declared upstream but never implemented): kelguncha 16,639, borguncha 4,221
old='%<gna_when%>:%>%{G%}ach # ;     ! FIXME: rename ! test build R17: was a literal g\n'
U=('%<gna_until%>:%>%{G%}uncha CLIT-GINA-OPT ; ! v8 P6 kelguncha\n'
   '%<gna_until%>%<px1sg%>:%>%{G%}unimcha # ; ! v8 P6 kelgunimcha\n%<gna_until%>%<px2sg%>:%>%{G%}uningcha # ; ! v8 P6\n'
   '%<gna_until%>%<px3sp%>:%>%{G%}unicha # ; ! v8 P6 kelgunicha\n%<gna_until%>%<px1pl%>:%>%{G%}unimizcha # ; ! v8 P6\n'
   '%<gna_until%>%<px2sg%>%<frm%>:%>%{G%}uningizcha # ; ! v8 P6\n%<gna_until%>%<px3pl%>:%>%{G%}unlaricha # ; ! v8 P6\n')
assert t.count(old)==2;t=t.replace(old,old+U)
# upstream typo: paradigm 'A1→A1' (undefined sublexicon, hfst-lexc warning; alayno never analysed)
sub('alayno:alayno A1→A1 ;','alayno:alayno A1 ; ! v8 was A1→A1 (upstream typo)')
add=['','! v8: the native reviewer batch-2 variants and forms (analysis only)',
 'taʼkidla%<mistake%>:takidla V-TV ; ! Dir/LR ! v8 misspelling, 1.1% of uses',
 'samo:samoʻ N1 ; ! Dir/LR ! v8 the native reviewer: samo, wrong sign',
 'qoplagich:qoplagʻich N1 ; ! Dir/LR ! v8 variant spelling (~54% of uses)',
 'temiryoʻl:temiryoʻl N1 ; ! Dir/LR ! v8 solid spelling of temir yoʻl',
 'buyoq%<prn%>%<adv%>%<px3sp%>:buyogʻi CASE-ETC ; ! Dir/LR ! v8 bundan buyogʻi',
 'boya:boya ADV1 ; ! v8 boyadan (beri)',
 'yey:yey IJ ; ! v8 exclamative/vocative particle (ketdi-yey, voy-yey); without it P5 made yey = ye<opt><p1><sg> only']
t=t.rstrip('\n')+'\n'+'\n'.join(add)+'\n';open(L,'w',encoding='utf-8').write(t);print('v8 applied')
# Phase 4: guesser stem pattern (separate uzb_guesser binary only; main transducer unaffected).
# Upstream pattern used ASCII o' / g' (never matches oʻ/gʻ text) and required every syllable to start with a consonant
# (so vowel-initial or vowel-cluster stems like anion, ozon, kakao never matched).
G='''define L [ a | b | c | d | e | f | g | h | i | j | k | l | m | n | o | p | q | r | s | t | u | v | x | y | z | "ʻ" | "ʼ" ] ;
define V [ a | e | i | o | u ] ;
define Stem [ L* V L* ] & [ L L L L* ] & ~[ ["ʻ"|"ʼ"] ?* ] & ~$[ \\[o|g] "ʻ" ] & ~$[ "ʼ" "ʼ" ] ;

regex Stem ;
'''
open(os.path.join(dst,'apertium-uzb.uzb.guesser'),'w',encoding='utf-8').write(G);print('v8 guesser pattern written')

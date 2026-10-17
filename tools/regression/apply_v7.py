#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""v7 grammar gaps on top of apply_v6 output. RULES env (comma list) selects rules; default all.
H1 R16 -(a)ver continuative aux, solid-written (qolaversa, boraveradi, oʻqiyveradi); analysis only, like -(a)qol.
H2 negative progressive participle/gerund -mayotgan (kelmayotgan, kelmayotganlar, kelmayotganini); generable.
H3 case/plural on -roq adverbs (nariroqda, keyinroqqa); <adv><comp><subst> like COMP-ADJ.
H4 -(a)yap present continuous after consonant stems (ketayapti, ketayap, aytayapman); older literary variant of -yap
   (~22% of uses in the corpus), analysis only, no <mistake>.
H5 -(a)yotib progressive converb (borayotib, kelmayotib) [generable, new tag <gna_prog>] and its evidential
   -ayotibdi (borayotibdi) [analysis only].
H6 colloquial pluperfect -(u)vdi = -gan edi (keluvdim, turuvdi, boʻluvdik); analysis only, tag <colloq>.
H7 archaic -dur: aorist -(a)dur (boʻladur, qiladurman), -(a)durgan (boʻladurgan), evidential -ibdur (qilibdur, debdur),
   nadur 'what is'; analysis only, tag <arch>.
H8 durang 'draw (sport)' N1."""
import sys,os,argparse
ap=argparse.ArgumentParser();ap.add_argument('dst');a=ap.parse_args()
R=set((os.environ.get('RULES') or 'H1,H2,H3,H4,H5,H6,H7,H8').split(','))
L=os.path.join(a.dst,'apertium-uzb.uzb.lexc');t=open(L,encoding='utf-8').read()
def sub1(old,new):
    global t
    assert t.count(old)==1,(old,t.count(old));t=t.replace(old,new)
def after_all(old,add,n=2):
    global t
    assert t.count(old)==n,(old,t.count(old));t=t.replace(old,old+add)
tags='%<ger_prog%>  ! -ayotganlik (v6 G4, R3 extension)\n'
sub1(tags,tags+'%<gna_prog%>  ! -(a)yotib progressive converb (v7 H5)\n%<colloq%>  ! colloquial form, analysis only (v7 H6)\n')
if 'H1' in R:
    sub1('%<prc_impf%>+ol%<vaux%>:%>ol V-AUX ;\n','%<prc_impf%>+ol%<vaux%>:%>ol V-AUX ;\n%<prc_impf%>+ber:%>%{E%}ver V-AUX ; ! Dir/LR ! v7 H1 R16 solid-written -(a)ver (qolaversa, boraveradi); analysis only\n')
if 'H2' in R:
    after_all('%<ger_pres%>:%>%{a%}yotgan GER-INFL ;\n','%<neg%>%<ger_pres%>:%>ma%>yotgan GER-INFL ; ! v7 H2 kelmayotgan\n')
    after_all('%<gpr_pres%>:%>%{a%}yotgan # ;\n','%<neg%>%<gpr_pres%>:%>ma%>yotgan # ; ! v7 H2\n')
if 'H5' in R:
    after_all('%<gpr_pres%>:%>%{a%}yotgan # ;\n','%<gna_prog%>:%>%{a%}yotib CLIT-GINA-OPT ; ! v7 H5 borayotib\n%<neg%>%<gna_prog%>:%>ma%>yotib CLIT-GINA-OPT ; ! v7 H5 kelmayotib\n')
    sub1('%<prog%>:%>%{a%}yab PERS ;\n','%<prog%>:%>%{a%}yab PERS ;\n%<prog%>%<evid%>:%>%{a%}yotib PERS3 ; ! Dir/LR ! v7 H5 borayotibdi\n')
if 'H4' in R:
    sub1('%<prog%>:%>%{a%}yab PERS ;\n','%<prog%>:%>%{a%}yab PERS ;\n%<prog%>:%>ayap PERS ; ! Dir/LR ! v7 H4 older literary -ayap after consonant stems (ketayapti)\n')
if 'H6' in R:
    sub1('%<past%>+e%<cop%>%<ifi%>:%>%{G%}an%>di PERS2 ;\n','%<past%>+e%<cop%>%<ifi%>:%>%{G%}an%>di PERS2 ;\n%<past%>+e%<cop%>%<ifi%>%<colloq%>:%>%{U%}v%>di PERS2 ; ! Dir/LR ! v7 H6 colloquial keluvdim = kelgan edim\n')
if 'H7' in R:
    sub1('%<fut2%>:%>%{a%}r PERS-FUT2 ;','%<aor%>%<arch%>:%>%{E%}dur PERS-DUR ; ! Dir/LR ! v7 H7 archaic boʻladur, qiladurman\n%<fut2%>:%>%{a%}r PERS-FUT2 ;')
    sub1('%<past%>%<evid%>:%>%{i%}b PERS3 ;\n','%<past%>%<evid%>:%>%{i%}b PERS3 ;\n%<past%>%<evid%>%<arch%>:%>%{i%}bdur PERS-DUR ; ! Dir/LR ! v7 H7 archaic qilibdur, debdur\n')
    after_all('%<gpr_impf%>:%>%{a%}digan # ;\n','%<gpr_impf%>%<arch%>:%>%{a%}durgan # ; ! Dir/LR ! v7 H7 boʻladurgan\n')
    after_all('%<ger_impf%>:%>%{E%}digan GER-INFL ;\n','%<ger_impf%>%<arch%>:%>%{E%}durgan GER-INFL ; ! Dir/LR ! v7 H7\n')
    sub1('LEXICON PERS\n','LEXICON PERS-DUR   ! v7 H7 archaic -dur person endings (analysis only)\n%<p3%>%<sg%>: CLITICS ;\n%<p1%>%<sg%>:%>man CLITICS ;\n%<p2%>%<sg%>:%>san CLITICS ;\n%<p2%>%<frm%>%<sg%>:%>siz CLITICS ;\n%<p1%>%<pl%>:%>miz CLITICS ;\n%<p2%>%<frm%>%<pl%>:%>sizlar CLITICS ;\n%<p3%>%<pl%>:%>lar CLITICS ;\n\nLEXICON PERS\n')
if 'H3' in R:
    sub1('%<adv%>%<comp%>:%>roq CLIT-GINA-OPT ;\n','%<adv%>%<comp%>:%>roq CLIT-GINA-OPT ;\n%<adv%>%<comp%>%<subst%>:%>roq SUBST ; ! v7 H3 nariroqda, keyinroqqa\n')
add=['','! v7 lexical additions (analysis-only unless noted)']
if 'H7' in R: add.append('na%<prn%>%<itg%>%<nom%>+e%<cop%>%<aor%>%<p3%>%<sg%>%<arch%>:nadur # ; ! Dir/LR ! v7 H7 archaic "Adabiyot nadur?"')
if 'H8' in R: add.append('durang:durang N1 ; ! v7 H8 "durang natija" draw (sport); corpus 2.9k tokens')
t=t.rstrip('\n')+'\n'+'\n'.join(add)+'\n'
open(L,'w',encoding='utf-8').write(t);print('v7 applied',sorted(R))

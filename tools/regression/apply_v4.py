#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Build apertium-uzb-v4 source from the test build (tb/morph/apertium-uzb-test).
Never touches the original apertium-uzb or the test-build source.
Usage: apply_v4.py SRC DST [--lemmas lemmas.tsv] [--batch extra.tsv ...]
"""
import sys,os,re,shutil,subprocess,csv,argparse
ap=argparse.ArgumentParser();ap.add_argument('src');ap.add_argument('dst')
ap.add_argument('--lemmas');ap.add_argument('--no-fixes',action='store_true')
a=ap.parse_args()
assert os.path.realpath(a.src)!=os.path.realpath(a.dst)
assert 'apertium-uzb-v4' in a.dst or 'scratch' in a.dst, 'refusing to write outside a v4/scratch dir'
for f in ('apertium-uzb.uzb.lexc','apertium-uzb.uzb.twol'):
    shutil.copy(os.path.join(a.src,f),os.path.join(a.dst,f))
L=os.path.join(a.dst,'apertium-uzb.uzb.lexc');T=os.path.join(a.dst,'apertium-uzb.uzb.twol')
t=open(L,encoding='utf-8').read();tw=open(T,encoding='utf-8').read()
def sub1(old,new,s):
    assert s.count(old)==1,(old,s.count(old));return s.replace(old,new)
if not a.no_fixes:
    # F1: -da postadv must end the word (CLIT-GINA after it broke hyphen compounds: dori-darmon -> dori + -da + rmon)
    t=sub1("%-da:%-da POSTADV ; ! \n","%-da:%-da POSTADV-END ; ! v4 F1: -da ends the word; with CLIT-GINA lt-proc split dori-darmon into dori + -da + rmon\n",t)
    t=sub1("LEXICON POSTADV\n%<postadv%>: CLIT-GINA-OPT ; ! test build R5: was #\n",
           "LEXICON POSTADV\n%<postadv%>: CLIT-GINA-OPT ; ! test build R5: was #\n\nLEXICON POSTADV-END   ! v4 F1\n%<postadv%>: # ;\n",t)
    # F2: uq (uqmoq 'grasp') keeps finite forms but no -(u)v / -(u)vchi: uquvchi is oʻquvchi without the ʻ
    t=sub1("uq:uq V-IV ; ! 0.9999268838228939\n","uq:uq V-IV-NOUV ; ! 0.9999268838228939 ! v4 F2: no -uv/-uvchi (uquvchi = oʻquvchi typo)\n",t)
    nf=re.search(r'LEXICON NON-FINITE\n.*?(?=\nLEXICON )',t,re.S).group(0)
    ge=re.search(r'LEXICON GERUND \n.*?(?=\nLEXICON )',t,re.S).group(0)
    vi=re.search(r'LEXICON VERB-INFL-COMMON\n.*?(?=\nLEXICON )',t,re.S).group(0)
    nf2=nf.replace('LEXICON NON-FINITE','LEXICON NON-FINITE-NOUV   ! v4 F2',1)
    nf2='\n'.join(l for l in nf2.split('\n') if '%{U%}' not in l)
    ge2=ge.replace('LEXICON GERUND ','LEXICON GERUND-NOUV   ! v4 F2',1)
    ge2='\n'.join(l for l in ge2.split('\n') if '%{U%}' not in l)
    vi2=vi.replace('LEXICON VERB-INFL-COMMON','LEXICON VERB-INFL-NOUV   ! v4 F2',1).replace('NON-FINITE ;','NON-FINITE-NOUV ;').replace('GERUND ;','GERUND-NOUV ;')
    block=("\n\nLEXICON V-IV-NOUV   ! v4 F2\n%<v%>%<iv%>: VERB-INFL-NOUV ;\n%<v%>%<iv%>%<coop%>:%>%{i%}sh VERB-INFL-NOUV ;\n\n"
           +vi2+"\n\n"+nf2+"\n\n"+ge2+"\n")
    t=sub1("\nLEXICON VERB-INFL-COMMON\n",block+"\nLEXICON VERB-INFL-COMMON\n",t)
    # F3: junk auto-added verbs that are typos of real verbs (lost ʻ): tupla (toʻpla), tugdir (tugʻdir)
    for old in ("tupla:tupla V-TV ; ! 0.9916869234680692\n","tugdir:tugdir V-TV-CAUS ; ! 0.9999999988134235\n"):
        t=sub1(old,"! v4 F3 removed junk entry (typo of a ʻ verb): "+old,t)
    # F4: ye- converb is yeya, not yey (yey is an exclamation): {й} surfaces before a word-final {E}
    tw=sub1("%{й%}:y <=> _ (%[%-coop%]:0) %>: [ %{i%}: [ :s :h | %{L%}: ] | %{U%}: ] ;\n",
            "%{й%}:y <=> _ (%[%-coop%]:0) %>: [ %{i%}: [ :s :h | %{L%}: ] | %{U%}: ] ;\n"
            "        .#. y: e: _ %>: %{E%}: .#. ; ! v4 F4: ye+{E} converb = yeya, not *yey\n",tw)
if a.lemmas:
    rows=list(csv.DictReader(open(a.lemmas,encoding='utf-8'),delimiter='\t'))
    out=["","LEXICON V4-Additions   ! v4: lemmas added from triage_top2000 (AI proposals, see phase2/lemmas_v4.tsv)",""]
    for r in rows:
        g=r.get('gloss','').replace('"',"'").replace('!','')
        for surf in r['surface'].split('|'):
            dl=' ! Dir/LR' if surf.endswith('@DirLR') else ''
            surf=surf.replace('@DirLR','')
            out.append(f"{r['lemma']}:{surf} {r['paradigm']} ; ! \"{g}\" ! v4 add{dl}{(' ! '+r['flag']) if r.get('flag') else ''}")
    t=sub1("LEXICON Root\n\n","LEXICON Root\n\nV4-Additions ; ! v4\n",t)
    t=t.rstrip('\n')+'\n'+'\n'.join(out)+'\n'
open(L,'w',encoding='utf-8').write(t);open(T,'w',encoding='utf-8').write(tw)
print('applied',a.dst)

#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""v5 changes on top of apply_v4.py output (run apply_v4.py ... --lemmas lemmas_v4.tsv first).
F5 exact-duplicate lexc entries commented out; F6 junk verbs bula/ut removed (frequent typo forms kept as <mistake>), oq without -uv/-uvchi;
F7 haqidagi / toʻgʻrisidagi = postposition + attributive -gi; F8 de- converb generates deya (dey kept analysis-only);
F9 topta (in lemmas_v5); F10 elidable stem vowel {ı}: bagʻir -> bagʻri, ogʻiz -> ogʻzi; F11 junk noun itarmoq removed (itar- verb added);
--lemmas lemmas_v5.tsv adds LEXICON V5-Additions."""
import sys,re,csv,json,argparse,os
ap=argparse.ArgumentParser();ap.add_argument('dst');ap.add_argument('--lemmas');a=ap.parse_args()
assert 'apertium-uzb-v4' in a.dst or 'scratch' in a.dst
L=os.path.join(a.dst,'apertium-uzb.uzb.lexc');T=os.path.join(a.dst,'apertium-uzb.uzb.twol')
t=open(L,encoding='utf-8').read();tw=open(T,encoding='utf-8').read()
def sub1(old,new,s):
    assert s.count(old)==1,(old,s.count(old));return s.replace(old,new)
# F5 exact duplicates (same upper:lower, continuation and Dir/LR status) -> comment out
ent=re.compile(r'^([^!%\s][^\s:]*):(\S+)\s+(\S+)\s*;(.*)$')
seen=set();lines=t.split('\n');nd=0;cur=None
for i,l in enumerate(lines):
    if l.startswith('LEXICON '): cur=l.split()[1];continue
    m=ent.match(l)
    if not m: continue
    k=(cur,m.group(1),m.group(2),m.group(3),'Dir/LR' in m.group(4))
    if k in seen: lines[i]='! v5 F5 duplicate: '+l;nd+=1
    else: seen.add(k)
t='\n'.join(lines)
# F6 junk verbs
for old in ('bula:bula VERB-TV ; ! "to dip in"\n','bula:bula V-TV ; ! \n'):
    if old in t: t=sub1(old,'! v5 F6 removed (forms are boʻl- typos: buladi 187k): '+old,t)
t=sub1('ut:ut V-TV-CAUS ; ! 0.8611835339953186\n','! v5 F6 removed (forms are oʻt-/yut- typos: utgan, utib, utish): ut:ut V-TV-CAUS ; ! 0.8611835339953186\n',t)
t=sub1('oq:oq VERB-IV ; !\n','oq:oq V-IV-NOUV ; ! v5 F6: no -uv/-uvchi (oquvchi = oʻquvchi typo)\n',t)
mist=json.load(open('work/morph/phase2/v5_mist_forms.json',encoding='utf-8'))
# F11 junk noun
t=sub1('itarmoq:itarmoq N1 ; ! 0.7047097954615895\n','! v5 F11 removed junk noun (infinitive of itar-): itarmoq:itarmoq N1 ; ! 0.7047097954615895\n',t)
# F10 elidable vowel symbol
t=sub1('%{й%}         !\n','%{й%}         !\n%{ı%}         ! v5 F10: elidable stem vowel (bagʻir/bagʻri, ogʻiz/ogʻzi)\n',t)
t=sub1('bagʻir:bagʻir N1 ; ! "bosom, breast; liver" ! v4 add ! elided stem bagʻr (analysis only)\n','bagʻir:bagʻ%{ı%}r N1 ; ! "bosom, breast; liver" ! v4 add ! v5 F10 elidable vowel\n',t)
t=sub1('bagʻir:bagʻr N1 ; ! "bosom, breast; liver" ! v4 add ! Dir/LR ! elided stem bagʻr (analysis only)\n','! v5 F10 replaced by {ı}: bagʻir:bagʻr N1 Dir/LR\n',t)
t=sub1('ogʻiz:ogʻiz N1 ; ! 0.9996553807436519\n','ogʻiz:ogʻ%{ı%}z N1 ; ! 0.9996553807436519 ! v5 F10 elidable vowel\nogʻiz:ogʻiz N1 ; ! Dir/LR ! v5 F10 unelided spelling (ogʻizi) kept for analysis\n',t)
for old in ('ogʻiz:ogʻiz N1 ; ! 0.9999963500658771\n','ogʻiz:ogʻiz N1 ; ! "mouth"\n'):
    t=sub1(old,'! v5 F10 duplicate of ogʻiz: '+old,t)
tw=sub1(' %{a%}:a\n',' %{a%}:a\n %{ı%}:i %{ı%}:0 ! v5 F10\n',tw) if ' %{a%}:a\n' in tw else sub1('%{a%}:a\n','%{a%}:a\n%{ı%}:i %{ı%}:0 ! v5 F10\n',tw)
tw=sub1('\nRules\n','\nRules\n\n"{ı} (elidable stem vowel: bagʻir, ogʻiz) is dropped before a vowel-initial suffix (v5 F10)"\n%{ı%}:0 <=> _ :Cons %>: [ :0 ]* :Vow ;\n',tw)
# F8 de- converb: deya (like ye -> yeya); dey analysis-only
tw=sub1('        .#. y: e: _ %>: %{E%}: .#. ; ! v4 F4: ye+{E} converb = yeya, not *yey\n','        .#. [ y: | d: ] e: _ %>: %{E%}: .#. ; ! v4 F4 + v5 F8: ye+{E} = yeya, de+{E} = deya (not *yey, *dey)\n',tw)
add=["","LEXICON V5-Additions   ! v5: fixes + lemmas verified from the batch-1 spot-check and uz.wikipedia (see phase2/lemmas_v5.tsv)","",
 "de%<v%>%<tv%>%<prc_impf%>:dey # ; ! Dir/LR ! v5 F8 colloquial dey kept for analysis; generator gives deya",
 "haqida%<post%>%<attr%>:haqidagi # ; ! v5 F7 haqidagi = haqida<post> + -gi (was haq<n><px3sp><loc><attr> only)",
 "toʻgʻrisida%<post%>%<attr%>:toʻgʻrisidagi # ; ! v5 F7"]
for v,forms in mist.items():
    for c,w in forms: add.append(f"{w}:{w} MIST ; ! Dir/LR ! v5 F6 typo form ({v}- verb removed/restricted), {c} uses")
if a.lemmas:
    for r in csv.DictReader(open(a.lemmas,encoding='utf-8'),delimiter='\t'):
        add.append(f"{r['lemma']}:{r['surface']} {r['paradigm']} ; ! v5 add ! {r['category']} ! {r['flag']}")
t=sub1("V4-Additions ; ! v4\n","V4-Additions ; ! v4\nV5-Additions ; ! v5\n",t)
t=t.rstrip('\n')+'\n'+'\n'.join(add)+'\n'
open(L,'w',encoding='utf-8').write(t);open(T,'w',encoding='utf-8').write(tw)
print('v5 applied; duplicates commented',nd,'additions',len(add)-3)

# SPDX-License-Identifier: GPL-3.0-only
"""Token coverage of a dictionary build, alone and with the guesser (confident / all guesses).
Usage: guesser_coverage.py TAG GUESSER_BIN [OUT.json]
  TAG: a build whose lt-proc outputs over the word-frequency types exist in work/verify (see ../regression/covlib.py)
A type unknown to the dictionary in every casing counts as covered if the guesser analyses every unit of it and
uzmorph.guesser.rank() returns a guess (confident: default rule; all: all_=True). Coverage is token-weighted over the
uz-books-v2 word-frequency list (types with >=3 uses), exactly as covlib.figures().
Anchoring: figures are also reported "anchored": each figure is shifted by a constant so that upstream apertium-uzb
00522e3 reads as in the first survey, which used an earlier version of this measurement (upstream raw values from
dictionary_coverage.py: all 86.151, clean 88.634, all_nomist 84.960, clean_nomist 88.521; survey: 87.51 / 88.21 / 86.42 / 88.12).
The headline number is 'all' (offset +1.359)."""
import sys,re,json,subprocess,os
sys.path.insert(0,'work/verify'); import covlib
from uzmorph import guesser
LU=re.compile(r'\^((?:\\.|[^$\\])*)\$'); SPLIT=re.compile(r'(?<!\\)/')
ANCHOR=dict(all=87.51-86.151,clean=88.21-88.634,all_nomist=86.42-84.960,clean_nomist=88.12-88.521)
tag,gbin=sys.argv[1],sys.argv[2]
st=covlib.load(tag); W=covlib.BASE['words']
unk=[i for i in range(len(W)) if all(st[k][i]=='U' for k in ('lower','title','upper'))]
out=subprocess.run(['lt-proc','-w',gbin],input='\n'.join(W[i] for i in unk)+'\n',capture_output=True,text=True,check=True).stdout.split('\n')
conf=set(); allg=set()   # type indices covered by the confident / unfiltered guesser
for i,l in zip(unk,out):
    lus=LU.findall(l); ok_c=ok_a=bool(lus)
    for x in lus:
        s,*rs=SPLIT.split(x)
        if not rs or rs[0].startswith('*'): ok_c=ok_a=False; break
        if any('<guess>' in r for r in rs):
            ok_c=ok_c and guesser.rank(s,rs,False) is not None
            ok_a=ok_a and guesser.rank(s,rs,False,all_=True) is not None
    if ok_c: conf.add(i)
    if ok_a: allg.add(i)
def fig(S):
    s={k:list(v) for k,v in st.items()}
    for i in S:
        for k in s:
            if s[k][i]=='U': s[k][i]='K'
    f=covlib.figures(s); return dict(raw={k:round(v,3) for k,v in f.items() if k!='known_tokens'},anchored={k:round(v+ANCHOR[k],2) for k,v in f.items() if k!='known_tokens'})
res=dict(tag=tag,unknown_types=len(unk),dictionary=fig(set()),confident=dict(types=len(conf),**fig(conf)),all_guesses=dict(types=len(allg),**fig(allg)))
print(json.dumps(res,indent=1))
if len(sys.argv)>3: json.dump(res,open(sys.argv[3],'w',encoding='utf-8'),indent=1)

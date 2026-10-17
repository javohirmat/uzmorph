# SPDX-License-Identifier: GPL-3.0-only
"""Acceptance of non-words. accept = analyzer returns >=1 known analysis. -> ../nonsense/results.json/.md"""
import json,os,re,subprocess,sys
from collections import Counter,defaultdict
B=os.path.join(os.path.dirname(__file__),'..'); N=B+'/nonsense'
A='work/morph/apertium-uzb-v4'; GW='work/morph/phase2/guesser/uzb_guess.py'
REAL={'boshqarmamoqda'}   # generator false positive: boshqar+ma+moqda is a real form
W=[x for x in (l.rstrip('\n').split('\t') for l in open(f'{N}/nonwords.tsv',encoding='utf-8')) if x[0]!='word' and x[0] not in REAL]
words=[w for w,_,_ in W]
def run(cmd): return subprocess.run(cmd,input='\n'.join(words)+'\n',capture_output=True,text=True).stdout.split('\n')[:len(words)]
ours=run(['lt-proc','-w',f'{A}/uzb.automorf.bin']); g=run(['python3',GW]); ga=run(['python3',GW,'--all'])
known=lambda line: bool(line) and '/*' not in line and '/' in line
zp=subprocess.run([f'{B}/tools/venv/bin/python','-c','''
import sys,json
from zirhuzmorph import Analyzer
an=Analyzer(); out=[]
for w in sys.stdin.read().split():
    rs=an.analyze(w); out.append(dict(known=any(a.known for a in rs),top_known=bool(rs and rs[0].known),top=rs[0].tagged() if rs else ""))
print(json.dumps(out))'''],input='\n'.join(words),capture_output=True,text=True)
Z=json.loads(zp.stdout)
rows=[];agg=defaultdict(Counter)
for (w,t,_),o,gg,gga,z in zip(W,ours,g,ga,Z):
    r=dict(word=w,type=t,ours=known(o),ours_guess=known(gg),ours_guess_all=known(gga),zirh_any_known=z['known'],zirh_top_known=z['top_known'],ours_analysis=o,zirh_top=z['top'])
    rows.append(r)
    for k in ('ours','ours_guess','ours_guess_all','zirh_any_known','zirh_top_known'):
        agg['ALL'][k]+=r[k]; agg[t][k]+=r[k]
    agg['ALL']['n']+=1; agg[t]['n']+=1
json.dump(rows,open(f'{N}/results.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
K=('ours','ours_guess','ours_guess_all','zirh_any_known','zirh_top_known')
L=['# Nonsense acceptance (lower is better). 299 non-words (300 generated, 1 real form removed), 0 hits in a 10.5M-type corpus frequency list.','',
   '| type | n | '+' | '.join(K)+' |','|'+'---|'*(len(K)+2)]
for t in ['ALL']+sorted(k for k in agg if k!='ALL'):
    a=agg[t]; L.append(f"| {t} | {a['n']} | "+' | '.join(f"{100*a[k]/a['n']:.0f}%" for k in K)+' |')
L+=['','Notes: boshqarmamoqda removed (real form). In case_before_pl, -dan+lar (3 words) and arguably -ning+lar (8) can be predicative plurals ("ular Toshkentdanlar"); -ni+lar and -ga+lar (19) cannot - Zirh accepts all 19 as PRED.PL. ours_guess_all guesses for any unknown string by design, so it is not a rejection test.']
open(f'{N}/results.md','w',encoding='utf-8').write('\n'.join(L)); print('\n'.join(L))

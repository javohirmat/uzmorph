# SPDX-License-Identifier: GPL-3.0-only
"""Nonsense acceptance after phase 3: v8d vs v9 (apertium-uzb-v5), alone and with the confident guesser, plus the phase-3
proper-noun layer on the Capitalised non-words. Zirh numbers are unchanged (see results.md). -> ../nonsense/results_v9.json/.md"""
import json,os,subprocess,sys
from collections import Counter,defaultdict
sys.path.insert(0,'work/morph/phase3'); import names as NM
B=os.path.join(os.path.dirname(__file__),'..'); N=B+'/nonsense'; GW='work/morph/phase2/guesser/uzb_guess.py'
REAL={'boshqarmamoqda'}
W=[x for x in (l.rstrip('\n').split('\t') for l in open(f'{N}/nonwords.tsv',encoding='utf-8')) if x[0]!='word' and x[0] not in REAL]
words=[w for w,_,_ in W]
def run(cmd,ws): return subprocess.run(cmd,input='\n'.join(ws)+'\n',capture_output=True,text=True).stdout.split('\n')[:len(ws)]
known=lambda line: bool(line) and '/*' not in line and '/' in line
cols={}
for tag,d in (('v8d','apertium-uzb-v4'),('v9','apertium-uzb-v5')):
    A=f'work/morph/{d}'
    cols[tag]=[known(x) for x in run(['lt-proc','-w',f'{A}/uzb.automorf.bin'],words)]
    cols[f'{tag}+guess']=[known(x) for x in run(['python3',GW,'--main',f'{A}/uzb.automorf.bin','--guesser',f'{A}/uzb_guesser.automorf.bin'],words)]
cap=[w[0].upper()+w[1:] for w in words]
capk=[known(x) for x in run(['lt-proc','-w','work/morph/apertium-uzb-v5/uzb.automorf.bin'],cap)]
cols['v9 Capitalised: analyzer + verified name list']=[k or bool(NM.listed(c)) for k,c in zip(capk,cap)]
cols['v9 Capitalised mid-sentence: + name guesser']=[k or bool(NM.guess_hyph(c)) for k,c in zip(capk,cap)]
agg=defaultdict(Counter)
for i,(w,t,_) in enumerate(W):
    for k,v in cols.items(): agg['ALL'][k]+=v[i]; agg[t][k]+=v[i]
    agg['ALL']['n']+=1; agg[t]['n']+=1
K=list(cols)
json.dump({k:dict(a) for k,a in agg.items()},open(f'{N}/results_v9.json','w',encoding='utf-8'),indent=1)
L=['# Nonsense acceptance after phase 3 (lower is better). Same 299 non-words as results.md (Zirh: 15% any-known, unchanged).','',
   '| type | n | '+' | '.join(K)+' |','|'+'---|'*(len(K)+2)]
for t in ['ALL']+sorted(k for k in agg if k!='ALL'):
    a=agg[t]; L.append(f"| {t} | {a['n']} | "+' | '.join(f"{100*a[k]/a['n']:.0f}%" for k in K)+' |')
L+=['','The proper-noun guesser accepts any capitalised unknown word in mid-sentence position by design (a fallback whose readings are marked <guess>), so its column is not a rejection test. Lower-case non-words never reach it. The verified name list accepted none of the non-words; the few Capitalised hits come from existing analyzer entries.']
open(f'{N}/results_v9.md','w',encoding='utf-8').write('\n'.join(L)+'\n'); print('\n'.join(L))

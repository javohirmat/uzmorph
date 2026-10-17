# SPDX-License-Identifier: GPL-3.0-only
"""Mine frequent capitalised unknown stems from the corpus (capstats; eval docs excluded) -> names_cand.tsv"""
import pickle,re,subprocess
from collections import defaultdict
import names as N
CAP,LO=N.CAP,N.LO
ws=[w for w,c in CAP.items() if c>=20 and c>=9*LO.get(w,0) and re.fullmatch(r"[a-zʻʼ'-]{3,}",w) and not w.startswith('-')]
cw=[w[0].upper()+w[1:] for w in ws]
out=subprocess.run(['lt-proc','-w','work/morph/apertium-uzb-v4/uzb.automorf.bin'],input='\n'.join(cw)+'\n',capture_output=True,text=True).stdout.strip().split('\n')
unk=[w for w,o in zip(cw,out) if '/*' in o and o.count('^')==1]
print('capitalised types',len(cw),'unknown',len(unk))
S=defaultdict(lambda:[0,set()])
for w in unk:
    g=N.guess_hyph(w)
    if not g: continue
    st=g[0][:g[0].find('<')]
    S[st][0]+=CAP[w.lower()]; S[st][1].add(w)
rows=sorted(((st,n,len(f),sorted(f)[:6]) for st,(n,f) in S.items() if n>=50 and len(st)>=3),key=lambda r:-r[1])
with open('names_cand.tsv','w',encoding='utf-8') as f:
    f.write('stem\ttokens\tnforms\tforms\n')
    for st,n,nf,fs in rows: f.write(f'{st}\t{n}\t{nf}\t{",".join(fs)}\n')
print('stems',len(rows)); print(rows[:30])

# SPDX-License-Identifier: GPL-3.0-only
import pickle,re
d=pickle.load(open('table.pkl','rb'))
HY=re.compile('[-‐‑–]')
def clean(k):
    core=HY.sub('',k).replace('ʻ','').replace('ʼ','')
    return len(core)>=3 and core.isalpha()
W,C,L,T,U,caps,mid,s3=d['words'],d['cnt'],d['low'],d['title'],d['upper'],d['caps'],d['mid'],d['s3']
n=0;a={k:0.0 for k in ['s3','lt','ltK','cc','ccK']}
for w,c,l,t,u,cp,m,s in zip(W,C,L,T,U,caps,mid,s3):
    if not clean(w): continue
    cc=c*(1-cp); n+=cc
    if s: a['s3']+=cc
    if l!='U' or t!='U': a['lt']+=cc
    if l=='K' or t=='K': a['ltK']+=cc
    a['cc']+= cc*(1-m)*(l!='U') + cc*m*(t!='U')
    a['ccK']+= cc*(1-m)*(l=='K') + cc*m*(t=='K')
print('clean tokens (types>=3)',f'{n:,.0f}')
for k,v in a.items(): print(k,f'{100*v/n:.2f}')

# SPDX-License-Identifier: GPL-3.0-only
import re,pickle,subprocess,os,sys
from parse import status
HY=re.compile('[-‐‑–]')
def clean(k):
    core=HY.sub('',k).replace('ʻ','').replace('ʼ','')
    return len(core)>=3 and core.isalpha()
BASE=pickle.load(open('work/verify/table.pkl','rb'))
CLEANMASK=[clean(w) for w in BASE['words']]
N=1463539297
def run(binary,tag,outdir='work/verify'):
    procs=[]
    for k,src in (('lower','words.txt'),('title','words_title.txt'),('upper','words_upper.txt')):
        out=f'{outdir}/{tag}_{k}.txt'
        if not os.path.exists(out+'.ok'):
            procs.append((subprocess.Popen(f'lt-proc -w {binary} < work/verify/{src} > {out} && touch {out}.ok',shell=True),k))
    for p,k in procs: p.wait()
    return load(tag,outdir)
def load(tag,outdir='work/verify'):
    pk=f'{outdir}/{tag}_status.pkl'
    if os.path.exists(pk): return pickle.load(open(pk,'rb'))
    d={k:[status(l) for l in open(f'{outdir}/{tag}_{k}.txt',encoding='utf-8')] for k in ('lower','title','upper')}
    pickle.dump(d,open(pk,'wb')); return d
def figures(st):
    C,caps,mid=BASE['cnt'],BASE['caps'],BASE['mid']
    L,T,U=st['lower'],st['title'],st['upper']
    a=aK=cl=clK=n=0.0
    for i in range(len(C)):
        c=C[i];cp=caps[i];m=mid[i];l=L[i];t=T[i];u=U[i];lp=c*(1-cp)
        a+=c*cp*(u!='U')+lp*(1-m)*(l!='U')+lp*m*(t!='U')
        aK+=c*cp*(u=='K')+lp*(1-m)*(l=='K')+lp*m*(t=='K')
        if CLEANMASK[i]:
            n+=lp; cl+=lp*(1-m)*(l!='U')+lp*m*(t!='U'); clK+=lp*(1-m)*(l=='K')+lp*m*(t=='K')
    return dict(all=100*a/N,clean=100*cl/n,all_nomist=100*aK/N,clean_nomist=100*clK/n,known_tokens=a)
def known_any(st,i): return st['lower'][i]!='U' or st['title'][i]!='U' or st['upper'][i]!='U'

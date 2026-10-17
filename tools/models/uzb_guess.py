#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Phase 4 guesser mode (separate from the main transducer).
Usage: echo "text" | apertium-destxt | uzb_guess.py   or   uzb_guess.py < one-word-per-line
Pipeline: lt-proc -w uzb.automorf.bin (main, unchanged); every LU it leaves unknown (^w/*w$) is sent to uzb_guesser.automorf.bin
(the upstream {🂡} stem-placeholder guesser, with the v8 stem pattern) and its readings are ranked by
  log P(tag sequence | known tokens) + 1.5 log(stem support in the corpus) + stem-ending plausibility - suffix-inside-stem penalty.
Output: the top reading(s) marked <guess>; --all keeps low-confidence guesses (default: confident only, else stays *unknown)."""
import sys,re,math,pickle,subprocess,argparse,os
D=os.path.dirname(os.path.abspath(__file__))
ap=argparse.ArgumentParser();ap.add_argument('--main',default='work/morph/apertium-uzb-v4/uzb.automorf.bin')
ap.add_argument('--guesser',default='work/morph/apertium-uzb-v4/uzb_guesser.automorf.bin')
ap.add_argument('--all',action='store_true');ap.add_argument('-n',type=int,default=1);a=ap.parse_args()
M=pickle.load(open(os.path.join(D,'guess_model.pkl'),'rb'));P,TOT,S,E=M['prior'],M['tot'],M['S'],M['E'];EN=E['_n']
COP0=re.compile(r'\+e<cop><aor><p3><(sg|pl)>')
SUFFIXY=('lar','lari','larin','ning','dagi','dan','ga','da','ni','si','miz','ingiz','im','lik')
FOREIGN=re.compile(r'w|c(?!h)|(ogo|ykh|aya|yye|skiy|skoy|skaya|tion|nnoy|ovna|ovich|evich|evna|iye)$')
norm=lambda t:COP0.sub('',t).replace('<iv>','<TD>').replace('<tv>','<TD>')
lp=lambda t:math.log((P.get(t,0)+1.0)/TOT)
def plaus(stem,pos): return math.log((E[pos].get(stem[-2:],0)+0.5)/(EN[pos]+200))-math.log(1/400)
def rank(surf,readings,cap):
    w=surf.lower();best=[]
    for r in readings:
        if '<guess>' not in r: continue
        k=r.find('<');stem=r[:k].lower();t=norm(r[k:].replace('<guess>',''));pos='v' if t.startswith('<v>') else 'n'
        if cap and pos=='v': continue        # capitalised mid-text: proper noun, nominal readings only
        if len(stem)>=len(w) or len(stem)<3: continue
        s=S.get((stem,pos),0)+(1 if pos=='n' and stem in M['bare'] else 0)
        if s<1: s=1
        best.append((lp(t)+1.5*math.log(s)+0.15*min(len(stem),10)+plaus(stem,pos)-(1.5 if stem.endswith(SUFFIXY) else 0)-(3 if '<vaux>' in t else 0),stem,t,s))
    sb=S.get((w,'n'),0)
    if sb>=3 and not any(x[3]>=sb for x in best): best.append((lp('<n><nom>')+1.5*math.log(sb)+0.15*min(len(w),10)+plaus(w,'n')-(1.5 if w.endswith(SUFFIXY) else 0),w,'<n><nom>',sb))
    best.sort(reverse=True)
    if not best: return None
    conf=best[0][3]>=2 and len(best[0][1])>=4 and '<vaux>' not in best[0][2] and not FOREIGN.search(w)
    if not conf and not a.all: return None
    out=[]
    for sc,stem,t,s in best[:a.n]:
        if cap: t=t.replace('<n>','<np>',1); stem=stem[:1].upper()+stem[1:]
        out.append(stem+t+'<guess>')
    return out
text=sys.stdin.read()
main=subprocess.run(['lt-proc','-w',a.main],input=text,capture_output=True,text=True).stdout
LU=re.compile(r'\^([^$]*)\$')
unk=sorted({m.group(1).split('/')[0] for m in LU.finditer(main) if '/*' in m.group(1)})
G={}
if unk:
    g=subprocess.run(['lt-proc','-w',a.guesser],input='\n'.join('^'+u+'$' if False else u for u in unk)+'\n',capture_output=True,text=True).stdout.split('\n')
    for u,l in zip(unk,g):
        m=LU.search(l)
        if m: G[u]=m.group(1).split('/')[1:]
def sub(m):
    x=m.group(1)
    if '/*' not in x: return m.group(0)
    surf=x.split('/')[0];r=rank(surf,G.get(surf,[]),surf[:1].isupper() and surf[1:2].islower())
    return '^'+surf+'/'+'/'.join(r)+'$' if r else m.group(0)
sys.stdout.write(LU.sub(sub,main))

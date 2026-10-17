# SPDX-License-Identifier: GPL-3.0-only
"""Apply the phase3 ranker to the eval sentences and score top-1 on dev (or test). Usage: rank_eval.py dev|test [variant ...]"""
import json,os,sys,re
sys.path.insert(0,os.path.dirname(__file__)); sys.path.insert(0,'work/morph/phase3')
import scheme as S
from score import judge,G,C,EXCL,nf
from rank_lib import Ranker,rules,norm,rclass
B=os.path.join(os.path.dirname(__file__),'..')
O=json.load(open(f"{B}/private/ours{os.environ.get('SUF','')}.json",encoding='utf-8'))
SPLIT=json.load(open(f'{B}/split.json',encoding='utf-8'))['split']
SENT=[json.loads(l) for l in open(f'{B}/private/sentences.jsonl',encoding='utf-8')]
GK={g['key']:g for g in G}
def head(lus):
    """mirror scheme.ap_candidates: -> (surface, reads, prefix) or None"""
    if not lus: return None
    if len(lus)>=3 and lus[-2].split('/')[0]=='-' and lus[-1].split('/')[0].lower() in S.CLITICS: lus=lus[:-2]
    elif len(lus)>=2 and lus[-1].split('/')[0].lower() in ('-a','-ya'): lus=lus[:-1]   # hyphen-initial clitic unit (upstream transducers)
    prefix=''
    if len(lus)>1:
        prefix=''.join(l.split('/')[0] for l in lus[:-1])
        if lus[-2].split('/')[0]!='-': prefix+='-'
    surf,*reads=re.split(r'(?<!\\)/',lus[-1])
    if not reads or any(x.startswith('*') for x in reads): return None
    return surf,list(dict.fromkeys(norm(x) for x in reads)),prefix.lower()
VARIANTS={
 'cg':None,
 'prior':dict(ctx=0,opts=set()),
 'prior+sg':dict(ctx=0,opts={'sg_default'}),
 'prior+sg+lemma':dict(ctx=0,opts={'sg_default','real_lemma'}),
 'prior+sg+lemma+imp':dict(ctx=0,opts={'sg_default','real_lemma','imp_medial'}),
 'full(ctx=0.5)':dict(ctx=0.5,opts={'sg_default','real_lemma','imp_medial'}),
 'full(ctx=1)':dict(ctx=1.0,opts={'sg_default','real_lemma','imp_medial'}),
 'ctx-only(1)+prior':dict(ctx=1.0,opts=set()),
}
RK=Ranker(ctx=True)
import pickle,numpy as np,math
from hmm import fb
HM=pickle.load(open('work/morph/phase3/hmm.pkl','rb')); HCI={c:i for i,c in enumerate(HM['cls'])}
VARIANTS['hmm+prior']=dict(hmm=1.0,ctx=0,opts=set())
VARIANTS['hmm+prior+sg']=dict(hmm=1.0,ctx=0,opts={'sg_default'})
VARIANTS['hmm+prior+sg+lemma+imp']=dict(hmm=1.0,ctx=0,opts={'sg_default','real_lemma','imp_medial'})
ALL={'sg_default','real_lemma','imp_medial','dup_lemma'}
VARIANTS['prior+sg+lemma+imp+dup']=dict(ctx=0,opts=ALL)
VARIANTS['full+dup(ctx=1)']=dict(ctx=1.0,opts=ALL)
VARIANTS['hmm+all']=dict(hmm=1.0,ctx=0,opts=ALL)
import names as NM
for k in list(VARIANTS):
    if k in('hmm+all','full+dup(ctx=1)'):
        VARIANTS[k+'+names']=dict(VARIANTS[k],names=1); VARIANTS[k+'+names2']=dict(VARIANTS[k],names=2)
BOUND=set('.!?…:;"«“(—–-')
def name_reading(toks,i,known,reads,level,have_guess=True,surf=None):
    w=toks[i]['lat']; gs=surf or w
    if not level or not w[:1].isupper(): return None
    acr=w.isupper() and len(w)>1
    medial=any(t['word'] for t in toks[:i]) and toks[i-1]['lat'] not in BOUND
    c,ratio=NM.capratio(w)
    if not known and level>=1:
        l=NM.listed(gs)
        if l: return l
    if not known:
        if (medial and not acr) or (c>=3 and ratio>=0.5) or (acr and level>=1) or not have_guess:
            g=NM.guess_hyph(gs); return g[0] if g else None
    elif level>=2 and medial and c>=20 and ratio>=0.9 and not any('<np>' in r for r in reads):
        g=NM.guess_hyph(gs); return g[0] if g else None
    return None
def hmm_post(margs):
    seq=[]
    for m in [{'P_sent':1.0}]+margs:
        m={c:p for c,p in m.items() if c in HCI} or {'UNK':1.0}
        z=sum(m.values()); seq.append((np.array([HCI[c] for c in m]),np.array([p/z for p in m.values()])))
    start=np.zeros(len(HCI)); start[HCI['P_sent']]=1
    post,_=fb(seq,HM['A'],HM['pi'],start)
    return [{HM['cls'][j]:p for j,p in zip(seq[t][0],post[t])} for t in range(1,len(seq))]
def rank_sentence(s,script,cfg,use_guess=True):
    # surfaces as the analyzer saw them (Cyrillic / 2026-Latin are transliterated to Latin first)
    toks=[dict(t,lat=O[script].get(f"{s['id']}:{t['i']}",{}).get('input',t['lat'])) for t in s['tokens']]; H=[]
    for t in toks:
        o=O[script][f"{s['id']}:{t['i']}"]
        h=head(o['lus'])
        if h is None and use_guess: h=head(o['guess'])
        H.append(h)
    margs=[RK.marg(h[1]) if h else ({'P_sent':1.0} if t['lat'] in '.!?…' else {'P_other' if not t['word'] else 'UNK':1.0}) for h,t in zip(H,toks)]
    out={}; HP=hmm_post(margs) if cfg.get('hmm') else None
    for i,(t,h) in enumerate(zip(toks,H)):
        if not t['word']: continue
        if not h:
            nr=name_reading(toks,i,False,[],cfg.get('names',0),have_guess=False)
            if nr:
                m=S.map_ap_reading(nr,''); out[f"{s['id']}:{t['i']}"]=[m[0],m[1],S.fstr(m[2])]
            continue
        surf,reads,prefix=h
        nxt=toks[i+1]['lat'] if i+1<len(toks) else None
        pm=margs[i-1] if i>0 else {'P_sent':1.0}; nm=margs[i+1] if i+1<len(toks) else {'P_sent':1.0}
        o=O[script][f"{s['id']}:{t['i']}"]
        nr=name_reading(toks,i,head(o['lus']) is not None,reads,cfg.get('names',0),surf=surf if prefix else None)
        if nr:
            m=S.map_ap_reading(nr,prefix); out[f"{s['id']}:{t['i']}"]=[m[0],m[1],S.fstr(m[2])]; continue
        if HP:
            pr={r:RK.prior(r) for r in reads}; cz={}
            for r in reads: cz.setdefault(rclass(r),[]).append(pr[r])
            lz={c:max(v)+math.log(sum(math.exp(x-max(v)) for x in v)) for c,v in cz.items()}
            sc=lambda r:(1-cfg['hmm'])*pr[r]+cfg['hmm']*(math.log(max(HP[i].get(rclass(r),HP[i].get('UNK',1e-9)),1e-12))+pr[r]-lz[rclass(r)])+rules(r,t['lat'],reads,nxt,cfg['opts'])
            best=max(reads,key=lambda r:(sc(r),-reads.index(r)))
        else: best=max(reads,key=lambda r:(RK.prior(r)+cfg['ctx']*RK.ctx(rclass(r),pm,nm)+rules(r,t['lat'],reads,nxt,cfg['opts']), -reads.index(r)))
        m=S.map_ap_reading(best,prefix)
        if m: out[f"{s['id']}:{t['i']}"]=[m[0],m[1],S.fstr(m[2])]
    return out
def evaluate(part,variant,script='lat',use_guess=True):
    cfg=VARIANTS[variant]; best={}
    if cfg is not None:
        for s in SENT:
            if SPLIT.get(s['id'])==part: best.update(rank_sentence(s,script,cfg,use_guess))
    n=0; acc={m:0 for m in ('lemma','upos','coarse','feats','lf','full')}
    for g in G:
        sid=g['key'].split(':')[0]
        if SPLIT.get(sid)!=part or set(g['flags'].split(','))&EXCL: continue
        n+=1; v=C[script][g['key']]
        if cfg is None:
            b=(v['ours_cg'] or v['ours'][:1]) if v['ours_known'] else (v['guess'][:1] if use_guess else [])
            b=b[0] if b else None
        else: b=best.get(g['key'])
        if b is None: continue
        j=judge(b,g)
        for m in acc: acc[m]+=j[m]
    return n,{m:round(100*a/n,1) for m,a in acc.items()}
if __name__=='__main__':
    part=sys.argv[1]; vs=sys.argv[2:] or list(VARIANTS)
    for v in vs:
        n,a=evaluate(part,v); print(f'{v:24s} n={n} '+' '.join(f'{k}={x}' for k,x in a.items()))

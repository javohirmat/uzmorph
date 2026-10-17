# SPDX-License-Identifier: GPL-3.0-only
"""Corpus-trained reading ranker (no gold data used in training).
score(r) = log θ(tag sequence) + log φ(lemma+POS) + λ·context(class bigrams) + rule penalties.
θ, φ: EM over unambiguous+ambiguous corpus tokens; context: reading-class bigrams; rules: see `rules`."""
import re,math
from .models import load
ZC=re.compile(r'\+e<cop><aor><p3>(?:<frm>)?<(?:sg|pl)>')
def norm(r): return ZC.sub('',r.replace('\\',''))
def key(r):
    k=r.find('<'); lem=r[:k]; tags=r[k:]
    m=re.match(r'<[^>]+>',tags); pos=m.group(0) if m else ''
    return lem.lower()+pos, tags
CASES=('nom','acc','gen','dat','loc','abl')
def rclass(r):
    """coarse reading class used by the context model"""
    tags=re.findall(r'<([^>]+)>',r.split('+')[0])
    if not tags: return 'X'
    p=tags[0]; ts=set(tags)
    if p in('n','np','prn','adj','num','det'):
        if p=='adj' and 'subst' not in ts and not ts&set(CASES[1:]): return 'adj'
        c=next((t for t in tags if t in CASES),'nom' if p!='det' else '')
        return f'{p}_{c}' if p in('n','np','prn') else (p if c in('nom','') else f'{p}_{c}')
    if p in('v','vaux'):
        if ts&{'imp','opt'}: return 'v_imp'
        if any(t.startswith('gpr') for t in tags): return 'v_part'
        if any(t.startswith('ger') for t in tags): return 'v_ger_'+next((t for t in tags if t in CASES),'nom')
        if any(t.startswith(('prc','gna_perf','gna_when','gna_until','gna_neg')) for t in tags): return 'v_conv'
        if 'gna_cond' in ts: return 'v_cond'
        return 'v_fin'
    if p=='cop': return 'cop'
    if p in('sent','cm','guio','lquot','rquot','lpar','rpar','apos','quot'): return 'P_'+('sent' if p=='sent' else 'other')
    return p
PL3=('dilar','tilar','sinlar','ganlar','qanlar','kanlar','dalar','rlar','chilar','tirlar','yaptilar','ishdi','ishadi','ishgan',
     'ishyapti','ishmoqda','moqdalar','adilar','ydilar','ishsin','ishar')
INFL=re.compile(r'<(?:px\w+|acc|gen|dat|loc|abl|ger\w*)>')
DEFAULT_RULES=frozenset({'sg_default','real_lemma','imp_medial','dup_lemma'})
class Ranker:
    def __init__(self,ctx_weight=1.0,rules=DEFAULT_RULES):
        d=load('priors.json.gz'); self.th=d['theta']; self.ph=d['phi']; self.ft=d['floor_t']; self.ff=d['floor_f']
        c=load('context.json.gz'); self.B={(a,b):v for a,b,v in c['p']}; self.uni=c['uni']; self.fl=c['floor']
        self.PU=load('paradigm.json.gz'); self.w=ctx_weight; self.opts=set(rules)
    def prior(self,r):
        l,t=key(r); return math.log(self.th.get(t,self.ft))+math.log(self.ph.get(l,self.ff))
    def marg(self,reads):
        """class distribution of a token under the priors"""
        if not reads: return {'UNK':1.0}
        sc=[self.prior(r) for r in reads]; m=max(sc); ps=[math.exp(s-m) for s in sc]; z=sum(ps); out={}
        for r,p in zip(reads,ps): c=rclass(r); out[c]=out.get(c,0)+p/z
        return out
    def ctx(self,c,prevm,nextm):
        B,fl,uni=self.B,self.fl,self.uni
        lp=math.log(sum(pm*B.get((cp,c),fl) for cp,pm in prevm.items()) or fl)
        ln=math.log(sum(nm*B.get((c,cn),fl)/max(uni.get(cn,fl),fl) for cn,nm in nextm.items()) or fl)
        return lp+ln
    def rules(self,r,surf,reads,nxt):
        """principled penalties (log space)"""
        o=self.opts; pen=0.0; s=surf.lower(); main=r.split('+')[0]; tags=re.findall(r'<([^>]+)>',main); lem=main[:main.find('<')].lower()
        # 3pl subject agreement is optional in Uzbek: prefer singular unless the form carries an overt plural ending
        if 'sg_default' in o and 'p3' in tags and 'pl' in tags and tags[0] in('v','vaux','cop') and not s.endswith(PL3): pen-=20
        # a 1sg/2sg-possessive reading whose lemma is a prefix of the word loses if the word itself is a lemma
        if 'real_lemma' in o and ('px1sg' in tags or 'px2sg' in tags) and lem!=s and len(lem)<len(s):
            if any(norm(x).split('+')[0][:norm(x).find('<')].lower()==s for x in reads): pen-=20
        # imperative/optative 2nd person is unlikely sentence-medially
        if 'imp_medial' in o and ('imp' in tags or 'opt' in tags) and 'p2' in tags and nxt not in(None,'.','!','?','…','"','”','»'): pen-=6
        if 'dup_lemma' in o: pen+=self.dup_lemma_pen(r,reads)
        return pen
    def dup_lemma_pen(self,r,reads,ratio=3):
        """a noun lemma with almost no corpus types of its own loses to an inflected reading of a well-attested lemma
        (e.g. shahri<n><loc> vs shahar<n><px3sp><loc>)"""
        PU=self.PU; ka,_=key(r.split('+')[0])
        if not ka.endswith('<n>'): return 0.0
        pa=PU.get(ka,0)
        for x in reads:
            mx=x.split('+')[0]; kb,_=key(mx)
            if kb!=ka and INFL.search(mx) and PU.get(kb,0)>=ratio*(pa+1): return -10.0
        return 0.0
    def score(self,r,surf,reads,nxt,pm,nm):
        return self.prior(r)+self.w*self.ctx(rclass(r),pm,nm)+self.rules(r,surf,reads,nxt)
    def rank(self,surf,reads,nxt,pm,nm):
        """-> [(reading, score)] best first; ties keep analyzer order"""
        sc=[(r,self.score(r,surf,reads,nxt,pm,nm)) for r in reads]
        return [x for _,x in sorted(enumerate(sc),key=lambda z:(-z[1][1],z[0]))]

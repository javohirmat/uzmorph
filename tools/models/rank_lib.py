# SPDX-License-Identifier: GPL-3.0-only
"""Corpus-trained reading ranker for v8d (no gold data used in training).
score(r) = log θ(tagseq) + log φ(lemma+pos) + w_ctx·context + rule penalties."""
import re,math,pickle,os
D=os.path.dirname(os.path.abspath(__file__))
ZC=re.compile(r'\+e<cop><aor><p3>(?:<frm>)?<(?:sg|pl)>')
def norm(r): return ZC.sub('',r.replace('\\',''))
def key(r):
    k=r.find('<'); lem=r[:k]; tags=r[k:]
    m=re.match(r'<[^>]+>',tags); pos=m.group(0) if m else ''
    return lem.lower()+pos, tags
CASES=('nom','acc','gen','dat','loc','abl')
def rclass(r):
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
class Ranker:
    def __init__(self,ctx=True):
        d=pickle.load(open(f'{D}/priors.pkl','rb'))
        self.th=d['theta']; self.ph=d['phi']; self.ft=d['floor_t']; self.ff=d['floor_f']
        self.bi=pickle.load(open(f'{D}/context.pkl','rb')) if ctx and os.path.exists(f'{D}/context.pkl') else None
    def prior(self,r):
        l,t=key(r); return math.log(self.th.get(t,self.ft))+math.log(self.ph.get(l,self.ff))
    def marg(self,reads):
        """class distribution of a token from priors"""
        if not reads: return {'UNK':1.0}
        sc=[self.prior(r) for r in reads]; m=max(sc); ps=[math.exp(s-m) for s in sc]; z=sum(ps)
        out={}
        for r,p in zip(reads,ps): c=rclass(r); out[c]=out.get(c,0)+p/z
        return out
    def ctx(self,c,prevm,nextm):
        if not self.bi: return 0.0
        B=self.bi['p']; fl=self.bi['floor']
        lp=math.log(sum(pm*B.get((cp,c),fl) for cp,pm in prevm.items()) or fl)
        ln=math.log(sum(nm*B.get((c,cn),fl)/max(self.bi['uni'].get(cn,fl),fl) for cn,nm in nextm.items()) or fl)
        return lp+ln
PL3=('dilar','tilar','sinlar','ganlar','qanlar','kanlar','dalar','rlar','chilar','tirlar','yaptilar','ishdi','ishdi','ishadi','ishgan','ishyapti','ishmoqda','yaptilar','moqdalar','adilar','ydilar','ishsin','ishar')
def rules(r,surf,reads,nxt,opts):
    """principled penalties (log-space); opts = set of enabled rule names"""
    pen=0.0; s=surf.lower(); main=r.split('+')[0]; tags=re.findall(r'<([^>]+)>',main); lem=main[:main.find('<')].lower()
    if 'sg_default' in opts and 'p3' in tags and 'pl' in tags and tags[0] in('v','vaux','cop') and not s.endswith(PL3):
        pen-=20
    if 'real_lemma' in opts and ('px1sg' in tags or 'px2sg' in tags) and lem!=s and len(lem)<len(s):
        if any(norm(x).split('+')[0][:norm(x).find('<')].lower()==s for x in reads): pen-=20
    if 'imp_medial' in opts and ('imp' in tags or 'opt' in tags) and 'p2' in tags and nxt not in(None,'.','!','?','…','"','”','»'):
        pen-=6
    return pen
_PU=None
INFL=re.compile(r'<(?:px\w+|acc|gen|dat|loc|abl|ger\w*)>')
def dup_lemma_pen(r,reads,ratio=3):
    """corpus-paradigm rule: a noun lemma with almost no corpus types of its own (PU = types it alone explains)
    loses to an inflected reading of another lemma whose paradigm is well attested (e.g. shahri<n><loc> vs shahar<n><px3sp><loc>)."""
    global _PU
    if _PU is None: _PU=pickle.load(open(f'{D}/paradigm.pkl','rb'))['PU']
    main=r.split('+')[0]; ka,_=key(main)
    if not ka.endswith('<n>'): return 0.0
    pa=_PU.get(ka,0)
    for x in reads:
        mx=x.split('+')[0]; kb,_=key(mx)
        if kb!=ka and INFL.search(mx) and _PU.get(kb,0)>=ratio*(pa+1): return -10.0
    return 0.0
_rules0=rules
def rules(r,surf,reads,nxt,opts):
    p=_rules0(r,surf,reads,nxt,opts)
    if 'dup_lemma' in opts: p+=dup_lemma_pen(r,reads)
    return p
CLOSED={'prn','post','cnjcoo','cnjsub','cnjadv','det','postadv'}
def closed_pen(r,reads,with_adv=False):
    """a closed-class reading (pronoun, postposition, conjunction, determiner) of the word beats open-class noun readings"""
    tags=re.findall(r'<([^>]+)>',r.split('+')[0])
    if not tags or tags[0]!='n': return 0.0
    cl=CLOSED|({'adv'} if with_adv else set())
    if any((re.findall(r'<([^>]+)>',x.split('+')[0]) or [''])[0] in cl for x in reads): return -8.0
    return 0.0
def bare_ger_pen(r):
    """-gan/-adigan/-r forms as a bare nominative verbal noun without possessive are rare; prefer participle/finite"""
    m=r.split('+')[0]
    if re.search(r'<ger_(?:past|impf|fut|perf)><nom>',m) and '<px' not in m: return -3.0
    return 0.0
def voice_pen(r,reads,ratio=3):
    """X+n/l lexical verb vs base X<pass>: keep the passive analysis when the base verb's paradigm is much better attested"""
    global _PU
    if _PU is None: _PU=pickle.load(open(f'{D}/paradigm.pkl','rb'))['PU']
    m=r.split('+')[0]; k,_=key(m)
    if not k.endswith('<v>') or '<pass>' in m: return 0.0
    lem=k[:-3]
    for x in reads:
        mx=x.split('+')[0]; kb,_=key(mx)
        if '<pass>' in mx and kb.endswith('<v>') and lem.startswith(kb[:-3]) and len(lem)==len(kb)-3+1+(lem.endswith('il') or lem.endswith('in')):
            if _PU.get(kb,0)>=ratio*(_PU.get(k,0)+1): return -6.0
    return 0.0
_rules1=rules
def rules(r,surf,reads,nxt,opts):
    p=_rules1(r,surf,reads,nxt,opts)
    if 'closed' in opts: p+=closed_pen(r,reads)
    if 'closed_adv' in opts: p+=closed_pen(r,reads,True)
    if 'bare_ger' in opts: p+=bare_ger_pen(r)
    if 'voice' in opts: p+=voice_pen(r,reads)
    return p

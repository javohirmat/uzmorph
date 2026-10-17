# SPDX-License-Identifier: GPL-3.0-only
"""Analyzer: lt-proc (Apertium uzb v9.1) + confident guesser + proper-noun guesser + corpus ranker."""
import re,shutil,subprocess
from dataclasses import dataclass,field
from typing import List,Optional
from . import textlib,translit,ud,names,guesser
from .models import path
from .ranker import Ranker,norm
ESC=re.compile(r'([\\\[\]^$/@<>{}*+#])')
LU=re.compile(r'\^((?:\\.|[^$\\])*)\$')
SPLIT=re.compile(r'(?<!\\)/')
CYR=re.compile(r'[\u0400-\u04FF]')
BOUND=set('.!?…:;"«“(—–-')
@dataclass
class Reading:
    analysis: str            # Apertium reading of the head unit, e.g. kitob<n><px1sg><acc>
    lemma: str
    upos: str
    feats: str               # UD-style, e.g. Case=Acc|Poss=1Sg
    score: Optional[float]   # ranker score (log scale; None for name readings)
    source: str              # 'lexicon' | 'guesser' | 'names-list' | 'names-guess'
@dataclass
class Token:
    text: str                # surface as analysed (official Latin)
    sent: int                # sentence index
    is_word: bool
    known: bool              # recognised by the main dictionary
    readings: List[Reading]=field(default_factory=list)
    prefix: str=''           # earlier parts of a hyphenated token that are folded into the lemma
    @property
    def best(self): return self.readings[0] if self.readings else None
CTRL=re.compile('[\x00-\x08\x0e-\x1f\x7f\ufffe\uffff\r\ud800-\udfff]')   # removed (incl. lone surrogates)
VTFF=re.compile('[\x0b\x0c]')                                          # vertical tab, form feed -> space
def _ctrl(s): return CTRL.sub('',VTFF.sub(' ',s))
TAGS=re.compile(r'(?:<[A-Za-z0-9_]+>)+')
BADOUT=re.compile(r'[#@*\s]')
TIMEOUT=120          # seconds per lt-proc call
def _find_lt(lt_proc):
    exe=shutil.which(lt_proc)
    if not exe: raise RuntimeError("lt-proc not found: install lttoolbox (e.g. `apt install lttoolbox`) or pass lt_proc=")
    return exe
def _clean(x):
    """one lookup unit: control characters removed; whitespace inside is an error (it would desynchronise lt-proc's lines)"""
    x=_ctrl(x)
    if not x or any(c.isspace() for c in x): raise ValueError(f'lookup unit must be a single non-empty token without whitespace: {x!r}')
    return x
def _run(cmd,inp,timeout=TIMEOUT):
    try:
        return subprocess.run(cmd,input=inp,capture_output=True,text=True,encoding='utf-8',check=True,timeout=timeout).stdout
    except subprocess.TimeoutExpired:
        raise RuntimeError(f'{cmd[0]} did not answer within {timeout} s ({" ".join(cmd[1:])}); input too large or lt-proc hung') from None
    except FileNotFoundError:
        raise RuntimeError(f'{cmd[0]} not found: install lttoolbox (e.g. apt install lttoolbox)') from None
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f'{" ".join(cmd)} failed (exit {e.returncode}): {e.stderr.strip()[:500]}') from None
def _lus(lines,binary,lt):
    """one lt-proc call for all units; returns the LU strings per unit, checked for line alignment"""
    if not lines: return []
    lines=[_clean(x) for x in lines]
    out=_run([lt,'-w',binary],'\n'.join(ESC.sub(r'\\\1',x) for x in lines)+'\n').split('\n')
    if out and out[-1]=='': out=out[:-1]
    if len(out)!=len(lines): raise RuntimeError(f'lt-proc returned {len(out)} lines for {len(lines)} inputs (alignment lost)')
    return [LU.findall(o) for o in out]
def _head(lus):
    """-> (surface, readings, prefix) of the head unit of a token, or None if unknown"""
    if not lus: return None
    # enclitic after a hyphen (keldi-yu, Keldingiz-a, men-da): analyse the host.  Either "- + clitic" units, or a single
    # "-a"/"-ya" unit as produced by transducers that still list the hyphen-initial clitic words (upstream apertium-uzb)
    if len(lus)>=3 and lus[-2].split('/')[0]=='-' and lus[-1].split('/')[0].lower() in ud.CLITICS: lus=lus[:-2]
    elif len(lus)>=2 and lus[-1].split('/')[0].lower() in ('-a','-ya'): lus=lus[:-1]
    prefix=''
    if len(lus)>1:
        prefix=''.join(l.split('/')[0] for l in lus[:-1])
        if lus[-2].split('/')[0]!='-': prefix+='-'
    surf,*reads=SPLIT.split(lus[-1])
    if not reads or any(x.startswith('*') for x in reads): return None
    reads=list(dict.fromkeys(norm(x) for x in reads))
    return surf,reads,prefix          # the prefix keeps its case (toshkent-Samarqand); scoring is case-insensitive
def to_latin(text,script='auto'):
    """script: 'lat' (official Latin), 'cyr' (Cyrillic), 'new' (2026 Latin with ö ü ş ç ğ), or 'auto' (Cyrillic if present)"""
    if script=='auto': script='cyr' if CYR.search(text) else 'lat'
    if script=='cyr': return translit.cyr2lat(text)
    if script=='new': return translit.new2lat(text)
    return text
class Analyzer:
    def __init__(self,guess=True,names_level=1,ctx_weight=1.0,lt_proc='lt-proc',
                 automorf=None,autogen=None,guesser_bin=None):
        self.lt=_find_lt(lt_proc); self.guess=guess; self.names=names_level
        self.morf=automorf or path('uzb.automorf.bin'); self.gen=autogen or path('uzb.autogen.bin')
        self.gbin=guesser_bin or path('uzb_guesser.automorf.bin'); self.rk=Ranker(ctx_weight=ctx_weight)
    # ------------------------------------------------------------------ lookup
    def lookup(self,words):
        """raw Apertium analyses: {word: [LU strings]}"""
        u=sorted(set(words)); return dict(zip(u,_lus(u,self.morf,self.lt)))
    def _guess_raw(self,surfaces):
        """raw guesser readings for unknown units: {surface: [readings]}"""
        G={}; unk=sorted(set(surfaces))
        for u,g in zip(unk,_lus(unk,self.gbin,self.lt)):
            if g: G[u]=SPLIT.split(g[0])[1:]
        return G
    def _guessed(self,lus,G):
        """replace unknown units by confident guesses (like the research pipeline); G from _guess_raw"""
        out=[]
        for l in lus:
            if '/*' in l:
                s=l.split('/')[0]; r=guesser.rank(s,G.get(s,[]),s[:1].isupper() and s[1:2].islower())
                if r: l=s+'/'+'/'.join(r)
            out.append(l)
        return out
    def _name(self,toks,i,known,reads,have_guess=True,surf=None):
        w=toks[i]; gs=w if surf is None else surf; level=self.names
        if not level or not w[:1].isupper(): return None
        acr=w.isupper() and len(w)>1
        medial=any(textlib.is_word(t) for t in toks[:i]) and toks[i-1] not in BOUND
        c,ratio=names.capratio(w)
        if not known:
            l=names.listed(gs)
            if l: return l,'names-list'
        if not known:
            if (medial and not acr) or (c>=3 and ratio>=0.5) or acr or not have_guess:
                g=names.guess_hyph(gs); return (g[0],'names-guess') if g else None
        elif level>=2 and medial and c>=20 and ratio>=0.9 and not any('<np>' in r for r in reads):
            g=names.guess_hyph(gs); return (g[0],'names-guess') if g else None
        return None
    # ------------------------------------------------------------------ analysis
    def analyze_sentences(self,sents,script='auto'):
        """sents: list of strings (one sentence each) -> list of lists of Token"""
        return self.analyze_tokens([textlib.tokenize(textlib.norm(to_latin(_ctrl(s),script))) for s in sents])
    def analyze_tokens(self,T):
        """pre-tokenised input (official Latin): list of lists of strings -> list of lists of Token.
        Control characters are removed; a token containing whitespace (or nothing else) raises ValueError.
        Token.known is True only if the main dictionary knows every part of the token (qwzz-kitob: False); it is
        always False for non-word tokens (punctuation, numbers)."""
        A=self.lookup([t for ts in T for t in ts])
        G=self._guess_raw([l.split('/')[0] for lus in A.values() if _head(lus) is None for l in lus if '/*' in l]) if self.guess else {}
        out=[]
        for si,toks in enumerate(T):
            H=[];K=[]
            L=[]                                   # head analysed by the main dictionary
            for t in toks:
                h=_head(A[t]); L.append(h is not None)
                K.append(h is not None and textlib.is_word(t) and not any('/*' in l for l in A[t]))
                if h is None and self.guess: h=_head(self._guessed(A[t],G))
                H.append(h)
            M=[self.rk.marg(h[1]) if h else ({'P_sent':1.0} if t in '.!?…' else {('UNK' if textlib.is_word(t) else 'P_other'):1.0}) for h,t in zip(H,toks)]
            res=[]
            for i,(t,h) in enumerate(zip(toks,H)):
                tok=Token(t,si,textlib.is_word(t),K[i]); res.append(tok)
                if not tok.is_word: continue
                if not h:
                    nr=self._name(toks,i,False,[],have_guess=False)
                    if nr: tok.readings=[self._mk(nr[0],'',None,nr[1])]
                    continue
                surf,reads,prefix=h; tok.prefix=prefix
                nr=self._name(toks,i,L[i],reads,surf=surf if prefix else None)
                pm=M[i-1] if i>0 else {'P_sent':1.0}; nm=M[i+1] if i+1<len(toks) else {'P_sent':1.0}
                nxt=toks[i+1] if i+1<len(toks) else None
                src='lexicon' if L[i] else 'guesser'
                rs=[self._mk(r,prefix,sc,src) for r,sc in self.rk.rank(t,reads,nxt,pm,nm)]
                if nr: rs=[self._mk(nr[0],prefix,None,nr[1])]+rs
                tok.readings=[r for r in rs if r]
            out.append(res)
        return out
    def _mk(self,r,prefix,score,src):
        m=ud.map_ap_reading(r.replace('\\',''),prefix)
        if not m: return Reading(r,r[:r.find('<')] if '<' in r else r,'X','_',score,src)
        return Reading(r,m[0],m[1],ud.fstr(m[2]),score,src)
    def analyze(self,text,script='auto'):
        """text -> flat list of Token (sentence index in Token.sent). The text is transliterated to official Latin
        first, so sentence splitting works for Cyrillic and 2026-Latin input too."""
        text=CTRL.sub(lambda m:'\n' if m.group(0)=='\r' else '',VTFF.sub(' ',text))
        text=to_latin(text,script)
        sents=textlib.split_sents(text) or ([text] if text.strip() else [])
        return [t for s in self.analyze_sentences(sents,'lat') for t in s]
    # ------------------------------------------------------------------ generation
    def generate(self,lemma,tags):
        """generate('oʻqi','<v><tv><prog><p1><sg>') or tags as a list ['v','tv','prog','p1','sg'] -> list of surface forms.
        Tags must match (<[A-Za-z0-9_]+>)+ (ValueError otherwise); outputs that are not clean word forms are dropped."""
        if not isinstance(tags,str): tags=''.join(f'<{x}>' for x in tags)
        if not TAGS.fullmatch(tags): raise ValueError(f'tags must look like <v><tv><prog><p1><sg>: {tags!r}')
        lemma=_clean(textlib.norm(lemma))      # same apostrophe normalisation as analyze(): o'qi -> oʻqi
        o=_run([self.lt,'-g',self.gen],'^'+ESC.sub(r'\\\1',lemma)+tags+'$\n').strip()
        return [x for x in o.split('/') if x and not BADOUT.search(x)]

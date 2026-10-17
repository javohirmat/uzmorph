# SPDX-License-Identifier: GPL-3.0-only
"""Annotation scheme + mappings from Apertium (v8d) and ZirhUzMorph analyses. See ../ANNOTATION.md."""
import re,sys
from uzmorph import translit as T
FEATS=('Case','Number','Poss','Person','VerbForm','Mood','TAM','Polarity','Voice')
NOMINAL=('NOUN','PROPN','PRON')
def finalize(upos,f,overt):
    f=dict(f)
    if upos in ('VERB','AUX'):
        vf=f.setdefault('VerbForm','Fin')
        if vf=='Fin':
            f.setdefault('Mood','Ind'); f.setdefault('Person','3')
            if 'Number' not in f or f.get('_agr')!='1': f['Number']=f.get('_num','Sing')
            if f['Mood']!='Ind': f.pop('TAM',None)
        else:
            for k in ('Mood','TAM','Person'): f.pop(k,None)
            f['Number']=f.get('_nnum','Sing') if overt else None
            if not overt: f.pop('Case',None)
            else: f.setdefault('Case','Nom')
    else:
        for k in ('VerbForm','Mood','TAM','Person','Polarity','Voice'): f.pop(k,None)
        if upos in NOMINAL or overt:
            f.setdefault('Case','Nom'); f['Number']=f.get('_nnum','Sing')
        else:
            f.pop('Case',None); f.pop('Number',None); f.pop('Poss',None)
    if f.get('Voice') not in (None,'Pass'): f.pop('Voice')
    return {k:v for k,v in f.items() if k in FEATS and v}
def fstr(f): return '|'.join(f'{k}={f[k]}' for k in FEATS if k in f) or '_'
def parse_fstr(s): return {} if s in ('','_') else dict(x.split('=',1) for x in s.split('|'))
def lnorm(x): return x.lower().replace("'","ʼ").replace('‘','ʻ').replace('’','ʼ')
# ---------------- Apertium
UPOS_AP={'n':'NOUN','np':'PROPN','adj':'ADJ','adv':'ADV','v':'VERB','vaux':'AUX','cop':'AUX','prn':'PRON','det':'DET','num':'NUM',
 'post':'ADP','postadv':'ADV','cnjcoo':'CCONJ','cnjsub':'SCONJ','cnjadv':'CCONJ','ij':'INTJ','qst':'PART','mod':'ADJ','abbr':'NOUN','part':'PART','emph':'PART'}
PUNCT_TAGS={'sent','cm','guio','lquot','rquot','lpar','rpar','apos','quot','percent','paren'}
CASE_AP={'nom':'Nom','acc':'Acc','gen':'Gen','dat':'Dat','loc':'Loc','abl':'Abl','term':'Ter','sim':'Equ'}
POSS_AP={'px1sg':'1Sg','px2sg':'2Sg','px3sp':'3','px1pl':'1Pl','px2pl':'2Pl','px3pl':'3'}
NONFIN={'gpr':'Part','ger':'Vnoun','prc':'Conv','gna':'Conv'}
def map_ap_reading(r,prefix=''):
    """r: one Apertium reading 'lemma<t>..(+lemma<t>..)*' -> (lemma,upos,feats) or None for punct/unknown"""
    parts=r.split('+'); main=parts[0]; cl=parts[1:]
    k=main.find('<')
    if k<0: return (prefix+main,'X',{})
    lem=main[:k]; tags=re.findall(r'<([^>]+)>',main)
    tags=[t for t in tags if t!='guess']
    if not tags: return (prefix+lem,'X',{})
    if tags[0] in PUNCT_TAGS: return None
    upos=UPOS_AP.get(tags[0],'X'); f={}; overt=False; person=None; num=None; agr=False
    for t in tags[1:]:
        if t in CASE_AP:
            f['Case']=CASE_AP[t]; overt|=t!='nom'
        elif t in POSS_AP:
            f['Poss']=POSS_AP[t]; overt=True
            if t=='px3pl': f['_nnum']='Plur'
        elif t=='pl' and person is None and upos not in ('VERB','AUX') or (t=='pl' and f.get('VerbForm') in ('Part','Vnoun','Inf')):
            f['_nnum']='Plur'; overt=True
        elif t in ('p1','p2','p3'): person=t[1]
        elif t in ('sg','pl') and person: num='Plur' if t=='pl' else 'Sing'
        elif t=='frm': f['_frm']=1
        elif t=='neg': f['Polarity']='Neg'
        elif t=='pass': f['Voice']='Pass'
        elif t=='ifi': f['TAM']='Past'
        elif t=='past': f['TAM']='Perf'
        elif t=='evid': f['TAM']='Evid'
        elif t=='aor': f['TAM']='Pres' if f.get('TAM')!='Evid' else 'Evid'
        elif t=='fut': f['TAM']='Fut'
        elif t=='fut2': f['TAM']='Aor'
        elif t in ('prog','prog_inf'): f['TAM']='Prog'
        elif t=='fut_plan': f['TAM']='Int'
        elif t in ('imp','opt'): f['Mood']='Imp'
        elif t=='gna_cond': f['Mood']='Cnd'
        elif t=='ger_inf': f['VerbForm']='Inf'
        elif t[:3] in NONFIN and '_' in t: f['VerbForm']=NONFIN[t[:3]]
        elif t=='ger': f['VerbForm']='Vnoun'
    if 'evid' in tags and 'past' in tags: f['TAM']='Evid'
    if upos=='AUX' and lem=='e' or tags[0]=='cop': lem='e'
    # copula clitic carrying tense on a verb form (kelgandi = past + e<cop><ifi>) -> pluperfect
    for c in cl:
        ct=re.findall(r'<([^>]+)>',c)
        if upos=='VERB' and c.startswith('e<cop>') and 'ifi' in ct and f.get('TAM')=='Perf': f['TAM']='Pqp'
    if f.get('_frm') and f.get('Poss')=='2Sg': f['Poss']='2Pl'
    if person: f['Person']=person; f['_num']=('Plur' if f.get('_frm') and person=='2' else (num or 'Sing')); f['_agr']='1'
    if upos in ('VERB','AUX') and f.get('VerbForm') in ('Part','Vnoun','Inf'):
        f.pop('TAM',None)
    return (prefix+lem,upos,finalize(upos,f,overt))
def ap_candidates(lus):
    """lus: list of LU strings for one token -> list of mapped candidates of the head (last non-punct) LU"""
    if not lus: return [],True
    lus=[l for l in lus]
    head=lus[-1]; prefix=''
    if len(lus)>=3 and lus[-2].split('/')[0]=='-' and lus[-1].split('/')[0].lower() in CLITICS:
        lus=lus[:-2]; head=lus[-1]          # oldingiz-u, keldi-yu, men-da: analyse the host
    elif len(lus)>=2 and lus[-1].split('/')[0].lower() in ('-a','-ya'):
        lus=lus[:-1]; head=lus[-1]          # hyphen-initial clitic unit (upstream transducers)
    if len(lus)>1:
        # hyphenated token: earlier LUs contribute their surface to the lemma (rang-barang, yemoq-ichmoq)
        pre=[l.split('/')[0] for l in lus[:-1]]
        prefix=''.join(pre)
        if lus[-2].split('/')[0]!='-': prefix=prefix+'-'
    surf,*reads=head.split('/')
    unk=any(x.startswith('*') for x in reads) or not reads
    if unk: return [],False
    out=[]
    for r in reads:
        m=map_ap_reading(r.replace('\\',''),prefix.lower() if prefix else '')
        if m: out.append(m)
    return out,True
CLITICS={'u','yu','da','ku','chi','mi','a','ya','ov'}
# ---------------- ZirhUzMorph
def z2lat(s): return T.new2lat(s).replace("'","ʼ")
GLUE={'LIK','CHI','CHILIK','SIZ','LI','DOSH','DER','IY','LA','AY','SIRA','AGENT','GICH','GULIK','DER.MA','DER.IK','DER.IM','DER.IN','DER.INDI','DER.GI','VN.UV','CHA'}
CASE_Z={'ACC':'Acc','GEN':'Gen','DAT':'Dat','LOC':'Loc','ABL':'Abl','GACHA':'Ter','DAY':'Equ'}
POSS_Z={'P1S':'1Sg','P2S':'2Sg','P3':'3','P1P':'1Pl','P2P':'2Pl'}
PERS_FORM={'m':('1','Sing'),'man':('1','Sing'),'ng':('2','Sing'),'san':('2','Sing'),'k':('1','Plur'),'miz':('1','Plur'),
 'ngiz':('2','Plur'),'siz':('2','Plur'),'lar':('3','Plur'),'dilar':('3','Plur'),'tilar':('3','Plur'),'nglar':('2','Plur'),'di':('3','Sing'),'ti':('3','Sing'),'':('3','Sing')}
def map_zirh(a,prefix=''):
    """a: zirhuzmorph Analysis -> (lemma,upos,feats); a.morphs=[(form,tag)]"""
    if a.pos in ('?','SUF') or not a.stem and a.pos!='N': return (z2lat(prefix+a.lemma),'X',{})
    ms=[(m,t) for m,t in a.morphs]
    # glue derivational morphs into the lemma (up to the last lexical derivation)
    last=-1; prev_case=False
    for j,(m,t) in enumerate(ms):
        if t in GLUE or (t=='GI' and not prev_case): last=j
        if t in VOICE and j<len(ms)-1 and any(tt in GLUE for _,tt in ms[j+1:]): pass
        prev_case=t in CASE_Z
    lemma=(a.stem+''.join(m for m,_ in ms[:last+1])) if last>=0 else a.lemma
    if a.stem!=a.lemma and last<0: lemma=a.lemma
    pos=a.pos
    # category of the glued word
    if last>=0:
        t=ms[last][1]
        pos='V' if t in ('LA','AY','SIRA') else 'N'
    rest=ms[last+1:]
    f={}; overt=False
    if pos=='N':
        upos='NOUN'
        for m,t in rest:
            if t=='PL': f['_nnum']='Plur'; overt=True
            elif t=='PL+P3': f['_nnum']='Plur'; f['Poss']='3'; overt=True
            elif t in POSS_Z: f['Poss']=POSS_Z[t]; overt=True
            elif t in CASE_Z: f['Case']=CASE_Z[t]; overt=True
        return (z2lat(prefix+lemma),upos,finalize(upos,f,overt))
    upos='VERB'; vf=None; person=None; num=None
    for j,(m,t) in enumerate(rest):
        nxt=rest[j+1][1] if j+1<len(rest) else None
        if t=='PASS': f['Voice']='Pass'
        elif t=='NEG': f['Polarity']='Neg'
        elif t=='PST': f['TAM']='Past'
        elif t=='PRF': f['TAM']='Perf'
        elif t in ('PROG','PROG2','PROG3'): f['TAM']='Prog'
        elif t=='AOR': f['TAM']='Aor'
        elif t=='FUT': f['TAM']='Fut'
        elif t=='INT': f['TAM']='Int'
        elif t=='COND': f['Mood']='Cnd'
        elif t=='PRS':
            if nxt in ('PERS','PERS3'): f['TAM']='Pres'
            else: vf='Conv'
        elif t=='CVB':
            if nxt=='PERS': f['TAM']='Evid'
            else: vf='Conv'
        elif t.startswith('CVB.'): vf='Conv'
        elif t.startswith('PTCP'): vf='Part'
        elif t in ('VN.ISH',): vf='Vnoun'
        elif t=='INF': vf='Inf'
        elif t in ('IMP3','IMP2P','IMP2','IMP2S','IMP1P','OPT1'):
            f['Mood']='Imp'
            person,num={'IMP3':('3','Plur' if m.endswith('lar') else 'Sing'),'IMP2P':('2','Plur'),'IMP2':('2','Sing'),'IMP2S':('2','Sing'),
                        'IMP1P':('1','Plur'),'OPT1':('1','Sing')}[t]
        elif t in ('PERS','PERS3'):
            if f.get('TAM')=='Perf' and m in ('di','dilar'): f['TAM']='Pqp'; person,num='3',('Plur' if m=='dilar' else 'Sing')
            else: person,num=PERS_FORM.get(m,('3','Sing'))
        elif vf and t=='PL': f['_nnum']='Plur'; overt=True
        elif vf and t=='PL+P3': f['_nnum']='Plur'; f['Poss']='3'; overt=True
        elif vf and t in POSS_Z: f['Poss']=POSS_Z[t]; overt=True
        elif vf and t in CASE_Z: f['Case']=CASE_Z[t]; overt=True
    if vf: f['VerbForm']=vf
    if person: f['Person']=person; f['_num']=num; f['_agr']='1'
    return (z2lat(prefix+lemma),upos,finalize(upos,f,overt))
VOICE={'PASS','REFL','RECP','CAUS'}
# ---------------- matching
VOICE_SUF=re.compile(r'^(il|l|in|n|ish|sh|t|it|tir|dir|ir|ar|iz|giz|kiz|qiz|gʻiz|gaz|qaz|kaz|iltir|ishtir|lan|lash)+$')
def lemma_ok(c,g,alts=()):
    c=lnorm(c); g=lnorm(g)
    if c==g or c in [lnorm(x) for x in alts]: return True
    for a,b in ((c,g),(g,c)):          # voice-neutral: yorit ~ yoritil, kel ~ keltir is NOT accepted unless keltir listed as alt
        if b.startswith(a) and len(a)>=2 and VOICE_SUF.match(b[len(a):]) and b[len(a):] in ('il','l','in','n','ish','sh','iltir','lan','lash','ishtir'): return True
    return False
def coarse(u): return 'V' if u in ('VERB','AUX') else ('N' if u in ('NOUN','PROPN','ADJ','NUM','PRON','DET','ADV') else 'O')

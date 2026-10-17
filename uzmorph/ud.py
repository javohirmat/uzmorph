# SPDX-License-Identifier: GPL-3.0-only
"""Mapping of Apertium uzb readings to UD-style (lemma, UPOS, feats), as used in the evaluation."""
import re
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
CLITICS={'u','yu','da','ku','chi','mi','a','ya','ov'}

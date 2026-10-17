# SPDX-License-Identifier: GPL-3.0-only
"""Apply manual review decisions to the proposal -> ../private/gold.tsv (+ gold.json).
Decision syntax (private/review_decisions.tsv): KEY<TAB>MAIN [mods]
  MAIN: jN (candidate N in review_print numbering) | = (accept proposal) | lemma;UPOS;Feat=Val,Feat=Val (or _)
  mods: +alt:a/b  #typo #affix #abbr #foreign  !low  !checked  !disputed
"""
import json,os,sys
sys.path.insert(0,os.path.dirname(__file__)); import scheme as S
from review_print_lib import cand_list
from propose_lib import fix_num
P=os.path.join(os.path.dirname(__file__),'..','private')
C=json.load(open(f'{P}/cands.json',encoding='utf-8'))['lat']
G=json.load(open(f'{P}/gold_proposal.json',encoding='utf-8'))
SENT={json.loads(l)['id']:json.loads(l) for l in open(f'{P}/sentences.jsonl',encoding='utf-8')}
EXCL={l.strip() for l in open(f'{P}/exclude_sents.txt',encoding='utf-8') if l.strip()}
D={}
for ln in open(f'{P}/review_decisions.tsv',encoding='utf-8'):
    ln=ln.rstrip('\n')
    if not ln or ln.startswith('#'): continue
    k,v=ln.split('\t'); D[k]=v      # later lines override earlier ones
def explicit(main):
    lem,upos,fs=main.split(';')
    f={} if fs=='_' else dict(x.split('=') for x in fs.split(','))
    overt=f.get('Case','Nom')!='Nom' or 'Poss' in f or f.get('Number')=='Plur'
    if upos in('VERB','AUX') and f.get('VerbForm','Fin')=='Fin':
        if 'Number' in f: f['_num']=f.pop('Number'); f['_agr']='1'
    elif 'Number' in f: f['_nnum']=f.pop('Number')
    return [lem,upos,S.fstr(S.finalize(upos,f,overt))]
JV={}
if os.path.exists(f'{P}/reviewer_verdicts.tsv'):
    for ln in open(f'{P}/reviewer_verdicts.tsv',encoding='utf-8'):
        k,o,x=(ln.rstrip('\n').split('\t')+['',''])[:3]; JV[k]=o
out=[];bad=[]
for g in G:
    sid,i=g['key'].split(':')
    if sid in EXCL: continue
    r=dict(g); r['alts']=''; flags=set(x for x in g['flags'].split(',') if x)
    conf={'auto-agree':'auto','auto-func':'auto','auto-nonword':'auto','auto-affix':'auto'}.get(g['src'],'high')
    if g['key'] in D:
        parts=D[g['key']].split(); main=parts[0]
        if main[0]=='j' and main[1:].isdigit():
            cl=cand_list(C[g['key']]); j=int(main[1:])
            if j>=len(cl): bad.append((g['key'],main,len(cl))); continue
            c=fix_num(cl[j],g['tok'])
        elif main=='=': c=[g['lemma'],g['upos'],g['feats']]
        else: c=explicit(main)
        r['lemma'],r['upos'],r['feats']=c; r['src']='review'
        for m in parts[1:]:
            if m.startswith('+alt:'): r['alts']=m[5:]
            elif m.startswith('#'): flags.add(m[1:])
            elif m=='!low': conf='low'
            elif m=='!checked': conf='checked'      # resolved from the native reviewer's N + fix
            elif m=='!disputed': conf='disputed'    # the native reviewer said N; gold kept on a convention question (see README)
    elif g['src']=='proposal': r['src']='review'
    if r['upos']=='PRON' and S.lnorm(r['lemma']) in ('ular','biz'):
        f=S.parse_fstr(r['feats']); f['Number']='Plur'; r['feats']=S.fstr(f)
    if r['upos']=='PROPN': flags.add('name')
    if JV.get(g['key'])=='Y' and conf!='disputed': conf='checked'
    r['flags']=','.join(sorted(flags)); r['conf']=conf
    out.append(r)
if bad: print('BAD j index',bad); sys.exit(1)
json.dump(out,open(f'{P}/gold.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
with open(f'{P}/gold.tsv','w',encoding='utf-8') as fo:
    fo.write('key\ttoken\tlemma\tupos\tfeats\talts\tflags\tconf\tsrc\n')
    for r in out: fo.write('\t'.join([r['key'],r['tok'],r['lemma'],r['upos'],r['feats'],r['alts'],r['flags'],r['conf'],r['src']])+'\n')
from collections import Counter
w=[r for r in out if r['upos'] not in('PUNCT',) and 'num' not in r['flags']]
print('tokens',len(out),'word tokens',len(w),Counter(r['conf'] for r in w),Counter(f for r in w for f in r['flags'].split(',') if f))
print('X without excl flag:',[ (r['key'],r['tok']) for r in w if r['upos']=='X' and not set(r['flags'].split(','))&{'foreign','affix','abbr','typo'}])

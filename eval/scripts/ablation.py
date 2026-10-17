# SPDX-License-Identifier: GPL-3.0-only
"""Dev-only component report for the phase-3 ranker (analyzer v9.1). -> ../results/ablation_dev.md / .json"""
import os,json
os.environ.setdefault('SUF',os.environ.get('AFTER','_v91'))
from rank_eval import *
FULL=dict(ctx=1.0,opts={'sg_default','real_lemma','imp_medial','dup_lemma'},names=1)
steps=[('CG -1 + guesser (baseline)',None),
 ('corpus EM prior only (replaces CG)',dict(ctx=0,opts=set())),
 ('+ singular default',dict(ctx=0,opts={'sg_default'})),
 ('+ real lemma beats short lemma+px1/2sg',dict(ctx=0,opts={'sg_default','real_lemma'})),
 ('+ demote medial imperatives',dict(ctx=0,opts={'sg_default','real_lemma','imp_medial'})),
 ('+ duplicate-lemma rule (corpus paradigm size)',dict(ctx=0,opts=FULL['opts'])),
 ('+ class-bigram context (λ=1)',dict(FULL,names=0)),
 ('+ proper-noun guesser & verified list = FINAL',FULL)]
rows=[]
def go(name,cfg):
    VARIANTS['_']=cfg; n,a=evaluate('dev','_'); rows.append((name,n,a)); print(f'{name:55s}',a)
for name,cfg in steps: go(name,cfg)
for o,lab in (('sg_default','singular default'),('real_lemma','real lemma'),('imp_medial','medial imperative'),('dup_lemma','duplicate lemma')):
    go(f'FINAL − {lab}',dict(FULL,opts=FULL['opts']-{o}))
go('FINAL − context',dict(FULL,ctx=0)); go('FINAL − names',dict(FULL,names=0))
for lam in (0.5,1.5): go(f'FINAL with λ={lam}',dict(FULL,ctx=lam))
go('FINAL but HMM (Baum-Welch) context instead of bigram',dict(hmm=1.0,ctx=0,opts=FULL['opts'],names=1))
for extra,lab in ((['closed'],'tried: closed-class reading beats noun'),(['bare_ger'],'tried: demote bare -gan verbal noun'),(['voice'],'tried: passive split over lexical -n/-l verb')):
    go('FINAL + '+lab,dict(FULL,opts=FULL['opts']|set(extra)))
M=('lemma','upos','coarse','feats','lf','full')
L=['# Ranker components, DEV split only (104 sentences, 1,062 main tokens after the native reviewer sheet; 1,063 before — numbers moved by ≤0.1), analyzer v9.1, Latin','',
   'Top-1 accuracy over all main tokens (uncovered = wrong); lf = lemma+feats. All tuning decisions were made on this table; test was scored once afterwards.','',
   '| step | '+' | '.join(M)+' |','|---|'+'---|'*len(M)]
for name,n,a in rows: L.append(f'| {name} | '+' | '.join(str(a[m]) for m in M)+' |')
open('../results/ablation_dev.md','w',encoding='utf-8').write('\n'.join(L)+'\n'); json.dump(rows,open('../results/ablation_dev.json','w',encoding='utf-8'),indent=1)

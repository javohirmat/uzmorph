# SPDX-License-Identifier: GPL-3.0-only
"""lemma+feats top-1 on the tokens the native reviewer confirmed or that were fixed from the reviewer's sheet (conf=checked), per split. -> ../results/checked_subset.md"""
import os,json
os.environ['SUF']=os.environ.get('AFTER','_v91')
import rank_eval as RE
from score import judge,G,EXCL
C8=json.load(open('../private/cands.json',encoding='utf-8'))['lat']
FINAL=dict(ctx=1.0,opts={'sg_default','real_lemma','imp_medial','dup_lemma'},names=1)
best={}
for s in RE.SENT: best.update(RE.rank_sentence(s,'lat',FINAL))
L=['# Accuracy on reviewer-checked tokens only (conf=checked: rows the reviewer marked correct, plus rows fixed after a "wrong" mark), lemma+feats top-1, Latin','','| split | n | before (v8d+CG+guess) | after (v9.1+ranker+guess+names) | Zirh |','|---|---|---|---|---|']
for part in ('test','dev'):
    n=b=a=z=0
    for g in G:
        if g['conf']!='checked' or RE.SPLIT.get(g['key'].split(':')[0])!=part or set(g['flags'].split(','))&EXCL or 'typo' in g['flags']: continue
        v=C8[g['key']]; n+=1
        bb=(v['ours_cg'] or v['ours'][:1]) if v['ours_known'] else v['guess'][:1]
        b+=bool(bb) and judge(bb[0],g)['lf']; a+=bool(best.get(g['key'])) and judge(best[g['key']],g)['lf']
        z+=bool(v['zirh_best']) and judge(v['zirh_best'][0],g)['lf']
    L.append(f'| {part} | {n} | {100*b/n:.1f} | {100*a/n:.1f} | {100*z/n:.1f} |')
open('../results/checked_subset.md','w',encoding='utf-8').write('\n'.join(L)+'\n'); print('\n'.join(L))

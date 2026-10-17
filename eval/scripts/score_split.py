# SPDX-License-Identifier: GPL-3.0-only
"""Before/after head-to-head on the frozen dev/test split (split.json). Same columns as scores.md.
before = v8d + CG -1 (cands.json); after = v9 + phase-3 ranker (cands_v9.json + rank_eval FINAL config).
-> ../results/split_scores.json, ../results/split_scores.md"""
import os,json,sys
AFTER=os.environ.get('AFTER','_v91'); os.environ['SUF']=AFTER
from collections import defaultdict
import rank_eval as RE
from score import judge,G,EXCL,systems
import scheme as S
B=os.path.dirname(os.path.abspath(__file__))+'/..'
C8=json.load(open(f'{B}/private/cands.json',encoding='utf-8')); C9=json.load(open(f'{B}/private/cands{AFTER}.json',encoding='utf-8')); CU=json.load(open(f'{B}/private/cands_up.json',encoding='utf-8'))
FINAL=dict(ctx=1.0,opts={'sg_default','real_lemma','imp_medial','dup_lemma'},names=1)
KNOWN=dict(FINAL,names=0)
RE.VARIANTS['FINAL']=FINAL; RE.VARIANTS['KNOWN']=KNOWN
GEN={'B':'books','W':'wiki','N':'news','T':'telegram'}
M=('lemma','upos','coarse','feats','lf','full')
def ranked(script,cfg,use_guess):
    out={}
    for s in RE.SENT:
        if s['id'] in RE.SPLIT: out.update(RE.rank_sentence(s,script,cfg,use_guess))
    return out
res={}
for script in ('lat','cyr','new'):
    RF=ranked(script,FINAL,True); RK=ranked(script,KNOWN,False)
    A=defaultdict(lambda:dict(n=0,cov=0,reads=0,mreads=0,**{f'or_{m}':0 for m in M},**{f'b_{m}':0 for m in M}))
    for g in G:
        sid=g['key'].split(':')[0]; part=RE.SPLIT.get(sid)
        fl=set(g['flags'].split(','))
        if part is None or fl&EXCL or 'typo' in fl: continue
        v8=C8[script][g['key']]; v9=C9[script][g['key']]; s8=systems(v8); s9=systems(v9)
        k9=v9['ours_known']
        rk=RK.get(g['key']) if k9 else None
        rf=RF.get(g['key'])
        fc=(v9['ours'] if k9 else v9['guess'])
        SY={'upstream apertium-uzb 00522e3 (CG -1)':systems(CU[script][g['key']])['ours'],'before: ours (v8d, CG)':s8['ours'],'before: ours+guess (v8d, CG)':s8['ours+guess'],
            'after: ours (v9.1, ranker)':(k9,v9['ours'] if k9 else [],[rk] if rk else []),
            'after: ours+guess+names (v9.1, ranker)':(bool(rf) or bool(fc),(fc+[rf]) if rf and rf not in fc else fc,[rf] if rf else []),
            'zirh_known':s8['zirh_known'],'zirh':s8['zirh']}
        for sysn,(cov,cands,best) in SY.items():
            for grp in ('all',GEN[sid[0]],'names' if 'name' in fl else 'nonnames'):
                a=A[(part,sysn,grp)]; a['n']+=1
                if not cov: continue
                a['cov']+=1; a['mreads']+=len(cands)
                vv=v9 if sysn.startswith('after') else (CU[script][g['key']] if sysn.startswith('upstream') else v8)
                a['reads']+=(vv['ours_nread'] if sysn.startswith(('before','after','upstream')) and vv['ours_known'] else (len(cands) if sysn.startswith(('before','after','upstream')) else vv['zirh_nread']))
                js=[judge(c,g) for c in cands]
                for m in M: a['or_'+m]+=any(j[m] for j in js)
                if best:
                    jb=judge(best[0],g)
                    for m in M: a['b_'+m]+=jb[m]
    res[script]={'|'.join(k):v for k,v in A.items()}
json.dump(res,open(f'{B}/results/split_scores.json','w',encoding='utf-8'),indent=1)
def pct(a,b): return f'{100*a/b:.1f}' if b else '-'
ORDER=['upstream apertium-uzb 00522e3 (CG -1)','before: ours (v8d, CG)','before: ours+guess (v8d, CG)','after: ours (v9.1, ranker)','after: ours+guess+names (v9.1, ranker)','zirh_known','zirh']
L=['# Before/after on the frozen split (dev = tuning, test = scored once)','',
   'Same scoring as scores.md: accuracy over ALL main tokens (uncovered = wrong), "oracle/best", typo/affix/abbr/foreign excluded. lemma+feats is the fair metric (UPOS is not comparable: Zirh only outputs N/V).',
   'upstream = apertium-uzb 00522e3 as released, CG -1, no guesser. before = v8d analyzer + CG -1 (+ confident guesser). after = v9.1 analyzer (-ish- fix, hyphen -a fix) + phase-3 corpus-trained ranker (+ guesser + proper-noun layer). Zirh rows are identical in both.','']
for script in ('lat','cyr','new'):
    for part in ('test','dev'):
        for grp in ('all','books','wiki','news','telegram','names','nonnames'):
            if script!='lat' and grp not in ('all',): continue
            L+=[f'## {script} / {part} / {grp}','','| system | n | cov | lemma or/best | UPOS or/best | coarse or/best | feats or/best | lemma+feats or/best | full or/best | readings raw/mapped |','|---|---|---|---|---|---|---|---|---|---|']
            for sysn in ORDER:
                a=res[script].get(f'{part}|{sysn}|{grp}')
                if not a: continue
                n=a['n']
                L.append(f"| {sysn} | {n} | {pct(a['cov'],n)} | "+' | '.join(f"{pct(a['or_'+m],n)} / {pct(a['b_'+m],n)}" for m in M)+f" | {a['reads']/max(a['cov'],1):.2f} / {a['mreads']/max(a['cov'],1):.2f} |")
            L.append('')
open(f'{B}/results/split_scores.md','w',encoding='utf-8').write('\n'.join(L)+'\n')
print('\n'.join(L[:40]))

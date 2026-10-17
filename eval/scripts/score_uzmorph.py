# SPDX-License-Identifier: GPL-3.0-only
"""Score the released `uzmorph` package itself on the private eval set (best reading only), per split and script.
Needs the private files listed in eval/README.md (eval/private/, not distributed).
Reproduces the "after: ours+guess+names (v9.1, ranker)" best column of results/split_scores.md.
Usage: python eval/scripts/score_uzmorph.py [OUT.md]   -> prints the table (and writes it, with a header, to OUT.md)"""
import json,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from score import judge,G,EXCL
from uzmorph import Analyzer,to_latin
B=os.path.dirname(os.path.abspath(__file__))+'/..'
SPLIT=json.load(open(f'{B}/split.json',encoding='utf-8'))['split']
SENT=[json.loads(l) for l in open(f'{B}/private/sentences.jsonl',encoding='utf-8')]
A=Analyzer(); M=('lemma','upos','feats','lf')
OUT=['| script | split | n | lemma | UPOS | feats | lemma+feats |','|---|---|---|---|---|---|---|']; print('\n'.join(OUT))
for script in ('lat','cyr','new'):
    toks=[[to_latin(t[script],script) for t in s['tokens']] for s in SENT]
    best={}
    for s,res in zip(SENT,A.analyze_tokens(toks)):
        for t,r in zip(s['tokens'],res):
            if r.best: best[f"{s['id']}:{t['i']}"]=[r.best.lemma,r.best.upos,r.best.feats]
    for part in ('dev','test'):
        n=0; acc=dict.fromkeys(M,0)
        for g in G:
            fl=set(g['flags'].split(','))
            if SPLIT.get(g['key'].split(':')[0])!=part or fl&EXCL or 'typo' in fl: continue
            n+=1; b=best.get(g['key'])
            if b:
                j=judge(b,g)
                for m in M: acc[m]+=j[m]
        OUT.append(f'| {script} | {part} | {n} | '+' | '.join(f'{100*acc[m]/n:.1f}' for m in M)+' |'); print(OUT[-1])
if len(sys.argv)>1:
    import uzmorph
    open(sys.argv[1],'w',encoding='utf-8').write(f'# The released package (uzmorph {uzmorph.__version__}, default settings) on the private eval set\n\n'
        'Top reading only, all scored tokens (unanalysed = wrong); output of `eval/scripts/score_uzmorph.py`. '
        'Matches the "after: ours+guess+names (v9.1, ranker)" best column of `split_scores.md`.\n\n'+'\n'.join(OUT)+'\n')

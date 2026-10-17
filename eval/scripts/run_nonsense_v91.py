# SPDX-License-Identifier: GPL-3.0-only
"""Non-word acceptance for the release (v9.1) next to ZirhUzMorph. Lower is better. -> ../nonsense/results_v91.json/.md
Rows: lower-case non-words (as generated) and the same strings Capitalised. Zirh columns come from results.json (run_zirh
over the same 299 lower-case strings): 'known stems' = top analysis has a dictionary stem; 'any output' additionally counts
unknown-stem segmentations (word+suffix guesses). A bare `word[?]` (no segmentation) is counted as rejected."""
import json,os,subprocess,sys
from collections import Counter,defaultdict
from uzmorph import names as NM
B=os.path.join(os.path.dirname(__file__),'..'); N=B+'/nonsense'; GW='work/morph/phase2/guesser/uzb_guess.py'
A='work/morph/apertium-uzb-v6'
REAL={'boshqarmamoqda'}
W=[x for x in (l.rstrip('\n').split('\t') for l in open(f'{N}/nonwords.tsv',encoding='utf-8')) if x[0]!='word' and x[0] not in REAL]
Z={r['word']:r for r in json.load(open(f'{N}/results.json',encoding='utf-8'))}
words=[w for w,_,_ in W]; cap=[w[0].upper()+w[1:] for w in words]
def run(cmd,ws): return subprocess.run(cmd,input='\n'.join(ws)+'\n',capture_output=True,text=True).stdout.split('\n')[:len(ws)]
known=lambda line: bool(line) and '/*' not in line and '/' in line
M=['lt-proc','-w',f'{A}/uzb.automorf.bin']; GC=['python3',GW,'--main',f'{A}/uzb.automorf.bin','--guesser',f'{A}/uzb_guesser.automorf.bin']
rows={}
for case,ws in (('lower-case',words),('Capitalised',cap)):
    d=[known(x) for x in run(M,ws)]; g=[known(x) for x in run(GC,ws)]; ga=[known(x) for x in run(GC+['--all'],ws)]
    cols={'uzmorph dictionary':d,'+ confident guesser':g,'+ unfiltered guesser (tools/models/uzb_guess.py --all)':ga}
    if case=='Capitalised':
        cols['+ verified name list']=[k or bool(NM.listed(c)) for k,c in zip(d,ws)]
        cols['+ proper-noun guesser (mid-sentence)']=[k or bool(NM.guess_hyph(c)) for k,c in zip(d,ws)]
    else:
        cols['Zirh, known stems']=[Z[w]['zirh_any_known'] for w in words]
        cols['Zirh, any segmentation (incl. unknown-stem guesses)']=[not Z[w]['zirh_top'].endswith('[?]') for w in words]
    rows[case]=cols
res={c:{k:sum(v) for k,v in cols.items()} for c,cols in rows.items()}; res['n']=len(words)
json.dump(res,open(f'{N}/results_v91.json','w',encoding='utf-8'),indent=1)
L=[f'# Non-word acceptance (release analyzer v9.1; {len(words)} non-words with 0 corpus hits; lower is better)','',
   '| input | system | accepted |','|---|---|---|']
for c,cols in rows.items():
    for k,v in cols.items(): L.append(f'| {c} | {k} | {100*sum(v)/len(v):.0f}% ({sum(v)}) |')
L+=['','- Zirh was run on the lower-case strings only. "any segmentation" counts every output that is not a bare `word[?]`;',
    '  46 of the 299 strings get a bare `word[?]` and count as rejected there.',
    '- Our unfiltered guesser and Zirh\'s unknown-stem guesses both analyse almost any string by design; neither is a rejection test.',
    '- The proper-noun guesser accepts any capitalised unknown word in mid-sentence position by design (readings marked `<guess>`).',
    '  At sentence start, `uzmorph.analyze` also falls back to it when the guesser has nothing.']
open(f'{N}/results_v91.md','w',encoding='utf-8').write('\n'.join(L)+'\n'); print('\n'.join(L))

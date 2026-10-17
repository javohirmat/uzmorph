#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""apply_batch.py DST LEMMAS_TSV : append a LEXICON B<NN>-Additions (auto-verified wiki lemmas) and hook it into Root.
NN is taken from the file name (lemmas_v7_batchNN.tsv)."""
import sys,os,re,csv
dst,f=sys.argv[1:3];nn=re.search(r'batch(\d+)',f).group(1)
L=os.path.join(dst,'apertium-uzb.uzb.lexc');t=open(L,encoding='utf-8').read()
rows=list(csv.DictReader(open(f,encoding='utf-8'),delimiter='\t'))
if not rows: print('empty',f);sys.exit()
hook='V6-Additions ; ! v6\n';assert t.count(hook)==1
t=t.replace(hook,hook+f'B{nn}-Additions ; ! v7 batch {nn}\n')
add=['',f'LEXICON B{nn}-Additions   ! v7: batch-{nn} auto-verified lemmas (uz.wikipedia + Wikidata), see phase2/{os.path.basename(f)}','']
add+=[f"{r['lemma']}:{r['surface']} {r['paradigm']} ; ! v7 add ! {r['category']} ! {r['flag']}" for r in rows]
t=t.rstrip('\n')+'\n'+'\n'.join(add)+'\n';open(L,'w',encoding='utf-8').write(t);print('batch',nn,'added',len(rows))

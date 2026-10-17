# SPDX-License-Identifier: GPL-3.0-only
"""Capitalisation stats per lowercase type from running text: n_lower, n_cap_medial (capitalised, not sentence-initial).
Eval docs excluded. Parallel over lat shards. -> capstats.pkl"""
import sys,re,json,glob,pickle
from collections import Counter
from multiprocessing import Pool
sys.path.insert(0,'work/morph/eval_gold/scripts'); import textlib as TL
import pyarrow.parquet as pq
EV={json.loads(l)['source'] for l in open('work/morph/eval_gold/private/sentences.jsonl',encoding='utf-8')}
def work(sh):
    name=sh.split('/')[-1].replace('.parquet',''); lo=Counter(); cap=Counter()
    t=pq.read_table(sh).column('text').to_pylist()
    for i,doc in enumerate(t):
        if f'tahrirchi/uz-books-v2:{name}:row{i}' in EV: continue
        for sent in TL.split_sents(TL.norm(doc[:300000])):
            toks=TL.TOKRE.findall(sent); first=True
            for tk in toks:
                if not TL.is_word(tk): 
                    if tk in '"«“(—–-:': pass
                    continue
                if tk[0].isupper():
                    if not first and not tk.isupper(): cap[tk.lower()]+=1
                else: lo[tk]+=1
                first=False
    return lo,cap
if __name__=='__main__':
    shs=sorted(glob.glob('work/data/lat-*.parquet'))[:int(sys.argv[1])]
    LO=Counter(); CAP=Counter()
    with Pool(6) as p:
        for lo,cap in p.imap_unordered(work,shs): LO.update(lo); CAP.update(cap); print('.',end='',flush=True)
    pickle.dump(dict(lo=dict(LO),cap=dict(CAP)),open('capstats.pkl','wb'))
    print('\ntypes lo',len(LO),'cap',len(CAP),'tokens',sum(LO.values())+sum(CAP.values()))

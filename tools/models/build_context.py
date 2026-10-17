# SPDX-License-Identifier: GPL-3.0-only
"""Class-bigram context model from running corpus text (uz-books-v2 lat shards; eval docs excluded).
Uses only tokens whose reading-class is nearly unambiguous under the EM priors (top class mass >= 0.9).
-> context.pkl {p[(c1,c2)] = P(c2|c1), uni, floor}"""
import sys,re,json,random,pickle,glob
from collections import Counter,defaultdict
sys.path.insert(0,'work/morph/eval_gold/scripts'); import textlib as TL
from rank_lib import Ranker,rclass,norm
import pyarrow.parquet as pq
LU=re.compile(r'\^((?:[^$\\]|\\.)*)\$')
R=Ranker(ctx=False)
# type -> class marginal
M={}
for line,fl in zip(open('types.ap',encoding='utf-8'),open('types400k.tsv',encoding='utf-8')):
    w=fl.split('\t')[0]; lus=LU.findall(line)
    if len(lus)!=1: continue
    parts=re.split(r'(?<!\\)/',lus[0]); reads=[norm(x) for x in parts[1:] if '<' in x]
    if reads: M[w]=R.marg(list(dict.fromkeys(reads)))
evaldocs={json.loads(l)['source'] for l in open('work/morph/eval_gold/private/sentences.jsonl',encoding='utf-8') if json.loads(l)['genre']=='books'}
rnd=random.Random(7); C=Counter(); U=Counter(); ntok=0
shards=sorted(glob.glob('work/data/lat-*.parquet'))
for sh in shards:
    t=pq.read_table(sh).column('text').to_pylist(); name=sh.split('/')[-1].replace('.parquet','')
    for i in rnd.sample(range(len(t)),25):
        if f'tahrirchi/uz-books-v2:{name}:row{i}' in evaldocs: continue
        txt=t[i][:400000]
        for sent in TL.split_sents(TL.norm(txt)):
            toks=TL.TOKRE.findall(sent)
            prev='P_sent'
            for tk in toks+['.']:
                lw=tk.lower()
                if not TL.is_word(tk): c={'P_sent':1.0} if tk in '.!?…' else ({'num':1.0} if tk[0].isdigit() else {'P_other':1.0})
                else: c=M.get(lw,{'UNK':1.0})
                top=max(c,key=c.get)
                cur=top if c[top]>=0.9 else None
                if prev and cur: C[(prev,cur)]+=1; U[prev]+=1
                prev=cur; ntok+=1
    print(sh,ntok,file=sys.stderr)
P={k:v/U[k[0]] for k,v in C.items()}
tot=sum(U.values()); uni={k:v/tot for k,v in U.items()}
pickle.dump(dict(p=P,uni=uni,floor=1e-5,ntok=ntok,npairs=sum(C.values())),open('context.pkl','wb'))
print('tokens',ntok,'pairs',sum(C.values()),'classes',len(U))
for a in ('n_gen','adj','v_part','det','v_conv'):
    print(a,sorted(((b,round(p,3)) for (x,b),p in P.items() if x==a),key=lambda z:-z[1])[:6])

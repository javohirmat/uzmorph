# SPDX-License-Identifier: GPL-3.0-only
"""Phase 4 guesser ranking. Inputs: unknown_words.txt / unknown_guess.txt (lt-proc -w uzb_guesser over v8-unknown types),
work/verify/v8d_lower.txt (known analyses, for the tag-sequence prior). Output guess_table.tsv + priors.json"""
import re,math,collections,json,sys
sys.path.insert(0,'work/verify');import covlib
B=covlib.BASE;W=B['words'];C=B['cnt']
LU=re.compile(r'\^(.*?)\$')
COP0=re.compile(r'\+e<cop><aor><p3><(sg|pl)>')
def norm(tags):
    return COP0.sub('',tags).replace('<iv>','<TD>').replace('<tv>','<TD>')
# 1. tag-sequence prior from known tokens (noun and verb readings only), token-weighted, split over readings
prior=collections.Counter()
with open('work/verify/v8d_lower.txt',encoding='utf-8') as f:
    for i,l in enumerate(f):
        lus=LU.findall(l)
        if len(lus)!=1 or '/*' in lus[0]: continue
        rs=set()
        for r in lus[0].split('/')[1:]:
            k=r.find('<')
            if k<0: continue
            t=norm(r[k:])
            if t.startswith('<n>') or t.startswith('<v>'): rs.add(t)
        for t in rs: prior[t]+=C[i]/len(rs)
tot=sum(prior.values())
json.dump(prior.most_common(300),open('priors_top.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
def lp(t): return math.log((prior.get(t,0)+1.0)/tot)
# 2. candidate readings per unknown LU
idx=[int(x) for x in open('unknown_idx.txt',encoding='utf-8')]
cands=[]  # per line: list of LUs, each (surface, [ (stem,pos,tags,raw) ])
S=collections.Counter()
with open('unknown_guess.txt',encoding='utf-8') as f:
    for j,l in enumerate(f):
        line=[]
        for lu in LU.findall(l):
            parts=lu.split('/');surf=parts[0]
            if len(parts)>1 and not parts[1].startswith('*') and not any('<guess>' in r for r in parts[1:]):
                line.append((surf,None));continue          # known piece (e.g. number, punctuation, known half of a hyphen compound)
            rd={}
            for r in parts[1:]:
                if '<guess>' not in r: continue
                k=r.find('<');stem=r[:k];tags=r[k:].replace('<guess>','')
                pos='v' if tags.startswith('<v>') else 'n'
                if len(stem)>=len(surf) or len(stem)<3: continue     # need an overt suffix and a stem of >=3 letters
                t=norm(tags);key=(stem,t)
                if key not in rd or len(r)<len(rd[key][3]): rd[key]=(stem,pos,t,r)
            line.append((surf,list(rd.values())))
            for st,pos in {(x[0],x[1]) for x in rd.values()}: S[(st,pos)]+=1
        cands.append(line)
# bare unknown words count as support for their own stem
bare=collections.Counter()
for line in cands:
    for surf,rs in line:
        if rs is not None and len(line)==1: bare[surf]+=1
E=json.load(open('stem_endings.json',encoding='utf-8'));EN=E['_n']
def plaus(stem,pos):
    c=E[pos].get(stem[-2:],0);return math.log((c+0.5)/(EN[pos]+0.5*400))-math.log(1/400)   # vs uniform over ~400 endings
SUFFIXY=('lar','lari','larin','ning','dagi','dan','ga','da','ni','si','miz','ingiz','im','lik')
FOREIGN=re.compile(r'w|c(?!h)|(ogo|ykh|aya|yye|skiy|skoy|skaya|tion|nnoy|ovna|ovich|evich|evna|iye)$')
out=open('guess_table.tsv','w',encoding='utf-8');n_g=0;n_c=0
for j,line in enumerate(cands):
    i=idx[j];res=[]
    ok=True
    for surf,rs in line:
        if rs is None: res.append(surf+'=known');continue
        best=[]
        name=B['mid'][i]>=0.6            # mostly capitalised mid-sentence: proper noun, so nominal readings only
        for stem,pos,t,r in rs:
            if name and pos=='v': continue
            s=S[(stem,pos)]+(1 if (pos=='n' and stem in bare) else 0)
            sc=lp(t)+1.5*math.log(s)+0.15*min(len(stem),10)+plaus(stem,pos)-(1.5 if stem.endswith(SUFFIXY) else 0)-(3 if '<vaux>' in t else 0)
            best.append((sc,stem,pos,t,s))
        if S[(surf,'n')]>=3 and not any(x[4]>=S[(surf,'n')] for x in best):   # skip if a suffixed reading has at least as much support                  # bare stem with >=3 suffixed relatives in the corpus competes as <n><nom>
            sb=S[(surf,'n')];best.append((lp('<n><nom>')+1.5*math.log(sb)+0.15*min(len(surf),10)+plaus(surf,'n')-(1.5 if surf.endswith(SUFFIXY) else 0),surf,'n','<n><nom>',sb))
        if not best: ok=False;res.append(surf+'=*');continue
        conf=True
        best.sort(reverse=True)
        res.append(' | '.join(f'{st}{t}<guess>:{sc:.1f}:{s}' for sc,st,pos,t,s in best[:3]))
        conf_ok = best[0][4]>=2 and not FOREIGN.search(surf)
        if not conf_ok: conf=False
    if ok: n_g+=1
    conf=ok and all(r.endswith('=known') or (float(r.split(' | ')[0].rsplit(':',1)[1])>=2 and len(r.split('<',1)[0])>=4 and '<vaux>' not in r.split(' | ')[0]) for r in res) and not FOREIGN.search(W[i].lower())
    if ok and B['mid'][i]>=0.6: res=[r if r.endswith('=known') else r.replace('<n>','<np>') for r in res]   # mostly capitalised mid-sentence in the corpus: proper noun
    if conf: n_c+=1
    out.write(f'{i}\t{W[i]}\t{C[i]}\t{int(ok)}\t{int(conf)}\t'+' ## '.join(res)+'\n')
print('guessed types',n_g,'confident',n_c,'of',len(cands))
import pickle
pickle.dump(dict(prior=dict(prior),tot=tot,S=dict(S),bare=dict(bare),E=E),open('guess_model.pkl','wb'))
print('model saved')

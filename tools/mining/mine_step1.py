# SPDX-License-Identifier: GPL-3.0-only
"""Phase 2 mining, step 1: candidate (stem, suffix) splits of still-unknown types, checked by analogy with model lemmas
through the v4 analyser itself (model + suffix must be analysed with the model's own lemma and POS)."""
import sys,pickle,re,subprocess,collections,json
sys.path.insert(0,'work/verify');import covlib
B=covlib.BASE;W=B['words'];C=B['cnt'];MID=B['mid'];CAPS=B['caps']
st=covlib.load('v4lem');K=('lower','title','upper')
ALPHA=re.compile(r"^[a-zʻʼ]+$")
unk=[i for i in range(len(W)) if all(st[k][i]=='U' for k in K) and ALPHA.match(W[i]) and len(W[i].replace('ʻ','').replace('ʼ',''))>=4]
print('unknown alphabetic types',len(unk),'tokens',sum(C[i] for i in unk))
MODELS={'N:C':'kitob','N:V':'olma','V:C':'yoz','V:A':'ishla','V:I':'oʻqi'}
POS={'N':'<n>','V':'<v>'}
def stemclass(s):
    last=s[-1]
    out=['N:'+('V' if last in 'aeiou' else 'C')]
    if last=='a': out.append('V:A')
    elif last=='i': out.append('V:I')
    elif last not in 'aeiouʻʼ': out.append('V:C')
    return out
splits=collections.defaultdict(list) # (cls, r) -> list of (i, stem)
for i in unk:
    w=W[i]
    for j in range(3,len(w)+1):
        s,r=w[:j],w[j:]
        if len(r)>14: continue
        if s.endswith('ʻ') and not s.endswith('oʻ'): continue
        if r.startswith('ʻ'): continue
        # k/q voicing before a vowel-initial suffix: yuragi = yurak + i
        cand=[s]
        if r and r[0] in 'aeiou':
            if s.endswith('gʻ'): cand.append(s[:-2]+'q')
            elif s.endswith('g'): cand.append(s[:-1]+'k')
        for s2 in cand:
            for cl in stemclass(s2):
                splits[(cl,r)].append((i,s2))
pairs=sorted({(cl,r) for cl,r in splits})
print('distinct (class,suffix)',len(pairs))
inp='\n'.join(MODELS[cl]+r for cl,r in pairs)+'\n'
out=subprocess.run(['lt-proc','-w','work/verify/v4lem.automorf.bin'],input=inp,capture_output=True,text=True).stdout.split('\n')
ok=set()
for (cl,r),l in zip(pairs,out):
    lus=re.findall(r'\^(.*?)\$',l)
    if len(lus)!=1: continue
    rs=lus[0].split('/')[1:]
    m=MODELS[cl];p=POS[cl[0]]
    if any(x.startswith(m+p) or (cl[0]=='N' and x.startswith(m+'<adj>')) for x in rs): ok.add((cl,r))
print('accepted (class,suffix)',len(ok))
cands=collections.defaultdict(lambda: collections.defaultdict(set))  # (stem,POS) -> suffix -> word idx
for (cl,r),lst in splits.items():
    if (cl,r) not in ok: continue
    for i,s in lst: cands[(s,cl[0])][r].add(i)
cands={k:{r:sorted(v) for r,v in d.items()} for k,d in cands.items() if len(d)>=3}
print('stems with >=3 accepted suffixes',len(cands))
pickle.dump(dict(unk=unk,cands=cands),open('work/morph/phase2/mining/step1.pkl','wb'))

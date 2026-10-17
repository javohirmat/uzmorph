# SPDX-License-Identifier: GPL-3.0-only
"""Phase 2 mining, step 2: greedy assignment, filters (known lemma, foreign/OCR, edit-distance-1 of a frequent known word),
POS/paradigm guess, ranked batches of 2,000 and spot-check sheets. Nothing is added to the lexicon."""
import sys,pickle,re,subprocess,collections,heapq,csv,random,json
sys.path.insert(0,'work/verify');import covlib
B=covlib.BASE;W=B['words'];C=B['cnt'];MID=B['mid']
st=covlib.load('v4lem');K=('lower','title','upper')
d=pickle.load(open('work/morph/phase2/mining/step1.pkl','rb'));cands=d['cands']
OUT='work/morph/phase2/mining'
MIN_TOK=50
tri=list(csv.DictReader(open('work/morph/triage/triage_top2000.csv',encoding='utf-8')))+list(csv.DictReader(open('work/morph/triage/hidden_unknowns.csv',encoding='utf-8')))
NONLEX={r['word'].lower() for r in tri if not ('ACTION: ADD' in r['note'] and r['category'] in ('new_stem','loanword_or_foreign','name'))}
widx={w:i for i,w in enumerate(W)}
PRETAKEN={widx[w] for w in NONLEX if w in widx}
print('triage-handled (rule/typo/skip) words removed from mining',len(PRETAKEN))
known_cnt={W[i]:C[i] for i in range(len(W)) if any(st[k][i]!='U' for k in K)}
# ---- candidate pre-scores
items=[]
for (s,P),suf in cands.items():
    ws=set(i for v in suf.values() for i in v)
    tok=sum(C[i] for i in ws)
    if tok<MIN_TOK: continue
    if len(s.replace('ʻ',''))<=3 and len(suf)<5: continue
    items.append([s,P,suf,tok])
print('pre-candidates',len(items))
# ---- is the stem already a known lemma of that POS?
import re as _re
VFRAG=_re.compile(r'(ayot|yot|averi|avera|aver|yver|guncha|gun|kun|qun|ar|ay|a)$')
NFRAG=_re.compile(r'(ka|ga|qa|da|dek|day|cha|ni)$')
probe=sorted({s for s,P,_,_ in items}|{s+'moq' for s,P,_,_ in items if P=='V'}
  |{VFRAG.sub('',s)+'moq' for s,P,_,_ in items if VFRAG.search(s)}|{NFRAG.sub('',s) for s,P,_,_ in items if NFRAG.search(s)})
out=subprocess.run(['lt-proc','-w','work/verify/v4lem.automorf.bin'],input='\n'.join(probe)+'\n',capture_output=True,text=True).stdout.split('\n')
an={}
for w,l in zip(probe,out):
    lus=re.findall(r'\^(.*?)\$',l)
    an[w]=lus[0].split('/')[1:] if len(lus)==1 and not lus[0].split('/')[1].startswith('*') else []
def known_as(s,P):
    if P=='N': return any(re.match(re.escape(s)+r'<(?!np|v>|mistake)',x) for x in an.get(s,[]))
    return any(re.match(re.escape(s)+r'<v>',x) for x in an.get(s+'moq',[]))
# ---- junk / foreign / typo filters
FOREIGN=re.compile(r"(ogo|ykh|yye|iye|nyy|skiy|skaya|skoe|stvo|stva|tion|ing|th|w|ee|oo|ll|ck|ph|sch)$|w|q[^aeiouʻ]|[^aeiou]{4}|(.)\2\2")
RU_END=re.compile(r"(ogo|ykh|iya$|iy$)")
ALPH='abcdefghijklmnopqrstuvxyzʻ'
def edit1(w):
    out=set()
    for i in range(len(w)+1):
        for c in ALPH: out.add(w[:i]+c+w[i:])
        if i<len(w):
            out.add(w[:i]+w[i+1:])
            for c in ALPH: out.add(w[:i]+c+w[i+1:])
    for a,b in (('u','oʻ'),('o','oʻ'),('g','gʻ'),('oʻ','u'),('oʻ','o'),('gʻ','g')):
        for m in re.finditer(re.escape(a),w): out.add(w[:m.start()]+b+w[m.end():])
    if w.startswith('e'): out.add('y'+w)
    out.discard(w);return out
DIA=(('u','oʻ'),('o','oʻ'),('g','gʻ'),('k','q'),('x','h'),('h','x'),('i','iy'),('e','ye'))
def dia_variants(w,depth=3):
    seen={w};frontier={w}
    for _ in range(depth):
        nxt=set()
        for x in frontier:
            for a,b in DIA:
                for m in re.finditer(re.escape(a),x):
                    if a=='o' and x[m.end():m.end()+1]=='ʻ': continue
                    if a=='g' and x[m.end():m.end()+1]=='ʻ': continue
                    y=x[:m.start()]+b+x[m.end():]
                    if y not in seen: seen.add(y);nxt.add(y)
        frontier=nxt
    seen.discard(w);return seen
def typo_of(w,c):
    best=None
    for v in dia_variants(w):
        k=known_cnt.get(v,0)
        if k>=3*c and k>=500 and (best is None or k>best[1]): best=(v,k,'lost-diacritic/variant spelling of')
    if best: return best
    for v in edit1(w):
        k=known_cnt.get(v,0)
        if k>=50*c and k>=1000 and (best is None or k>best[1]): best=(v,k,'edit-distance-1 of')
    return best
SUFFIXLIKE=set('lan lash lik lig li lar ish gan dagi chi siz lab la lan lash lashtir tir dir gina dek day cha moq mas ma ni ning dan ga da di sa gacha roq dir lari lari ing imiz ingiz uvchi ovchi ganlik maslik yap yotgan digan adigan rish lish nish sh'.split())
# ---- greedy (lazy) assignment
taken=set(PRETAKEN);heap=[(-t,n,s,P) for n,(s,P,suf,t) in enumerate(items)];heapq.heapify(heap)
idx={(s,P):(suf) for s,P,suf,t in items}
final=[];excluded=collections.Counter();exl=[]
while heap:
    negt,n,s,P=heapq.heappop(heap);suf=idx[(s,P)]
    live={r:[i for i in v if i not in taken] for r,v in suf.items()}
    live={r:v for r,v in live.items() if v}
    tok=sum(C[i] for v in live.values() for i in v)
    if tok<MIN_TOK or len(live)<3: continue
    if tok< -negt:
        heapq.heappush(heap,(-tok,n,s,P));continue
    words=sorted({i for v in live.values() for i in v},key=lambda i:-C[i])
    top=W[words[0]]
    reason=None
    if s in SUFFIXLIKE: reason='stem is a suffix fragment (tokenizer/line-break artefact)'
    elif known_as(s,P): reason='known lemma (rule/paradigm gap, not a new lemma)'
    elif VFRAG.search(s) and len(VFRAG.sub('',s))>=2 and an.get(VFRAG.sub('',s)+'moq') and any('<v>' in x for x in an[VFRAG.sub('',s)+'moq']): reason='known verb + aspect/converb fragment (rule gap)'
    elif NFRAG.search(s) and len(NFRAG.sub('',s))>=3 and an.get(NFRAG.sub('',s)) and not any(x.startswith('*') for x in an[NFRAG.sub('',s)]) and len(an[NFRAG.sub('',s)])>0 and not known_as(s,'N') and NFRAG.sub('',s) in an and not s.endswith(('cha','da')) : reason='known word + case/clitic fragment (rule gap)'
    elif FOREIGN.search(s) or 'w' in top: reason='foreign or OCR-looking'
    else:
        t1=typo_of(top,C[words[0]])
        if t1: reason=f'{t1[2]} known {t1[0]} ({t1[1]})'
        elif P=='V' and sum(C[i]*MID[i] for i in words)/tok>=0.5: reason='capitalised: name, not a verb'
        elif P=='V' and re.search(r'(aver|yver)$',s) and an.get(s[:-4]+'moq') : reason='rule R16 (-aver) on a known verb'
        elif P=='V' and re.search(r'(aver|yver)$',s): reason='rule R16 (-aver)'
        elif any(r.startswith('yy') for r in live): reason='suffix yy (R28 artefact)'
    if reason:
        excluded[reason.split(' known')[0].split(' (')[0]]+=tok;exl.append((s,P,tok,reason,[W[i] for i in words[:5]]))
        continue
    for i in words: taken.add(i)
    final.append((s,P,live,tok,words))
print('accepted candidates',len(final),'tokens',sum(f[3] for f in final));print('excluded tokens',dict(excluded))
# ---- POS / paradigm
POSS=re.compile(r'^(i|si|im|ing|imiz|ingiz|lari|ini|ida|iga|idan|ining|sini|sida|siga|sidan|sining)')
def guess(s,P,live,words):
    tok=sum(C[i] for i in words)
    capw=sum(C[i]*MID[i] for i in words)/tok
    if P=='N':
        if capw>=0.6:
            if re.search(r'(ov|ova|ev|eva|yev|yeva|iy)$',s): return 'NP-COG-MF','name (surname)',capw
            return 'NP-ANT/TOP?','name',capw
        bare=sum(C[i] for i in live.get('',[]))/tok
        inf=sum(C[i] for r,v in live.items() if POSS.match(r) or r.startswith('lar') for i in v)/tok
        if bare>=0.6 and inf<0.1: return 'A1','adjective (bare use dominant)',capw
        return 'N1','noun',capw
    if re.search(r'(lan|lash|in|il|ish|ay|ar)$',s): return 'V-IV','verb (intransitive guess)',capw
    return 'V-TV','verb (transitive guess)',capw
rows=[]
for s,P,live,tok,words in final:
    par,desc,capw=guess(s,P,live,words)
    lemma=s if not par.startswith('NP') else s[:1].upper()+s[1:]
    rows.append(dict(lemma=lemma,proposed_pos=par,description=desc,tokens=tok,n_forms=len(words),n_suffixes=len(live),
        example_forms=', '.join(W[i] for i in words[:6]),suffixes=', '.join(sorted(live,key=lambda r:-sum(C[i] for i in live[r]))[:10]),
        capitalised_share=round(capw,2)))
rows.sort(key=lambda r:-r['tokens'])
for n,r in enumerate(rows): r['rank']=n+1
fields=['rank','lemma','proposed_pos','description','tokens','n_forms','n_suffixes','example_forms','suffixes','capitalised_share']
nb=0
for b in range(0,len(rows),2000):
    nb+=1;batch=rows[b:b+2000]
    with open(f'{OUT}/batch_{nb:02d}.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(batch)
    random.seed(1000+nb);samp=random.sample(batch,min(100,len(batch)))
    with open(f'{OUT}/batch_{nb:02d}_spotcheck.csv','w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['lemma','proposed_pos','example_forms','tokens','ok(Y/N)','fix'])
        for r in sorted(samp,key=lambda r:-r['tokens']): w.writerow([r['lemma'],r['proposed_pos'],r['example_forms'],r['tokens'],'',''])
with open(f'{OUT}/excluded.tsv','w',encoding='utf-8') as f:
    f.write('stem\tclass\ttokens\treason\tforms\n')
    for e in sorted(exl,key=lambda e:-e[2]): f.write(f'{e[0]}\t{e[1]}\t{e[2]}\t{e[3]}\t{", ".join(e[4])}\n')
summ=dict(candidates=len(rows),batches=nb,tokens=sum(r['tokens'] for r in rows),
  per_batch=[sum(r['tokens'] for r in rows[b:b+2000]) for b in range(0,len(rows),2000)],
  pos=collections.Counter(r['proposed_pos'] for r in rows),excluded_tokens=dict(excluded),excluded_n=len(exl))
json.dump(summ,open(f'{OUT}/summary.json','w',encoding='utf-8'),indent=1,default=dict)
print(json.dumps(summ,indent=1,default=dict)[:1500])

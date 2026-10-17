# SPDX-License-Identifier: GPL-3.0-only
"""Phase 2 mining, step 3 (v2 filters after the native reviewer's batch-1 spot-check): greedy assignment, filters (known lemma, foreign/OCR, edit-distance-1 of a frequent known word),
POS/paradigm guess, ranked batches of 2,000 and spot-check sheets. Nothing is added to the lexicon."""
import sys,pickle,re,subprocess,collections,heapq,csv,random,json
sys.path.insert(0,'work/verify');import covlib
B=covlib.BASE;W=B['words'];C=B['cnt'];MID=B['mid']
st=covlib.load('v4lem');K=('lower','title','upper')
d=pickle.load(open('work/morph/phase2/mining/step1.pkl','rb'));cands=d['cands']
OUT='work/morph/phase2/mining_v2'
import os;os.makedirs(OUT,exist_ok=True)
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
AUX='qol ber ol yubor boʻl chiq ket kel tur yur oʻtir yot tashla qoʻy ko'.split()
VSUF=sorted(set('ayotganlik ayotgan yotgan ganlik maslik masmi mas mish ayotir ayoti ayot yot b averi avera aver yver guncha gun kun qun'.split()
   +[c+a for c in ('a','y','ib') for a in AUX]),key=len,reverse=True)
NSUF=sorted('roq nisi nis dek day gi ki mi ku'.split(),key=len,reverse=True)
VFRAG=_re.compile(r'(ayot|yot|averi|avera|aver|yver|guncha|gun|kun|qun|ar|ay|a)$')
NFRAG=_re.compile(r'(ka|ga|qa|da|dek|day|cha|ni)$')
probe=sorted({s for s,P,_,_ in items}|{s+'moq' for s,P,_,_ in items if P=='V'}
  |{VFRAG.sub('',s)+'moq' for s,P,_,_ in items if VFRAG.search(s)}|{NFRAG.sub('',s) for s,P,_,_ in items if NFRAG.search(s)}
  |{s[:-len(q)]+'moq' for s,P,_,_ in items for q in VSUF if s.endswith(q) and len(s)-len(q)>=2}
  |{s[:-len(q)] for s,P,_,_ in items for q in NSUF if s.endswith(q) and len(s)-len(q)>=2}
  |{s[:-2] for s,P,_,_ in items if P=='V' and s.endswith('la') and len(s)>=5}|{s[:-1] for s,P,_,_ in items if s.endswith('a') and len(s)>=5})
out=subprocess.run(['lt-proc','-w','work/verify/v4lem.automorf.bin'],input='\n'.join(probe)+'\n',capture_output=True,text=True).stdout.split('\n')
an={}
for w,l in zip(probe,out):
    lus=re.findall(r'\^(.*?)\$',l)
    an[w]=lus[0].split('/')[1:] if len(lus)==1 and not lus[0].split('/')[1].startswith('*') else []
def known_as(s,P):
    if P=='N': return any(re.match(re.escape(s)+r'<(?!np|v>|mistake)',x) for x in an.get(s,[])) or any('+' not in x and not re.search(r'<(np|mistake|v|vaux)>',x) for x in an.get(s,[]))
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
VOW='aoiue'
def vowel_variants(s):
    out=set()
    for i,ch in enumerate(s):
        if ch in VOW and not (ch=='o' and s[i+1:i+2]=='ʻ'):
            for v in VOW:
                if v!=ch: out.add(s[:i]+v+s[i+1:])
    return out
def stem_typo(s,words,tok):
    best=None
    for v in vowel_variants(s)|dia_variants(s,2):
        k=sum(known_cnt.get(v+W[i][len(s):],0) for i in words if W[i].startswith(s))
        if k>=3*tok and k>=1000 and (best is None or k>best[1]): best=(v,k)
    return best
import pymorphy3,wordfreq
RU=pymorphy3.MorphAnalyzer()
def ru_translit(s):
    if any(x in s for x in ('ʻ','ʼ','q')): return None
    s2=s
    for a,b in (('shch','щ'),('sh','ш'),('ch','ч'),('ts','ц'),('yo','ё'),('yu','ю'),('ya','я'),('ye','е')): s2=s2.replace(a,b)
    m=dict(zip('abvgdezijklmnoprstufxhy','абвгдезийклмнопрстуфххй'))
    return ''.join(m.get(c,c) for c in s2)
def russian_inflected(s):
    r=ru_translit(s)
    if not r or not RU.word_is_known(r) or not re.search(r'(a|i|y|ya|yu|e|u|o)$',s): return None
    ps=RU.parse(r)
    if any(('nomn' in p.tag and 'sing' in p.tag) or 'Fixd' in p.tag for p in ps): return None
    p=ps[0]
    if p.score>=0.4 and 'NOUN' in p.tag and ((p.normal_form.endswith(('ие','ье')) and not r.endswith(('ие','ье'))) or ('gent' in p.tag and p.normal_form.endswith('ок'))): return p.normal_form
    return None
def english_word(s):
    r=ru_translit(s)
    return len(s)>=3 and wordfreq.zipf_frequency(s,'en')>=4.0 and not (r and RU.word_is_known(r))
def fragment(s,tok):
    b=s[:-1]
    if s[-1] not in 'aeiouʻy' and len(b)>=4 and known_cnt.get(b,0)>=20*tok and an.get(b): return f'known word {b} + {s[-1]}'
    bare=C[widx[s]] if s in widx else 0
    for w in PREF.get(s,()):
        if known_cnt.get(w,0)>=50*tok and len(w)-len(s)<=2 and bare>=0.5*tok: return f'prefix of known {w}'
    return None
# fragments: candidate stem is a proper prefix (1-3 letters short) of a frequent known word (taxm -> taxmin)
PREF=collections.defaultdict(list)
_cs={s for s,P,_,_ in items}
for w,c in known_cnt.items():
    if c<20000: continue
    for k in (1,2,3):
        if len(w)-k>=4 and w[:-k] in _cs: PREF[w[:-k]].append(w)
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
    elif any(s.endswith(q) and len(s)-len(q)>=2 and any('<v>' in x for x in an.get(s[:-len(q)]+'moq',[])) for q in VSUF): reason='form of a known verb (aspect/converb/compound-verb chain)'
    elif any(s.endswith(q) and len(s)-len(q)>=2 and an.get(s[:-len(q)]) for q in NSUF): reason='form of a known word (+roq/-nisi/case/clitic)'
    elif fragment(s,tok): reason='fragment: '+fragment(s,tok)
    elif re.match(r"(u|bu|shu|oʻsha)nisi?$",s): reason='form of a known word (pronoun + -nisi)'
    elif P=='N' and s.endswith('a') and known_cnt.get(s[:-1],0)>=500 and any(x.startswith(s[:-1]+'<n>') for x in an.get(s[:-1],[])) and ru_translit(s) and RU.word_is_known(ru_translit(s)): reason='Russian-spelling variant of known %s'%s[:-1]
    elif russian_inflected(s): reason='Russian inflected form in Latin letters ('+russian_inflected(s)+')'
    elif english_word(s): reason='English word'
    elif stem_typo(s,words,tok): reason='typo/variant of known stem %s (%d)'%stem_typo(s,words,tok)
    else:
        t1=typo_of(top,C[words[0]])
        if t1: reason=f'{t1[2]} known {t1[0]} ({t1[1]})'
        elif P=='V' and sum(C[i]*MID[i] for i in words)/tok>=0.5: reason='capitalised: name, not a verb'
        elif P=='V' and re.search(r'(aver|yver)$',s) and an.get(s[:-4]+'moq') : reason='rule R16 (-aver) on a known verb'
        elif P=='V' and re.search(r'(aver|yver)$',s): reason='rule R16 (-aver)'
        elif any(r.startswith('yy') for r in live): reason='suffix yy (R28 artefact)'
    if reason:
        excluded[reason.split(' known')[0].split(' (')[0].split(':')[0]]+=tok;exl.append((s,P,tok,reason,[W[i] for i in words[:5]]))
        continue
    for i in words: taken.add(i)
    final.append((s,P,live,tok,words))
print('accepted candidates',len(final),'tokens',sum(f[3] for f in final));print('excluded tokens',dict(excluded))
# ---- POS / paradigm
POSS=re.compile(r'^(i|si|im|ing|imiz|ingiz|lari|ini|ida|iga|idan|ining|sini|sida|siga|sidan|sining)')
ADJ_END=re.compile(r'(ik|iv|al|ar|yar|on|ent|ant|oid|li|siz|iy|simon|chan|kor|bop|viy|niy|aviy|oviy)$')
def guess(s,P,live,words):
    tok=sum(C[i] for i in words)
    capw=sum(C[i]*MID[i] for i in words)/tok
    if P=='N':
        if capw>=0.6:
            if re.search(r'(ov|ova|ev|eva|yev|yeva|iy)$',s): return 'NP-COG-MF','name (surname)',capw
            return 'NP-ANT/TOP?','name',capw
        bare=sum(C[i] for i in live.get('',[]))/tok
        inf=sum(C[i] for r,v in live.items() if POSS.match(r) or r.startswith('lar') for i in v)/tok
        caps=sum(C[i]*B['caps'][i] for i in words)/tok
        if caps>=0.4 and len(s)<=5: return 'ABBR','abbreviation (mostly all-caps)',capw
        li=sum(C[i] for r,v in live.items() if r.startswith('li') and not r.startswith('lik') for i in v)/tok
        if li>=0.6: return 'A1:'+s+'li','adjective in -li (lemma %sli)'%s,capw
        ing=sum(C[i] for r,v in live.items() if r.startswith('ing') for i in v)/tok
        if ing>=0.6: return 'N1:'+s+'ing','noun in -ing (lemma %sing)'%s,capw
        if bare>=0.6 and inf<0.1 and ADJ_END.search(s): return 'A1','adjective (bare use dominant, adjectival ending)',capw
        return 'N1','noun',capw
    if s.endswith('la') and len(s)>=5:
        base=s[:-2]
        lash=sum(C[i] for i in words if W[i].startswith(s+'sh'))/tok
        bk='' if an.get(base) else ' [stem %s also unknown: add it]'%base
        if lash>=0.9: return 'V-IV:'+s+'sh','bogus -la: forms are %ssh- (lash verb)%s'%(s,bk),capw
        return 'V-TV','derived -la verb (stem %s%s)'%(base,' known' if not bk else ' unknown'),capw
    if re.search(r'(lan|lash|in|il|ish|ay|ar)$',s): return 'V-IV','verb (intransitive guess)',capw
    return 'V-TV','verb (transitive guess)',capw
rows=[]
for s,P,live,tok,words in final:
    par,desc,capw=guess(s,P,live,words)
    lemma=s if not par.startswith('NP') else s[:1].upper()+s[1:]
    if ':' in par: par,lemma=par.split(':')
    if par=='ABBR': lemma=s.upper()
    rows.append(dict(stem=s,lemma=lemma,proposed_pos=par,description=desc,tokens=tok,n_forms=len(words),n_suffixes=len(live),
        example_forms=', '.join(W[i] for i in words[:6]),suffixes=', '.join(sorted(live,key=lambda r:-sum(C[i] for i in live[r]))[:10]),
        capitalised_share=round(capw,2)))
rows.sort(key=lambda r:-r['tokens'])
for n,r in enumerate(rows): r['rank']=n+1
fields=['rank','stem','lemma','proposed_pos','description','tokens','n_forms','n_suffixes','example_forms','suffixes','capitalised_share']
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

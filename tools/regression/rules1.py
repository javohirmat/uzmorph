# SPDX-License-Identifier: GPL-3.0-only
import pickle,re,subprocess,json,collections
d=pickle.load(open('table.pkl','rb'))
W,C,L,T=d['words'],d['cnt'],d['low'],d['title']
unk=[(w,c) for w,c,l,t in zip(W,C,L,T) if l=='U' and t=='U']
print('unknown types>=3',len(unk),'tokens',f'{sum(c for _,c in unk):,}')
V='aeiouoʻ'
def vow(ch): return ch in 'aeiou'
CASE=r'(?:lar)?(?:i|si|im|ing|imiz|ingiz|lari)?(?:ni|ning|ga|da|dan|ka|qa|dagi|gi|dek|day|cha|ta)?(?:dir|mi|ku|ki)?'
cands=collections.defaultdict(set)  # word -> list of (rule, base, need)
def add(rule,w,base,need): cands[(rule,w)].add((base,need))
for w,c in unk:
    # R10 -(u)vchi (+ plural/case)
    m=re.match(r'^(.+?)(uvchi|ovchi)('+CASE+r')$',w)
    if m:
        s,suf=m.group(1),m.group(2)
        if suf=='ovchi': add('R10',w,s+'amoq','v')
        else:
            add('R10',w,s+'moq','v'); add('R10',w,s+'imoq','v')
    # R3 -ganlik / -maslik
    m=re.match(r'^(.+?)(gan|kan|qan|mas)li[kg]('+CASE+r')$',w)
    if m:
        s,suf=m.group(1),m.group(2)
        if suf=='mas': add('R3',w,s+'mas','v_or_cop')
        else: add('R3',w,s+suf,'v_or_cop')
    # R8 -roq
    m=re.match(r'^(.+?)(roq|rogʻ)('+CASE+r')$',w)
    if m and len(m.group(1))>=2: add('R8',w,m.group(1),'adj_adv')
    # R5 -gina
    m=re.match(r'^(.+?)(gina|kina|qina)$',w)
    if m and len(m.group(1))>=2: add('R5',w,m.group(1),'any')
    # R4 -ki
    m=re.match(r'^(.+?)ki$',w)
    if m and len(m.group(1))>=2: add('R4',w,m.group(1),'any')
    # R11 -(u)v verbal noun
    m=re.match(r'^(.+?)(uv|ov)('+CASE+r')$',w)
    if m and len(m.group(1))>=2:
        s,suf=m.group(1),m.group(2)
        if suf=='ov': add('R11',w,s+'amoq','v')
        else: add('R11',w,s+'moq','v'); add('R11',w,s+'imoq','v')
    # R7 non-voicing k/q: Vq+V...  -> try voiced spelling
    m=re.match(r'^(.*[aeiou](?:ʻ)?)(q|k)([aeiou].*)$',w)
    if m:
        pre,cons,rest=m.groups()
        alt=pre+('gʻ' if cons=='q' else 'g')+rest
        add('R7',w,alt,'n_known_voiced')
        add('R7',w,pre+cons,'n')   # bare stem must be known noun-ish
    # R9 -gacha
    m=re.match(r'^(.+?)(gacha|kacha|qacha)$',w)
    if m and len(m.group(1))>=2: add('R9',w,m.group(1),'any')
bases=sorted({b for v in cands.values() for b,_ in v})
print('bases',len(bases))
out=subprocess.run(['lt-proc','-w','work/morph/apertium-uzb/uzb.automorf.bin'],input='\n'.join(bases)+'\n',capture_output=True,text=True).stdout.split('\n')
an={}
for b,line in zip(bases,out):
    m=re.findall(r'\^(.*?)\$',line)
    if len(m)!=1 or '/*' in line: an[b]=[]
    else: an[b]=[a for a in m[0].split('/')[1:] if '<mistake>' not in a]
def ok(b,need):
    a=an.get(b,[])
    if not a: return False
    if need=='v': return any('<v>' in x for x in a)
    if need=='v_or_cop': return any('<v>' in x or '<cop>' in x for x in a)
    if need=='adj_adv': return any(('<adj>' in x or '<adv>' in x) and '+' not in x.split('<')[0] for x in a)
    if need=='n': return any(re.match(r'^[^<]+<(n|adj)>',x) for x in a)
    return True
res=collections.defaultdict(lambda:[0,0,[]])
cnt=dict(unk)
r7=collections.defaultdict(dict)
for (rule,w),bs in cands.items():
    if rule=='R7':
        r7[w].update({need:ok(b,need) for b,need in bs}); continue
    if any(ok(b,n) for b,n in bs):
        r=res[rule]; r[0]+=1; r[1]+=cnt[w]; r[2].append((cnt[w],w))
for w,f in r7.items():
    if f.get('n') and f.get('n_known_voiced'):
        r=res['R7']; r[0]+=1; r[1]+=cnt[w]; r[2].append((cnt[w],w))
prior={'R10':3421051,'R3':2642209,'R8':1304307,'R5':1128371,'R4':1264410,'R11':1193257,'R7':1141716,'R9':989504}
est={'R10':3421051,'R3':2642209,'R8':1292893,'R5':1116748,'R4':1087473,'R11':1085379,'R7':1072982,'R9':989504}
out={}
for k in prior:
    t,tok,ex=res[k]; ex.sort(reverse=True)
    print(f'{k}: my raw types {t:,} tokens {tok:,} | earlier raw {prior[k]:,} est {est[k]:,}')
    print('   top', ', '.join(f'{w} {c}' for c,w in ex[:15]))
    out[k]=dict(types=t,tokens=tok,top=ex[:300])
json.dump(out,open('rule_hits.json','w',encoding='utf-8'),ensure_ascii=False)

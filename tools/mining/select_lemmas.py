# SPDX-License-Identifier: GPL-3.0-only
import csv,collections,pickle,re,sys
B=pickle.load(open('work/verify/table.pkl','rb'));cnt=dict(zip(B['words'],B['cnt']))
r=list(csv.DictReader(open('work/morph/triage/work/stem_ranking.csv',encoding='utf-8')))
tri=list(csv.DictReader(open('work/morph/triage/triage_top2000.csv',encoding='utf-8')))+list(csv.DictReader(open('work/morph/triage/hidden_unknowns.csv',encoding='utf-8')))
act=collections.defaultdict(collections.Counter)
for t in tri:
    n=t['note'];a='ADD' if 'ACTION: ADD' in n else ('SKIP' if 'SKIP' in n else ('NORM' if 'NORMALISE' in n else 'OTHER'))
    act[t['lemma']][a]+=int(t['count'])
OKP={'N1','A1','A2','ABBR','NP-COG-MF','V-TV','ADV','NP-ANT-M','NP-ANT-F','NP-TOP','V-IV','NP-AL','NP-ORG','IJ','ADV1','V-TV-CAUS','ADV2','CS','CC','CA','PAREN'}
for x in r: x['tok']=int(x['tokens_top2000'])+int(x['tokens_hidden'])
r.sort(key=lambda x:-x['tok'])
sel=[];skipped=[]
for x in r:
    lem=x['lemma'];p=x['paradigm'];why=None
    a=act[lem];top=a.most_common(1)[0][0] if a else 'NONE'
    forms=[f.strip() for f in x['forms'].split(',') if f.strip()]
    if top!='ADD': why='action '+top
    elif ' ' in lem: why='multiword'
    elif p not in OKP: why='paradigm '+p
    elif x['confidence']=='low': why='low confidence'
    elif x['confidence']=='medium' and p in ('ABBR','IJ','ADV1','ADV2','CS','CC','CA','PAREN'): why='medium closed-class'
    elif p=='ABBR' and not any(f.lower()==lem.lower() for f in forms): why='abbr surface differs from lemma'
    if why: skipped.append((lem,p,x['tok'],why)); continue
    surf=[lem];flag=''
    # non-voicing k/q (R7 style) for nominals ending in vowel+k/q
    if p in('N1','A1','A2') and re.search(r'[aeiou](k|q)$',lem):
        c=lem[-1];v=lem[:-1]+('g' if c=='k' else 'gʻ')
        nv=sum(cnt.get(lem+s,0) for s in('i','ini','ida','iga','im'));vv=sum(cnt.get(v+s,0) for s in('i','ini','ida','iga','im'))
        if nv>vv:
            surf=[lem[:-1]+('%{K%}' if c=='k' else '%{Q%}')];flag=f'no voicing ({lem}i {nv} vs {v}i {vv})'
            if vv>=0.2*nv: surf.append(lem+'@DirLR');flag+='; voiced form kept for analysis'
    # elision: forms that do not start with the lemma
    if p in('N1',) and any(not f.startswith(lem) for f in forms) and re.search(r'[aeiou][a-zʻ]$',lem):
        el=re.sub(r'([aeiou])([a-zʻ]+)$',lambda m:m.group(2),lem) if False else lem[:-2]+lem[-1]
        if any(f.startswith(el) for f in forms): surf.append(el+'@DirLR');flag=(flag+'; ' if flag else '')+f'elided stem {el} (analysis only)'
    for f in forms:
        if f.lower()==lem.lower() and f!=lem and p in('ABBR','NP-TOP','NP-ORG','NP-AL'): surf.append(f+'@DirLR');flag=(flag+'; ' if flag else '')+f'casing variant {f} (analysis only)'
    sel.append(dict(lemma=lem,surface='|'.join(surf),paradigm=p,gloss=x['gloss'],tokens=x['tok'],category=x['category'],confidence=x['confidence'],forms=x['forms'],flag=flag))
    if len(sel)>=int(sys.argv[1]): break
w=csv.DictWriter(open('lemmas_v4.tsv','w',encoding='utf-8'),fieldnames=list(sel[0].keys()),delimiter='\t');w.writeheader();w.writerows(sel)
with open('lemmas_v4_skipped.tsv','w',encoding='utf-8') as f:
    f.write('lemma\tparadigm\ttokens\treason\n')
    for s in skipped: f.write('\t'.join(map(str,s))+'\n')
print(len(sel),'selected; skipped before cutoff',len(skipped),'; tokens',sum(s['tokens'] for s in sel))
print([s for s in sel if s['flag']][:30])

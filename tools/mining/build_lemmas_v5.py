# SPDX-License-Identifier: GPL-3.0-only
"""lemmas_v5.tsv = (a) batch-1 rows adjudicated good (with fixes) + strong corrected lemmas, (b) Wikipedia/Wikidata-verified regenerated batch-1 lemmas.
Skips anything the v4 analyzer already analyses as that lemma."""
import csv,subprocess,re
M='work/morph/phase2/'
PAR={'N1':'N1','A1':'A1','V-TV':'V-TV','V-IV':'V-IV','NP-TOP':'NP-TOP','NP-ANT-M':'NP-ANT-M','NP-ANT-F':'NP-ANT-F','NP-COG-MF':'NP-COG-MF','ABBR':'ABBR','ADV':'ADV'}
out=[]
for r in csv.DictReader(open(M+'mining/batch_01_adjudicated.csv',encoding='utf-8')):
    if r['final_ok'] in 'YF':
        out.append(dict(lemma=r['final_lemma'],surface=r['final_lemma'],paradigm=PAR[r['final_pos']],gloss='',tokens=r['tokens'],category='batch01_adjudicated_'+r['category'],confidence='verified',forms=r['example_forms'],flag='v5 batch-1 spot-check (the native reviewer + evidence)'))
EXTRA=[('zaiflash','V-IV','zaiflashib 4,751, zaiflashgan 2,684; batch-1 row zaifla'),('barqarorlash','V-IV','barqarorlashgan 1,858; batch-1 row barqarorla'),
       ('diskont','N1','bare diskont 4,479; stem of batch-1 row diskontla'),('topta','V-TV','toptab 1,688, toptay 1,718: open item')]
for l,p,ev in EXTRA: out.append(dict(lemma=l,surface=l,paradigm=p,gloss='',tokens='',category='v5_corrected',confidence='verified',forms=ev,flag='v5 corrected lemma'))
for r in csv.DictReader(open(M+'wiki/batch01_wiki_accepted.tsv',encoding='utf-8'),delimiter='\t'):
    out.append(dict(lemma=r['lemma'],surface=r['lemma'],paradigm=r['paradigm'],gloss='',tokens=r['tokens'],category='wiki_verified',confidence='high',forms=r['forms'],flag='v5 uz.wiki '+r['wiki_title']+' '+(r['qid'] or '')))
seen=set();o2=[]
for r in out:
    k=(r['lemma'].lower(),r['paradigm'][:2])
    if k in seen: continue
    seen.add(k);o2.append(r)
probe=[r['lemma']+('moq' if r['paradigm'].startswith('V') else '') for r in o2]
an=subprocess.run(['lt-proc','-w','work/verify/v4lem.automorf.bin'],input='\n'.join(probe)+'\n',capture_output=True,text=True).stdout.split('\n')
final=[];skip=[]
for r,a in zip(o2,an):
    tag={'N1':'<n>','A1':'<adj>','V-':'<v>','NP':'<np>','AB':'<abbr>','AD':'<adv>'}[r['paradigm'][:2]]
    if re.search(r'/'+re.escape(r['lemma'])+re.escape(tag),a,re.I): skip.append(r['lemma']);continue
    final.append(r)
with open(M+'lemmas_v5.tsv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(final[0]),delimiter='\t');w.writeheader();w.writerows(final)
print('lemmas_v5',len(final),'skipped already-known',skip)
import collections;print(collections.Counter(r['category'].split('_')[0] for r in final))

# SPDX-License-Identifier: GPL-3.0-only
import csv,subprocess,re,sys
M='work/morph/phase2/'
prev={r['lemma'].lower() for f in ('lemmas_v4.tsv','lemmas_v5.tsv','lemmas_v6_batch02.tsv') for r in csv.DictReader(open(M+f,encoding='utf-8'),delimiter='\t')}
MALE={'Alyosha','Slava'};TOPOK={'Dalvarzin','Qazvin','Saxalin','Muruntov','Qoratov'}
for b in sys.argv[1:]:
    rows=[];seen=set()
    for r in csv.DictReader(open(M+f'wiki/batch{b}_wiki_accepted.tsv',encoding='utf-8'),delimiter='\t'):
        k=r['lemma'].lower()
        if k in prev or k in seen: continue
        seen.add(k);rows.append(dict(lemma=r['lemma'],surface=r['lemma'],paradigm=r['paradigm'],gloss='',tokens=r['tokens'],category=f'wiki_verified_batch{b}',confidence='high',forms=r['forms'],flag='uz.wiki '+r['wiki_title']+' '+(r['qid'] or '')))
    an=subprocess.run(['lt-proc','-w','work/verify/v7.automorf.bin'],input='\n'.join(r['lemma'] for r in rows)+'\n',capture_output=True,text=True).stdout.split('\n')
    fin=[];skip=[]
    for r,a in zip(rows,an):
        tag={'N1':'<n>','A1':'<adj>','NP':'<np>'}[r['paradigm'][:2]]
        if re.search('/'+re.escape(r['lemma'])+re.escape(tag),a,re.I): skip.append(r['lemma']);continue
        if '<v>' in a: skip.append(r['lemma']+'(verb form)');continue   # e.g. baholash = bahola+sh
        if r['paradigm']=='N1' and re.search(r'(lar)$',r['lemma']):   # plural page title -> singular lemma
            r['lemma']=r['surface']=r['lemma'][:-3];r['flag']+=' (plural title, singularised)'
        if r['paradigm'].startswith('NP-ANT-F') and r['lemma'] in MALE: r['paradigm']='NP-ANT-M';r['flag']+=' (gender fixed)'
        if r['paradigm']=='NP-TOP' and re.search(r'(ov|ev|in|yev)$',r['lemma']) and r['lemma'] not in TOPOK:
            r['paradigm']='NP-COG-MF';r['flag']+=' (surname-shaped place title -> COG)'
        fin.append(r)
    prev|={r['lemma'].lower() for r in fin}
    with open(M+f'lemmas_v7_batch{b}.tsv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(fin)
    import collections
    print(b,[x for x in skip],len(fin),'skipped',len(skip),collections.Counter(r['paradigm'] for r in fin),sum(int(r['tokens']) for r in fin))

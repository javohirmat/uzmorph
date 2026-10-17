# SPDX-License-Identifier: GPL-3.0-only
import os,csv,json,collections,random
M='work/morph/phase2/'
B=os.environ.get('BATCH','01')
rows={r['lemma']:r for r in csv.DictReader(open(M+'mining_v2/batch_%s.csv'%B+'',encoding='utf-8'))}
W=json.load(open(M+'wiki/batch%s_wiki.json'%B+'',encoding='utf-8'))
adj={r['lemma'].lower() for r in csv.DictReader(open(M+'mining/batch_01_adjudicated.csv',encoding='utf-8'))}
BAD={'Q5','Q101352','Q202444','Q12308941','Q11879590','Q3409032','Q4167410','Q11424','Q482994','Q7366','Q5398426','Q13442814','Q134556','Q7725634','Q571','Q1004','Q215380','Q4830453','Q43229','Q783794','Q891723','Q3918','Q875538','Q163740','Q15632617','Q95074','Q14897293'}
GEOOK={'Q265','Q232','Q863','Q813','Q874','Q889','Q794','Q159','Q796','Q858','Q851','Q43','Q79','Q843','Q668','Q148','Q212','Q184','Q230','Q227','Q399'}
REGION={'Q5107','Q855697','Q82794','Q6256','Q3624078','Q55833','Q1620908','Q34876','Q15642541','Q3024240','Q28171280'}
NAMEM={'Q12308941','Q202444','Q3409032'};NAMEF={'Q11879590'};FAM={'Q101352'}
out=[];why=collections.Counter()
for l,v in W.items():
    r=rows[l]; pos=r['proposed_pos']
    if l.lower() in adj: why['already adjudicated']+=1;continue
    if not v['exists'] or v['disambig']: why['no page/disambig']+=1;continue
    if len(l)<=3 or pos=='ABBR': why['short/abbr']+=1;continue
    p31=set(v.get('p31',[]) or [])
    human='Q5' in p31; place=v.get('p625') or False
    if pos.startswith('NP'):
        if human: np='NP-ANT-F' if 'Q6581072' in (v.get('p21') or []) else 'NP-ANT-M'
        elif p31&FAM or (pos=='NP-COG-MF' and not place): np='NP-COG-MF' if p31&FAM else None
        elif p31&NAMEF: np='NP-ANT-F'
        elif p31&NAMEM: np='NP-ANT-M'
        elif place and not p31&BAD and not v['redirect'] and (set(v.get('p17') or [])&GEOOK or (p31|set(v.get('p279') or []))&REGION): np='NP-TOP'
        else: np=None
        if not np: why['NP but wiki item not person/place/name']+=1;continue
        out.append(dict(lemma=l,paradigm=np,tokens=int(r['tokens']),wiki_title=v['title'],qid=v.get('qid'),forms=r['example_forms'],basis='uz.wiki page + Wikidata class'))
    else:
        if human or place or p31&BAD or 'Q41710' in p31 or v.get('p21') or not (p31 or v.get('p279')): why['common-noun guess but wiki item is a name/place/work']+=1;continue
        if not v.get('qid'): why['page without Wikidata item']+=1;continue
        par='A1' if pos=='A1' and l.endswith(('ik','iv')) and not l.endswith('lik') else 'N1'
        tt=v['title'].lower()
        if v['redirect']:
            if l.lower().startswith(tt) and len(tt)>=4: l=tt
            elif not tt.startswith(l.lower()[:max(4,len(l)-3)]): why['redirect to a different title']+=1;continue
        out.append(dict(lemma=l,paradigm=par,tokens=int(r['tokens']),wiki_title=v['title'],qid=v.get('qid'),forms=r['example_forms'],basis='uz.wiki page (common noun) + Wikidata item'))
out.sort(key=lambda r:-r['tokens'])
with open(M+'wiki/batch%s_wiki_accepted.tsv'%B+'','w',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0]),delimiter='\t');w.writeheader();w.writerows(out)
print(len(out),sum(r['tokens'] for r in out),dict(why),collections.Counter(r['paradigm'] for r in out))
random.seed(3)
for r in random.sample(out,45): print(r['lemma'],r['paradigm'],r['tokens'],r['wiki_title'],'|',r['forms'][:50])

# SPDX-License-Identifier: GPL-3.0-only
"""Map all analyses into the scheme -> ../private/cands.json (per script, per word token)."""
import json,os,sys
sys.path.insert(0,os.path.dirname(__file__)); import scheme as S
from types import SimpleNamespace as NS
P=os.path.join(os.path.dirname(__file__),'..','private')
SUF=os.environ.get('SUF',''); O=json.load(open(f'{P}/ours{SUF}.json',encoding='utf-8')); Z=json.load(open(f'{P}/zirh.json',encoding='utf-8'))
def uniq(xs):
    seen=set();out=[]
    for x in xs:
        k=(S.lnorm(x[0]),x[1],S.fstr(x[2]))
        if k not in seen: seen.add(k); out.append([x[0],x[1],S.fstr(x[2])])
    return out
res={}
for script in ('lat','cyr','new'):
    R={}
    for key,zs in Z[script].items():
        o=O[script][key]
        allc,known=S.ap_candidates(o['lus'])
        cg,_=S.ap_candidates(o['cg'])
        gc,gk=S.ap_candidates(o['guess']); gac,gak=S.ap_candidates(o['guess_all'])
        nread=len(o['lus'][-1].split('/'))-1 if o['lus'] and known else 0
        zc=[S.map_zirh(NS(**{k:v for k,v in z.items() if k not in('prefix','tagged','cost')}),z['prefix']) for z in zs]
        R[key]=dict(input=o['input'],ours=uniq(allc),ours_known=known,ours_nread=nread,ours_cg=uniq(cg)[:1],
                    guess=uniq(gc) if not known else [],guess_all=uniq(gac) if not known else [],
                    zirh=uniq(zc),zirh_known=bool(zs and zs[0]['known']),zirh_nread=len(zs),zirh_best=uniq(zc)[:1],
                    zirh_tagged=[z['tagged'] for z in zs[:3]])
    res[script]=R
json.dump(res,open(f'{P}/cands{SUF}.json','w',encoding='utf-8'),ensure_ascii=False)
L=res['lat']
agree=sum(1 for v in L.values() if v['ours_cg'] and v['zirh_best'] and S.lemma_ok(v['ours_cg'][0][0],v['zirh_best'][0][0]) and v['ours_cg'][0][2]==v['zirh_best'][0][2])
print('tokens',len(L),'ours known',sum(v['ours_known'] for v in L.values()),'zirh known',sum(v['zirh_known'] for v in L.values()),'cg==zirh(lemma+feats)',agree)

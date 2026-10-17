# SPDX-License-Identifier: GPL-3.0-only
"""Head-to-head scoring against the provisional gold. Writes ../results/scores.json and ../results/scores.md"""
import json,os,sys
from collections import defaultdict
sys.path.insert(0,os.path.dirname(__file__)); import scheme as S
B=os.path.join(os.path.dirname(__file__),'..'); P=B+'/private'; R=B+'/results'; os.makedirs(R,exist_ok=True)
C=json.load(open(f"{P}/cands{os.environ.get('SUF','')}.json",encoding='utf-8'))
G=[g for g in json.load(open(f'{P}/gold.json',encoding='utf-8')) if g['upos']!='PUNCT' and 'num' not in g['flags'].split(',')]
EXCL={'affix','abbr','foreign','typo'}
GEN={'B':'books','W':'wiki','N':'news','T':'telegram'}
def nf(u,f):
    f=S.parse_fstr(f) if isinstance(f,str) else dict(f)
    if f.get('VerbForm') in('Part','Vnoun'): f['VerbForm']='PartVn'
    if 'Poss' not in f and f.get('Case')=='Nom': f.pop('Case')
    if f.get('Number')=='Sing' and f.get('VerbForm')!='Fin': f.pop('Number')
    if u=='PRON': f.pop('Number',None)
    return tuple(sorted(f.items()))
def judge(c,g):
    alts=[a for a in g['alts'].split('/') if a]
    lem=S.lemma_ok(c[0],g['lemma'],alts); up=c[1]==g['upos']; co=S.coarse(c[1])==S.coarse(g['upos'])
    fe=nf(c[1],c[2])==nf(g['upos'],g['feats'])
    return dict(lemma=lem,upos=up,coarse=co,feats=fe,lf=lem and fe,full=lem and co and fe)
def systems(v):
    """-> {system: (covered, candidates, best)}"""
    o=v['ours']; ok=v['ours_known']
    best=(v['ours_cg'] or o[:1]) if ok else []
    gu=v['guess']; ga=v['guess_all']
    return {
     'ours':(ok,o if ok else [],best[:1]),
     'ours+guess':(ok or bool(gu),o if ok else gu,best[:1] if ok else gu[:1]),
     'ours+guess_all':(ok or bool(ga),o if ok else ga,best[:1] if ok else ga[:1]),
     'zirh_known':(v['zirh_known'],v['zirh'] if v['zirh_known'] else [],v['zirh_best'] if v['zirh_known'] else []),
     'zirh':(True,v['zirh'],v['zirh_best']),
    }
M=('lemma','upos','coarse','feats','lf','full')
def blank(): return dict(n=0,cov=0,reads=0,mreads=0,**{f'or_{m}':0 for m in M},**{f'b_{m}':0 for m in M})
def main():
    res={}
    for script in ('lat','cyr','new'):
        A=defaultdict(blank)
        for g in G:
            fl=set(g['flags'].split(','))
            sub='typo' if 'typo' in fl else ('excluded' if fl&EXCL else 'main')
            v=C[script][g['key']]; gen=GEN[g['key'][0]]
            for sysn,(cov,cands,best) in systems(v).items():
                for grp in (('all',sub),(gen,sub),('names' if 'name' in fl else 'nonnames',sub)):
                    a=A[(sysn,)+grp]; a['n']+=1
                    if not cov: continue
                    a['cov']+=1
                    a['mreads']+=len(cands)
                    a['reads']+=(v['ours_nread'] if sysn.startswith('ours') and v['ours_known'] else (len(cands) if sysn.startswith('ours') else v['zirh_nread']))
                    js=[judge(c,g) for c in cands]
                    for m in M:
                        a[f'or_{m}']+=any(j[m] for j in js)
                        a[f'b_{m}']+=bool(best) and judge(best[0],g)[m]
        res[script]={'|'.join(k):v for k,v in A.items()}
    json.dump(res,open(f'{R}/scores.json','w',encoding='utf-8'),indent=1)
    def pct(a,b): return f'{100*a/b:.1f}' if b else '-'
    L=['# Provisional head-to-head (gold = model-built first pass, NOT yet checked by the native reviewer)','',
       'Accuracy is over ALL evaluable word tokens (an uncovered token counts as wrong). "oracle" = gold among the candidates; "best" = first/top reading (ours: CG -1; Zirh: lowest cost).',
       'Excluded from main: typo, affix fragments, abbreviations/letters, foreign-language words. Feats compare Case/Number/Poss/Person/VerbForm(Part≡Vnoun)/Mood/TAM/Polarity/Voice=Pass; full = lemma + coarse POS + feats.','']
    for script in ('lat','cyr','new'):
        for grp in ('all','books','wiki','news','telegram','names','nonnames'):
            L.append(f'## {script} / {grp} (main tokens)'); L.append('')
            L.append('| system | n | cov | lemma or/best | UPOS or/best | coarse or/best | feats or/best | lemma+feats or/best | full or/best | readings raw/mapped |')
            L.append('|---|---|---|---|---|---|---|---|---|---|')
            for sysn in ('ours','ours+guess','ours+guess_all','zirh_known','zirh'):
                a=res[script].get(f'{sysn}|{grp}|main')
                if not a: continue
                n=a['n']
                L.append(f"| {sysn} | {n} | {pct(a['cov'],n)} | "+' | '.join(f"{pct(a['or_'+m],n)} / {pct(a['b_'+m],n)}" for m in M)+f" | {a['reads']/max(a['cov'],1):.2f} / {a['mreads']/max(a['cov'],1):.2f} |")
            L.append('')
        a1=res[script]
        L.append(f'### {script} / typo tokens'); L.append('')
        for sysn in ('ours','ours+guess','zirh_known','zirh'):
            a=a1.get(f'{sysn}|all|typo')
            if a: L.append(f"- {sysn}: n={a['n']} cov={pct(a['cov'],a['n'])} lemma-oracle={pct(a['or_lemma'],a['n'])} full-best={pct(a['b_full'],a['n'])}")
        L.append('')
    open(f'{R}/scores.md','w',encoding='utf-8').write('\n'.join(L))
    print('\n'.join(L[:60]))
    
if __name__=="__main__": main()

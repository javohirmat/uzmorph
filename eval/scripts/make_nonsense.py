# SPDX-License-Identifier: GPL-3.0-only
"""Generate ~300 plausible Uzbek non-words with 0 corpus hits (wordfreq_lat_full, 10.5M types). -> ../nonsense/nonwords.tsv"""
import json,os,random,sqlite3,re
B=os.path.join(os.path.dirname(__file__),'..')
db=sqlite3.connect('work/cache/wordfreq_lat_full.sqlite')
def hits(w): r=db.execute('select n from wf where w=?',(w,)).fetchone(); return r[0] if r else 0
G=json.load(open(f'{B}/private/gold.json',encoding='utf-8'))
rnd=random.Random(20261017)
V='aeiouoʻ'
def isv(ch): return ch in 'aeiou'
ok=lambda w: re.fullmatch(r"[a-zʻʼ]+",w) is not None
nouns=sorted({g['lemma'] for g in G if g['upos']=='NOUN' and ok(g['lemma']) and 3<=len(g['lemma'])<=9 and hits(g['lemma'])>5000 and not g['flags']})
verbs=sorted({g['lemma'] for g in G if g['upos']=='VERB' and ok(g['lemma']) and 2<=len(g['lemma'])<=8 and hits(g['lemma']+'moq')+hits(g['lemma']+'ish')>2000 and not g['lemma'].endswith(('sh','ish'))})
forms=sorted({g['tok'].lower() for g in G if g['upos'] in('NOUN','VERB','ADJ') and ok(g['tok'].lower()) and len(g['tok'])>=6 and hits(g['tok'].lower())>2000 and not g['flags']})
print(len(nouns),len(verbs),len(forms))
def px3(n): return n+('si' if n[-1] in 'aeiou' else 'i')
def pl(n): return n+'lar'
gens={
 # NB: options that can be legal clitics/colloquial copulas (-da, -am/-m, -di, -sh nominals) removed
 # spelling errors on real frequent word forms
 'typo_swap':   lambda: (lambda w,i: w[:i]+w[i+1]+w[i]+w[i+2:])(*(lambda w:(w,rnd.randrange(1,len(w)-2)))(rnd.choice(forms))),
 'typo_drop':   lambda: (lambda w,i: w[:i]+w[i+1:])(*(lambda w:(w,rnd.randrange(1,len(w)-1)))(rnd.choice(forms))),
 'typo_subst':  lambda: (lambda w,i: w[:i]+rnd.choice('bdfgklmnprstvxyz' if not isv(w[i]) else 'aeiu')+w[i+1:])(*(lambda w:(w,rnd.randrange(1,len(w)-1)))(rnd.choice(forms))),
 # morphotactic violations
 'case_before_pl':   lambda: rnd.choice(nouns)+rnd.choice(['dan','ni','ga','ning'])+'lar',
 'case_before_poss': lambda: rnd.choice(nouns)+rnd.choice(['ga','da','dan'])+rnd.choice(['im','ing','imiz']),
 'double_case':      lambda: rnd.choice(nouns)+rnd.choice(['ning','ga','dan'])+rnd.choice(['ni','dan','ga']),
 'wrong_px3_allomorph': lambda: (lambda n: n+('i' if n[-1] in 'aeiou' else 'si'))(rnd.choice(nouns)),
 'verb_stem+case':   lambda: rnd.choice(verbs)+rnd.choice(['larda','dan','ning','lardan','ni']),
 'noun+verb_tense':  lambda: rnd.choice(nouns)+rnd.choice(['yapti','moqda','ib','adi','gan']),
 'tense_before_neg': lambda: rnd.choice(verbs)+rnd.choice(['dima','ganma','yaptima'])+rnd.choice(['di','k']),
}
out=[];seen=set()
for name,f in gens.items():
    want=30; tries=0; got=0
    while got<want and tries<5000:
        tries+=1
        try: w=f()
        except (IndexError,ValueError): continue
        if w in seen or not ok(w) or len(w)<4 or hits(w)>0: continue
        seen.add(w); out.append((w,name)); got+=1
with open(f'{B}/nonsense/nonwords.tsv','w',encoding='utf-8') as fo:
    fo.write('word\ttype\tcorpus_hits\n')
    for w,t in out: fo.write(f'{w}\t{t}\t0\n')
from collections import Counter; print(len(out),Counter(t for _,t in out))

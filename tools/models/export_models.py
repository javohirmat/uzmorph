# SPDX-License-Identifier: GPL-3.0-only
"""Write the shipped, pickle-free model files in uzmorph/data/ from the research (corpus) models.

Usage: python tools/models/export_models.py PHASE3_DIR GUESSER_DIR OUT_DIR
  PHASE3_DIR  : priors.pkl, context.pkl, paradigm.pkl, capstats.pkl, name_sufprior.pkl, names_list.tsv
                (built by em_priors.py, build_context.py, paradigm.py, capstats.py, name_sufprior.py, names_mine.py + names_verify.py)
  GUESSER_DIR : guess_model.pkl (built by build_guess_table.py)
  OUT_DIR     : normally uzmorph/data

Every mapping is written with its keys sorted alphabetically (lists sorted too), so no file preserves the order in which
words were met in the corpus. The pruning below is lossless for the code paths in uzmorph/ that read these files."""
import sys,pickle,json,gzip,csv,os
P3,GD,OUT=sys.argv[1:4]
def dump(name,obj):
    with gzip.GzipFile(os.path.join(OUT,name),'wb',mtime=0) as g:      # mtime=0: reproducible bytes
        g.write(json.dumps(obj,ensure_ascii=False,separators=(',',':'),sort_keys=True).encode('utf-8'))
pr=pickle.load(open(f'{P3}/priors.pkl','rb'))
# q (per-word posteriors of the top types) is not read at run time
dump('priors.json.gz',dict(theta=pr['theta'],phi=pr['phi'],floor_t=pr['floor_t'],floor_f=pr['floor_f']))
cx=pickle.load(open(f'{P3}/context.pkl','rb'))
dump('context.json.gz',dict(p=sorted([a,b,v] for (a,b),v in cx['p'].items()),uni=cx['uni'],floor=cx['floor']))
dump('paradigm.json.gz',pickle.load(open(f'{P3}/paradigm.pkl','rb'))['PU'])
cs=pickle.load(open(f'{P3}/capstats.pkl','rb')); CAP,LO=cs['cap'],cs['lo']
# names.py reads CAP/LO only in evidence() (forms with cap>=lo) and capratio() (thresholds need cap>=3)
cap={w:c for w,c in CAP.items() if c>=3 or c>=LO.get(w,0)}
dump('capstats.json.gz',dict(cap=cap,lo={w:LO[w] for w,c in cap.items() if c>=3 and w in LO}))
with open(os.path.join(OUT,'name_sufprior.json'),'w',encoding='utf-8') as f:
    json.dump(pickle.load(open(f'{P3}/name_sufprior.pkl','rb')),f,ensure_ascii=False,indent=0,sort_keys=True)
with open(f'{P3}/names_list.tsv',encoding='utf-8') as f:
    rows=list(csv.DictReader(f,delimiter='\t'))
with open(os.path.join(OUT,'names_list.tsv'),'w',encoding='utf-8') as fo:
    fo.write('stem\tclass\ttokens\twikidata\n')       # Wikipedia titles dropped (CC BY-SA); Wikidata ids are CC0
    for r in sorted(rows,key=lambda r:r['stem']): fo.write(f"{r['stem']}\t{r['class']}\t{r['tokens']}\t{r['qid']}\n")
gm=pickle.load(open(f'{GD}/guess_model.pkl','rb'))
# an S value of 1 behaves like absence (s<1 -> 1) unless the stem is also in 'bare' (+1); 'bare' only matters for stems in S
bare={st for (st,pos) in gm['S'] if pos=='n' and st in gm['bare']}
S={f'{st}\t{pos}':v for (st,pos),v in gm['S'].items() if v>1 or (pos=='n' and st in bare)}
dump('guess_model.json.gz',dict(prior=gm['prior'],tot=gm['tot'],S=S,bare=sorted(bare),E=gm['E']))
for f in sorted(os.listdir(OUT)): print(f,os.path.getsize(os.path.join(OUT,f)))

# SPDX-License-Identifier: GPL-3.0-only
"""Run v8d (+CG best, +guesser) on all eval tokens in 3 scripts -> ../private/ours.json
Latin: direct. Cyrillic: our cyr2lat then v8d (pipeline). 2026-Latin: our new2lat then v8d (pipeline)."""
import json,sys,os,re,subprocess
from uzmorph import translit as T
P=os.path.join(os.path.dirname(__file__),'..','private')
A=os.environ.get('MORPHDIR','work/morph/apertium-uzb-v4'); SUF=os.environ.get('SUF','')   # SUF=_v9 with MORPHDIR=apertium-uzb-v5
MORPH=f'{A}/uzb.automorf.bin'; RLX=f'{A}/uzb.rlx.bin'; GW='work/morph/phase2/guesser/uzb_guess.py'
LU=re.compile(r'\^((?:[^$\\]|\\.)*)\$')
S=[json.loads(l) for l in open(f'{P}/sentences.jsonl',encoding='utf-8')]
def to_lat(t,script):
    if script=='lat': return t['lat']
    if script=='cyr': return T.cyr2lat(t['cyr'])
    return T.new2lat(t['new'])
ESC=re.compile(r'([\\\[\]^$/@<>{}*+#])')
def lus_of(lines,binary_cmd):
    out=subprocess.run(binary_cmd,input='\n'.join(ESC.sub(r'\\\1',x) for x in lines)+'\n',capture_output=True,text=True).stdout.split('\n')
    return [LU.findall(o) for o in out[:len(lines)]]
res={}
for script in ('lat','cyr','new'):
    toks=[(s['id'],t['i'],to_lat(t,script)) for s in S for t in s['tokens']]
    uniq=sorted({x[2] for x in toks})
    an=dict(zip(uniq,lus_of(uniq,['lt-proc','-w',MORPH])))
    gu=dict(zip(uniq,lus_of(uniq,['python3',GW,'--main',MORPH,'--guesser',f'{A}/uzb_guesser.automorf.bin'])))         # main analyses; unknown LUs replaced by confident guesses
    gua=dict(zip(uniq,lus_of(uniq,['python3',GW,'--all','--main',MORPH,'--guesser',f'{A}/uzb_guesser.automorf.bin'])))
    # CG best: one sentence per line, LUs in order
    sent_lines=[];spans={}
    for s in S:
        parts=[]
        for t in s['tokens']:
            l=an[to_lat(t,script)]; spans[(s['id'],t['i'])]=(len(parts),len(parts)+len(l)); parts+=l
        sent_lines.append(' '.join('^'+p+'$' for p in parts)+' ^./.<sent>$')
    cg=subprocess.run(['cg-proc','-1',RLX],input='\n'.join(sent_lines)+'\n',capture_output=True,text=True).stdout.split('\n')
    R={}
    for s,line in zip(S,cg):
        got=LU.findall(line)
        for t in s['tokens']:
            a,b=spans[(s['id'],t['i'])]; src=to_lat(t,script)
            R[f"{s['id']}:{t['i']}"]=dict(input=src,lus=an[src],cg=got[a:b],guess=gu[src],guess_all=gua[src])
    n=sum(1 for s in S for t in s['tokens'] if len(LU.findall(cg[S.index(s)]))!=0)
    res[script]=R
    print(script,'tokens',len(R),file=sys.stderr)
json.dump(res,open(f'{P}/ours{SUF}.json','w',encoding='utf-8'),ensure_ascii=False)

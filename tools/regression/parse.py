# SPDX-License-Identifier: GPL-3.0-only
import re,gzip,sys,pickle
lu=re.compile(r'\^(.*?)\$')
def status(line):
    lus=lu.findall(line)
    if not lus: return 'U'
    mis=False
    for x in lus:
        parts=x.split('/')
        if len(parts)<2 or parts[1].startswith('*'): return 'U'
        if all('<mistake>' in a for a in parts[1:]): mis=True
    return 'M' if mis else 'K'
def load(fn):
    with open(fn,encoding='utf-8') as f: return [status(l) for l in f]
if __name__=='__main__':
    words=[];cnt=[];s3=[];caps=[];mid=[]
    with gzip.open('work/morph/full_step3/word_freq.tsv.gz','rt') as f:
        next(f)
        for l in f:
            p=l.rstrip('\n').split('\t')
            words.append(p[0]);cnt.append(int(p[1]));s3.append(p[3]=='1');mid.append(float(p[4] or 0));caps.append(float(p[5] or 0))
    d=dict(words=words,cnt=cnt,s3=s3,mid=mid,caps=caps,low=load('lt_lower.txt'))
    for k in ('title','upper'):
        try: d[k]=load(f'lt_{k}.txt')
        except FileNotFoundError: pass
    pickle.dump(d,open('table.pkl','wb'))
    print(len(words),{k:len(v) for k,v in d.items()})

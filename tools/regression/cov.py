# SPDX-License-Identifier: GPL-3.0-only
import pickle
d=pickle.load(open('table.pkl','rb'))
N=1463539297
cnt=d['cnt'];tot=sum(cnt);print('word_freq tokens',f'{tot:,}','share',tot/N,'rest (<3)',f'{N-tot:,}')
def cov(pred): return sum(c for c,p in zip(cnt,pred) if p)
L,T,U=d['low'],d['title'],d['upper']
rows=[('step3 apertium_known flag',d['s3']),
('lowercase lookup',[x!='U' for x in L]),('lowercase, no mistake-only',[x=='K' for x in L]),
('lower|Title',[a!='U' or b!='U' for a,b in zip(L,T)]),('lower|Title no-mistake',[a=='K' or b=='K' for a,b in zip(L,T)]),
('any of lower/Title/UPPER',[a!='U' or b!='U' or c!='U' for a,b,c in zip(L,T,U)]),
('any, no-mistake',[a=='K' or b=='K' or c=='K' for a,b,c in zip(L,T,U)])]
for n,p in rows:
    v=cov(p);print(f'{n:30s} {v:>15,} {100*v/N:.2f}%')
est=0;estK=0
for c,a,b,u,cap,mid in zip(cnt,L,T,U,d['caps'],d['mid']):
    lp=c*(1-cap)
    est+= c*cap*(u!='U') + lp*(1-mid)*(a!='U') + lp*mid*(b!='U')
    estK+= c*cap*(u=='K') + lp*(1-mid)*(a=='K') + lp*mid*(b=='K')
print('case-class approx',f'{100*est/N:.2f}','no-mistake',f'{100*estK/N:.2f}')
# disagreement step3 vs lower|title
dis=[(c,w,s,a,b) for w,c,s,a,b in zip(d['words'],cnt,d['s3'],L,T) if s!=((a!='U') or (b!='U'))]
dis.sort(reverse=True);print('disagreements',len(dis),sum(x[0] for x in dis));print(dis[:25])

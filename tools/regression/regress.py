#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Regression + coverage for a build. Usage: regress.py TAG GENBIN [PREVTAG]
Statuses come from work/verify/<tag>_status.pkl (lt-proc over word_freq types >=3 in lower/Title/UPPER)."""
import sys,pickle,random,re,subprocess,json
sys.path.insert(0,'work/verify');import covlib
tag,gen=sys.argv[1],sys.argv[2];prev=sys.argv[3] if len(sys.argv)>3 else 'tb'
GEN=[('yondash<v><iv><ger><nom>','yondashuv'),('koʻzla<v><tv><pass><gpr_rsub>','koʻzlangan'),('gap<n><loc><attr>','gapdagi'),
('obroʻ<n><px3sp><nom>','obroʻsi'),('ye<v><tv><aor><p3><sg>','yeydi'),('de<v><tv><fut2><p1><sg>','derman'),('uy<n><loc><subst><pl><nom>','uydagilar'),
('ye<v><tv><prc_impf>','yeya'),('huquq<n><px3sp><nom>','huquqi'),('kel<v><iv><gpr_pot>','keluvchi'),
('bagʻir<n><px3sp><nom>','bagʻri'),('ogʻiz<n><px3sp><acc>','ogʻzini'),('ogʻiz<n><loc>','ogʻizda'),('de<v><tv><prc_impf>','deya'),('topta<v><tv><prc_perf>','toptab'),('haqida<post><attr>','haqidagi'),
('kel<v><iv><ger_prog><px3sp><nom>','kelayotganligi'),('nari<adv><comp>','nariroq'),('tushun<v><iv><prc_perf>','tushunib'),('muloqot<n><loc>','muloqotda'),('talafot<n><pl><nom>','talafotlar'),('ustuvorlik<n><px3sp><nom>','ustuvorligi'),('OTM<abbr><dat>','OTMga'),
('kel<v><iv><neg><gpr_pres>','kelmayotgan'),('kel<v><iv><neg><ger_pres><pl><acc>','kelmayotganlarni'),('bor<v><iv><gna_prog>','borayotib'),('nari<adv><comp><subst><loc>','nariroqda'),('durang<n><dat>','durangga'),
('ket<v><iv><prog><p3><sg>','ketyapti'),('oʻqi<v><tv><prog><p1><sg>','oʻqiyapman'),('kel<v><iv><neg><prog><p3><sg>','kelmayapti'),('bil<v><tv><ger_inf><px3sp><nom>','bilmogʻi'),('bil<v><tv><ger_inf><nom>','bilmoq'),('taʼkidla<v><tv><prc_perf>','taʼkidlab'),('samo<n><dat>','samoga'),('qoplagich<n><px3sp><nom>','qoplagichi'),('alahla<v><iv><prc_perf>','alahlab'),('qara<v><iv><opt><p1><pl>','qaraylik'),('qara<v><iv><opt><p1><sg>','qaray'),('bor<v><iv><opt><p1><pl>','boraylik'),('ye<v><tv><opt><p1><pl>','yeylik'),('kel<v><iv><gna_until>','kelguncha'),('chiq<v><iv><gna_until>','chiqquncha'),('kel<v><iv><gna_until><px3sp>','kelgunicha')]
# v7: analysis-only rules must not generate
NOGEN=['bor<v><iv><prc_impf>+ber<vaux><aor><p3><sg>','kel<v><iv><past>+e<cop><ifi><colloq><p1><sg>','boʻl<v><iv><aor><arch><p3><sg>','qil<v><tv><past><evid><arch><p3><sg>','bor<v><iv><prog><evid><p3><sg>','qoʻy<v><tv><prc_impf>+qol<vaux><imp><p2><sg>','boʻl<v><iv><fut2>+e<cop><past><evid><p3><sg>','qil<v><tv><ger_inf><arch><nom>']
inp='\n'.join('^'+a+'$' for a,_ in GEN)+'\n'
out=subprocess.run(['lt-proc','-g',gen],input=inp,capture_output=True,text=True).stdout.strip().split('\n')
gres=[(a,w,o,w in o.split('/') and not any(b in o for b in ('tushin','muloqat','talofat','ustivor','takidla','samoʻ','qoplagʻich','ayab'))) for (a,w),o in zip(GEN,out)]
ng=subprocess.run(['lt-proc','-g',gen],input='\n'.join('^'+a+'$' for a in NOGEN)+'\n',capture_output=True,text=True).stdout.strip().split('\n')
gres+=[(a,'#',o,o.startswith('#')) for a,o in zip(NOGEN,ng)]
B=covlib.BASE;W=B['words'];C=B['cnt']
st=covlib.load(tag);orig=pickle.load(open('work/verify/orig_status.pkl','rb'));pv=covlib.load(prev) if prev!='orig' else orig
K=('lower','title','upper')
def known(s,i): return any(s[k][i]!='U' for k in K)
loss_orig=[(C[i],W[i]) for i in range(len(W)) if known(orig,i) and not known(st,i)]
loss_prev=[(C[i],W[i]) for i in range(len(W)) if known(pv,i) and not known(st,i)]
gain_prev=[(C[i],i) for i in range(len(W)) if not known(pv,i) and known(st,i)]
loss_orig.sort(reverse=True);loss_prev.sort(reverse=True)
random.seed(1);samp=random.sample(gain_prev,min(50,len(gain_prev)))
an={}
want={i for _,i in samp}
with open(f'work/verify/{tag}_lower.txt',encoding='utf-8') as f:
    for j,l in enumerate(f):
        if j in want: an[j]=l.strip()
with open(f'work/verify/{tag}_title.txt',encoding='utf-8') as f:
    for j,l in enumerate(f):
        if j in want and ('/*' in an.get(j,'/*')): an[j]=l.strip()
fig=covlib.figures(st)
res=dict(tag=tag,figures=fig,generation=gres,loss_vs_orig=dict(types=len(loss_orig),tokens=sum(c for c,_ in loss_orig),top=loss_orig[:80]),
 loss_vs_prev=dict(prev=prev,types=len(loss_prev),tokens=sum(c for c,_ in loss_prev),top=loss_prev[:80]),
 gain_vs_prev=dict(types=len(gain_prev),tokens=sum(c for c,_ in gain_prev)),
 sample=[(C[i],W[i],an.get(i,'')[:200]) for c,i in sorted(samp,reverse=True)])
json.dump(res,open(f'work/morph/phase2/regress_{tag}.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(json.dumps({k:res[k] for k in ('figures','generation')},ensure_ascii=False,indent=0))
print('loss vs orig',res['loss_vs_orig']['types'],res['loss_vs_orig']['tokens'],loss_orig[:30])
print('loss vs',prev,res['loss_vs_prev']['types'],res['loss_vs_prev']['tokens'],loss_prev[:30])
print('gain vs',prev,res['gain_vs_prev'])

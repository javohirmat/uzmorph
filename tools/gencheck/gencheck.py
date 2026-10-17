# SPDX-License-Identifier: GPL-3.0-only
"""Generation check for the -ish- plural flaw: verbs x tenses x persons; flags outputs carrying an -ish- variant outside p3 pl."""
import subprocess,json
V=[('oʻqi','tv'),('kel','iv'),('bor','iv'),('yoz','tv'),('ishla','iv'),('ayt','tv'),('qara','iv')]
T=['<prog>','<aor>','<ifi>','<past>','<fut>','<neg><aor>','<neg><ifi>','<gna_cond>','<neg><gna_cond>','<fut2>','<opt>','<imp>']
P=['<p1><sg>','<p2><sg>','<p3><sg>','<p1><pl>','<p2><pl>','<p2><frm>','<p3><pl>']
def run(gen):
    q=[f'{v}<v><{t}>{tn}{p}' for v,t in V for tn in T for p in P]
    out=subprocess.run(['lt-proc','-g',gen],input='\n'.join('^'+x+'$' for x in q)+'\n',capture_output=True,text=True).stdout.strip().split('\n')
    bad=[];n=0;multi=0
    for a,o in zip(q,out):
        if o.startswith('#'): continue
        n+=1; v=a.split('<')[0]; forms=o.split('/'); multi+=len(forms)>1
        stem=v[:-1] if v.endswith(('a','i')) else v
        if any('ish' in f[len(stem):len(stem)+4] for f in forms) and '<p3><pl>' not in a: bad.append((a,o))
    return n,multi,bad
res={}
for tag,g in (('v8d','work/morph/apertium-uzb-v4/uzb.autogen.bin'),('v9','work/morph/apertium-uzb-v5/uzb.autogen.bin'),('v9.1','work/morph/apertium-uzb-v6/uzb.autogen.bin')):
    n,multi,bad=run(g); res[tag]=dict(generated=n,multi_output=multi,ish_outside_p3pl=len(bad),examples=bad[:6])
    print(tag,'generated',n,'multi-form outputs',multi,'-ish- outside p3 pl:',len(bad),bad[:3])
json.dump(res,open('gencheck.json','w'),ensure_ascii=False,indent=1)

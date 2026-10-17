# SPDX-License-Identifier: GPL-3.0-only
"""Raw token coverage of one or more dictionary builds (covlib.figures over the uz-books-v2 word-frequency list, types >=3 uses).
Usage: dictionary_coverage.py OUT.json TAG [TAG ...]   (TAG: lt-proc outputs in work/verify, e.g. orig = upstream 00522e3)"""
import sys,json
sys.path.insert(0,'work/verify'); import covlib
res={t:{k:round(v,3) for k,v in covlib.figures(covlib.load(t)).items() if k!='known_tokens'} for t in sys.argv[2:]}
print(json.dumps(res,indent=1)); json.dump(res,open(sys.argv[1],'w',encoding='utf-8'),indent=1)

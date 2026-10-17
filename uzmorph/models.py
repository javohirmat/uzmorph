# SPDX-License-Identifier: GPL-3.0-only
"""Lazy loading of the bundled model files in uzmorph/data/."""
import gzip,json,os,functools
DATA=os.path.join(os.path.dirname(os.path.abspath(__file__)),'data')
def path(name): return os.path.join(DATA,name)
@functools.lru_cache(None)
def load(name):
    p=path(name)
    if name.endswith('.gz'):
        with gzip.open(p,'rt',encoding='utf-8') as f: return json.load(f)
    with open(p,encoding='utf-8') as f: return json.load(f)

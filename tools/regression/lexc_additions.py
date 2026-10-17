# SPDX-License-Identifier: GPL-3.0-only
"""Count what this release adds to apertium-uzb.uzb.lexc relative to upstream (line multiset diff, like `diff`).
usage: lexc_additions.py UPSTREAM_LEXC OUR_LEXC [OUT.json]"""
import sys,json,collections,difflib
up=open(sys.argv[1],encoding='utf-8').read().split('\n'); ours=open(sys.argv[2],encoding='utf-8').read().split('\n')
add=[];rem=[]
for op,a1,a2,b1,b2 in difflib.SequenceMatcher(None,up,ours,autojunk=False).get_opcodes():
    if op in ('replace','delete'): rem+=up[a1:a2]
    if op in ('replace','insert'): add+=ours[b1:b2]
def kind(l):
    s=l.strip()
    if not s: return 'blank'
    if s.startswith('!'): return 'comment'          # notes, and upstream entries that were commented out
    return 'entry_or_rule'
r={'added_lines':len(add),'removed_lines':len(rem),
   'added_by_kind':dict(collections.Counter(map(kind,add))),'removed_by_kind':dict(collections.Counter(map(kind,rem))),
   'note':'entry_or_rule = non-blank, non-comment added lines (new or edited lexicon entries and continuation-class lines); '
          'an edited upstream line counts once as removed and once as added.'}
print(json.dumps(r,indent=1))
if len(sys.argv)>3: json.dump(r,open(sys.argv[3],'w',encoding='utf-8'),indent=1)

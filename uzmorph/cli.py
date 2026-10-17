# SPDX-License-Identifier: GPL-3.0-only
"""Command line: `uzmorph analyze [TEXT]` (stdin if no text) and `uzmorph generate LEMMA TAGS`."""
import argparse,json,sys
from dataclasses import asdict
from .analyzer import Analyzer
def main(argv=None):
    try: return _main(argv)
    except RuntimeError as e:          # lt-proc missing, failing or hanging
        print(f'uzmorph: {e}',file=sys.stderr); return 2
def _main(argv=None):
    ap=argparse.ArgumentParser(prog='uzmorph',description='Uzbek morphological analyzer and generator')
    sp=ap.add_subparsers(dest='cmd',required=True)
    a=sp.add_parser('analyze',help='analyse text (one token per line, best reading first)')
    a.add_argument('text',nargs='*'); a.add_argument('--script',default='auto',choices=['auto','lat','cyr','new'],
        help="input script: official Latin, Cyrillic, 2026 Latin, or auto-detect Cyrillic (default)")
    a.add_argument('-n','--nbest',type=int,default=1,help='readings per token (0 = all)')
    a.add_argument('--json',action='store_true',help='JSON lines output (one token per line)')
    a.add_argument('--no-guess',action='store_true',help='dictionary only: no guesser, no proper-noun guessing')
    g=sp.add_parser('generate',help='generate surface forms'); g.add_argument('lemma'); g.add_argument('tags',help="e.g. '<v><tv><prog><p1><sg>' or v.tv.prog.p1.sg")
    x=ap.parse_args(argv)
    if x.cmd=='generate':
        an=Analyzer(); tags=x.tags if '<' in x.tags else x.tags.split('.')
        try: forms=an.generate(x.lemma,tags)
        except ValueError as e: print(f'uzmorph: {e}',file=sys.stderr); return 2
        print('\n'.join(forms) if forms else f'(no form generated for {x.lemma}{x.tags})'); return 0 if forms else 1
    an=Analyzer(guess=not x.no_guess,names_level=0 if x.no_guess else 1)
    text=' '.join(x.text) if x.text else sys.stdin.read()
    toks=an.analyze(text,x.script)        # one batch: all lines in a single lt-proc call per transducer
    for i,t in enumerate(toks):
        if i and t.sent!=toks[i-1].sent and not x.json: print()      # blank line between sentences
        rs=t.readings if x.nbest==0 else t.readings[:x.nbest]
        if x.json: print(json.dumps(dict(asdict(t),readings=[asdict(r) for r in rs]),ensure_ascii=False)); continue
        if not t.is_word: print(t.text); continue
        if not rs: print(f'{t.text}\t*unknown'); continue
        for r in rs: print('\t'.join([t.text,r.lemma,r.upos,r.feats,r.analysis,r.source]))
    return 0
if __name__=='__main__': sys.exit(main())

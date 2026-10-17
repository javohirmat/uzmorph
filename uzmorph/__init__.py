# SPDX-License-Identifier: GPL-3.0-only
"""uzmorph: Uzbek morphological analysis and generation (improved Apertium uzb + guesser + corpus ranker)."""
from .analyzer import Analyzer,Token,Reading,to_latin
__version__='0.9.0'
_default=None
def _get():
    global _default
    if _default is None: _default=Analyzer()
    return _default
def analyze(text,script='auto'):
    """text -> list of Token with ranked readings. script: 'auto' | 'lat' | 'cyr' | 'new' (2026 Latin)"""
    return _get().analyze(text,script)
def generate(lemma,tags):
    """lemma + Apertium tags (string '<v><tv>...' or list) -> surface forms"""
    return _get().generate(lemma,tags)
__all__=['analyze','generate','Analyzer','Token','Reading','to_latin']

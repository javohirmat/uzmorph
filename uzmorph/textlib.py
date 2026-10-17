# SPDX-License-Identifier: GPL-3.0-only
"""Normalisation, tokenisation and sentence splitting (the same rules used to build the evaluation set)."""
import re
AP="‘’'`ʼʻ"
def norm(s):
    """Normalise to current official Latin as used by our tools: oʻ gʻ with U+02BB, tutuq ʼ U+02BC."""
    s=s.replace('\u00a0',' ').replace('\u200b','')
    s=re.sub(r"([OoGg])["+AP+"]",r"\1ʻ",s)
    s=re.sub(r"(?<=[A-Za-z])["+AP.replace("ʻ","")+r"](?=[A-Za-z])","ʼ",s)
    s=re.sub(r"[ \t]+"," ",s).strip()
    return s
# a run of other letters (e.g. Cyrillic left untransliterated) is one non-word token, not one token per character
TOKRE=re.compile(r"\d+(?:[.,:]\d+)*(?:-[A-Za-zʻʼ]+)?|[A-Za-zʻʼ]+(?:-[A-Za-zʻʼ]+)*|[^\W\dA-Za-z_ʻʼ]+|[^\sA-Za-z\dʻʼ]")
def tokenize(s): return TOKRE.findall(s)
def is_word(t): return bool(re.match(r"^[A-Za-zʻʼ]",t))
HYPH_BREAK=re.compile(r"(\w)-[ \t]*\n[ \t]*(?=[a-zʻʼ])")
def split_sents(t,drop_hyphen_breaks=False):
    """paragraphs -> sentences. A word broken across lines by a hyphen (kito-\nblar) is rejoined when the next line
    continues in lower case. drop_hyphen_breaks=True instead drops such paragraphs (used only to build the evaluation
    set, where OCR-damaged paragraphs were excluded)."""
    t=t.replace('\r\n','\n').replace('\r','\n')
    t=re.sub(r"\s*\n\s*\n\s*","\n\n",t)
    out=[]
    for para in re.split(r"\n\n+",t):
        if drop_hyphen_breaks and re.search(r"\w-\n\w",para): continue     # the evaluation-set rule, kept as it was
        if re.search(r"\w-[ \t]*\n[ \t]*\w",para):                    # kito-\nblar and kito- \nblar
            para=HYPH_BREAK.sub(r"\1",para)
            para=re.sub(r"(\w)-[ \t]*\n[ \t]*(?=\w)",r"\1-",para)      # before a capital: keep the hyphen (ilmiy-\nAmaliy)
        para=re.sub(r"\s*\n\s*"," ",para)
        out+= [x.strip() for x in re.split(r"(?<=[.!?…])\s+(?=[A-Z«“\"—–(])",para) if x.strip()]
    return out

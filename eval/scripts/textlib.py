# SPDX-License-Identifier: GPL-3.0-only
import re
AP="‘’'`ʼʻ"
def norm(s):
    """Normalise to current official Latin as used by our tools: oʻ gʻ with U+02BB, tutuq ʼ U+02BC."""
    s=s.replace('\u00a0',' ').replace('\u200b','')
    s=re.sub(r"([OoGg])["+AP+"]",r"\1ʻ",s)
    s=re.sub(r"(?<=[A-Za-z])["+AP.replace("ʻ","")+r"](?=[A-Za-z])","ʼ",s)
    s=re.sub(r"[ \t]+"," ",s).strip()
    return s
TOKRE=re.compile(r"\d+(?:[.,:]\d+)*(?:-[A-Za-zʻʼ]+)?|[A-Za-zʻʼ]+(?:-[A-Za-zʻʼ]+)*|[^\sA-Za-z\dʻʼ]")
def tokenize(s): return TOKRE.findall(s)
def is_word(t): return bool(re.match(r"^[A-Za-zʻʼ]",t))
def split_sents(t):
    t=re.sub(r"\s*\n\s*\n\s*","\n\n",t)
    out=[]
    for para in re.split(r"\n\n+",t):
        if re.search(r"\w-\n\w",para): continue                       # hyphenated line breaks (OCR)
        para=re.sub(r"\s*\n\s*"," ",para)
        out+= [x.strip() for x in re.split(r"(?<=[.!?…])\s+(?=[A-Z«“\"—–(])",para) if x.strip()]
    return out
EMOJI=re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200d\u2B00-\u2BFF\U000E0000-\U000E007F]+")
def good_sent(s,minw=5,maxw=35,need_end=True):
    if re.search(r"[\u0400-\u04FF]",s): return False
    if re.search(r"http|www\.|@|#|\.uz\b|\.com\b|[|_=<>{}\[\]\\]",s): return False
    if re.search(r"[^\x20-\x7E‘’ʼʻ“”«»…—–№°]",s): return False        # other scripts, ü/ö (2026 Latin or Turkish), symbols
    if need_end and s[-1] not in ".!?…": return False
    if not re.match(r"^[A-Z«“\"—–(]",s): return False
    toks=tokenize(norm(s)); w=[t for t in toks if is_word(t)]
    if not (minw<=len(w)<=maxw): return False
    if sum(1 for x in w if len(x)==1 and x.lower() not in ("u","a","va","i")) >1: return False
    if sum(1 for x in w if x.isupper() and len(x)>1)>2: return False
    if len(w)/max(1,len(toks))<0.6: return False
    fw=sum(1 for x in w if x.lower() in FOREIGN_SW)
    if fw>=2 or (fw>=1 and len(w)<8): return False
    if re.search(r"\d[A-Za-z]{3,}\d",s): return False                    # glued page chrome (700koʻrishlar0izoh)
    return True
FOREIGN_SW={"the","of","and","to","in","for","with","on","is","po","na","dlya","chto","ti","ili","ot","pri","von","der","und","de","la","le","du"}
def template_key(s): return re.sub(r"\d+([.,]\d+)?","0",s.lower())

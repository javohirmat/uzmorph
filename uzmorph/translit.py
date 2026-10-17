# SPDX-License-Identifier: GPL-3.0-only
"""Deterministic Uzbek script converters.
Input Latin = 1995 Latin as normalised by uzmorph.textlib.norm (ʻ in oʻ/gʻ, ʼ = tutuq belgisi).
lat2cyr, cyr2lat, lat2new (2026 reform: oʻ->ö, gʻ->ğ, sh->ş, ch->ç; ng unchanged), new2lat."""
import re
V="aeiouoʻAEIOU"
LV=set("aeiouAEIOU")
# --- loanword helpers for Latin->Cyrillic (ц, word-initial е/э) ---
TS_WORDS={"sirk":"цирк","sement":"цемент","sex":"цех","sentner":"центнер","sentr":"центр","sentral":"централ","sikl":"цикл","sivilizatsiya":"цивилизация","sitata":"цитата","sifer":"цифер","sifr":"цифр"}
def _case(src,out):
    if not src: return out
    if src.isupper() and len(src)>1: return out.upper()
    if src[0].isupper(): return out[:1].upper()+out[1:]
    return out
L2C=[("oʻ","ў"),("gʻ","ғ"),("sh","ш"),("ch","ч"),("ng","нг"),("yo","ё"),("yu","ю"),("ya","я"),("ye","е"),("ts","ц"),
     ("a","а"),("b","б"),("d","д"),("e","е"),("f","ф"),("g","г"),("h","ҳ"),("i","и"),("j","ж"),("k","к"),("l","л"),("m","м"),
     ("n","н"),("o","о"),("p","п"),("q","қ"),("r","р"),("s","с"),("t","т"),("u","у"),("v","в"),("x","х"),("y","й"),("z","з"),("ʼ","ъ"),("c","ц"),("w","в")]
def _lat2cyr_word(w):
    lw=w.lower().replace("‘","ʻ").replace("'","ʼ").replace("’","ʼ")
    core=lw
    for k,v in TS_WORDS.items():
        if core.startswith(k): return _case(w,v+_lat2cyr_word(w[len(k):]).lower()) if len(w)>len(k) else _case(w,v)
    out=[];i=0;n=len(lw)
    while i<n:
        c=lw[i]
        if c=="s" and lw[i+1:i+3]=="ʼh": out.append("сҳ");i+=3;continue          # Isʼhoq -> Исҳоқ
        if lw.startswith("tsiya",i) or (lw.startswith("siya",i) and i>0 and lw[i-1] in "nk"):
            out.append("ция");i+=5 if lw.startswith("tsiya",i) else 4;continue
        if c=="e":
            prev=lw[i-1] if i>0 else ""
            out.append("э" if (i==0 or prev in "aeiou") else "е");i+=1;continue          # ʼe -> ъе (объект), review fix P1
        if c=="y" and i+1<n and lw[i+1] in "oaue" and lw[i:i+3]!="yoʻ":
            prev=lw[i-1] if i>0 else ""
            m={"o":"ё","a":"я","u":"ю","e":"е"}[lw[i+1]]
            if prev=="ʼ": out[-1]="ъ"
            elif m=="е" and prev and prev not in "aeiouʻ": out.append("ъ")
            out.append(m);i+=2;continue
        if c=="y" and lw[i:i+3]=="yoʻ": out.append("йў");i+=3;continue
        if lw.startswith("ngʻ",i): out.append("н");i+=1;continue
        for a,b in L2C:
            if lw.startswith(a,i) and a not in("yo","yu","ya","ye","ts"):
                if a=="ng" : b="нг"
                out.append(b);i+=len(a);break
        else: out.append(c);i+=1
    res="".join(out)
    return _recase(w,res)
def _recase(src,out):
    if src.islower(): return out
    if src.isupper() and len(src)>1: return out.upper()
    # mixed: map uppercase source letters (digraphs count as one) onto output positions
    lw=src.lower();caps=[];i=0
    while i<len(lw):
        step=2 if lw[i:i+2] in("sh","ch","oʻ","gʻ","yo","yu","ya") or (lw[i:i+2]=="ye") else 1
        caps.append(src[i].isupper());i+=step
    o=list(out)
    for k in range(min(len(o),len(caps))):
        if caps[k]: o[k]=o[k].upper()
    return "".join(o)
LEX={}
def load_lex(path):
    import json;LEX.update(json.load(open(path,encoding='utf-8')))
TOK=re.compile(r"[A-Za-zʻʼ‘’']+")
# Native-word protection (review fix P3): exception-table entries learned from technical books must not
# override common native words. These keys always go through the rules (mol->мол, kuyov->куёв, yodda->ёдда).
# Bare 'yod' (iodine, йод) is left to the table; only suffixed yod- forms ('memory') are protected.
NATIVE_PROTECT=re.compile(r"^(mol|kuyov\w*|yod(da|dan|ga|im|ing|i|idan|ida|ini|lash\w*|la\w*))$")
# Loanword additions the rules cannot predict (review P6). Prefix match, suffix by rules; 'alt' exact only.
LOAN_ADD={'evropa':'европа','qaer':'қаер','abzas':'абзац','slanes':'сланец','asetilen':'ацетилен','pesa':'пьеса',
     'interer':'интерьер','motsart':'моцарт','operasion':'операцион','gravitasion':'гравитацион','transaksiya':'трансакция','alt':'альт'}
LOAN_EXACT={'alt'}
# -nsiya/-ksiya words that keep -сия (Russian -нсия/-ксия), which the -siya->-ция rule would over-correct. filter_lex.py
# drops their table entries (fewer ц than the rules), so they are listed here. sirka 'vinegar' would hit TS_WORDS 'sirk'.
LOAN_ADD.update({'pensiya':'пенсия','sirka':'сирка','gipoksiya':'гипоксия','asfiksiya':'асфиксия','anoreksiya':'анорексия',
     'ataksiya':'атаксия','refleksiya':'рефлексия','kaxeksiya':'кахексия','anafilaksiya':'анафилаксия','apopleksiya':'апоплексия',
     'disleksiya':'дислексия','ekspansiya':'экспансия'})
FOREIGN_LATIN=re.compile(r"c(?!h)|w")   # review P5: Latin-script foreign words (Microsoft, Excel, Cobra, cos) stay in Latin
# Stem fallback: an inflected form not in the table whose stem is (антратситга -> антрацит+га), so good/bad
# pairs that differ only by a suffix keep the same stem spelling. Suffix must be a chain of common Uzbek suffixes;
# skipped when the table stem ends in ь (модель+лар -> моделлар is the rule-correct spelling).
SUFFIX_CHAIN=re.compile(r"^(lar|lari|larning|ning|ni|ga|ka|qa|da|dan|dir|li|lik|siz|lab|lash|lan|i|si|ini|ida|idan|im|ing|imiz|ingiz|mi|gi|dagi|day|cha|ga)+$")
def _lex_stem(k):
    r=_lat2cyr_word(k)
    for n in range(len(k)-1,4,-1):
        st=k[:n]
        if st in LEX:
            cs=LEX[st];rs=_lat2cyr_word(st)
            if cs.endswith("ь") or cs==rs or not r.startswith(rs) or not SUFFIX_CHAIN.match(k[n:]): return None
            return st
    return None
def _lat2cyr_lex(w):
    k=w.lower().replace("‘","ʻ").replace("'","ʼ").replace("’","ʼ")
    if FOREIGN_LATIN.search(k): return w                                                 # P5
    for stem,cy in sorted(LOAN_ADD.items(),key=lambda x:-len(x[0])):                   # P6
        if stem in LOAN_EXACT and k!=stem: continue
        if k.startswith(stem):
            out=cy+(_lat2cyr_word(w[len(stem):]).lower() if len(w)>len(stem) else '')
            return _recase(w,out) if not (w.isupper() and len(w)>1) else out.upper()
    if NATIVE_PROTECT.match(k): return _lat2cyr_word(w)                                 # P3
    if k in LEX: return _recase(w,LEX[k]) if not (w.isupper() and len(w)>1) else LEX[k].upper()
    st=_lex_stem(k)                                                                     # suffixed form of a table stem
    if st: out=LEX[st]+_lat2cyr_word(k)[len(_lat2cyr_word(st)):];return _recase(w,out) if not (w.isupper() and len(w)>1) else out.upper()
    r=_lat2cyr_word(w)
    if "тс" in r.lower():                                                                # P4: word-initial ts / ts+i+vowel -> ц
        k2=re.sub(r"^ts","c",k);k2=re.sub(r"ts(?=i[aoeuy])","c",k2)
        if k2!=k: r=_recase(w,_lat2cyr_word(k2))
    return r
def lat2cyr(s): return TOK.sub(lambda m:_lat2cyr_lex(m.group(0)) if re.search("[A-Za-z]",m.group(0)) else m.group(0),s)
C2L={"а":"a","б":"b","в":"v","г":"g","д":"d","ж":"j","з":"z","и":"i","й":"y","к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f","х":"x","ш":"sh","ч":"ch","ъ":"ʼ","ь":"","э":"e","ю":"yu","я":"ya","ё":"yo","ў":"oʻ","қ":"q","ғ":"gʻ","ҳ":"h"}
CV=set("аеёиоуэюяўАЕЁИОУЭЮЯЎ")
def _cyr2lat_word(w):
    lw=w.lower();out=[]
    for i,c in enumerate(lw):
        prev=lw[i-1] if i>0 else ""
        if c=="е": out.append("ye" if (i==0 or prev in "аеёиоуэюяўъь") else "e")
        elif c=="ц": out.append("ts" if (i>0 and prev in "аеёиоуэюяў") else "s")
        elif c=="ҳ" and prev=="с": out.append("ʼh")
        elif c=="ъ" and i+1<len(lw) and lw[i+1]=="е": out.append("")
        else: out.append(C2L.get(c,c))
    if w.islower(): return "".join(out)
    if w.isupper() and len(w)>1: return "".join(out).upper()
    res=[]
    for i,(c,o) in enumerate(zip(w,out)):
        if c.isupper() and o:
            nxt_up=i+1<len(w) and w[i+1].isupper()
            o=o.upper() if nxt_up else o[0].upper()+o[1:]
        res.append(o)
    return "".join(res)
CTOK=re.compile(r"[А-Яа-яЁёЎўҚқҒғҲҳ]+")
def cyr2lat(s): return CTOK.sub(lambda m:_cyr2lat_word(m.group(0)),s)
def lat2new(s):
    s=s.replace("‘","ʻ")
    for a,b in (("Oʻ","Ö"),("oʻ","ö"),("Gʻ","Ğ"),("gʻ","ğ"),("SH","Ş"),("Sh","Ş"),("sh","ş"),("CH","Ç"),("Ch","Ç"),("ch","ç")): s=s.replace(a,b)
    return s
def new2lat(s):
    s=re.sub(r"([ŞÇ])(?=[A-ZÖĞŞÇʻ])|(?<=[A-ZÖĞŞÇ])([ŞÇ])",lambda m:{"Ş":"SH","Ç":"CH"}[m.group(0)],s)
    for a,b in (("Ö","Oʻ"),("ö","oʻ"),("Ğ","Gʻ"),("ğ","gʻ"),("Ş","Sh"),("ş","sh"),("Ç","Ch"),("ç","ch")): s=s.replace(a,b)
    return s

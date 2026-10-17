# Annotation scheme (eval_gold v1, 2026-10-17)

Per token: **lemma**, **UPOS** (UD), **features**, **alts** (other acceptable lemmas), **flags**, **confidence**.
Gold is written in current Latin (Oʻ/Gʻ = U+02BB, tutuq = U+02BC). Cyrillic and 2026-Latin copies are generated with
`uzmorph/translit.py` (round-trip check: 0 mismatches).

## Features scored
| Feature | Values | Notes |
|---|---|---|
| Case | Nom Acc Gen Dat Loc Abl Ter(-gacha) Equ(-day/-dek) | -dagi → Case=Loc (the -gi is not a case). Present on NOUN/PROPN/PRON and on any word with overt nominal inflection |
| Number | Sing Plur | nouns: -lar. Finite 3rd-person verbs: Plur only with overt plural agreement (‑dilar, ‑ishdi, ‑sinlar, ‑ganlar, ‑yaptilar …). 2nd person polite/plural (-ngiz, -siz) → Plur. **Not scored on PRON** (gold has ular/biz = Plur, neither tool encodes it) |
| Poss | 1Sg 2Sg 3 1Pl 2Pl | -lari = Poss=3 + Number=Plur |
| Person | 1 2 3 | finite verbs only |
| VerbForm | Fin Part Vnoun Conv Inf | Part (-gan/-adigan/-uvchi/-yotgan attributive) and Vnoun (-ish/-uv/-gan+case) are distinguished in gold but **merged for scoring** |
| Mood | Ind Imp Cnd | Imp includes optative/1st-person -ay/-aylik; Cnd = -sa |
| TAM | Past(-di) Perf(-gan finite) Pqp(-gandi) Evid(-ibdi, ekan) Pres(-a/-y) Prog(-yap/-moqda) Aor(-ar) Fut(-adigan finite) Int(-moqchi) | finite indicative only |
| Polarity | Neg | -ma, emas |
| Voice | Pass | only passive scored; Cau/Rcp/Rfl ignored |

## UPOS conventions
- UPOS follows lexical category: adjectives used adverbially stay ADJ (yaxshi, chuqur, ochiq). Demonym -lik words used attributively (oʻzbekistonlik dzyudochi) = ADJ (low confidence).
- AUX only for the copula e- (edi, ekan, emas; lemma `e`, alt = surface). Light/auxiliary verbs after -ib/-a (ol, qoʻy, ber, chiq, kel, yubor, bor) are VERB.
- Closed-class table (context-free): va/yoki/lekin/ammo/biroq/hamda/yaʼni CCONJ; chunki/agar/garchi SCONJ; uchun/bilan/kabi/qadar/orqali/boʻyicha/tomonidan/nisbatan/koʻra/haqida/toʻgʻrisida/oid/doir/qarshi(+Dat)/soʻng/keyin/avval/buyon (postpositional) ADP; ham/esa/faqat/hatto/balki/mi PART; yana/eng/juda/ancha/shuningdek ADV.
- bu/shu/u/ushbu/har/bir(as "a, one each")/boshqa/barcha/butun/qaysi/qanday/bunday/shunday before a noun = DET; standing alone = PRON (u, bu = "he/this one").
- Ordinals (ikkinchi, uchinchi): NUM, lemma = ordinal or cardinal (alt). Cardinal + -ta (ikkita, uchta): NUM, alt = -ta form.
- Postpositional nouns (ichida, orasida, ustida, oʻrniga, yaqinida) = NOUN with Case+Poss=3.

## Lemma conventions
- Lemma = dictionary headword. Derivations that make new dictionary words stay in the lemma: -lik, -chi, -li, -siz, -uvchi (when lexical: yozuvchi, foydalanuvchi), -uv (sotuv, toʻlov), -ma (eslatma), -ish nouns (oʻzgartirish, kelishuv).
- Productive verbal nouns/participles are lemmatised to the verb (qilish → qil, Vnoun).
- Voice-neutral lemma matching: candidate and gold lemmas match if one is the other + il/l/in/n/ish/sh/iltir/lan/lash/ishtir (yoritil ~ yorit, kelish ~ kel). Causatives (-tir, -dir, -ir, -ar, -t) are NOT neutral (ettir ≠ et unless listed as alt).
- `+alt` lists other acceptable lemmas for debatable cases (diminutive -cha, ordinals, -dagi, ular/u, emas/e).
- Hyphenated clitics (oldingiz-u, Toyota-yu) are analysed as the host.

## Flags (excluded from the main score unless noted)
- `name` — PROPN (kept in main score; also reported separately).
- `foreign` — non-Uzbek word/phrase (Latin binomials, English, Arabic formulas). Excluded.
- `typo` — misspelt; gold lemma = intended word. Excluded from main, reported separately.
- `affix` — suffix fragment written as its own token after a quote/number/% ("Neftchi" **ning**, 20:30 **da**, km 2 **dir**). Excluded.
- `abbr` — single letters/initials (O. , S, Yo. s). Excluded.
- `num`, `punct` — not scored.

## Confidence
`auto` = auto-accepted (ZirhUzMorph top reading compatible with ours and ours unambiguous at the scored level, or closed-class table);
`high` = adjudicated in context by an AI assistant; `low` = AI-adjudicated, but genuinely uncertain; `checked` = confirmed or corrected by the native reviewer. `high` and `low` labels were not reviewed by a person.
Spot-check of auto tokens: 150 random, 6 wrong (4.0 %, 95 % CI ≈ 1.5–8.5 %), all corrected; 3 of the 6 were convention issues (ordinals, demonym ADJ).

## Mapping: Apertium (v8d) → scheme
`scripts/scheme.py:map_ap_reading`. Main tags: n/np/adj/adv/v/vaux/cop/prn/det/num/post/cnj*/ij/qst/mod/abbr → UPOS (cop & vaux "e" → AUX, abbr → NOUN, mod → ADJ).
Case: nom acc gen dat loc abl term(→Ter) sim(→Equ). Poss: px1sg px2sg px3sp px1pl px2pl px3pl(→3+Plur); `frm` + px2sg → 2Pl; frm + p2 → Plur.
TAM: ifi→Past, past→Perf, evid(+past)→Evid, aor→Pres, fut→Fut, fut2→Aor, prog/prog_inf→Prog, fut_plan→Int; past + e<cop><ifi> clitic → Pqp.
Mood: imp/opt→Imp, gna_cond→Cnd. VerbForm: gpr_*→Part, ger/ger_*→Vnoun, ger_inf→Inf, prc_*/gna_*→Conv. neg→Neg, pass→Pass. `<guess>` dropped; other `+e<cop>` clitics ignored.
For hyphenated tokens the earlier parts' surface is prefixed to the head lemma.

## Mapping: ZirhUzMorph 0.1.1 → scheme
`scripts/scheme.py:map_zirh`. POS N→NOUN, V→VERB (Zirh has no other categories, so UPOS accuracy is structurally capped; use **coarse** POS or lemma+feats for a fair comparison).
Lemma: stem + glued derivational morphs (LIK CHI CHILIK SIZ LI DOSH IY LA AY SIRA AGENT GICH CHA DER.* VN.UV, and GI when not after a case), converted back from Zirh's ö/ğ/ş/ç alphabet with uztranslit new2lat, ' → ʼ. A glued LA/AY/SIRA makes a verb lemma, any other glued morph a noun.
Nominal: PL, PL+P3, P1S/P2S/P3/P1P/P2P, ACC GEN DAT LOC ABL GACHA(→Ter) DAY(→Equ).
Verbal: PASS, NEG, PST→Past, PRF→Perf (PRF+PERS di → Pqp), PROG*→Prog, AOR→Aor, FUT→Fut, INT→Int, COND→Cnd, PRS+PERS→Pres (else Conv), CVB+PERS→Evid (else Conv), CVB.*→Conv, PTCP*→Part, VN.ISH→Vnoun, INF→Inf, IMP*/OPT1→Imp; person from the PERS morph form.
Coarse POS classes: V = VERB/AUX; N = NOUN PROPN ADJ NUM PRON DET ADV; O = everything else.

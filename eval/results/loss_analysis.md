# Where we lose to ZirhUzMorph (Latin, main tokens, top reading, lemma+feats)

Historical (v8d analyzer with the CG ranker, whole gold before the dev/test split; written to pick the later fixes). Counts only: example tokens from the gold were removed.

ours+guess right & Zirh wrong: 225  |  Zirh right & ours+guess wrong: 335

-  111  ours top: wrong lemma (right reading present, CG picked another)
-   61  ours: no analysis (name)
-   57  ours top: wrong Number (right reading present, CG picked another)
-   37  ours top: wrong VerbForm (right reading present, CG picked another)
-   20  ours top: wrong lemma (right reading absent)
-   18  ours top: wrong Mood+Number+Person+TAM+VerbForm (right reading present, CG picked another)
-   11  ours: no analysis
-    4  ours top: wrong Case+Poss (right reading present, CG picked another)
-    4  ours top: wrong Case (right reading present, CG picked another)
-    2  ours top: wrong Case+Poss (right reading absent)
-    2  ours top: wrong Mood+Number+Person+TAM+VerbForm (right reading absent)
-    2  ours top: wrong Poss (right reading present, CG picked another)
-    1  ours top: wrong VerbForm (right reading absent)
-    1  ours top: wrong Case+Mood+Number+Person+TAM+VerbForm (right reading present, CG picked another)
-    1  ours top: wrong Mood+Number+Person+TAM+VerbForm+Voice (right reading absent)
-    1  ours top: wrong Number+Voice (right reading present, CG picked another)
-    1  ours top: wrong Polarity (right reading absent)
-    1  ours top: wrong Case+Mood+Number+Person+Poss+VerbForm (right reading present, CG picked another)
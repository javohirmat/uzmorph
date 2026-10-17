# Non-word acceptance (release analyzer v9.1; 299 non-words with 0 corpus hits; lower is better)

| input | system | accepted |
|---|---|---|
| lower-case | uzmorph dictionary | 1% (2) |
| lower-case | + confident guesser | 17% (50) |
| lower-case | + unfiltered guesser (tools/models/uzb_guess.py --all) | 90% (268) |
| lower-case | Zirh, known stems | 15% (44) |
| lower-case | Zirh, any segmentation (incl. unknown-stem guesses) | 85% (253) |
| Capitalised | uzmorph dictionary | 1% (4) |
| Capitalised | + confident guesser | 13% (38) |
| Capitalised | + unfiltered guesser (tools/models/uzb_guess.py --all) | 79% (237) |
| Capitalised | + verified name list | 1% (4) |
| Capitalised | + proper-noun guesser (mid-sentence) | 100% (299) |

- Zirh was run on the lower-case strings only. "any segmentation" counts every output that is not a bare `word[?]`;
  46 of the 299 strings get a bare `word[?]` and count as rejected there.
- Our unfiltered guesser and Zirh's unknown-stem guesses both analyse almost any string by design; neither is a rejection test.
- The proper-noun guesser accepts any capitalised unknown word in mid-sentence position by design (readings marked `<guess>`).
  At sentence start, `uzmorph.analyze` also falls back to it when the guesser has nothing.

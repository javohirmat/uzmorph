# Corresponding Source for the transducers in this directory (GPL-3.0, section 6)

`uzb.automorf.bin` (analyser), `uzb.autogen.bin` (generator) and `uzb_guesser.automorf.bin` (guesser) are object code. They were compiled from a modified version of **apertium-uzb**, which is licensed under the GNU General Public License version 3 only (GPL-3.0-only; full text in `LICENSE` / `apertium-uzb/COPYING`).

## Where the Corresponding Source is

1. **In the source distribution.** `uzmorph-0.9.0.tar.gz` (the sdist, published next to every wheel) contains the complete source under `apertium-uzb/`. That covers the lexc, twol, rlx, guesser and `coopfilter.regexp` files, the `Makefile.am` / `configure.ac` / `autogen.sh` build scripts, upstream `COPYING` and `AUTHORS`, and `CHANGES.md`, which lists every modification.
2. **In the repository.** The `apertium-uzb/` directory of the uzmorph repository, at the tag `v0.9.0`: https://github.com/javohirmat/uzmorph/tree/v0.9.0/apertium-uzb
3. **Upstream base.** https://github.com/apertium/apertium-uzb, commit `00522e3` (2025-05-16). Our changes are applied on top of it.

## How to rebuild these exact files

```bash
sudo apt install lttoolbox lttoolbox-dev hfst cg3 cg3-dev apertium apertium-dev autoconf automake pkg-config make gawk
cd apertium-uzb && ./autogen.sh && make
# uzb.automorf.bin, uzb.autogen.bin, uzb_guesser.automorf.bin are byte-identical to the files here
# (tested with apertium 3.9, lttoolbox 3.7, hfst 3.16 on Ubuntu)
```

## Written offer

For at least three years after the last distribution of this version, and for as long as spare parts or customer support for it are offered, the maintainer will give anyone who possesses the object code a copy of the complete Corresponding Source. The copy comes on a durable physical medium customarily used for software interchange, or by download, for no more than the reasonable cost of physically performing the transfer. Contact: Javohir Matniyazov, javohirmatniyazovv@gmail.com.

## The other files here

The `*.json.gz`, `name_sufprior.json` and `names_list.tsv` files are model data, not compiled from source code. They are derived from corpus statistics by the scripts in `tools/models/` (see `tools/README.md`). The final step is `tools/models/export_models.py`.

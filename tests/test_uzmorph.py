# SPDX-License-Identifier: GPL-3.0-only
"""Fast smoke tests (a few seconds). Run: python -m unittest discover tests   (or pytest)"""
import shutil,subprocess,sys,unittest
import uzmorph
from uzmorph import translit,textlib
@unittest.skipUnless(shutil.which('lt-proc'),'lt-proc (lttoolbox) not installed')
class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.A=uzmorph.Analyzer()
    def best(self,text,script='auto'):
        return {t.text:t.best for t in self.A.analyze(text,script) if t.is_word}
    def test_known_word(self):
        b=self.best('Men kitobimni oʻqidim.')['kitobimni']
        self.assertEqual((b.lemma,b.upos,b.feats),('kitob','NOUN','Case=Acc|Number=Sing|Poss=1Sg'))
    def test_coop_fix(self):
        # v9 fix: no spurious cooperative (-ish-) reading for -yap- forms
        t=[t for t in self.A.analyze('oʻqiyapman') if t.is_word][0]
        self.assertTrue(t.known)
        self.assertFalse(any('<coop>' in r.analysis for r in t.readings))
        self.assertEqual(t.best.analysis,'oʻqi<v><tv><prog><p1><sg>')
    def test_generate(self):
        self.assertEqual(uzmorph.generate('oʻqi','<v><tv><prog><p1><sg>'),['oʻqiyapman'])
        self.assertEqual(uzmorph.generate('kitob',['n','pl','px1sg','acc']),['kitoblarimni'])
        self.assertEqual(self.A.generate('kitob','<v><nonsense>'),[])
    def test_singular_default(self):
        b=self.best('U kecha keldi.')['keldi']
        self.assertIn('Number=Sing',b.feats)
    def test_cyrillic(self):
        self.assertEqual(translit.cyr2lat('Ўзбекистон'),'Oʻzbekiston')
        b=self.best('Тошкентда яшайман.')
        self.assertEqual(b['Toshkentda'].lemma,'Toshkent'); self.assertEqual(b['yashayman'].lemma,'yasha')
    def test_name_guess(self):
        b=self.best('Kecha Zarafshonbekni koʻrdim.')['Zarafshonbekni']
        self.assertEqual((b.lemma,b.upos,b.source),('Zarafshonbek','PROPN','names-guess'))
        self.assertIn('Case=Acc',b.feats)
    def test_nonsense_rejected(self):
        t=[t for t in self.A.analyze('qwzzxor') if t.is_word][0]
        self.assertFalse(t.known); self.assertEqual(t.readings,[])
    def test_hyphen_line_break(self):
        # a word split by a hyphen at a line end is rejoined, not dropped
        self.assertEqual(textlib.split_sents('Men kito-\nblarimni oʻqidim.'),['Men kitoblarimni oʻqidim.'])
        self.assertEqual(textlib.split_sents('ilmiy-\nAmaliy ish.'),['ilmiy-Amaliy ish.'])
        self.assertEqual(textlib.split_sents('Men kito-\nblarimni oʻqidim.',drop_hyphen_breaks=True),[])
        b=self.best('Men kito-\nblarimni oʻqidim.')
        self.assertEqual(b['kitoblarimni'].lemma,'kitob')
    def test_hyphen_compounds(self):
        # v9.1: second parts starting with a-/ya- are no longer cut into the -a/-ya clitic
        b=self.best('Bu ilmiy-amaliy anjuman. Oʻzbekiston-Amerika aloqalari.')
        self.assertEqual((b['ilmiy-amaliy'].lemma,b['ilmiy-amaliy'].upos),('ilmiy-amaliy','ADJ'))
        self.assertEqual(b['Oʻzbekiston-Amerika'].upos,'PROPN')
        k=self.best('Keldingiz-a?')['Keldingiz-a']
        self.assertEqual((k.lemma,k.upos),('kel','VERB'))
    def test_input_validation(self):
        with self.assertRaises(ValueError): self.A.generate('kitob','n.pl')
        with self.assertRaises(ValueError): self.A.generate('kitob','<n><pl>$^x')
        with self.assertRaises(ValueError): self.A.lookup(['kitob lar'])
        with self.assertRaises(ValueError): self.A.analyze_tokens([['kitob','a b']])
        self.assertEqual(self.A.lookup(['kito\x00b\r'])['kito\x00b\r'][0].split('/')[1],'kitob<n><nom>')
        self.assertEqual([t.text for t in self.A.analyze('ki\x00tob\uffff keldi\r\n') if t.is_word],['kitob','keldi'])
        self.assertEqual(self.A.analyze(''),[])
    def test_lt_proc_errors(self):
        from uzmorph import analyzer
        with self.assertRaises(RuntimeError) as e: analyzer._run(['lt-proc','-w','/nonexistent.bin'],'x\n')
        self.assertIn('lt-proc',str(e.exception))
        with self.assertRaises(RuntimeError) as e: analyzer._run(['sleep','5'],'',timeout=0.3)
        self.assertIn('did not answer',str(e.exception))
    def test_leftovers(self):
        self.assertEqual(textlib.split_sents('Men kito- \nblarni oldim.'),['Men kitoblarni oldim.'])
        self.assertEqual([t.text for t in self.A.analyze('kitob\x0bdaftar\x0cqalam \ud800ruchka')],['kitob','daftar','qalam','ruchka'])
        with self.assertRaises(ValueError): self.A.lookup(['kitob\x0bdaftar'])
        self.assertEqual(self.A.generate("o'qi",'<v><tv><prog><p1><sg>'),['oʻqiyapman'])
        toks=self.A.analyze('qwzz-kitob oldim.')
        self.assertFalse(toks[0].known); self.assertTrue(toks[1].known); self.assertFalse(toks[2].known)
        self.assertEqual(self.best('Toshkent-Samarqand yoʻli.')['Toshkent-Samarqand'].lemma[:9],'Toshkent-')
        # Cyrillic: transliterated before sentence splitting; with --script lat a Cyrillic word stays one token
        self.assertEqual([t.sent for t in self.A.analyze('Мен келдим. У кетди.') if t.is_word],[0,0,1,1])
        self.assertEqual([t.text for t in self.A.analyze('Мен келдим.',script='lat')],['Мен','келдим','.'])
    def test_cli(self):
        o=subprocess.run([sys.executable,'-m','uzmorph','analyze','kitobimni'],capture_output=True,text=True,check=True).stdout
        self.assertTrue(o.startswith('kitobimni\tkitob\tNOUN'))
        o=subprocess.run([sys.executable,'-m','uzmorph','analyze'],input='Bolalar keldi.\nUlar ketdi.\n',capture_output=True,text=True,check=True).stdout
        self.assertIn('.\n\nUlar',o)       # one batch, blank line between sentences
        r=subprocess.run([sys.executable,'-m','uzmorph','generate','kitob','n.$'],capture_output=True,text=True)
        self.assertEqual(r.returncode,2); self.assertIn('tags',r.stderr)
if __name__=='__main__': unittest.main()

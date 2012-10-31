import unittest
import string
from boolmatch import combine_ors, tokenize, tagstr, _tagstr, make_parse_tree, AND, OR, NOT, Token, matches, ParseException

class SimpleFilterTestCase(unittest.TestCase):
    def T(self, filter_string, text):
        self.assertTrue(matches(filter_string, text), msg=(filter_string, text))

    def F(self, filter_string, text):
        self.assertFalse(matches(filter_string, text), msg=(filter_string, text))

    def test_empty(self):
        self.T('', 'anything')

    def test_word_boundaries(self):
        # Test beginning of string.
        self.T("hivefire", "Hivefire is awesome.")

        # Test middle of word.
        self.F("hivefire", "pbdHivefire is awesome.")

        # Test puncuation.
        self.T("hivefire", "'Hivefire is awesome.'")
        self.T("hivefire", "'Hivefire is awesome.'")
        self.T("hivefire", "(Hivefire) is awesome.'")
        self.T("hivefire", "Hivefire-enabled portals is awesome.'")
        self.T("hivefire", "'Hivefire!! is awesome.'")
        self.T("hivefire", "'Hivefire? is awesome.'")

    def test_bools(self):
        self.T('hi mom', 'mom says hi')
        self.T('hi and mom', 'mom says hi')
        self.T('hi or mom', 'mom says hi')
        self.T('hi or mom', 'mom says go play')
        self.F('not mom', 'mom says hi')
        self.F('not mom and not hi', 'says hi')
        self.F('not mom and not hi', 'mom says go play')
        # & | are not special
        self.F('mom & hi', 'hi mom')
        self.F('mom | hi', 'hi')
        self.F('mom | hi', 'hello')
        self.T('X&Y', 'X&Y')
        self.T('hi & mom', 'hi & mom')
        return
        self.T('& or @', 'hi &')
        self.T('& or @', 'hi @')

    def test_symbols(self):
        # regexps don't like non-alphanumerics much.  We at least try to make these work.
        self.T('X&Y', 'X&Y')
        self.T('&', 'bob & sue')
        self.F('|', '&')
        self.T('| and &', 'sue & and | and bob')
        self.T('| or &', '|')
        self.T('| or &', '&')

    def test_quotes(self):
        self.F('"hi mom"', 'mom says hi')
        self.T('"hi mom"', 'hi mom')
        self.F('"hi and mom"', 'hi mom')
        self.T('"hi and mom"', 'hi and mom')

    def test_groups(self):
        self.T('(hi or mom)', 'hi')
        self.T('(hi or mom)', 'mom')
        self.F('(hi and mom) or hello', 'hi')
        self.T('(hi and mom) or hello', 'hello')
        self.T('(hi and mom) or hello', 'hi mom')
        self.T('a(hi and mom)b or hello', 'hi mom a b')

    def test_wildcard(self):
        # the original library has limited wildcard support
        # e.g. wildcards on the left side and bare wildcards are ignored
        self.T('hive*', 'hivefire')
        self.T('hive *fire', 'hive fire')
        self.F('one * four', 'one two three')
        self.F('one* four', 'one two three')
        self.T('one * three', 'one two three')
        self.T('one * four', 'one two three four')

    def test_implicit_and(self):
        # "a b" means "a AND b"
        self.F("a b", "b")
        self.F("a AND b", "b")
        self.T("a b", "b a")
        self.T("a AND b", "b a")

    def test_capitalization(self):
        # bare words
        self.T("this", "This")
        self.T("This", "this")
        self.T("This", "THIS")
        self.T("THIS", "this")
        self.T("THIS", "This")
        # grouped
        self.T('"A B"', 'a b')
        self.T('"A B"', 'A b')
        self.F('"B A"', 'a b')
        self.T('(A B)', 'b a')

    def test_real(self):
        filter_string = u'Defense or budget or technology or technologies or electronics or electronic or network or networks or command or control or communication or autonomous or "mixed-signal" or "mixed signal" or "field-portable" or "field portable" or "soldier monitoring" or "soldier monitor" or "future warrior" or "future soldier" or microelectronics or "rapid prototyping" or RDT&E or R&D or autonomous or tactical or covert or strategic or space or medical or biomedical or cybersecurity or cyber or lunar or mems or miniaturization or miniaturized or complex or optics or cockpit or robot or robotics or multichip or mcm or microelectromechanical or "homeland security" or underground or microscale or precision or GN&C or guidance or navigation or gyro or gyros or ISR or sensor or sensors or payload or GPS or geospatial or GIS or weapon or missile or strike or UAS or UAV or UUV or drone or unmanned or intelligence or surveillance or reconnaissance or ISR or c3i or c4i or energy or environment'
        text = u"Study: Defense spending is \u2018weak job engine\u2019 Spending on 'clean energy,' health care and education are more effective at employing people than defense, the authors say. "
        self.T(filter_string, text)
        filter_string = u'"space command" or "space and missile center" or smc or reentry or re-entry or shuttle or "space shuttle" or "on-orbit control system" or "command and control" or "space station" or iss or "space guidance" or "space navigation" or "space-based sensor" or "long range precision strike" or "ballistic missile" or "conventional strike" or geospatial or GIS or "global position system" or "global strike" or "GN&C" or "guidance system" or "navigation system" or gyro or ICBM or IMU or "inertial measurement unit" or intelligence or reconnaissance or "intercontinental ballistic" or navair or navsea or "prompt global strike" or sensor or payload or reconnaissance or Trident or UAS or UAV or "unmanned aerial" or "unmanned underwater" or UUV or "weapon system" or "defense technology" or ISR or ballistic or space or Aries or "guidance navigation and control" or ISS'
        self.F(filter_string, '')

        filter_string = u'bioptigen, AND imalux, AND "Lantis Laser" AND , AND Glucolight, AND "Lightlab Imaging, " AND Michelson AND Diagnostics", Optiphase, Optopol, Optovue, "Ophthalmic AND Technologies AND Inc'
        self.F(filter_string, '')

        filter_string = u'((trends OR predictions OR forecast)AND technology) OR ("cloud computing" AND security) OR (forrester AND ("top 15" OR "top 10")) OR (("social networking" OR cloud) AND government) OR ((merger OR acquisition) AND (microsoft OR emc OR apple OR "sun microsystems" OR cisco OR ibm OR oracle OR facebook OR google OR twitter)) OR "context aware computing" OR "innovation management tools" OR soa OR "enterprise collaboration" OR ereader OR ebook OR "augemented reality" OR "open id" OR "unified communications" OR "open government" OR "government 2.0" OR "expert labs" OR cyberspace OR cybersecurity OR "data loss" OR "data protection" OR "enterprise architecture" OR "enterprise search" OR "information architecture" OR "web hosting" OR telepresence OR "video walls" OR foursquare OR gowalla OR loopt OR getglue OR "google latitude" OR "facebook places"'
        self.F(filter_string, '')

        filter_string = u'airport or "air traffic" NOT  (Pratt OR Whitney OR Bell OR helicopter OR copter OR rolls OR royce OR eurocopter OR "american airlines" OR AMR OR fashion OR "victoria secret" OR "victoria\'s secret")'
        self.F(filter_string, '')

    def test_possessive(self):
        self.T("boar's head", "boar's head")
        self.T("(boar's head)", "boar's head")

    def test_nonalphas(self):
        self.T('999', '999')
        self.T('1', '1 2 3')

    def test_chinese(self):
        words = u'\u6c49\u8bed/\u6f22\u8a9e\u534e\u8bed/\u83ef\u8a9e'
        char = u'\u6c49'
        self.T(char, char)
        self.F(char, words)
        self.T(char, u'\u8bed \u6c49 \u6f22')


class TestAndParser(unittest.TestCase):

    def test_bad_parse(self):
        self.assertRaises(ParseException, make_parse_tree, '(a')
        self.assertRaises(ParseException, make_parse_tree, '"a')
        self.assertRaises(ParseException, make_parse_tree, 'a)')
        make_parse_tree('*hive') # backwards compat, '*' gets silently dropped
        make_parse_tree('"(a"')
        make_parse_tree('"a)"')

    def test_combine_ors(self):
        def _combine_ors(l):
            return combine_ors(map(tagstr, l))
        self.assertEqual(['a OR b'], _combine_ors(['a', 'OR', 'b']))
        self.assertEqual(['a OR b OR c'], _combine_ors(['a', 'OR', 'b', 'OR', 'c']))
        do_nothing = ['a', 'AND', 'b', 'AND', 'c']
        self.assertEqual(do_nothing, _combine_ors(do_nothing))
        # lower case
        self.assertEqual(['a OR b'], _combine_ors(['a', 'OR', 'b']))
        self.assertEqual(['a OR b OR c'], _combine_ors(['a', 'OR', 'b', 'OR', 'c']))
        do_nothing = ['a', 'and', 'b', 'AND', 'c']
        self.assertEqual(do_nothing, _combine_ors(do_nothing))

    def test_long_parse(self):
        # patterns with over 116 parts smash the FilterParser stack (the old parser)
        letters = (c for c in string.ascii_letters * 3)
        fstring = next(letters)
        count = 0
        for c in letters:
            fstring += ' AND ' + c
            count += 1
        self.assertTrue(count > 130)
        self.assertFalse(matches(fstring, 'zzzz'))
        self.assertTrue(matches(fstring, ' '.join(string.ascii_letters)))
        # new parser is more robust
        self.assertTrue(make_parse_tree(' OR '.join(map(str, range(2000)))).matches('999'))
        self.assertTrue(make_parse_tree('%s Hi %s' % ('(' * 100, ')' * 100)).matches('hi'))

class TestParser(unittest.TestCase):
    def test_tokenize(self):
        self.assertEqual(tokenize('this that'), ['this', 'AND', 'that'])
        self.assertEqual(tokenize('"this that"'), ['"this that"'])
        self.assertEqual(tokenize('(this that)'), ['(this that)'])
        self.assertEqual(tokenize('(())'), ['(())'])
        self.assertEqual(tokenize('"(this OR that)"'), ['"(this OR that)"'])
        self.assertEqual(tokenize('this OR that'), ['this', 'OR', 'that'])
        self.assertEqual(tokenize('NOT Bob'), ['NOT Bob'])
        self.assertEqual(tokenize('NOT Bob Smith'), ['NOT Bob', 'AND', 'Smith'])
        self.assertEqual(tokenize('NOT "Bob Smith"'), ['NOT "Bob Smith"'])
        self.assertEqual(tokenize('a NOT (Bob Smith) b'), ['a', 'AND', 'NOT (Bob Smith)', 'AND', 'b'])
        self.assertEqual(tokenize('a(b)'), ['a', 'AND', '(b)'])
        def both(txt): return combine_ors(tokenize(txt))
        self.assertEqual(both('this OR that AND jelly'), ['this OR that', 'AND', 'jelly'])
        self.assertEqual(both('this OR NOT that AND jelly'), ['this OR NOT that', 'AND', 'jelly'])
        self.assertEqual(both('NOT this, that'), ['NOT this,', 'AND', 'that'])
        self.assertEqual(type(both('abc')[0]), _tagstr)
        self.assertEqual(both('abc 123')[-1].char, 4)
        self.assertEqual(both('abc 123')[0].lineno, 0)
        self.assertEqual(both('abc\n123')[-1].char, 4)
        self.assertEqual(both('abc\n123')[-1].lineno, 1)


    def test_parse_obs(self):
        class Yes(object):
            def matches(self, text): return True
        class No(object):
            def matches(self, text): return False
        self.assertTrue(Yes().matches(''))
        self.assertFalse(No().matches(''))

        self.assertTrue(OR([Yes(), No()]).matches(''))
        self.assertTrue(OR([Yes(), Yes()]).matches(''))
        self.assertFalse(OR([No(), No()]).matches(''))

        self.assertTrue(AND([Yes(), Yes()]).matches(''))
        self.assertFalse(AND([No(), Yes()]).matches(''))
        self.assertFalse(AND([No(), No()]).matches(''))

        self.assertFalse(NOT(Yes()).matches(''))
        self.assertTrue(NOT(No()).matches(''))

        self.assertTrue(Token(_tagstr('hello')).matches('hello'))
        self.assertFalse(Token(_tagstr('hello')).matches('goodbye'))
        self.assertTrue(Token(_tagstr('hello world')).matches('hello world'))
        self.assertFalse(Token(_tagstr('hello world')).matches('hello'))

        x = AND([AND(['a', 'b']), AND(['c', 'd'])])
        x.flatten()
        self.assertEqual(x.parts, list('abcd'))

    def test_parse(self):
        bigquery = '''
(Axsun OR "Volcano Corporation" OR Bioptigen OR ("Heidelberg Engineering" OR Imalux) OR Innolume OR NOT "Isis Optronics" OR "Lantis Laser" OR "Lightlab Imaging" OR "Michelson Diagnostics" OR Optiphase OR Optopol OR Optovue OR "Ophthalmic Technologies Inc")'''
        parens = "(a b(c d e)(f('g')))"
        parens2 = "(a b(c d e) OR (f('g')))"

        for p in ['(this)', '(this OR that)', 'this\nNOT that', '"bob smith"', bigquery, parens, parens2]:
            tree = make_parse_tree(p)

if __name__ == "__main__":
    unittest.main()

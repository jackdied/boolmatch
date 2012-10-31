"""
Copyright Curata, Inc.
Written by Jack Diederich (jackdied@gmail.com)
"""

import re
import itertools as it

class ParseException(Exception):  # minimally compatible with pyparsing.ParseException
    def __init__(self, msg, loc=0):
        self.msg = msg
        self.loc = loc

class _tagstr(unicode):
    def pretty(self):
        return '<_tagstr %r lineno=%d char=%d>' % (self.txt, self.lineno, self.char)

def tagstr(txt=None, lineno=0, char=0):
    if txt is None:
        val = _tagstr()
        val.txt = ''
    else:
        val = _tagstr(txt)
        val.txt = txt
    val.lineno = lineno
    val.char = char
    return val

def _tokenize(text):
    """ break the string into tokens of words, quoted strings, and parens """
    parts = []
    stack = [None]
    stack_i = [None]
    lineno = getattr(text, 'lineno', 0)
    char = getattr(text, 'char', 0)

    curr = tagstr(lineno=lineno, char=char)
    for i, c in enumerate(text):
        if c == '\n':
            lineno += 1
        if c.isspace() and stack[-1] is None:
            parts.append(curr)
            curr = tagstr(u'', lineno=lineno, char=char+i+1)
            continue
        elif c == '(' and stack[-1] is None and curr:
            parts.append(curr)
            curr = tagstr(u'', lineno=lineno, char=char+i+1)

        curr = tagstr(curr + c, lineno=curr.lineno, char=curr.char)
        if c not in '()"':
            continue
        if stack[-1] == '"': # waiting for a closing quote
            if c == '"':
                stack.pop()
                stack_i.pop()
        elif c == '"':
            stack.append(c)
            stack_i.append(i)
        else:
            if c == '(':
                stack.append('(')
                stack_i.append(i)
            elif c == ')':
                if stack[-1] != '(':
                    raise ParseException("mismatched closing parenthesis at character %d" % i, loc=i)
                stack.pop()
                stack_i.pop()
                if stack[-1] is None:
                    parts.append(curr)
                    curr = tagstr(u'', lineno=lineno, char=char+i+1)
            else:
                raise ParseException("bad parse")
    if curr:
        parts.append(curr)
    if stack[-1] is not None:
        if stack[-1] == '"':
            raise ParseException("mismatched quotes starting at character %d" % stack_i[-1], loc=stack_i[-1])
        elif stack[-1] == '(':
            raise ParseException("mismatched parenthesis starting at character %d" % stack_i[-1], loc=stack_i[-1])
        else:
            raise ParseException("bad parse")

    return filter(None, parts)

def combine_nots(chunks):
    parts = []
    while chunks:
        top = chunks.pop(0)
        if top.upper() == 'NOT':
            if not chunks:
                raise ParseException("trailing NOT on line %d" % top.lineno)
            parts.append(tagstr(u'NOT %s' % chunks.pop(0), lineno=top.lineno, char=top.char))
        else:
            parts.append(top)
    return parts

def combine_ors(chunks):
    parts = []
    while chunks:
        top = chunks.pop(0)
        if top.upper() == 'OR':
            if not chunks:
                raise ParseException("bare OR at beginning of terms")
            if not parts:
                raise ParseException("bare OR at end of terms line %d" % top.lineno)
            parts[-1] = tagstr(u'%s OR %s' % (parts[-1], chunks.pop(0)), lineno=parts[-1].lineno, char=parts[-1].char)
        else:
            parts.append(top)
    return parts

def tokenize(text):
    toks = combine_nots(_tokenize(text))
    if not toks:
        return toks

    for i, tok in enumerate(toks):
        if tok == '*':
            toks[i] = ''
            continue # backwards compatible bug
            raise ParseException("wildcards can not be bare '*' on line %d" % (tok.lineno))
        elif '*' in tok and not tok.endswith('*'):
            toks[i] = tagstr(tok.replace('*', ''), lineno=tok.lineno, char=tok.char) # backwards compatible bug
            # raise ParseException("%r wildcards can only be at the end of words" % tok)

    chunks = combine_ors(toks)
    # normalize explicit and implicit ANDs
    chunks = [chunk for chunk in chunks if (chunk and chunk.upper() != 'AND')]
    parts = []
    for chunk in chunks:
        parts.extend(combine_nots(_tokenize(chunk)))
        parts.append(tagstr('AND'))
    parts.pop()
    return parts

class AND(object):
    word = 'AND'
    last = '?'

    def __init__(self, parts=None):
        self.parts = parts or []

    def matches(self, text):
        for part in self.parts:
            if not part.matches(text):
                self.last = False
                return False
        self.last = True
        return True

    def __repr__(self):
        return '<AND %s %s>' % (self.parts, self.last)

    def flatten(self):
        for child in self.parts:
            val = getattr(child, 'flatten', int)()
        newparts = []
        for child in self.parts:
            if child.__class__ == self.__class__:
                newparts.extend(child.parts)
            elif isinstance(child, AND) and len(child.parts) == 1 and isinstance(child.parts[0], Token):
                newparts.append(child.parts[0])
            else:
                newparts.append(child)
        self.parts = newparts
        return

    def pretty(self):
        self.flatten()
        word = ' ' + self.word + ' '
        if len(self.parts) > 1:
            return '(%s)' % word.join(part.pretty() for part in self.parts)
        return self.word + ' ' + self.parts[0].pretty()

class OR(AND):
    word = 'OR'

    def matches(self, text):
        for part in self.parts:
            if part.matches(text):
                self.last = True
                return True
        self.last = False
        return False

    def __repr__(self):
        return '<OR %s %s>' % (self.parts, self.last)

class NOT(object):
    word = 'NOT'
    last = '?'

    def __init__(self, tree):
        self.tree = tree

    def matches(self, text):
        return not self.tree.matches(text)

    def __repr__(self):
        return '<NOT %s %s>' % (self.tree, self.last)

    def flatten(self):
        if isinstance(self.tree, AND) and len(self.tree.parts) == 1 and isinstance(self.tree.parts[0], Token):
            self.tree = self.tree.parts[0]

    def pretty(self):
        return 'NOT %s' % self.tree.pretty()

def make_regexp_matching(word, left_anchor=None, right_anchor=None):
    """ make a regexp that will find word in a block of text.
        This function also works for symbols.
    """
    if left_anchor is None:
        left_anchor = r'((?<=\W)|\b)' # preceded by a word break or preceded by not-an-alpha
    if right_anchor is None:
        right_anchor = r'((?=\W)|\b)'
    combined = left_anchor + re.escape(word) + right_anchor
    return combined

def make_regex(text):
    if text.endswith('*'):
        return make_regexp_matching(text.rstrip('*'), right_anchor='')
    return make_regexp_matching(text)

class Token(object):
    last = '?'

    def __init__(self, string):
        self.word = string
        if string.startswith('"'):
            string = tagstr(string[1:-1], lineno=string.lineno, char=string.char+1)
        self.string = string
        self.raw_regex = make_regex(string)
        self.regex = re.compile(self.raw_regex, re.I)
        self.uni_regex = re.compile(re.escape(string))

    def matches(self, text):
        if self.regex.search(text):
            self.last = True
            return True
        for m in self.uni_regex.finditer(text):
            beg, end = m.start(), m.end()
            if (beg == 0 or text[beg-1].isspace()) and \
               (end == len(text) or text[end].isspace() or text[end] in ',.\t '):
                self.last = True
                return True
        self.last = False
        return False

    def __repr__(self):
        return '<Token %r (%d, %d)>' % (self.string, self.string.lineno, self.string.char)

    def flatten(self):
        pass

    def pretty(self):
        spaces = any(c.isspace() for c in self.string)
        if spaces:
            return repr(self.string)
        return self.string

def make_parse_tree(pattern):
    pattern = tagstr(pattern.strip(), lineno=getattr(pattern, 'lineno', 0), char=getattr(pattern, 'char', 0))

    parts = tokenize(pattern)
    # stage 1, text and NOTs
    for i, part in enumerate(parts):
        if part.startswith('('):
            parts[i] = make_parse_tree(tagstr(part[1:-1], lineno=part.lineno, char=part.char+1))
        elif part in {'AND', 'OR'}:
            pass
        else:
            if part.startswith('NOT '):
                part = tagstr(part[len('NOT '):], lineno=part.lineno, char=part.char)
                part = NOT(make_parse_tree(part))
            else:
                part = Token(part)
            parts[i] = part
    # stage 2, ANDs & ORs
    count = 0
    parts = parts[::-1]
    for op, opclass in [('AND', AND), ('OR', OR)]:
        result = []
        while parts:
            count += 1
            part = parts.pop()
            if part == op:
                result.append(opclass([result.pop(), parts.pop()]))
                if not count % 200: # copy overhead versus stack blowing
                    result[-1].flatten()
            else:
                result.append(part)
        parts = result
    tree = AND(parts)
    tree.flatten()
    return tree

def matches(pattern, text):
    return make_parse_tree(pattern.lower()).matches(text.lower())

def pprint_tree(node, indent=0):
    if False and node.last == '?':
        return
    print ' ' * indent * 2, str(node.last)[0], node.word
    if getattr(node, 'parts', []):
        for part in node.parts:
            pprint_tree(part, indent+1)


if __name__ == '__main__':
    pass

#!/usr/bin/env python
"""
lipy - Pythonic Lisp
====================

"In order to be fluent you must lisp first."

An experimental implementation of clojure/lisp in python. One that gels well
with python.

Tests
=====

>>> evals("(+ 1 2)")
3
>>> evals("1 2")
Traceback (most recent call last):
...
SyntaxError: Only lists can be evaled
>>>
>>> evals('(print (string.upper "hello world"))')
HELLO WORLD
>>> evals("(print (+ 1 2 (* 23 45 2)))")
2073
>>> evals("(print (len (range 100)))")
100
>>> evals("(map print (range 2 9 2))")
2
4
6
8
[None, None, None, None]
>>> evals('(eval "print(1 + len([1, 2, 3]))")')
4
>>> evals('(print ("hello world" upper))')
HELLO WORLD
>>> evals('(= x 10)')
10
>>> evals('(do (= x 10) (+ x 12))')
22

"""
from __future__ import print_function
import sys
from pprint import pprint
try:
    import __builtin__
except ImportError:
    import builtins as __builtin__
from pyparsing import *

class Token(object):
    def __init__(self, t):
        self.t = t
    def __str__(self): return repr(self)
    def __repr__(self): return "<%s %r>" % (self.__class__.__name__, self.t[0])
    def val(self): return self.t[0]

class Tick(Token): pass
class Symbol(Token): pass
class Keyword(Token): pass
class Decimal(Token):
    def val(self): return int(self.t[0])
class Real(Token):
    def val(self): return float(self.t[0])
class String(Token):
    def val(self): return self.t[0][1:-1]
class List(Token): pass
class Vector(Token): pass
class Map(Token): pass
class Set(Token): pass
class Literal(Token): pass
class Tilda(Token): pass
class DTilda(Token): pass

def set_class(p, C):
    p.setParseAction(lambda t: C(t))
    return p

(
    LPAR, RPAR, LBRK, RBRK, LBRC, RBRC, HASH, QUOTE, TICK, COLON, TILDA, STAR
) = map(Suppress, "()[]{}#'`:~*")

symbol = set_class(Regex(r'[\w\d\-./_*+=]+'), Symbol)
keyword = set_class(Group(COLON + symbol), Keyword)

decimal = set_class(Regex(r'-?0|[1-9]\d*'), Decimal)
real = set_class(Regex(r"[+-]?\d+\.\d*([eE][+-]?\d+)?"), Real)

dblQuotedString = set_class(dblQuotedString, String)

scalars = real | decimal | symbol | keyword | dblQuotedString

sexp = Forward()
sexpList = set_class(Group(LPAR + ZeroOrMore(sexp) + RPAR), List)
sexpVector = set_class(Group(LBRK + ZeroOrMore(sexp) + RBRK), Vector)
sexpMap = set_class(Group(LBRC + ZeroOrMore(sexp) + RBRC), Map)
sexpSet = set_class(Group(HASH + LBRC + ZeroOrMore(sexp) + RBRC), Set)
sexpLiteral = set_class(Group(QUOTE + sexp), Literal)
sexpTilda = set_class(Group(TILDA + sexp), Tilda)
sexpDTilda = set_class(Group(TILDA + TILDA + sexp), DTilda)
sexpTicked = set_class(Group(TICK + sexp), Tick)
sexp << (
    scalars |
    sexpList |
    sexpVector |
    sexpMap |
    sexpSet |
    sexpLiteral |
    sexpTicked |
    sexpDTilda |
    sexpTilda 
)

def clean_up(tree):
    tree_type = type(tree)
    # currently we do not distinguish between List and Vector, both become
    # python list. List should become a linked list, and Vector remain list.
    if tree_type in (List, Vector):
        val = tree.val()
        return [clean_up(i) for i in val]
    elif tree_type in (String, Decimal, Real):
        return tree.val()
    elif tree_type == Symbol:
        return tree
    elif tree_type == Tick:
        return Tick([clean_up(tree.val())])
    elif tree_type == Tilda:
        return Tilda([tree.val()[0].val()])
    elif tree_type == DTilda:
        return DTilda([tree.val()[0].val()])
    elif tree_type == Keyword:
        return Keyword([tree.val()[0].val()])
    elif tree_type == Map:
        val = tree.val()
        assert len(val) % 2 == 0, "wrong number of items passed to Hash"
        return dict(
            [
                (clean_up(val[2 * i]), clean_up(val[2 * i + 1])) 
                for i in range(len(val)/2)
            ]
        )
    elif tree_type == Literal:
        val = tree.val()
        return Literal([[clean_up(i) for i in val]])
    elif tree_type == Set:
        val = tree.val()
        return set([clean_up(i) for i in val])
    else:
        print(tree_type)
        raise SyntaxError("Bad tree type %s: %s" % (tree_type, tree))

def parse(s):
    return clean_up(sexp.parseString(s, parseAll=False)[0])

STACK = []
GLOBALS = {}
MACROS = {}

def summer(*args): return sum(args)
def minuser(first, *rest): return reduce(lambda x, y: x - y, rest, first)
def prodder(*args): return reduce(lambda x, y: x * y, args, 1)
def divider(first, *rest): return reduce(lambda x, y: x / y, rest, first)
def prit(*args): print(*args, end="")

def setter(name, value):
    if name in STACK[-1]: raise SyntaxError("Value already set")
    assert type(name) == Symbol
    STACK[-1][name.val()] = value
    return value

def msetter(name, value):
    if name in MACROS: raise SyntaxError("Value already set")
    assert type(name) == Symbol
    MACROS[name.val()] = value
    return value

def gsetter(name, value):
    if name in GLOBALS: raise SyntaxError("Value already set")
    assert type(name) == Symbol
    MACROS[name.val()] = value
    return value

def defmacro(name, body):
    return gsetter(name, Macro(name, body))

CORE = {
    "prit": prit,
    "+": summer,
    "-": minuser,
    "*": prodder,
    "/": divider,
    "=": setter,
}

def get_mod_func(callback):
    # Converts 'django.views.news.stories.story_detail' to
    # ['django.views.news.stories', 'story_detail']
    try:
        dot = callback.rindex('.')
    except ValueError:
        return callback, ''
    return callback[:dot], callback[dot+1:]

def merge_leading_and_rest(leading, rest, and_resolve=True):
    if leading:
        rest.insert(0, leading)
    if not and_resolve: return rest
    rest2 = []
    for item in rest:
        if isinstance(item, list):
            rest2.append(eval_list(item))
        elif isinstance(item, Symbol):
            rest2.append(eval_symbol(item))
        else:
            rest2.append(item)
    return rest2

class Macro(object):
    def __init__(self, name, body):
        self.name = name
        self.body = body
        assert(isinstance(self.body[0], list))

    def __repr__(self):
        return "<%s:%s [%s]>" % (
            self.__class__.__name__, self.name.val(), self.body
        )

    def __str__(self): return repr(self)
    def __call__(self, *args):
        stack_incr()
        try:
            print(self.name, self.body, args)
            for var in self.body[0]:
                print("var", var)
                assert(isinstance(var, Symbol))
                if var.val().startswith("*"):
                    setter(Symbol([var.val()[1:]]), args[:])
                    args = []
                    break
                else:
                    setter(var, args[0])
                    args = args[1:]
            if args:
                raise SyntaxError("arguments do not match")
            print(STACK, self.body[1:])
        finally:
            stack_decr()

class Lambda(Macro): pass

def stack_incr():
    STACK.append({})

def stack_decr():
    STACK.pop()

def eval_symbol(symbol0):
    symbol = symbol0.val()
    val = CORE.get(symbol)
    if val:
        return val
    mod_name, func_name = get_mod_func(symbol)
    try:
        val = getattr(__import__(mod_name, {}, {}, ['']), func_name)
    except ImportError:
        try:
            val = getattr(__builtin__, symbol)
        except AttributeError:
            pass
    if val:
        return val
    if symbol in STACK[-1]:
        return STACK[-1][symbol]
    if symbol in MACROS:
        return MACROS[symbol]
    return symbol0

def resolve(head, leading, rest):
    # head can be:
    #   a callable
    #       see if it has leading named attribute on it
    #   a list
    #       call eval_list on it
    #   a symbol
    #       already defined lambda or macro
    #       a "local"/"global" variable
    #   else it is syntax error
    if isinstance(head, list):
        return eval_list(head), merge_leading_and_rest(leading, rest)
    elif isinstance(head, Symbol) and head.val() == "defmacro":
        return defmacro, (leading, rest)
    elif isinstance(head, Symbol):
        head = eval_symbol(head)
        return head, merge_leading_and_rest(
            leading, rest, not isinstance(head, Macro)
        )
    elif (
        leading
        and isinstance(leading, Symbol)
        and hasattr(head, leading.val())
        and callable(getattr(head, leading.val()))
    ):
        return getattr(head, leading.val()), rest
    elif callable(head):
        return head, merge_leading_and_rest(leading, rest)
    else:
        raise SyntaxError(
            "head must be either a list of a symbol, found %s" % head
        )

def eval_list(expr_list, new_stack=True):
    if new_stack: stack_incr()
    if not isinstance(expr_list, list):
        raise SyntaxError("Only lists can be evaled")
    head = expr_list[0]
    leading = None
    rest = []
    if len(expr_list) >= 2:
        leading, rest = expr_list[1], expr_list[2:]
    callback, rest = resolve(head, leading, rest)
    print(callback, rest)
    val = callback(*rest)
    if new_stack: stack_decr()
    return val

def evals(s, dump_tree=False):
    tree = parse(s)
    if dump_tree:
        pprint(tree)
    return eval_list(tree)

evals("(defmacro do [x *args] (~~ args2))")
print(MACROS, GLOBALS)

# http://blog.hackthology.com/writing-an-interactive-repl-in-python
# http://docs.python.org/2/library/cmd.html
# http://www.alittletooquiet.net/media//docs/sclapp-0.5.3.html
# https://github.com/iridium172/PyTerm/blob/master/pyterm.py
# http://openbookproject.net/py4fun/userInput/userInput.html

def test():
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)

def main():
    import argparse
    parser = argparse.ArgumentParser(
        prog="lipy", description='lipy - a pythonic lisp'
    )
    parser.add_argument("--test", "-t", action="store_true")
    parser.add_argument("--eval", "-e")
    parser.add_argument("--tree", action="store_true")
    parser.add_argument("file", nargs="?")

    args = parser.parse_args()

    if args.test:
        test()
    elif args.eval:
        evals(args.eval, args.tree)
    elif args.file:
        print(args.file)
        if args.file == "-":
            evals(sys.stdin.read(), args.tree)
        else:
            evals(file(args.file).read(), args.tree)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

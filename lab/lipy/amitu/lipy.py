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

#>>> evals("1 2") # how to handle this?, clojure treats as two statements
Traceback (most recent call last):
...
SyntaxError: Only lists can be evaled
#>>>

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
>>> evals('(var x 10)')
>>> evals('(print x)')
10
>>> evals('(= y 10)')
Traceback (most recent call last):
...
SyntaxError: setting an unknown variable y
>>> evals("(var x 12)")
Traceback (most recent call last):
...
AssertionError: variable redeclared? x
>>> evals("(= x 20)")
>>> evals("(print x)")
20
>>> evals('(do (print 1) (print 10))')
1
10
"""
from __future__ import print_function

"""
>>> evals('(do (var y 12) (print y))')
12
>>> evals('(defmacro test1 [x] (print (~ x)))')
<Macro:test1 ...>
>>> evals('(test1 1)')
1
>>> evals('(test1 (string.upper "hello"))')
HELLO
>>> evals('(== 1 2)')
False
>>> evals('(< 1 2)')
True
>>> evals('(>= 200 200)')
True
>>> evals('(not (< (+ 1 2) (* 3 6)))')
False
>>> evals('(not True)')
False
>>> evals('(if (== 2 2) (do (print "yo") (print "man")) (print ":-("))')
yo
man
>>> evals("\
(do\
    (var dofact (fn [x acc]\
        (if (== x 1)\
            (~ acc)\
            (dofact (- x 1) (* acc x))\
        )\
    ))\
    (print (dofact 5 1))\
)\
")
120

"""
import sys, inspect
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

def set_class(p, C):
    p.setParseAction(lambda t: C(t))
    return p

(
    LPAR, RPAR, LBRK, RBRK, LBRC, RBRC, HASH, QUOTE, TICK, COLON, STAR
) = map(Suppress, "()[]{}#'`:*")

symbol = set_class(Regex(r'[\w\d\-./~_*+=?<>]+'), Symbol)
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
sexpTicked = set_class(Group(TICK + sexp), Tick)
sexp << (
    scalars |
    sexpList |
    sexpVector |
    sexpMap |
    sexpSet |
    sexpLiteral |
    sexpTicked
)
msexp = ZeroOrMore(sexp)

def clean_up(tree):
    tree_type = type(tree)
    # currently we do not distinguish between List and Vector, both become
    # python list. List should become a linked list, and Vector remain list.
    if tree_type in (List, Vector):
        val = tree.val()
        return [clean_up(i) for i in val]
    elif tree_type == list:
        return [clean_up(i) for i in tree]
    elif tree_type in (String, Decimal, Real):
        return tree.val()
    elif tree_type == Symbol:
        return tree
    elif tree_type == Tick:
        return Tick([clean_up(tree.val())])
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
    #print("parse", s, msexp.parseString(s).asList())
    return clean_up(msexp.parseString(s).asList())

STACK = [{}]
GLOBALS = {}
MACROS = {}

def summer(*args): return sum(args)
def minuser(first, *rest): return reduce(lambda x, y: x - y, rest, first)
def prodder(*args): return reduce(lambda x, y: x * y, args, 1)
def divider(first, *rest): return reduce(lambda x, y: x / y, rest, first)
def prit(*args): print(*args, end="")

def setter(name, value):
    assert type(name) == Symbol, "n=%s v=%s" % (name, value)
    stack_set(name.val(), value)
    return value

def msetter(name, value):
    assert type(name) == Symbol, name
    MACROS[name.val()] = value
    return value

def gsetter(name, value):
    assert type(name) == Symbol, name
    GLOBALS[name.val()] = value
    return value

def defmacro(name, body):
    if (name.val() == "if"):
        return msetter(name, IF(name, body))
    elif (name.val() == "fn"):
        return msetter(name, Lambda(name, body))
    elif (name.val() == "var"):
        return msetter(name, Var(name, body))
    elif (name.val() == "="):
        return msetter(name, Equal(name, body))
    else:
        return msetter(name, Macro(name, body))

def eval_llist(expr_llist):
    #print ("eval_llist", expr_llist)
    last = None
    for expr_list in expr_llist:
        last = eval_list(expr_list)
    #print("eval_list done", expr_llist, last)
    return last

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

    def eval_vars(self, args):
        for var in self.body[0]:
            #print("var", var)
            assert(isinstance(var, Symbol))
            if var.val().startswith("*"):
                stack_set(Symbol([var.val()[1:]]), args[:], True)
                args = []
                break
            else:
                stack_set(var, args[0], True)
                args = args[1:]
        if args:
            raise SyntaxError("arguments do not match")

    def __call__(self, *args):
        self.eval_vars(args)
        last = None
        for body in self.body[1:]:
            last = eval_list(body)
        return last

def s(sym):
    return Symbol([sym])

class IF(Macro):
    def __call__(self, *args):
        self.eval_vars(args)
        if eval_list([s("?"), [s("~"), s("cond")]]):
            return eval_list([Symbol(["~"]), Symbol(["then"])])
        else:
            return eval_list([Symbol(["~"]), Symbol(["else"])])

class Var(Macro):
    def __call__(self, *args):
        assert len(args) % 2 == 0, "uneven number of params passed"
        for i in range(len(args)/2):
            k, v = args[2 * i], args[2 * i + 1]
            assert isinstance(k, Symbol), (
                "key is not a symbol: %s, %s" % (k, args)
            )
            stack_set(k.val(), v, top=True)

class Equal(Macro):
    def __call__(self, name, value):
        assert isinstance(name, Symbol)
        if stack_lookup(name.val()) == NOT_FOUND:
            raise SyntaxError("setting an unknown variable %s" % name.val())
        stack_set(name.val(), value)

class Lambda(Macro):
    def __call__(self, *args):
        stack_incr()
        try:
            self.eval_vars(args)
            def fn(*fn_args):
                for arg in eval_symbol(s("args")):
                    setter(arg, fn_args[0])
                    fn_args = fn_args[1:]
                if fn_args:
                    raise SyntaxError("bad number of params")
                return eval_llist(eval_symbol(s("body")))
            return fn
        finally:
            stack_decr()

def stack_reset():
    global STACK
    STACK = [{}]

def stack_incr():
    STACK.append({})

def stack_decr():
    STACK.pop()

NOT_FOUND = object()

def eval_symbol(symbol0):
    symbol = symbol0.val()
    if symbol == "True":
        return True
    if symbol == "False":
        return False
    val = CORE.get(symbol, NOT_FOUND)
    if val != NOT_FOUND:
        return val
    val = stack_lookup(symbol)
    if val != NOT_FOUND:
        return val
    mod_name, func_name = get_mod_func(symbol)
    try:
        val = getattr(__import__(mod_name, {}, {}, ['']), func_name)
    except ImportError:
        try:
            val = getattr(__builtin__, symbol)
        except AttributeError:
            val = NOT_FOUND
    except ValueError:
        val = NOT_FOUND
    if val != NOT_FOUND:
        return val
    if symbol in MACROS:
        return MACROS[symbol]
    return symbol0

def stack_set(name, value, top=False):
    #print("stack_set", name, value, top)
    if top:
        assert name not in STACK[-1], "variable redeclared? %s" % name
        STACK[-1][name] = value
        return
    else:
        for i in range(len(STACK) - 1, -1, -1):
            stack = STACK[i]
            if name in stack:
                stack[name] = value
                return
        raise SyntaxError("setting an unknown variable %s" % name)


def stack_lookup(symbol):
    for i in range(len(STACK) - 1, -1, -1):
        stack = STACK[i]
        if symbol in stack:
            return stack[symbol]
    return NOT_FOUND

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
    #print("resolve", head, leading, rest)
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

max_stack = 0

def check_stack_depth():
    global max_stack
    current_stack_depth = len(inspect.stack())
    if max_stack < current_stack_depth:
        max_stack = current_stack_depth

def eval_list(expr_list):
    check_stack_depth()
    if type(expr_list) != list: return expr_list
    if not isinstance(expr_list, list):
        raise SyntaxError("Only lists can be evaled")
    head = expr_list[0]
    leading = None
    rest = []
    if len(expr_list) >= 2:
        leading, rest = expr_list[1], expr_list[2:]
    callback, rest = resolve(head, leading, rest)
    #print("eval_list before", callback, rest)
    assert callable(callback), "%s is not callable [%s]" % (callback, expr_list)
    val = callback(*rest)
    #print("eval_list after", callback, rest, val, "END")
    return val

CORE = {
    "prit": prit,
    "+": summer,
    "-": minuser,
    "*": prodder,
    "/": divider,
    "~": eval_list,
    "~~": eval_llist,
    "==": lambda x, y: x == y,
    ">": lambda x, y: x > y,
    ">=": lambda x, y: x >= y,
    "<": lambda x, y: x < y,
    "<=": lambda x, y: x <= y,
    "?": lambda x: True if x else False,
}

def evals(s, dump_tree=False):
    tree = parse(s)
    if dump_tree:
        pprint(tree)
    return eval_llist(tree)

evals("(defmacro do [*args] (~~ args))")
evals("(defmacro if [cond then else] (...))")
#evals("(defmacro fn [args *body] (~~ body))")
#evals("(defmacro not [p] (if (~ p) (~ False) (~ True)))")
evals("(defmacro var [*args] (...))")
evals("(defmacro = [name value] (...))")
#evals("(defmacro defn [name args *body] (= name (fn args (~~ body))))")

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
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--eval", "-e")
    parser.add_argument("--tree", action="store_true")
    parser.add_argument("file", nargs="?")

    args = parser.parse_args()

    if args.test:
        test()
    elif args.eval:
        evals(args.eval, args.tree)
    elif args.file:
        sys.setrecursionlimit(40000)
        if args.file == "-":
            evals(sys.stdin.read(), args.tree)
        else:
            evals(file(args.file).read(), args.tree)
    else:
        parser.print_help()
    if args.verbose:
        print("Done, max_stack =", max_stack)

if __name__ == "__main__":
    main()

# whats remaining:
#   * eval_list becomes eval_form, processes every form, recirsively if
#     its a collection
#   * (defmacro fn), it takes all arguments and wraps them around (~)
#   * stack
#   * can we convert eval_list from recursive to iterative form? required for
#     tail call optimization/stacklessness
#   * booleans and conditions, how to handle them
#   * modules and import

# https://bitbucket.org/pypy/pypy/src/default/pypy/interpreter/mixedmodule.py
# http://mail.python.org/pipermail/pypy-dev/2006-April/002985.html
# http://doc.pypy.org/en/latest/coding-guide.html#implementing-a-mixed-interpreter-application-level-module
# http://stackoverflow.com/questions/10470800/compile-pypy-to-exe
# http://pyppet.blogspot.in/2010/08/rpython-callbacks-from-c.html
# http://code.google.com/p/rpythonic/wiki/UnderstandingRpython
# http://pyppet.blogspot.in/2010/08/rpython-callbacks-from-c.html

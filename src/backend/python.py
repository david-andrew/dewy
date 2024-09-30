from dataclasses import dataclass

from ..postparse import post_parse
from ..tokenizer import tokenize
from ..postok import post_process
from ..parser import top_level_parse, Scope
from ..syntax import (
    AST,
    Type,
    ListOfASTs, Tuple, Block, Array, Group, Range, Object, Dict,
    TypedIdentifier,
    Void, void, Undefined, undefined,
    String, IString,
    Flowable, Flow, If, Loop, Default,
    PrototypeIdentifier, Identifier, Express,
    FunctionLiteral, PrototypePyAction, PyAction, Call,
    Assign,
    Int, Bool,
    Range, IterIn,
    Less, LessEqual, Greater, GreaterEqual, Equal, MemberIn,
    LeftShift, RightShift, LeftRotate, RightRotate, LeftRotateCarry, RightRotateCarry,
    Add, Sub, Mul, Div, IDiv, Mod, Pow,
    And, Or, Xor, Nand, Nor, Xnor,
    Not, UnaryPos, UnaryNeg, UnaryMul, UnaryDiv,
    # DeclarationType,
)
from pathlib import Path
from typing import Protocol, cast, Callable
from functools import cache

import pdb


class Iter(AST):
    item: AST
    i: int

    def __str__(self):
        return f'Iter({self.item}, i={self.i})'


def python_interpreter(path: Path, args: list[str]):

    with open(path) as f:
        src = f.read()

    tokens = tokenize(src)
    post_process(tokens)

    ast = top_level_parse(tokens)
    ast = post_parse(ast)

    #TODO: put these under a verbose/etc. flag
    print_ast(ast)
    print(repr(ast))
    # from ..postparse import traverse_ast
    # for parent, child in traverse_ast(ast):
    #     print(f'{parent=},\n||||{child=}')
    # pdb.set_trace()

    res = top_level_evaluate(ast)
    if res is not void:
        print(res)

def print_ast(ast: AST):
    """little helper function to print out the equivalent source code of an AST"""
    print('```dewy')
    if isinstance(ast, (Block, Group)):
        for i in ast.__iter_asts__(): print(i)
    else:
        print(ast)
    print('```')


def top_level_evaluate(ast:AST) -> AST:
    scope = Scope.default()
    insert_pyactions(scope)
    return evaluate(ast, scope)


class EvalFunc[T](Protocol):
    def __call__(self, ast: T, scope: Scope) -> AST: ...


def no_op[T](ast: T, scope: Scope) -> T:
    """For ASTs that just return themselves when evaluated"""
    return ast

def cannot_evaluate(ast: AST, scope: Scope) -> AST:
    raise ValueError(f'INTERNAL ERROR: evaluation of type {type(ast)} is not possible')


@cache
def get_eval_fn_map() -> dict[type[AST], EvalFunc]:
    return {
        Call: evaluate_call,
        Block: evaluate_block,
        Group: evaluate_group,
        Array: evaluate_array,
        Assign: evaluate_assign,
        IterIn: evaluate_iter_in,
        FunctionLiteral: evaluate_function_literal,
        Closure: evaluate_closure,
        PyAction: evaluate_pyaction,
        String: no_op,
        IString: evaluate_istring,
        Identifier: cannot_evaluate,
        Express: evaluate_express,
        Int: no_op,
        Range: no_op,
        Loop: evaluate_loop,
        Less: evaluate_less,
        And: evaluate_and,
        Or: evaluate_or,
        Add: evaluate_add,
        #TODO: other AST types here
    }

def evaluate(ast:AST, scope:Scope) -> AST:
    eval_fn_map = get_eval_fn_map()

    ast_type = type(ast)
    if ast_type in eval_fn_map:
        return eval_fn_map[ast_type](ast, scope)

    raise NotImplementedError(f'evaluation not implemented for {ast_type}')



def evaluate_call(ast: Call, scope: Scope) -> AST:
    f = ast.f
    if isinstance(f, Group):
        f = evaluate(f, scope)
    if isinstance(f, Identifier):
        f = scope.get(f.name).value
    assert isinstance(f, (PyAction, Closure)), f'expected Function or PyAction, got {f}'

    if isinstance(f, PyAction):
        args, kwargs = collect_args(ast.args, scope)
        return f.action(*args, **kwargs, scope=scope)

    if isinstance(f, Closure):
        args, kwargs = collect_args(ast.args, scope)
        return evaluate(f.fn.body, f.scope)

    pdb.set_trace()
    raise NotImplementedError(f'Function evaluation not implemented yet')

def collect_args(args: AST | None, scope: Scope) -> tuple[list[AST], dict[str, AST]]:
    match args:
        case None: return [], {}
        case Identifier(name): return [scope.get(name).value], {}
        case Assign(): raise NotImplementedError('Assign not implemented yet')
        # case Tuple(items): raise NotImplementedError('Tuple not implemented yet')
        case String() | IString(): return [args], {}
        case _: raise NotImplementedError(f'collect_args not implemented yet for {args}')


    raise NotImplementedError(f'collect_args not implemented yet for {args}')

def evaluate_group(ast: Group, scope: Scope):

    expressed: list[AST] = []
    for expr in ast.items:
        res = evaluate(expr, scope)
        if res is not void:
            expressed.append(res)
    if len(expressed) == 0:
        return void
    if len(expressed) == 1:
        return expressed[0]
    raise NotImplementedError(f'Block with multiple expressions not yet supported. {ast=}, {expressed=}')


def evaluate_block(ast: Block, scope: Scope):
    scope = Scope(scope)
    return evaluate_group(Group(ast.items), scope)

def evaluate_array(ast: Array, scope: Scope):
    return Array([evaluate(i, scope) for i in ast.items])

def evaluate_assign(ast: Assign, scope: Scope):
    match ast:
        case Assign(left=Identifier(name), right=right):
            right = evaluate(right, scope)
            scope.assign(name, right)
            return void
    pdb.set_trace()
    raise NotImplementedError('Assign not implemented yet')

def evaluate_iter_in(ast: IterIn, scope: Scope):
    def step_iter_in(iter_props: tuple[Callable, Iter], scope: Scope) -> AST:
        binder, iterable = iter_props
        cond, val = iter_next(iterable).items
        binder(val)
        return cond

    if hasattr(ast, 'iter_props'):
        return step_iter_in(ast.iter_props, scope)

    match ast:
        case IterIn(left=Identifier(name), right=right):
            right = evaluate(right, scope)
            binder, iterable = lambda x: scope.assign(name, x), Iter(item=right, i=0)
            ast.iter_props = binder, iterable
            return step_iter_in(ast.iter_props, scope)

    pdb.set_trace()
    raise NotImplementedError('IterIn not implemented yet')

# TODO: probably break this up into one function per type of iterable
def iter_next(iter: Iter):
    match iter.item:
        case Array(items):
            if iter.i >= len(items):
                cond, val = Bool(False), undefined
            else:
                cond, val = Bool(True), items[iter.i]
            iter.i += 1
            return Array([cond, val])
        case Range(left=Int(val=l), right=Void(), brackets=brackets):
            offset = int(brackets[0] == '(') # handle if first value is exclusive
            cond, val = Bool(True), Int(l + iter.i + offset)
            iter.i += 1
            return Array([cond, val])
        case Range(left=Tuple(items=[Int(val=r0), Int(val=r1)]), right=Void(), brackets=brackets):
            offset = int(brackets[0] == '(') # handle if first value is exclusive
            step = r1 - r0
            cond, val = Bool(True), Int(r0 + (iter.i + offset) * step)
            iter.i += 1
            return Array([cond, val])
        #TODO: other range cases...
        case _:
            pdb.set_trace()
            raise NotImplementedError(f'iter_next not implemented yet for {iter.item=}')



class Closure(AST):
    fn: FunctionLiteral
    scope: Scope
    # call_args: AST|None=None # TBD how to handle
    def __str__(self):
        return f'Closure({self.fn}, scope={self.scope})'

def evaluate_function_literal(ast: FunctionLiteral, scope: Scope):
    return Closure(fn=ast, scope=scope)

def evaluate_closure(ast: Closure, scope: Scope):
    fn_scope = Scope(ast.scope)
    #TODO: for now we assume everything is 0 args. need to handle args being attached to the closure
    return evaluate(ast.fn.body, fn_scope)

    #grab arguments from scope and put them in fn_scope
    pdb.set_trace()
    ast.fn.args
    raise NotImplementedError('Closure not implemented yet')

def evaluate_pyaction(ast: PyAction, scope: Scope):
    # fn_scope = Scope(ast.scope)
    #TODO: currently just assuming 0 args in and no return
    return ast.action(scope)


def evaluate_istring(ast: IString, scope: Scope) -> String:
    parts = (py_stringify(i, scope) for i in ast.parts)
    return String(''.join(parts))


def evaluate_express(ast: Express, scope: Scope):
    val = scope.get(ast.id.name).value
    return evaluate(val, scope)


#TODO: this needs improvements!
def evaluate_loop(ast: Loop, scope: Scope):
    ast._was_entered = False
    scope = Scope(scope)
    while cast(Bool, evaluate(ast.condition, scope)).val:
        ast._was_entered = True
        evaluate(ast.body, scope)

    # for now loops can't return anything
    return void
    # ast.body
    # ast.condition
    # pdb.set_trace()


def evaluate_less(ast: Less, scope: Scope):
    left = evaluate(ast.left, scope)
    right = evaluate(ast.right, scope)
    match left, right:
        case Int(val=l), Int(val=r): return Bool(l < r)
        case _:
            raise NotImplementedError(f'Less not implemented for {left=} and {right=}')


def evaluate_and(ast: And, scope: Scope):
    left = evaluate(ast.left, scope)
    right = evaluate(ast.right, scope)
    match left, right:
        case Bool(val=l), Bool(val=r): return Bool(l and r)
        case _:
            raise NotImplementedError(f'And not implemented for {left=} and {right=}')

def evaluate_or(ast: Or, scope: Scope):
    left = evaluate(ast.left, scope)
    right = evaluate(ast.right, scope)
    match left, right:
        case Bool(val=l), Bool(val=r): return Bool(l or r)
        case _:
            raise NotImplementedError(f'Or not implemented for {left=} and {right=}')

def evaluate_add(ast: Add, scope: Scope):
    left = evaluate(ast.left, scope)
    right = evaluate(ast.right, scope)
    match left, right:
        case Int(val=l), Int(val=r): return Int(l + r)
        case _:
            raise NotImplementedError(f'Add not implemented for {left=} and {right=}')

######################### Builtin functions and helpers ############################
def py_stringify(ast: AST, scope: Scope) -> str:
    ast = evaluate(ast, scope)
    match ast:
        case String(val): return val
        case Int(val): return str(val)
        case _:
            pdb.set_trace()
            raise NotImplementedError(f'stringify not implemented for {type(ast)}')
    pdb.set_trace()

    raise NotImplementedError('stringify not implemented yet')

def py_printl(s:String|IString, scope: Scope) -> Void:
    py_print(s, scope)
    print()
    return void

def py_print(s:String|IString, scope: Scope) -> Void:
    if not isinstance(s, (String, IString)):
        raise ValueError(f'py_print expected String or IString, got {type(s)}:\n{s!r}')
    if isinstance(s, IString):
        s = cast(String, evaluate(s, scope))
    print(s.val, end='')
    return void

def py_readl(scope: Scope) -> String:
    return String(input())

def insert_pyactions(scope: Scope):
    """replace pyaction stubs with actual implementations"""
    if 'printl' in scope.vars:
        assert isinstance((proto:=scope.vars['printl'].value), PrototypePyAction)
        scope.vars['printl'].value = PyAction(proto.args, py_printl, proto.return_type)
    if 'print' in scope.vars:
        assert isinstance((proto:=scope.vars['print'].value), PrototypePyAction)
        scope.vars['print'].value = PyAction(proto.args, py_print, proto.return_type)
    if 'readl' in scope.vars:
        assert isinstance((proto:=scope.vars['readl'].value), PrototypePyAction)
        scope.vars['readl'].value = PyAction(proto.args, py_readl, proto.return_type)

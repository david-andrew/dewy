from typing import Callable


def python_interpreter(path:str, args:list[str]):
    from tokenizer import tokenize
    from postok import post_process
    from parser import top_level_parse
    from dewy import Scope

    with open(path) as f:
        src = f.read()
    
    tokens = tokenize(src)
    post_process(tokens)

    root = Scope.default()
    ast = top_level_parse(tokens, root)
    res = ast.eval(root)
    if res: print(res)


def llvm_compiler(path:str, args:list[str]):
    raise NotImplementedError('LLVM backend is not yet supported')

def c_compiler(path:str, args:list[str]):
    raise NotImplementedError('C backend is not yet supported')

def x86_64_compiler(path:str, args:list[str]):
    raise NotImplementedError('x86_64 backend is not yet supported')

backend_map = {
    'python': python_interpreter,
    'llvm': llvm_compiler,
    'c': c_compiler,
    'x86_64': x86_64_compiler
}
backends = [*backend_map.keys()]

def get_backend(name:str) -> Callable[[str, list[str]], None]:
    try:
        return backend_map[name.lower()]
    except:
        raise ValueError(f'Unknown backend "{name}"') from None
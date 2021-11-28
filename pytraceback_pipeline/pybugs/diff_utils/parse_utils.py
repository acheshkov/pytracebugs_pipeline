import ast
from typing import Tuple, Union


def gen_ast_subnodes(ast_node: Union[ast.Module, ast.AST]) -> Tuple[str, str, Union[ast.Module, ast.AST]]:
    for child in ast.walk(ast_node):
        if child == ast_node:
            continue
        if not isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.Lambda, ast.AsyncFunctionDef)):
            continue

        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decorators = " ".join(["@" + ast.unparse(c) for c in child.decorator_list])
            if isinstance(ast_node, ast.Module):
                yield child.name, decorators,  child
            else:
                yield f'{ast_node.name}.{child.name}', decorators, child
        yield from gen_ast_subnodes(child)


def gen_ast_nodes(text: str) -> Tuple[str, str, Union[ast.Module, ast.AST]]:
    try:
        ast_parsed = ast.parse(text)
        yield from gen_ast_subnodes(ast_parsed)
    except Exception as e:
        print("Parsing error", e)


def gen_python_func_names_and_texts(text: str) -> Tuple[str, str, Union[ast.Module, ast.AST]]:
    for name, decorators, ast_node in gen_ast_nodes(text):
        yield name, decorators, ast.unparse(ast_node)


def gen_python_func_names_and_texts_full(text: str) -> Tuple[str, str, Union[ast.Module, ast.AST]]:
    for name, decorators, ast_node in gen_ast_nodes(text):
        yield name, decorators, '\n'.join(text.split('\n')[ast_node.lineno-1: ast_node.end_lineno])

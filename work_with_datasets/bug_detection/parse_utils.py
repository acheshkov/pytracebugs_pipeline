from pathlib import Path

import utils


def build_tree_sitter_lib(output_dir, output_lib, install=True, clone=True):
    if install:
        utils.install('tree_sitter')
        utils.install('GitPython')
    
    from tree_sitter import Language
    import git

    tree_sitter_dir = Path(output_dir)
    tree_sitter_dir.mkdir(parents=True, exist_ok=True)

    if clone:
        git.Repo.clone_from('https://github.com/tree-sitter/tree-sitter-python' , tree_sitter_dir / Path('tree-sitter-python' ), branch='master')
        git.Repo.clone_from('https://github.com/tree-sitter/tree-sitter-java'   , tree_sitter_dir / Path('tree-sitter-java'   ), branch='master')
        git.Repo.clone_from('https://github.com/tree-sitter/tree-sitter-c-sharp', tree_sitter_dir / Path('tree-sitter-c-sharp'), branch='master')

    tree_sitter_lib = tree_sitter_dir / Path(output_lib)
    Language.build_library(
        str(tree_sitter_lib),
        [
            tree_sitter_dir / Path('tree-sitter-python'),
            tree_sitter_dir / Path('tree-sitter-java'),
            tree_sitter_dir / Path('tree-sitter-c-sharp')
        ]
    )
    return tree_sitter_lib

def subnodes_by_type(node, node_type):
    if node.type == node_type:
        return [node]
    nodes = []
    for child in node.children:
        nodes.extend(subnodes_by_type(child, node_type))
    return nodes

def extract_methods(text, parser):
    tree = parser.parse(bytes(text, 'utf8'))
    return subnodes_by_type(tree.root_node, 'function_definition')

def balanced_parentheses_check(s):
    parentheses = ['()', '{}', '[]']
    s_ = ''.join([ch for ch in s if ch in ''.join(parentheses)])
    while any(x in s_ for x in parentheses):
        for p in parentheses:
            s_ = s_.replace(p, '')
    return not s_

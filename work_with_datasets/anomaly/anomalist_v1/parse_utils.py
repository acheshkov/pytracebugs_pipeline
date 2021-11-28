import ast
import tokenize

import intervaltree

def path_to_parse_tree(path):
    with tokenize.open(path) as f:
        return ast.parse(f.read(), filename=path)

def code_to_parse_tree(code):
    return ast.parse(code)

def parse_tree_to_set(parse_tree, types):
    set_all = set([])
    for node in ast.walk(parse_tree):
        if isinstance(node, types):
            # from 1, end incl.
            beg, end = node.lineno, node.end_lineno
            # from 0, incl.
            set_all |= set(range(beg-1, end))
    return set_all

def parse_tree_to_interval_tree(parse_tree, types):
    interval_tree = intervaltree.IntervalTree()
    for node in ast.walk(parse_tree):
        if isinstance(node, types):
            # from 1, end incl.
            beg, end = node.lineno, node.end_lineno
            # from 0, end excl.
            interval_tree[beg-1:end] = node
    return interval_tree
    
def path_to_interval_tree(path, types):
    return parse_tree_to_interval_tree(path_to_parse_tree(path), types)

def code_to_interval_tree(code, types):
    return parse_tree_to_interval_tree(code_to_parse_tree(code), types)

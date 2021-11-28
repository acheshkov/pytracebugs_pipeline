from tree_sitter import Language, Parser

PY_LANGUAGE = Language('D:\\tree-sitter-python\\build\\my-languages.so', 'python')


def is_correct_Python_code_snippet(code_snippet):
    def walk_tree(node):
        if node.type == 'ERROR':
            return False
        for child in node.children:
            if child.type == 'ERROR':
                return False
            else:
                if not walk_tree(child):
                    return False

        return True

    if not code_snippet:
        return False
    print('Processing code snippet')

    parser = Parser()
    parser.set_language(PY_LANGUAGE)
    tree = parser.parse(bytes(code_snippet, "utf8"))
    is_correct = walk_tree(tree.root_node)
    if is_correct:
        print('It is a correct Python snippet')
    else:
        print('It is not a correct Python snippet')
    return is_correct


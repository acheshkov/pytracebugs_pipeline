import ast
import uuid
import javalang

from parse_utils import code_to_interval_tree
from code_storage import CodeStorageLines, CodeStorageFile, CodeStorageFragment


def balanced_parentheses_check(s):
    parentheses = ['()', '{}', '[]']
    s_ = ''.join([ch for ch in s if ch in ''.join(parentheses)])
    while any(x in s_ for x in parentheses):
        for p in parentheses:  
            s_ = s_.replace(p, '')
    return not s_


class CodeItem:
    def __init__(self, lang, storage=None):
        self._lang = lang
        self._storage = storage
                
    def beg(self):
        return self._storage.beg()
     
    def end(self):
        return self._storage.end()
    
    def lines(self):
        return self._storage.lines()
    
    def invalid(self):
        return self.beg() is None or self.end() is None or self.lines() is None

    def get_text(self):
        return self._storage.get_text()

    def get_id(self):
        q = '0'*4
        return str(uuid.uuid3(uuid.UUID(f'{q}{q}-{q}-{q}-{q}-{q}{q}{q}'), self.get_text()))

    def pretty(self, value=None, width=100):
        return f'\n{"="*width}\n{str(value) if value is not None else ""} {self.beg()}:{self.end()}\n{"-"*width}\n{self.get_text()}'
     
    def number_of_lines(self):
        return self._storage.number_of_lines()
 
    def number_of_chars(self):
        return self._storage.number_of_chars()
        
    def load_from_lines(self, path, beg=None, end=None):
        self._storage = CodeStorageLines(path, beg, end)

    def load_from_file(self, path, beg=None, end=None, use_cache=True):
        self._storage = CodeStorageFile(path, beg, end, use_cache)   
        
    def load_from_code(self, code, beg=None, end=None):
        self._storage = CodeStorageFragment(code._storage, beg, end)

    def extract_fragments(self, fragments_types=None, skip=False):
        if self._lang == 'py':
            return self._extract_fragments_py(fragments_types=fragments_types)

        if self._lang == 'java':
            return self._extract_fragments_java(skip=skip)

        assert False

    def _extract_fragments_py(self, fragments_types):
        if fragments_types is None:
            fragments_types = (ast.FunctionDef, ast.AsyncFunctionDef)

        interval_tree = code_to_interval_tree(self.get_text(), fragments_types)

        fragments = []
        for beg, end, node in interval_tree:
            assert isinstance(node, fragments_types)

            fragment = CodeItem(lang=self._lang)
            fragment.load_from_code(self, beg=beg, end=end)
            fragments.append(fragment)

        return fragments

    def _extract_fragments_java(self, skip, check=True):
        lines = self.lines()
        try:
            tree = javalang.parse.parse(self.get_text())
        except Exception as e:
            raise Exception(f'Error in javalang.parse: {e}')

        def find_end(lines, beg):
            for end in range(beg+1, len(lines)):
                if balanced_parentheses_check(''.join(lines[beg:end])):
                    return end
            return -1

        fragments = []
        for _, node in tree.filter(javalang.tree.MethodDeclaration):
            beg = node.position.line-1
            end = find_end(lines, beg)
            if beg >= end:
                continue

            fragment = CodeItem(lang=self._lang)
            fragment.load_from_code(self, beg=beg, end=end)
            fragments.append(fragment)

        return fragments

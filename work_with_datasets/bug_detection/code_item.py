import uuid
from enum import IntEnum, unique

from code_storage import CodeStorageLines, CodeStorageFile, CodeStorageFragment
import parse_utils

@unique
class FragmentType(IntEnum):
    FUNCTION = 0
    WINDOW = 1


class CodeItem:
    def __init__(self, lang, storage=None):
        self._lang = lang
        self._storage = storage

    def __repr__(self):
        r = f'{self._lang} {self.beg()}:{self.end()}'
        r += '\n' + '\n'.join(self.lines())
        return r
                
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
        
    def load_from_lines(self, lines, beg=None, end=None):
        self._storage = CodeStorageLines(lines, beg, end)

    def load_from_file(self, path, beg=None, end=None, use_cache=True):
        self._storage = CodeStorageFile(path, beg, end, use_cache)   
        
    def load_from_code(self, code, beg=None, end=None):
        self._storage = CodeStorageFragment(code._storage, beg, end)

    def extract_fragments(self, parser):
        assert self._lang == 'py', self._lang
        nodes = parse_utils.extract_methods(self.get_text(), parser)
        fragments = []
        for node in nodes:
            fragment = CodeItem(lang=self._lang)
            fragment.load_from_code(self, beg=node.start_point[0], end=node.end_point[0]+1)
            fragments.append(fragment)
        return fragments

    def extract_windows(self, window_size, overlap):
        lines = self.lines()
        step = 1 if overlap else window_size
        locations = [(beg, beg+window_size) for beg in range(0, len(lines)-window_size, step)]
        fragments = []
        for beg, end in locations:
            fragment = CodeItem(lang=self._lang)
            fragment.load_from_lines(lines, beg=beg, end=end)
            fragments.append(fragment)
        return fragments

    def get_fragments(self, fragment_type=None, parser=None, window_size=None, overlap=True):
        if fragment_type == FragmentType.FUNCTION:
            return self.extract_fragments(parser)
        if fragment_type == FragmentType.WINDOW:
            return self.extract_windows(window_size=window_size, overlap=overlap)
        raise NotImplementedError

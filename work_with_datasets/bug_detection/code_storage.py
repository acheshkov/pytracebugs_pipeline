from file_utils import read_lines, read_lines_cacheless


class CodeStorage:
    
    def __init__(self):
        pass
    
    def beg(self):
        pass
    
    def end(self):
        pass
    
    def lines(self):
        pass
    
    def get_text(self):
        return '\n'.join(self.lines())
    
    def number_of_lines(self):
        return self.end()-self.beg()

    def number_of_chars(self):
        if not self.lines():
            return 0
        return sum(len(line) for line in self.lines()) + len(self.lines()) - 1


class CodeStorageLines(CodeStorage):
    
    def __init__(self, lines, beg=None, end=None):
        self.lines_ = lines        
        self.beg_, self.end_ = 0, len(lines)
        assert beg is None or self.beg_ <= beg
        assert end is None or end <= self.end_
        if beg is not None:
            self.beg_ = beg
        if end is not None:
            self.end_ = end
        assert self.beg_ is not None and self.end_ is not None
        assert self.beg_ <= self.end_
        assert self.end_-self.beg_ == len(self.lines_)
    
    def beg(self):
        return self.beg_
    
    def end(self):
        return self.end_
    
    def lines(self):
        return self.lines_


class CodeStorageFile(CodeStorage):
    
    def __init__(self, path, beg=None, end=None, use_cache=True):
        reader = read_lines if use_cache else read_lines_cacheless
        try:
            lines = [line.rstrip('\n') for line in reader(path)]
        except UnicodeDecodeError:
            self.beg_ = None
            self.end_ = None
            self.lines_ = None
            return
        
        self.beg_, self.end_ = 0, len(lines)
        assert beg is None or self.beg_ <= beg
        assert end is None or end <= self.end_
        if beg is not None:
            self.beg_ = beg
        if end is not None:
            self.end_ = end
        assert self.beg_ is not None and self.end_ is not None
        assert self.beg_ <= self.end_
        self.lines_ = lines[self.beg_:self.end_]

    def beg(self):
        return self.beg_
    
    def end(self):
        return self.end_
    
    def lines(self):
        return self.lines_


class CodeStorageFragment(CodeStorage):
    
    def __init__(self, code_storage, beg=None, end=None):
        self.code_storage_ = code_storage
        
        self.beg_, self.end_ = 0, code_storage.number_of_lines()
        assert beg is None or self.beg_ <= beg
        assert end is None or end <= self.end_, f'end={end} self.end_={self.end_}'
        if beg is not None:
            self.beg_ = beg
        if end is not None:
            self.end_ = end
        assert self.beg_ is not None and self.end_ is not None
        assert self.beg_ <= self.end_

    def beg(self):
        return self.beg_
    
    def end(self):
        return self.end_
    
    def lines(self):
        return self.code_storage_.lines()[self.beg_:self.end_]    
    
    def number_of_lines(self):
        return self.end_ - self.beg_

    def number_of_chars(self):
        if not self.lines():
            return 0
        return sum(len(line) for line in self.lines()) + len(self.lines()) - 1

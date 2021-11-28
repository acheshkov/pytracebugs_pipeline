from functools import lru_cache


@lru_cache(maxsize=1)
def read_lines(path):
    with open(path, 'r', encoding='utf8') as f:
        return f.readlines()

def read_lines_cacheless(path):
    with open(path, 'r', encoding='utf8') as f:
        return f.readlines()

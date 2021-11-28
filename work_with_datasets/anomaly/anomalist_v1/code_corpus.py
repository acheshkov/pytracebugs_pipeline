from code_item  import CodeItem


class CodeCorpus:
    
    def __init__(self, lang, paths, with_path=False):
        self._lang = lang
        self._paths = paths
        self._with_path = with_path
    
    def __len__(self):
        return len(self._paths)
    
    def __getitem__(self, idx):
        code = CodeItem(lang=self._lang)
        code.load_from_file(self._paths[idx])
        if self._with_path:
            return code, self._paths[idx]
        return code

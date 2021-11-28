import tarfile
import zipfile
import requests
import pandas as pd
from pathlib import Path

import pickle5

from ml_utils import splitter
from code_item import CodeItem


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


def download_py150(output_dir=Path('py150'), temp_file_path=Path('py150.tar.gz')):
    #url = f'http://files.srl.inf.ethz.ch/data/py150.tar.gz'
    url = f'http://files.srl.inf.ethz.ch/data/py150_files.tar.gz'
    r = requests.get(url)
    with open(temp_file_path, 'wb') as f:
        f.write(r.content)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tar = tarfile.open(temp_file_path, 'r:gz')
    tar.extractall(output_dir)
    tar.close()

    temp_file_path.unlink()

    source_archive = output_dir / Path('data.tar.gz')
    tar = tarfile.open(source_archive, 'r:gz')
    tar.extractall(output_dir)
    tar.close()

    source_archive.unlink()


class CodeCorpusPy150(CodeCorpus):

    def __init__(self, dataset_dir, split, download=False):
        assert split in [0, 2], split
        if download:
            download_py150(dataset_dir)
        split_path = dataset_dir / (Path('python100k_train.txt') if split == 0 else Path('python50k_eval.txt'))

        with open(split_path, encoding='utf-8') as f:
            content = f.readlines()
            paths = [x.strip() for x in content]
            paths = [dataset_dir / Path(x) for x in paths]

        super().__init__(lang='py', paths=paths, with_path=True)


def unzip_bugsinpy(zipfile_path, output_dir=Path('bugsinpy')):
    with zipfile.ZipFile(zipfile_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)


class CodeCorpusBugsInPy(CodeCorpus):

    def __init__(self, dataset_dir, split, label):
        assert split in [0, 1, 2], split
        assert label in ['before', 'after']

        ext = 'old' if label == 'before' else 'new'

        paths = Path(dataset_dir).glob(f'**/*.{ext}')
        paths = [path for path in paths if splitter(path.stem) == split]

        super().__init__(lang='py', paths=paths, with_path=True)


def unpack_pybugs(df_path, output_dir=Path('pybugs')):
        assert df_path.is_file(), df_path

        # create directories
        split_to_dirs = {0: output_dir / Path('0'), 1: output_dir / Path('1'), 2: output_dir / Path('2')}
        for _, path in split_to_dirs.items():
            path.mkdir(parents=True, exist_ok=True)

        with open(df_path, 'rb') as f:
            df = pickle5.load(f)

        for index, row in df.iterrows():
            fragments = [(row['before_merge'], 'before'), (row['after_merge'], 'after')]
            fragment_id = f'{index}'
            split = splitter(fragment_id)

            for fragment, extension in fragments:
                path = split_to_dirs[split] / Path(f'{fragment_id}.{extension}') 
                with open(path, 'w') as fout:
                    fout.write(fragment)            


class CodeCorpusPybugs(CodeCorpus):

    def __init__(self, dataset_dir, split, label):
        assert split in [0, 1, 2], split
        assert label in ['before', 'after']

        ext = label
        paths = list((Path(dataset_dir) / Path(f'{split}')).glob(f'**/*.{ext}'))
        super().__init__(lang='py', paths=paths, with_path=True)


class CodeCorpusRepo(CodeCorpus):

    def __init__(self, dataset_dir, split):
        assert split in [0, 1, 2], split

        ext = 'py'
        paths = Path(dataset_dir).glob(f'**/*.{ext}')
        paths = [path for path in paths if splitter(path.stem) == split]

        super().__init__(lang='py', paths=paths, with_path=True)


def download_javagithub(output_dir=Path('javagithub'), temp_file_path=Path('java_projects.tar.gz')):
    url = 'https://groups.inf.ed.ac.uk/cup/javaGithub/java_projects.tar.gz'
    r = requests.get(url, stream=True)
    handle = open(temp_file_path, 'wb')
    for chunk in r.iter_content(chunk_size=100000000):
        if chunk:
            handle.write(chunk)

    output_dir.mkdir(parents=True, exist_ok=True)

    tar = tarfile.open(temp_file_path, 'r')
    tar.extractall(output_dir)
    tar.close()

    temp_file_path.unlink()


class CodeCorpusJavagithub(CodeCorpus):

    def __init__(self, dataset_dir, split, download=False):
        assert split in [0, 2], split
        if download:
            download_javagithub(dataset_dir)

        paths = []
        # TODO

        super().__init__(lang='java', paths=paths, with_path=True)

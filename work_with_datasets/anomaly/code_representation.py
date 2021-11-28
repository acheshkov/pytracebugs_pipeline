import sys
import pickle
import datetime
import argparse
from pathlib import Path

import utils
from ml_utils import chunks
from parse_utils import build_tree_sitter_lib
from code_corpus import CodeCorpus
from code_corpus import CodeCorpusPy150, download_py150
from code_corpus import CodeCorpusBugsInPy
from code_corpus import CodeCorpusPybugs, unpack_pybugs
from code_corpus import CodeCorpusRepo
from code_item import FragmentType
from representator import Representator


def get_corpora(data, download, label, verbose, base_dir=None):

    base_dir = Path('/home/u1018/zephyr/anomaly')

    if data == 'pytest':
        corpus = CodeCorpus(lang='py', paths=['_0003_auto_20160401_1656.py', '_cybox_core.py', '_groomer.py'], with_path=True)
        corpora = {0: corpus}
        return corpora

    if data == 'py150':
        py150_dir = base_dir / Path('data') / Path('py150')
        py150_temp_file = base_dir / Path('data') / Path('py150.tar.gz')
        
        if download:
            if py150_temp_file.is_file():
                utils.log(label='corpora', message=f'CANCEL download, file exists: {py150_temp_file}', enable=verbose)
            else:
                download_py150(output_dir=py150_dir, temp_file_path=py150_temp_file)
                utils.log(label='corpora', message=f'fetched, corpora dir: {py150_dir}', enable=verbose)

        corpus0 = CodeCorpusPy150(py150_dir, split=0, download=False)
        corpus2 = CodeCorpusPy150(py150_dir, split=2, download=False)
        corpora = {0: corpus0, 2: corpus2}
        return corpora

    if data == 'bugsinpy':
        bugsinpy_dir = base_dir / Path('data') / Path('bugsinpy')
        corpus0 = CodeCorpusBugsInPy(bugsinpy_dir, split=0, label=label)
        corpus1 = CodeCorpusBugsInPy(bugsinpy_dir, split=1, label=label)
        corpus2 = CodeCorpusBugsInPy(bugsinpy_dir, split=2, label=label)
        corpora = {0: corpus0, 1: corpus1, 2: corpus2}
        return corpora

    if data == 'pybugs':
        pybugs_dir = base_dir / Path('data') / Path('pybugs')
        if download:
            df_path = base_dir / Path('data') / Path('pybugs') / Path('filtered_traceback_bugfixes.pickle')
            unpack_pybugs(df_path, pybugs_dir)

        corpus0 = CodeCorpusPybugs(pybugs_dir, split=0, label=label)
        corpus1 = CodeCorpusPybugs(pybugs_dir, split=1, label=label)
        corpus2 = CodeCorpusPybugs(pybugs_dir, split=2, label=label)
        corpora = {0: corpus0, 1: corpus1, 2: corpus2}
        return corpora

    if data in ['numpy', 'django']:
        repo_dir = base_dir / Path('data') / Path(data)

        corpus0 = CodeCorpusRepo(repo_dir, split=0)
        corpus1 = CodeCorpusRepo(repo_dir, split=1)
        corpus2 = CodeCorpusRepo(repo_dir, split=2)
        corpora = {0: corpus0, 1: corpus1, 2: corpus2}
        return corpora



class CodeRepresentation:
    def __init__(self, install, download, data, tree_sitter_dir,
        fragment_type, fragment_window_size, fragment_overlap,
        model_name, device_id, chunk_size=100000, verbose=1):
        '''
        verbose:
        0 --- no output
        1 --- partially
        2 --- fully
        '''
        self.install = install
        self.download = download
        self.verbose = verbose

        self.data = data

        self.tree_sitter_dir = tree_sitter_dir
        self.tree_sitter_lib = 'langs_py_java_csharp.so'

        self.fragment_type = fragment_type
        self.fragment_window_size = fragment_window_size
        self.fragment_overlap = fragment_overlap

        self.model_name = model_name
        self.device_id = device_id
        self.representator = Representator(model_name=self.model_name, device_id=self.device_id)

        self.prefix = utils.now()
        utils.log(label='init', message=f'output prefix: {self.prefix}', enable=self.verbose)

        self.error_parse_path = f'{self.prefix}_{self.data}_error_parse'
        self.error_model_path = f'{self.prefix}_{self.data}_error_model'
        utils.log(label='init', message=f'error_parse_path: {self.error_parse_path}', enable=self.verbose)
        utils.log(label='init', message=f'error_model_path: {self.error_model_path}', enable=self.verbose)

        self.chunk_size = chunk_size
        utils.log(label='init', message=f'chunk size: {self.chunk_size}', enable=self.verbose)

        self.batch_size = 32

    def __repr__(self):
        return 'CodeRepresentation'

    def run(self, limit=None):
        utils.log(label='run', message=f'beg run with limit: {limit}', enable=self.verbose)

        tree_sitter_lib = self.build_tree_sitter_lib()
        parser = CodeRepresentation.create_parser(tree_sitter_lib=tree_sitter_lib, lang='python', verbose=self.verbose)

        labels = [None] if self.data in ['pytest', 'py150', 'numpy', 'django'] else ['before', 'after']
        for label in labels:
            utils.log(label='run', message=f'beg {label}', enable=self.verbose)
            corpora = self.create_corpora(label)
            utils.log(label='run', message=f'corpora: {list((x, len(y)) for x, y in corpora.items())}', enable=self.verbose)

            total = self.create_representations(corpora, label, parser, limit)
            utils.log(label='run', message=f'end {label}: {total}', enable=self.verbose)

        utils.log(label='run', message=f'end run, total: {sum([len(corpus) for _, corpus in corpora.items()])}', enable=self.verbose)
 
    def create_corpora(self, label):
        utils.log(label='corpora', message=f'beg, download: {self.download}', enable=self.verbose)
        corpora = get_corpora(self.data, self.download, label, self.verbose)
        utils.log(label='corpora', message=f'end', enable=self.verbose)
        return corpora

    def build_tree_sitter_lib(self):
        utils.log(label='tree_sitter', message=f'beg, install: {self.install}, download: {self.download}', enable=self.verbose)
        if self.install:
            utils.install('tree_sitter')
            utils.log(label='tree_sitter', message=f'tree_sitter installed', enable=self.verbose)

            utils.install('GitPython')
            utils.log(label='tree_sitter', message=f'GitPython installed', enable=self.verbose)

        tree_sitter_lib = Path(self.tree_sitter_dir) / Path(self.tree_sitter_lib)
        if self.download:
            if tree_sitter_lib.is_file():
                utils.log(label='tree_sitter', message=f'CANCEL build tree_sitter, file exists: {tree_sitter_lib}', enable=self.verbose)
            else:
                utils.log(label='tree_sitter', message=f'beg clone and build', enable=self.verbose)
                tree_sitter_lib = build_tree_sitter_lib(output_dir=self.tree_sitter_dir, output_lib=self.tree_sitter_lib, install=False, clone=True)
                utils.log(label='tree_sitter', message=f'end clone and build, lib: {tree_sitter_lib}', enable=self.verbose)
        assert tree_sitter_lib.is_file(), f'{tree_sitter_lib}'

        return tree_sitter_lib

    @staticmethod
    def create_parser(tree_sitter_lib, lang, verbose):
        utils.log(label='parser', message=f'beg parser, lang: {lang}', enable=verbose)
        from tree_sitter import Language, Parser
        parser = Parser()
        parser.set_language(Language(tree_sitter_lib, lang))
        utils.log(label='parser', message=f'end parser', enable=verbose)
        return parser

    def create_representations(self, corpora, label, parser, limit):
        utils.log(label='repr', message=f'beg create repr {self.data}_{label}, limit: {limit}, model: {self.model_name}', enable=self.verbose)
 
        error_parse, error_model = [], []
        data = []
        count = 0
        # total index for all corpora
        index, total = 0, 0
        for split, corpus in corpora.items():
            utils.log(label='repr', message=f'{index} split: {split}', enable=self.verbose)
            if limit is not None and index >= limit:
                break

            corpus_index = 0
            for code_item, path in corpus:
                index += 1
                corpus_index += 1
                if limit is not None and index >= limit:
                    utils.log(label='repr', message=f'{index} limit is reached: {limit}', enable=self.verbose)
                    break

                try:
                    #fragments = code_item.extract_fragments(parser)
                    #fragments = code_item.get_fragments(fragment_type=FragmentType.FUNCTION, parser=parser)
                    #fragments = code_item.get_fragments(fragment_type=FragmentType.WINDOW, window_size=window_size, overlap=overlap)
                    fragments = code_item.get_fragments(
                        fragment_type=self.fragment_type,
                        parser=parser,
                        window_size=self.fragment_window_size,
                        overlap=self.fragment_overlap)
                except Exception as e:
                    error_parse.append((split, code_item, path))
                    utils.log(label='repr', message=f'{index} ERROR in parsing: {path}, errors: {len(error_parse)}, message: {e}', enable=self.verbose)
                    continue

                if not fragments:
                    utils.log(label='repr', message=f'{index} WARNING: {path}, empty fragments', enable=self.verbose)
                    continue

                textes = [fragment.get_text() for fragment in fragments]
                batches = chunks(textes, self.batch_size)

                for batch_index, batch in enumerate(batches):
                    try:
                        r, b = self.representator.run(batch, padding=True, truncation=True)

                        for index_in_batch in range(len(batch)):
                            fragment_index = batch_index * self.batch_size + index_in_batch
                            data.append((label, split, corpus_index, path, fragment_index, fragments[fragment_index], r[index_in_batch], b[index_in_batch]))

                        total += r.shape[0]
                        utils.log(label='repr', message=f'{index} success: {path}:{batch_index}, total: {total}', enable=(self.verbose==2))

                    except Exception as e:
                        error_model.append((split, path, ))
                        utils.log(label='repr', message=f'{index} ERROR in {self.model_name}: {path}:{batch_index}, errors: {len(error_model)}, message: {e}', enable=self.verbose)

                if len(data) >= self.chunk_size:
                    output_path = f'{self.prefix}_{self.data}_{label}_{split}_{count:02d}.pickle'
                    pickle.dump(data, open(output_path, 'wb'))
                    utils.log(label='repr', message=f'{index} chunk {count}: {output_path}, data: {len(data)}', enable=self.verbose)

                    data = []
                    count = count + 1

            if data:
                output_path = f'{self.prefix}_{self.data}_{label}_{split}_{count:02d}.pickle'
                pickle.dump(data, open(output_path, 'wb'))
                utils.log(label='repr', message=f'{index} chunk {count}: {output_path}, data: {len(data)}', enable=self.verbose)

                data = []
                count = count + 1

        pickle.dump(error_parse, open(f'{self.error_parse_path}_{label}.pickle', 'wb'))
        utils.log(label='repr', message=f'error parse: {self.error_parse_path}, errors: {len(error_parse)}', enable=self.verbose)

        pickle.dump(error_model, open(f'{self.error_model_path}_{label}.pickle', 'wb'))
        utils.log(label='repr', message=f'error model: {self.error_model_path}, errors: {len(error_model)}', enable=self.verbose)

        utils.log(label='repr', message=f'end create repr {self.data}_{label}: {total}', enable=self.verbose)
        return total

def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--install', help='install packages', action='store_true')
    parser.add_argument('--download', help='download resources', action='store_true')
    parser.add_argument('--data', help='choose data', type=str, choices=['pytest', 'py150', 'bugsinpy', 'pybugs', 'numpy', 'django'], required=True)
    parser.add_argument('--fragment_type', help='choose fragment type', type=str, choices=['function', 'window'], required=True)
    parser.add_argument('--fragment_wsize', help='choose fragment window type', type=int, choices=list(range(128)), default=0)
    parser.add_argument('--fragment_overlap', help='windows overlapping', action='store_true')
    parser.add_argument('--gpu', help='use gpu', action='store_true')
    parser.add_argument('--repr', help='code representation', type=str, choices=['cb', 'gcb'], default='gcb')
    parser.add_argument('--verbose', help='verbose level', type=int, choices=[0,1,2], default=1)
    parser.add_argument('--limit', help='verbose level', type=int, default=-1)

    args = parser.parse_args()
    #print(f'install={args.install}')
    #print(f'download={args.download}')
    #print(f'data={args.data}')
    fragment_type = FragmentType[args.fragment_type.upper()]
    device_id = 'cpu' if not args.gpu else 'cuda:0'
    model_names = {'cb': 'microsoft/codebert-base', 'gcb': 'microsoft/graphcodebert-base'}
    model_name = model_names[args.repr]
    #print(f'device_id={device_id}')
    #print(f'verbose={args.verbose}')
    limit = args.limit if args.limit != -1 else None
    #print(f'limit={limit}')

    home_dir = Path('/home/u1018/zephyr/anomaly')

    CodeRepresentation(install=args.install,
        download=args.download,
        data=args.data,
        tree_sitter_dir=home_dir / Path('tree_sitter'),
        fragment_type=fragment_type,
        fragment_window_size=args.fragment_wsize,
        fragment_overlap=args.fragment_overlap,
        model_name=model_name,
        device_id=device_id,
        chunk_size=100000,
        verbose=args.verbose).run(limit=limit)


if __name__ == '__main__':
    main()

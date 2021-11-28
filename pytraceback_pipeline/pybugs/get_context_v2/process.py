"""
Usage:
    process.py [options] INPUT_DIR OUTPUT_DIR

Options:
    -h --help
    --language LANGUAGE             Language
    --processes PROCESSES           # of processes to use [default: 16]
    --license-filter FILE           License metadata to filter, every row contains [nwo, license, language, score] (e.g. ['pandas-dev/pandas', 'bsd-3-clause', 'Python', 0.9997])
    --tree-sitter-build FILE        [default: /src/build/py-tree-sitter-languages.so]
"""
import functools
from multiprocessing import Pool
import pickle
import os
import hashlib
from typing import Optional, Tuple, Type, List, Dict, Any

from docopt import docopt
from dpu_utils.codeutils.deduplication import DuplicateDetector
import pandas as pd
from tree_sitter import Language, Parser

from language_data import LANGUAGE_METADATA
from parsers.language_parser import LanguageParser, tokenize_docstring
from utils import download, get_sha, flatten, remap_nwo, walk

class DataProcessor:

    PARSER = Parser()

    def __init__(self, language: str, language_parser: Type[LanguageParser]):
        self.language = language
        self.language_parser = language_parser

    def process_definitions(self, nwo, repo_dir, ext) -> List[Dict[str, Any]]:
        # Process dependees (libraries) to get function implementations

        indexes = []
        #_, nwo = remap_nwo(nwo)
        if nwo is None:
            return indexes

        #tmp_dir = download(nwo)
        work_dir = os.getcwd()
        repo_dir = os.path.normpath(repo_dir)
        files = walk(repo_dir, ext)
        # files = glob.iglob(tmp_dir.name + '/**/*.{}'.format(ext), recursive=True)
        sha = None

        for f in files:
            definitions = self.get_function_definitions(f,nwo,repo_dir)
            # print(definitions)
            if definitions is None:
                continue
            if sha is None:
                sha = get_sha(repo_dir, nwo)
            os.chdir(work_dir)

            nwo, path, functions = definitions
            # print(path)
            indexes.extend((self.extract_function_data(func, nwo, path, sha) for func in functions if len(func['function_tokens']) > 1))
        return indexes

    def process_calls(self, nwo, repo_dir, ext, library_candidates) -> List[Dict[str, Any]]: #Tuple[List[Dict[str, Any]], List[Tuple[str, str]]]:
        # Process dependents (applications) to get function calls
        dents = []
        edges = []
        #_, nwo = remap_nwo(nwo)
        if nwo is None:
            return dents, edges

        work_dir = os.getcwd()
        repo_dir = os.path.normpath(repo_dir)
        files = walk(repo_dir, ext)
        sha = None

        for f in files:
            context_and_calls = self.get_context_and_function_calls(f,nwo,repo_dir)
            # print("context_and_calls", context_and_calls)
            if context_and_calls is None:
                continue
            if sha is None:
               sha = get_sha(repo_dir, nwo)
            os.chdir(work_dir)

            nwo, path, context, calls = context_and_calls

            libraries = []
            for cxt in context:
                if type(cxt) == dict:
                    libraries.extend([v.split('.')[0] for v in cxt.values()])
                elif type(cxt) == list:
                    libraries.extend(cxt)

            # print(libraries)
            match_scopes = {}
            for cxt in set(libraries):
                if cxt in library_candidates:
                    match_scopes[cxt] = library_candidates[cxt]

            # print(match_scopes)
            # print("library_candidates", library_candidates)

            # print("BAY calls", calls)
            for call in calls:
                # print("call", call)
                # print(match_scopes)
                for depended_library_name, dependend_library_functions in match_scopes.items():
                    for depended_library_function in dependend_library_functions:
                        # print("depended_library_function", depended_library_function)
                        # Other potential filters: len(call['identifier']) > 6 or len(call['identifier'].split('_')) > 1
                        # print(call['identifier'] not in self.language_parser.STOPWORDS,/)

                        # print("depended_library_function", depended_library_function)
                        if (call['identifier'] not in self.language_parser.STOPWORDS and
                            ((depended_library_function['identifier'].split('.')[-1] == '__init__' and
                              call['identifier'] == depended_library_function['identifier'].split('.')[0]) or
                             ((len(call['identifier']) > 9 or
                               (not call['identifier'].startswith('_') and len(call['identifier'].split('_')) > 1)) and
                              call['identifier'] == depended_library_function['identifier'] )
                            )):
                            dent = {
                                'calling_nwo': nwo,
                                'calling_sha': sha,
                                'calling_path': path,
#                                'language': self.language,
                                'called_identifier': call['identifier'],
                                'called_library_name': depended_library_name,
#                                'argument_list': call['argument_list'],
                                'calling_start_point': call['start_point'],
                                'calling_end_point': call['end_point'],
                                'call_nwo': depended_library_function['nwo'],
                                'call_path': depended_library_function['path'],
                                'call_start_point': depended_library_function['start_point'],
                                'call_end_point': depended_library_function['end_point'],
                                # 'call_func_text_sha256': hashlib.sha256(depended_library_function['encode'])
#                                'call_url': 'https://github.com/{}/blob/{}/{}#L{}-L{}'.format(nwo, sha, path,
#                                                                                              call['start_point'][0] + 1,
#                                                                                              call['end_point'][0] + 1),
#                                'called_url': depended_library_function['url']
                            }
                            dents.append(dent)
                            #depended_library_function['called'].append({'calling_library': depended_library_name, 'calling_nwo':nwo, 'calling_path':path, 'start_point':call['start_point'][0],'end_point':call['end_point'][0]})
                            #edges.append((dent['url'], depended_library_function['url']))
        return dents#, edges

    def process_single_file(self, filepath: os.PathLike, tmp_dir: str) -> List[Dict[str, Any]]:
        definitions = self.get_function_definitions(filepath,tmp_dir)
        if definitions is None:
            return []
        _, _, functions = definitions

        return [self.extract_function_data(func, '', '', '') for func in functions if len(func['function_tokens']) > 1]

    def extract_function_data(self, function: Dict[str, Any], nwo, path: str, sha: str):
        # print("BAY",function['function'], "============")
        return {
            'nwo': nwo,
            'sha': sha,
            'path': path,
#            'language': self.language,
            'identifier': function['identifier'],
#            'parameters': function.get('parameters', ''),
#            'argument_list': function.get('argument_list', ''),
#            'return_statement': function.get('return_statement', ''),
#            'docstring': function['docstring'].strip(),
#            'docstring_summary': function['docstring_summary'].strip(),
#            'docstring_tokens': tokenize_docstring(function['docstring_summary']),
            'function': function['function'].strip(),
#            'function_tokens': function['function_tokens'],
            'start_point': function['start_point'],
            'end_point': function['end_point'],
            'called': [],
            'calls': [],
#            'url': 'https://github.com/{}/blob/{}/{}#L{}-L{}'.format(nwo, sha, path, function['start_point'][0] + 1,
#                                                                     function['end_point'][0] + 1)
        }

    def get_context_and_function_calls(self, filepath: str, nwo: str, work_dir: str) -> Optional[Tuple[str, str, List, List]]:
        path = os.path.normpath(filepath).split(os.path.normpath(nwo))[-1]
        if any(fp in path.lower() for fp in self.language_parser.FILTER_PATHS):
            return None
        try:
            with open(filepath) as source_code:
                blob = source_code.read()
            tree = DataProcessor.PARSER.parse(blob.encode())
            return (nwo, path, self.language_parser.get_context(tree, blob), self.language_parser.get_calls(tree, blob))
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError, ValueError, OSError):
            return None

    def get_function_definitions(self, filepath: str, nwo: str, work_dir: str) -> Optional[Tuple[str, str, List]]:
        # path = os.path.normpath(filepath).split(os.path.normpath(nwo))[-1]
        path = os.path.normpath(filepath)
        # print("nwo", nwo, "filepath", filepath, "path", path)
        if any(fp in path.lower() for fp in self.language_parser.FILTER_PATHS):
            return None
        try:
            with open(filepath) as source_code:
                blob = source_code.read()
            tree = DataProcessor.PARSER.parse(blob.encode())
            return (nwo, path, self.language_parser.get_definition(tree, blob))#, self.language_parser.get_context(tree, blob))
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError, ValueError, OSError):
            return None


if __name__ == '__main__':
    args = docopt(__doc__)

    repository_dependencies = pd.read_csv(args['INPUT_DIR'] + 'repository_dependencies-1.6.0-2020-01-12.csv', index_col=False)
    projects = pd.read_csv(args['INPUT_DIR'] + 'projects_with_repository_fields-1.6.0-2020-01-12.csv', index_col=False)

    repository_dependencies['Manifest Platform'] = repository_dependencies['Manifest Platform'].apply(lambda x: x.lower())
    id_to_nwo = {project['ID']: project['Repository Name with Owner'] for project in projects[['ID', 'Repository Name with Owner']].dropna().to_dict(orient='records')}
    nwo_to_name = {project['Repository Name with Owner']: project['Name'] for project in projects[['Repository Name with Owner', 'Name']].dropna().to_dict(orient='records')}

    filtered = repository_dependencies[(repository_dependencies['Host Type'] == 'GitHub') & (repository_dependencies['Manifest Platform'] == LANGUAGE_METADATA[args['--language']]['platform'])][['Repository Name with Owner', 'Dependency Project ID']].dropna().to_dict(orient='records')

    dependency_pairs = [(rd['Repository Name with Owner'], id_to_nwo[int(rd['Dependency Project ID'])])
                        for rd in filtered if int(rd['Dependency Project ID']) in id_to_nwo]

    dependency_pairs = list(set(dependency_pairs))

    dents, dees = zip(*dependency_pairs)
    # dents = list(set(dents))
    dees = list(set(dees))

    DataProcessor.PARSER.set_language(Language(args['--tree-sitter-build'], args['--language']))

    processor = DataProcessor(language=args['--language'],
                              language_parser=LANGUAGE_METADATA[args['--language']]['language_parser'])

    with Pool(processes=int(args['--processes'])) as pool:
        output = pool.imap_unordered(functools.partial(processor.process_definitions,
                                                       ext=LANGUAGE_METADATA[args['--language']]['ext']),
                                     dees)

    definitions = list(flatten(output))
    with open(args['OUTPUT_DIR'] + '{}_definitions.pkl'.format(args['--language']), 'wb') as f:
        pickle.dump(definitions, f)

    license_filter_file = args.get('--license-filter')
    if license_filter_file is not None:
        with open(license_filter_file, 'rb') as f:
            license_filter = pickle.load(f)
        valid_nwos = dict([(l[0], l[3]) for l in license_filter])

        # Sort function definitions with repository popularity
        definitions = [dict(list(d.items()) + [('score', valid_nwos[d['nwo']])]) for d in definitions if d['nwo'] in valid_nwos]
        definitions = sorted(definitions, key=lambda x: -x['score'])

        # dedupe
        seen = set()
        filtered = []
        for d in definitions:
            if ' '.join(d['function_tokens']) not in seen:
                filtered.append(d)
                seen.add(' '.join(d['function_tokens']))

        dd = DuplicateDetector(min_num_tokens_per_document=10)
        filter_mask = [dd.add_file(id=idx,
                                   tokens=d['function_tokens'],
                                   language=d['language']) for idx, d in enumerate(filtered)]
        exclusion_set = dd.compute_ids_to_exclude()
        exclusion_mask = [idx not in exclusion_set for idx, _ in enumerate(filtered)]
        filtered = [d for idx, d in enumerate(filtered) if filter_mask[idx] & exclusion_mask[idx]]

        with open(args['OUTPUT_DIR'] + '{}_dedupe_definitions.pkl'.format(args['--language']), 'wb') as f:
            pickle.dump(filtered, f)

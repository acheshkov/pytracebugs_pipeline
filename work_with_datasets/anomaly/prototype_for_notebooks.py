import sys
import os
import re
import json
from pathlib import Path

import requests
import utils
from tree_sitter import Language, Parser
from code_item import FragmentType
from code_corpus import CodeCorpus
from representator import Representator
from code_representation import CodeRepresentation
from anomalist import Anomalist


def run(parser, anomalist, representator, paths, verbose=True):
    corpus = CodeCorpus(lang='py', paths=paths, with_path=True)

    FRAGMENT_TYPE = FragmentType.FUNCTION

    data = []
    for code_item, path in corpus:
        try:
            fragments = code_item.get_fragments(
                fragment_type=FRAGMENT_TYPE,
                parser=parser,
                window_size=None,
                overlap=None)
        except Exception as e:
            data.append((path, None, None, None, None))
            if verbose:
                print(f'ERROR in parsing: {path}, message: {e}')
            continue

        if not fragments:
            continue

        for fragment_index, fragment in enumerate(fragments):
            text = fragment.get_text()
            try:
                r, b = representator.run([text], padding=True, truncation=True)
                data.append((path, fragment_index, fragment, r, b))

            except Exception as e:
                data.append((path, fragment_index, fragment, None, None))
                if verbose:
                    print(f'ERROR in model: {path}, message: {e}')

    result = []
    for path, fragment_index, fragment, r, b in data:
        if fragment_index is None or fragment is None:
            result.append((path, fragment_index, fragment, None, 'error in parsing'))
            continue
        if r is None or b is None:
            result.append((path, fragment_index, fragment, None, 'error in graphcodebert'))
            continue

        error_message = ''
        if b[0][0] == representator._max_size:
            error_message = f'truncated to {representator._max_size}'
        reconstruction, reconstruction_loss = anomalist.run_repr(r)
        loss = reconstruction_loss[0][0]
        result.append((path, fragment_index, fragment, loss, error_message))

    return result

def get_method_name(fragment):
    lines = [line.strip() for line in fragment.lines()]
    for bad in '#\'"@':
        lines = [line for line in lines if not line.startswith(bad)]

    tokens = (' '.join(lines)).split(' ')
    for token in tokens:
        if token not in ['def', 'async']:
            name = token.split('(')[0]
            return name
    return ''


def result_to_json_string(result):
    res = []
    for path, fragment_index, fragment, loss, error_message in result:
        item = {'a-index': f'{loss:.2f}',
                'path': path,
                'first_line': get_method_name(fragment),
                'fragment_range': {
                    'beg': fragment.beg(),
                    'end': fragment.end()
                },
                'fragment_index': fragment_index,
                'message' : error_message}
        res.append(item)
    return json.dumps(res)


def get_python_paths(dir_name):
    paths = []
    for root, dirs, files in os.walk(dir_name):
        for filename in files:
            if filename.endswith(".py"):
                paths.append(os.path.join(root, filename))
    return paths


def download_and_get_pull_requests_pathes(user, repo, pull_id):
    print("downloading file list", file=sys.stderr)
    s = requests.session()
    files = []

    MAX_PAGES = 30
    PER_PAGE = 100

    for page in range(1, MAX_PAGES+1):
        url = f"https://api.github.com/repos/{user}/{repo}/pulls/{pull_id}/files?per_page={PER_PAGE}&page={page}"
        resp = s.get(url)

        cur_files = resp.json()
        files += cur_files

        if len(cur_files) < PER_PAGE:
            break

    file_names = []
    for file in files:
        file_name = file["filename"]
        raw_url = file["raw_url"]

        if ".." in file_name or os.path.isabs(file_name):
            # don't allow to write into arbitrary locations
            continue

        if not file_name.endswith(".py"):
            continue

        dir_name, file_base_name = os.path.split(file_name)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        print("getting", file_name, file=sys.stderr)
        contents = s.get(raw_url).text

        with open(file_name, "w") as f:
            f.write(contents)

        file_names.append(file_name)
    return file_names


def calc_anomalies(paths):
    AUX_SIZE = 78
    HIDDEN_SIZE = 8
    SCALER_PATH = Path('anomalist_data/scaler_214_995415.pickle')
    VAE_PATH = Path('anomalist_data/vae_214_995415.pth')
    DEVICE_ID = 'cpu'
    VERBOSE = False
    MODEL_NAME = 'microsoft/graphcodebert-base'

    assert SCALER_PATH.is_file(), f'{SCALER_PATH} doesn\'t exist'
    assert VAE_PATH.is_file(), f'{VAE_PATH} doesn\'t exist'

    parser = Parser()
    parser.set_language(Language('D://tree-sitter-python//build//my-languages.so', 'python'))

    representator = Representator(model_name=MODEL_NAME, device_id=DEVICE_ID)
    anomalist = Anomalist(aux_size=AUX_SIZE, hidden_size=HIDDEN_SIZE,
                          scaler_path=SCALER_PATH, vae_path=VAE_PATH,
                          device_id=DEVICE_ID, verbose=VERBOSE)

    result = run(parser, anomalist, representator, paths, verbose=VERBOSE)
    
    return result


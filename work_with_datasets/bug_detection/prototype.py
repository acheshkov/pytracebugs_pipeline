import os
import re
import sys
from typing import Dict, List, Optional, Tuple

import joblib
import json
from pathlib import Path
import requests
from tree_sitter import Language, Parser

from code_item import FragmentType, CodeItem
from code_corpus import CodeCorpus
from representator import Representator
import utils


def run(parser, classifier, representator, paths) -> List[Tuple[str, int, CodeItem, Optional[float], Optional[str]]]:
    verbose = True
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
            utils.log(label='repr', message=f'ERROR in parsing: {path}, message: {e}', enable=verbose)
            continue

        if not fragments:
            continue

        for fragment_index, fragment in enumerate(fragments):
            text = fragment.get_text()
            comment = None
            try:
                r = representator.run([text], padding=True, truncation=False)
                if isinstance(r, str):
                    comment = r
                data.append((path, fragment_index, fragment, r, comment))

            except Exception as e:
                utils.log(label='repr', message=f'{fragment_index} ERROR: {path}, message: {e}', enable=verbose)

    result = []
    for path, fragment_index, fragment, r, comment in data:
        if comment:
            result.append((path, fragment_index, fragment, None, comment))
        else:
            prediction = classifier.predict_proba(r)
            bugginess_probability = prediction[0][1]
            result.append((path, fragment_index, fragment, bugginess_probability, None))

    return result


def get_python_paths(dir_name: str) -> List[str]:
    paths = []
    for root, dirs, files in os.walk(dir_name):
        for filename in files:
            if filename.endswith(".py"):
                paths.append(os.path.join(root, filename))
    return paths


def download_and_get_pull_requests_pathes(user: str, repo: str, pull_id: str) -> List[str]:
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


def _convert_buggines_calcs_to_list(buggines_calcs: List[Tuple[str, int, CodeItem, Optional[float], Optional[str]]]) -> List[Dict]:
    result = list()
    for path, fragment_index, fragment, bugginess_probability, comment in buggines_calcs:
        result.append({
            'path': path,
            'fragment_range': {
                'beg': fragment.beg(),
                'end': fragment.end(),
            },
            'bugginess_probability': bugginess_probability,
            'first_line': fragment.lines()[0],
            'comment': comment
        })
    return result


def calc_buggines(paths: List[str], result_file_name: str):
    DEVICE_ID = 'cpu'
    MODEL_NAME = 'microsoft/codebert-base'
    CLASSIFIER_PATH = Path('clf_lgb_1M_stable_vs_14k_bugs_351338s_14089b.joblib')

    assert CLASSIFIER_PATH.is_file()

    parser = Parser()
    parser.set_language(Language('./langs_py_java_csharp.so', 'python'))

    representator = Representator(model_name=MODEL_NAME, device_id=DEVICE_ID)
    classifier = joblib.load(CLASSIFIER_PATH)

    result = run(parser, classifier, representator, paths)

    result = _convert_buggines_calcs_to_list(result)
    print(json.dumps(result, indent=4, sort_keys=True))


def _make_dir_ignore_exists(d: str):
    try:
        return os.mkdir(d)
    except FileExistsError as E:
        pass


if len(sys.argv) < 2:
    print("Usage: ./prototype.py <path|pull_request_id>")
    exit(0)


m = re.fullmatch(r"https://github.com/([^/]+)/([^/]+)/pull/(\d+)", sys.argv[1])

if m:
    pull_request = sys.argv[1]
    user = m[1]
    repo = m[2]
    pull_id = m[3]
    paths = download_and_get_pull_requests_pathes(user, repo, pull_id)
    result_file_name = f'{user}_{repo}_{pull_id}'

else:
    dir_name = sys.argv[1]
    paths = get_python_paths(dir_name)
    result_file_name = dir_name


calc_buggines(paths, result_file_name)

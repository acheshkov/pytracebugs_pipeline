import ast
from collections import defaultdict
import io
import os
import re
from typing import Dict, List, Optional, Tuple

import git
import pandas as pd
from tqdm.auto import tqdm

from parse_utils import gen_python_func_names_and_texts_full

import logging
logging.basicConfig(filename=f'logs.txt',
                    filemode='a',
                    level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)

PULL_REQUEST_DF_COLUMNS = [
    'issue_url',
    'pr_type',
    'pr_url',
    'merge_commit_sha',
    'filename',
    'function_name',
    'before_merge',
    'function_name_before_merge',
    'function_name_after_merge',
    'after_merge',
    'full_file_code_before_merge',
    'full_file_code_after_merge',
]

COMMIT_DF_COLUMNS = [
    'issue_url',
    'commit_type',
    'commit_sha',
    'filename',
    'function_name',
    'before_merge',
    'after_merge',
    'function_name_before_merge',
    'function_name_after_merge',
    'full_file_code_before_merge',
    'full_file_code_after_merge',
]

ISSUE_DF_COLUMNS = [
    'issue_url',
    'pr_type',
    'pr_url',
    'merge_commit_sha',
    'commit_type',
    'commit_sha',
    'filename',
    'function_name',
    'before_merge',
    'after_merge',
    'full_file_code_before_merge',
    'full_file_code_after_merge',
]

ALL_RELEVANT_PULL_REQUEST_TYPES = [
    'all relevant PRs'
]

MOST_RELEVANT_PULL_REQUEST_TYPES = [
    'most relevant PRs'
]

ALL_RELEVANT_COMMIT_TYPES = [
    'all relevant commits'
]
MOST_RELEVANT_COMMIT_TYPES = [
    'most relevant commits'
]

REPOS_DIR = os.getenv("HOME") + f"/zephyr_data/repo/"


def _get_repo(repo_url: str) -> git.Repo:
    """
    Return git repository object found by repository url.
    Function return object of existed repository if it is already cloned to filesystem.
    Otherwise firstly repository will be cloned.
    :param repo_url: URL of a repository.
    :return: git.Repo object.
    """
    repo_dir = repo_url.replace("/", "_")
    repo_path = REPOS_DIR + "/" + repo_dir

    make_dir_ignore_exists(REPOS_DIR)

    repo_name = _get_repo_name_from_url(repo_url)

    if not os.path.exists(repo_path):
        repo = git.Repo.clone_from(repo_url, repo_path, branch=False, multi_options=["--bare"])
        LOGGER.info(f'{repo_name} cloned to {repo_path}')
    else:
        repo = git.Repo(repo_path)
        LOGGER.info(f'{repo_name} already exists in {repo_path}')

    return repo


def _get_repo_name_from_url(repo_url: str) -> str:
    """
    Return formatted git repository name.
    For 'git@github.com:user/repository_name.git',
        'https://github.com/user/repository_name.git',
        'https://github.com/user/repository_name' it returns 'repository_name'.

    :param repo_url: URL of a repository.
    :return: repository name.
    """
    repo_name = repo_url.split('/')[-1]
    if repo_name.endswith('.git'):
        repo_name = repo_name.split('.')[0]
    return repo_name


def functions_bodies_are_equal(body_a: str, body_b: str) -> bool:
    """
    Check if two function bodies are equal up to indentation and spaces.

    :param body_a: first function body.
    :param body_b: second function body.
    :return: True if functions are equal and False otherwise.
    """
    return re.sub(r'\s', '', body_a) == re.sub(r'\s', '', body_b)


def get_files_to_function_bodies_dict(commit: git.objects.commit.Commit,
                                      files: List[str]) -> Dict[str, Dict[str, Tuple[str, str, str]]]:
    """
    Parse files versions from repository in particular revision
        defined by commit.
        Return dictionary where keys is file names
        and values is a dictionary with names of function as a key
        and function source code as a value:
        file_name -> function_name -> (decorators, function_body, file_src).

    :param commit: revision of repository to parse.
    :param files: list of files to parse.
    :return: dictionary where keys is file names
        and values is a dictionary with names of function as a key
        and function source code as a value.
    """

    # file name -> function name -> decorators, function body, file source code
    filename_to_function_body_dict = defaultdict(dict)

    for file in files:
        try:
            _file = commit.tree / file
            with io.BytesIO(_file.data_stream.read()) as f:
                file_src = f.read().decode('utf-8')
            for function_name, decorators, text in gen_python_func_names_and_texts_full(file_src):
                filename_to_function_body_dict[file][function_name] = (decorators, text, file_src)
        except Exception as e:
            LOGGER.warning(f'commit: {commit}, file: {file}, error: {e}')
    return filename_to_function_body_dict


def get_files_to_function_bodies_dict_for_commit(
        repo: git.Repo,
        commit_sha: str,
        files: List[str]
) -> Optional[Dict[str, Dict[str, Tuple[str, str, str]]]]:
    """
    Return dictionary with functions versions from commit.
    :param repo: git repository. git.Repo object.
    :param commit_sha: SHA of commit.
    :param files: list of files for each of which
        functions presented in file will be found.
    :return: dictionary where keys is file names,
        and value is a dictionary with function name as key
        and a tuple of a function body and a full file's source code as values:
        file_name -> function_name -> (decorators, function body, full_file_code).
    """
    try:
        commit = repo.commit(commit_sha)
    except Exception as e:
        LOGGER.warning(f'Could not checkout to {commit_sha}: {e}')
        return None
    return get_files_to_function_bodies_dict(commit, files)


def get_function_versions(
        repo: git.Repo,
        commit_sha: Optional[str] = None,
        files: Optional[List[str]] = None,
        filter_tests: bool = False,
        filter_setup: bool = False
) -> Optional[Dict[str, Dict[str, Dict[str, Tuple[str, str, str]]]]]:
    """
    Return dict with pair of function's versions.
    :param repo: git repository.
    :param commit_sha: SHA of commit.
    :param files: list of files with changes,
        versions of functions in `commit_sha`
        and preceding commit from these files
        will be compared.
    :param filter_tests: flag if need to filter out files with tests.
    :param filter_setup: flag if need to filter out setup.py files.
    :return: dictionary where keys is file names,
        and value is dictionaries with function name as key
        and 'old' and 'new' as values.
        Value for 'new' ('old') key is a tuple of a version of function
        from commit with `commit_sha` (commit preceding for commit with `commit_sha`),
        and a full file's source code from commit with `commit_sha`
        (commit preceding for commit with `commit_sha`):
        file_name -> function_name -> {'old', 'new'} -> (decorators, function_body, full_file_code).
    """
    if not files:
        files = get_python_files_modified_in_commit(repo, commit_sha, filter_tests, filter_setup)
    if not files:
        LOGGER.warning(f'No python files for {commit_sha}')
        return None

    # file name -> function name -> (decorators, function body, full_file_code)
    new_file_function_body_dict = get_files_to_function_bodies_dict_for_commit(repo,
                                                                               commit_sha,
                                                                               files)
    if not new_file_function_body_dict:
        return None

    # file name -> function name -> (decorators, function body, full_file_code)
    old_file_function_body_dict = get_files_to_function_bodies_dict_for_commit(repo,
                                                                               f'{commit_sha}~',
                                                                               files)

    if not old_file_function_body_dict:
        return None

    # file name -> function name -> ['old', 'new'] -> (function body, full_file_code)
    result = defaultdict(dict)
    for filename in new_file_function_body_dict:
        if filename not in old_file_function_body_dict:
            continue
        else:
            result[filename] = defaultdict(dict)
            for function_name in new_file_function_body_dict[filename]:
                if function_name not in old_file_function_body_dict[filename]:
                    continue
                else:
                    old_decorators, old_func_body, old_full_file_code = old_file_function_body_dict[filename][function_name]
                    new_decorators, new_func_body, new_full_file_code = new_file_function_body_dict[filename][function_name]
                    if not functions_bodies_are_equal(old_func_body, new_func_body):
                        result[filename][function_name]['old'] = (old_decorators, old_func_body, old_full_file_code)
                        result[filename][function_name]['new'] = (new_decorators, new_func_body, new_full_file_code)


    return result


def get_python_files_modified_in_commit(repo: git.Repo,
                                        commit_sha: str,
                                        filter_tests: bool = False,
                                        filter_setup: bool = False) -> Optional[List[str]]:
    """
    Collect file names for files modified in specific commit.
    :param repo: git repository.
    :param commit_sha: SHA of commit.
    :param filter_tests: flag if need to filter out files with tests.
    :param filter_setup: flag if need to filter out setup.py files.
    :return: list of files modified in specific commit.
    """
    try:
        output = repo.git.diff('--name-only', commit_sha, f'{commit_sha}~')
        files = [file for file in output.strip().split('\n') if file.endswith('.py')]
        if filter_tests:
            files = [file for file in files if 'test' not in file]
        if filter_setup:
            files = [file for file in files if not file.endswith('setup.py')]

    except Exception as e:
        LOGGER.warning(f'Could not get changed files for commit {commit_sha}: {e}')
        return None
    return files


def get_rows_for_commits(issue: pd.Series,
                         column_name: str,
                         repo: git.Repo,
                         filter_tests: bool = False,
                         filter_setup: bool = False) -> pd.DataFrame:
    """
    Collect and return versions of functions that was changed in commit.
    :param issue: pd.Series that contains column `column_name` with commit information.
    :param column_name: name of column with commit information.
    :param repo: git repository that contains commit described in `issue[column_name]`.
    :param filter_tests: flag if need to filter out files with tests.
    :param filter_setup: flag if need to filter out setup.py files.
    :return: pd.DataFrame where each row is contains one function versions (before and after merge)
        that was changed in commit.
    """
    _file_versions_df = pd.DataFrame(columns=COMMIT_DF_COLUMNS)

    if isinstance(issue[column_name], str):
        commits = eval(issue[column_name])
    else:
        commits = issue[column_name]

    if len(commits) != 0:
        for commit in commits:
            commit_sha = commit['commitUrl'].split('/')[-1]
            func_versions = get_function_versions(repo=repo,
                                                  commit_sha=commit_sha,
                                                  files=None,
                                                  filter_tests=filter_tests,
                                                  filter_setup=filter_setup)

            if not func_versions:
                continue

            commit_summary, commit_message = get_commit_summary_message(repo, commit_sha=commit_sha)

            for filename, functions in func_versions.items():
                if len(functions) == 0:
                    continue
                for function_name, versions in functions.items():
                    decorators_before_merge, function_body_before_merge, full_file_code_before_merge = versions['old']
                    decorators_after_merge, function_body_after_merge, full_file_code_after_merge = versions['new']

                    function_name_before_merge = function_name
                    function_name_after_merge = function_name
                    if decorators_before_merge:
                        function_name_before_merge = decorators_before_merge + ' ' + function_name_before_merge
                    if decorators_after_merge:
                        function_name_after_merge = decorators_after_merge + ' ' + function_name_after_merge

                    _file_versions_df = _file_versions_df.append([{
                        'issue_url': issue['url'],
                        'commit_type': column_name,
                        'commit_sha': commit_sha,
                        'filename': filename,
                        'function_name': function_name,
                        'before_merge': function_body_before_merge,
                        'after_merge': function_body_after_merge,
                        'function_name_before_merge': function_name_before_merge,
                        'function_name_after_merge': function_name_after_merge,
                        'full_file_code_before_merge': full_file_code_before_merge,
                        'full_file_code_after_merge': full_file_code_after_merge,
                        'commit_summary': commit_summary,
                        'commit_message': commit_message
                    }], sort=True)

    return _file_versions_df


def get_rows_for_prs(issue: pd.Series,
                     column_name: str,
                     repo: git.Repo,
                     filter_tests: bool = False,
                     filter_setup: bool = False) -> pd.DataFrame:
    """
    Collect and return versions of functions that was changed in pull requests.
    :param issue: pd.Series that contains column `column_name` with pull request information.
    :param column_name: name of column with pull request information.
    :param repo: git repository that contains pull request described in `issue[column_name]`.
    :param filter_tests: flag if need to filter out files with tests.
    :param filter_setup: flag if need to filter out setup.py files.
    :return: pd.DataFrame where each row is contains one function versions (before and after merge)
        that was changed in pull request.
    """
    _file_versions_df = pd.DataFrame(columns=PULL_REQUEST_DF_COLUMNS)

    if isinstance(issue[column_name], str):
        prs = eval(issue[column_name])
    else:
        prs = issue[column_name]
    if isinstance(prs, float):
        print(prs, issue)
    if len(prs) != 0:
        for pr in prs:
            pr_url = pr['url']
            is_merged = pr['merged']

            if not is_merged:
                continue

            if 'mergeCommit' not in pr.keys() or not pr['mergeCommit']:
                continue

            merge_commit_sha = pr['mergeCommit']['commitUrl'].split('/')[-1]
            func_versions = get_function_versions(repo=repo,
                                                  commit_sha=merge_commit_sha,
                                                  files=None,
                                                  filter_tests=filter_tests,
                                                  filter_setup=filter_setup)

            if not func_versions:
                continue

            commit_summary, commit_message = get_commit_summary_message(repo, commit_sha=merge_commit_sha)

            for filename, functions in func_versions.items():
                if len(functions) == 0:
                    continue
                for function_name, versions in functions.items():
                    decorators_before_merge, function_body_before_merge, full_file_code_before_merge = versions['old']
                    decorators_after_merge, function_body_after_merge, full_file_code_after_merge = versions['new']

                    function_name_before_merge = function_name
                    function_name_after_merge = function_name
                    if decorators_before_merge:
                        function_name_before_merge = decorators_before_merge + ' ' + function_name_before_merge
                    if decorators_after_merge:
                        function_name_after_merge = decorators_after_merge + ' ' + function_name_after_merge

                    _file_versions_df = _file_versions_df.append([{
                        'issue_url': issue['url'],
                        'pr_type': column_name,
                        'pr_url': pr_url,
                        'merge_commit_sha': merge_commit_sha,
                        'filename': filename,
                        'function_name': function_name,
                        'before_merge': function_body_before_merge,
                        'after_merge': function_body_after_merge,
                        'function_name_before_merge': function_name_before_merge,
                        'function_name_after_merge': function_name_after_merge,
                        'full_file_code_before_merge': full_file_code_before_merge,
                        'full_file_code_after_merge': full_file_code_after_merge,
                        'commit_summary': commit_summary,
                        'commit_message': commit_message
                    }], sort=True)

    return _file_versions_df


def get_commit_summary_message(repo: Optional[git.Repo] = None,
                               repo_path: Optional[str] = None,
                               commit_sha: str = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Collect commit summary and commit message for specific commit and repo
    :param repo: git repository that must be used for commit message and summary extraction
    :param repo_path: path to git repository
    :param commit_sha: SHA of commit
    :return: pair of summary and message
    """
    if not repo:
        if not repo_path:
            raise ValueError('At least one of arguments `repo` and `repo_path` must be not None')
        else:
            try:
                repo = git.Repo(repo_path)
            except Exception as e:
                return None, None
    try:
        commit = repo.commit(commit_sha)
        summary = commit.summary
        message = commit.message

        return summary, message

    except Exception as e:
        return None, None


def make_dir_ignore_exists(d: str):
    """
    Made directory `d`, do nothing if directory `d` exists
    :param d: directory path
    """
    try:
        return os.mkdir(d)
    except FileExistsError as E:
        pass


def process_issues_dataframe(issues_df: pd.DataFrame,
                             repo_url: str,
                             filter_tests: bool = False,
                             filter_setup: bool = False,
                             pr_and_commit_type: str = 'all') -> pd.DataFrame:
    """
    :param issues_df: pd.DataFrame with issues info.
    :param repo_url: url for repository that we want to process.
    :param filter_tests: flag to filter out tests files.
    :param filter_setup: flag to filter out setup.py files.
    :param pr_and_commit_type: which type of pull requests and commit process.
        Can be 'most' (for most relevant) and 'all' (for all relevant).
    """
    repo = _get_repo(repo_url)
    file_versions_df = pd.DataFrame(columns=ISSUE_DF_COLUMNS)

    for index, issue in tqdm(issues_df.sort_values(by='closedAt', ascending=False).iterrows(), total=len(issues_df)):
        if pr_and_commit_type not in ['most', 'all']:
            raise ValueError(f'`pr_and_commit_type` must be "all" or "most", you pass {pr_and_commit_type}')
        if pr_and_commit_type == 'all':
            pull_request_types = ALL_RELEVANT_PULL_REQUEST_TYPES
            commit_types = ALL_RELEVANT_COMMIT_TYPES
        else:
            pull_request_types = MOST_RELEVANT_PULL_REQUEST_TYPES
            commit_types = MOST_RELEVANT_COMMIT_TYPES

        for pr_column_name in pull_request_types:
            _file_versions_df = get_rows_for_prs(issue, pr_column_name, repo, filter_tests, filter_setup)
            file_versions_df = file_versions_df.append(_file_versions_df, sort=True)

        for commit_column_name in commit_types:
            _file_versions_df = get_rows_for_commits(issue, commit_column_name, repo, filter_tests, filter_setup)
            file_versions_df = file_versions_df.append(_file_versions_df, sort=True)

    return file_versions_df

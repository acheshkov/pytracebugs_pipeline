import sys
import os
from get_issues.src.form_issues_datasets_api4 import create_issues_dataset_api4
import pandas as pd
from diff_utils.git_diff_utils import process_issues_dataframe
from collect_snippets.src.analyze_issues import filter_PRs, filter_commits
import datetime


REPO_NAME = sys.argv[1]
REPO_CREATION_DATE = datetime.datetime.strptime(sys.argv[2],
                                                "%Y-%m-%dT%H:%M:%SZ").date() if len(sys.argv) > 2 else None
DATA_DIR = os.getenv("HOME") + '/zephyr_data/'


def _make_data_dirs(path):

    def _make_dir_ignore_exists(d):
        try:
            os.mkdir(d)
        except FileExistsError as E:
            pass
        return None

    issues_dir = path + 'issues/'
    bugfixes_dir = path + 'bugfixes/'
    _make_dir_ignore_exists(issues_dir)
    _make_dir_ignore_exists(bugfixes_dir)
    return {'issues_dir': issues_dir,
            'bugfixes_dir': bugfixes_dir}


def process_repo(repo_name,
                 repo_creation_date,
                 path,
                 extract_issues_only=False):
    #print(repo_name)
    repo_issues_dataset, repo_full_web_link = create_issues_dataset_api4(repo_name,
                                                                         repo_creation_date,
                                                                         remove_irrelevant_issues=True)
    repo_issues_dataset = filter_PRs(repo_issues_dataset)
    repo_issues_dataset = filter_commits(repo_issues_dataset)

    data_dirs = _make_data_dirs(path)
    repo_issues_dataset.to_pickle(data_dirs['issues_dir'] +
                                  repo_name.replace('/', '_') +
                                  '_issues.pickle')
    if not extract_issues_only:
        repo_file_versions = process_issues_dataframe(repo_issues_dataset,
                                                      repo_full_web_link + '.git',
                                                      pr_and_commit_type='most')
        repo_file_versions.to_pickle(data_dirs['bugfixes_dir'] +
                                     repo_name.replace('/', '_') +
                                     '_issues_functions_versions.pickle')


def process_repo_offline(repo_name,
                         path):
    data_dirs = _make_data_dirs(path)
    repo_issues_dataset = pd.read_pickle(data_dirs['issues_dir'] +
                                         repo_name.replace('/', '_') +
                                         '_issues.pickle')
    repo_issues_dataset = filter_PRs(repo_issues_dataset)
    repo_issues_dataset = filter_commits(repo_issues_dataset)
    repo_full_web_link = 'https://github.com/' + repo_name

    repo_file_versions = process_issues_dataframe(repo_issues_dataset,
                                                  repo_full_web_link + '.git',
                                                  pr_and_commit_type='most')
    repo_file_versions.to_pickle(data_dirs['bugfixes_dir'] +
                                 repo_name.replace('/', '_') +
                                 '_issues_functions_versions.pickle')
    return repo_issues_dataset


if __name__ == "__main__":
    process_repo_offline(REPO_NAME,
                         DATA_DIR)
    #process_repo(REPO_NAME,
    #             REPO_CREATION_DATE,
    #             DATA_DIR)

from form_issues_datasets_api4 import create_issues_dataset_api4
from git_diff_utils import process_issues_dataframe
import datetime
import jsonlines
import pandas as pd


VERY_BIG_LIST_OF_REPOS_FILENAME = 'python_repos_interesting_top_90_percent_no_forks.json'


def _extract_repo_name_n_creation_date(repo_record):
    return repo_record['nameWithOwner'], datetime.datetime.strptime(repo_record['createdAt'],
                                                                    "%Y-%m-%dT%H:%M:%SZ").date()


def _process_repo(repo_name,
                  repo_creation_date,
                  path_to_repos_list,
                  extract_issues_only=False):
    print(repo_name)
    repo_issues_dataset, repo_full_web_link = create_issues_dataset_api4(repo_name,
                                                                         repo_creation_date,
                                                                         remove_duplicate_issues=True)
    repo_issues_dataset.to_csv(path_to_repos_list + repo_name.replace('/', '_') + '_issues.csv')
    if not extract_issues_only:
        repo_file_versions = process_issues_dataframe(repo_issues_dataset,
                                                      repo_full_web_link + '.git')
        repo_file_versions.to_csv(path_to_repos_list + repo_name.replace('/', '_') +
                                  '_issues_functions_versions.tsv',
                                  sep='\t', index=False)


def collect_buggy_snippets_from_repos_list_in_json(path_to_repos_list,
                                                   repos_list_json_filename):
    repos_counter = 0
    with jsonlines.open(path_to_repos_list + repos_list_json_filename) as reader:
        for repo_record in reader:
            repo_name, repo_creation_date = _extract_repo_name_n_creation_date(repo_record)
            _process_repo(repo_name,
                          repo_creation_date,
                          path_to_repos_list)
            repos_counter += 1


def collect_buggy_snippets_from_repos_list_in_csv(path_to_repos_list,
                                                  repos_list_csv_filename):
    df = pd.read_csv(path_to_repos_list + repos_list_csv_filename)
    df.set_index('nameWithOwner',
                 inplace=True)
    for repos_counter, repo_name in enumerate(df.index):
        repo_creation_date = datetime.datetime.strptime(df.at[repo_name,
                                                              'createdAt'],
                                                        "%Y-%m-%dT%H:%M:%SZ").date()
        _process_repo(repo_name,
                      repo_creation_date,
                      path_to_repos_list)


def collect_issues_from_repos_list_in_csv(path_to_repos_list,
                                          repos_list_csv_filename):
    df = pd.read_csv(path_to_repos_list + repos_list_csv_filename)
    df.set_index('nameWithOwner',
                 inplace=True)
    for repos_counter, repo_name in enumerate(df.index):
        repo_creation_date = datetime.datetime.strptime(df.at[repo_name,
                                                              'createdAt'],
                                                        "%Y-%m-%dT%H:%M:%SZ").date()
        _process_repo(repo_name,
                      repo_creation_date,
                      path_to_repos_list,
                      extract_issues_only=True)
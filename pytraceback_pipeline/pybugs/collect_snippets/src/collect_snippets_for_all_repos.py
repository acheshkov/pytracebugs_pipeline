import datetime
import jsonlines
import pandas as pd
from .collect_snippets_for_single_repo import process_repo


VERY_BIG_LIST_OF_REPOS_FILENAME = 'python_repos_interesting_top_90_percent_no_forks.json'


def _extract_repo_name_n_creation_date(repo_record):
    return repo_record['nameWithOwner'], datetime.datetime.strptime(repo_record['createdAt'],
                                                                    "%Y-%m-%dT%H:%M:%SZ").date()


def collect_buggy_snippets_from_repos_list_in_json(path_to_repos_list,
                                                   repos_list_json_filename):

    with jsonlines.open(path_to_repos_list + repos_list_json_filename) as reader:
        for repo_record in reader:
            repo_name, repo_creation_date = _extract_repo_name_n_creation_date(repo_record)
            process_repo(repo_name,
                         repo_creation_date,
                         path_to_repos_list)


def collect_buggy_snippets_from_repos_list_in_csv(path_to_repos_list,
                                                  repos_list_csv_filename):
    df = pd.read_csv(path_to_repos_list + repos_list_csv_filename)
    df.set_index('nameWithOwner',
                 inplace=True)
    for repos_counter, repo_name in enumerate(df.index):
        repo_creation_date = datetime.datetime.strptime(df.at[repo_name,
                                                              'createdAt'],
                                                        "%Y-%m-%dT%H:%M:%SZ").date()
        process_repo(repo_name,
                     repo_creation_date,
                     path_to_repos_list)

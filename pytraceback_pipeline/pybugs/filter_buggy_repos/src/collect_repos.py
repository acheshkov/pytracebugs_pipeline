from get_issues.src.utils_api4 import fetch_github_paged_graphql_api_data
from get_issues.src.local_settings import *
from datetime import timedelta, date
import jsonlines
import pandas as pd


RECENT_PERIOD_LENGTH_IN_DAYS = 180


def _collect_additional_repos_info(repositories_info,
                                   params):
    repos_info = repositories_info.copy().set_index('nameWithOwner')
    a_params = params.copy()
    a_params['token'] = GITHUB_TOKENS[0]

    additional_repos_info = []
    for repo_index, repo_name in enumerate(list(repos_info.index)):
        print(repo_index, repo_name)
        raw_additional_repo_info = fetch_github_paged_graphql_api_data(repo_name,
                                                                       a_params)
        if not raw_additional_repo_info:
            continue

        params['token'] = GITHUB_TOKENS[(repo_index + 1) % len(GITHUB_TOKENS)]
        additional_repos_info.append({**raw_additional_repo_info,
                                      'nameWithOwner': repo_name})

    return pd.concat((repos_info,
                      pd.json_normalize(additional_repos_info).set_index('nameWithOwner')),
                     axis=1)


def _rough_filter_out_repos(repositories_info):
    quantile_threshold = 0.75
    selected_repositories_info = repositories_info.loc[
        (repositories_info['stargazerCount'] >= repositories_info['stargazerCount'].quantile(q=quantile_threshold)) &
        (repositories_info['issues.totalCount'] >= repositories_info['issues.totalCount'].quantile(q=quantile_threshold)) &
        (repositories_info['pullRequests.totalCount'] >= repositories_info['pullRequests.totalCount'].quantile(q=quantile_threshold))]
    return selected_repositories_info


def create_repos_dataset_with_tags(path_to_repos_list,
                                   repos_list_filename):
    repositories_info = load_repo_info_from_json(path_to_repos_list,
                                                 repos_list_filename)
    repositories_info = repositories_info.astype({'forkCount': 'int32', 'stargazerCount': 'int32',
                                                  'diskUsage': 'float64', 'commitComments.totalCount': 'int32',
                                                  'watchers.totalCount': 'int32', 'issues.totalCount': 'int32',
                                                  'pullRequests.totalCount': 'int32', 'releases.totalCount': 'int32'})
    extended_repositories_info = \
        _collect_additional_repos_info(_rough_filter_out_repos(repositories_info).drop(['licenseInfo'],
                                                                                       axis=1),
                                       params={'query_type': 'repository'})
    extended_repositories_info.to_csv('../data/extended_interesting_repos_info.csv')
    return extended_repositories_info


def load_repo_info_from_json(path_to_repos_list,
                             repos_list_filename):
    block_of_records = []
    with jsonlines.open(path_to_repos_list + repos_list_filename) as reader:
        for repo_record in reader:
            block_of_records.append(repo_record)
    return pd.json_normalize(block_of_records)


def _finer_filter_out_repos(repositories_info):
    quantile_threshold = 0.25
    repositories_info['max_tags_n_releases'] = repositories_info[['releases.totalCount',
                                                                  'refs.totalCount']].max(axis=1)
    selected_repositories_info = repositories_info.loc[
        repositories_info['max_tags_n_releases'] >= repositories_info['max_tags_n_releases'].quantile(q=quantile_threshold)
    ]
    return selected_repositories_info


def create_repos_dataset_with_recent_PR_count(path_to_repos_dataset,
                                              repos_dataset_filename):
    repositories_info = _finer_filter_out_repos(pd.read_csv(path_to_repos_dataset + repos_dataset_filename))

    params = {'query_type': 'repository_pull_requests_count',
              'starting_date': (date.today() - timedelta(RECENT_PERIOD_LENGTH_IN_DAYS)).strftime('%Y-%m-%d'),
              'ending_date': date.today().strftime('%Y-%m-%d')}
    extended_repositories_info = _collect_additional_repos_info(repositories_info,
                                                                params=params)
    extended_repositories_info.to_csv('../data/further_extended_interesting_repos_info.csv')
    return extended_repositories_info

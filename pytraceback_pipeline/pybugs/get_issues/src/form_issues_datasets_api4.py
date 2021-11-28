import pandas as pd
from pandas import json_normalize

from .utils_api4 import fetch_github_paged_graphql_api_data
from .extract_bug_fixing_info_from_issue_text import get_source_code_n_error_messages
from .form_issues_datasets import infer_bug_label
from .local_settings import *
from datetime import timedelta, date
import time


TIME_PERIOD_FOR_SINGLE_API_QUERY = {'issue': 30, 'pull request': 30}
IRRELEVANT_LABELS = ['dependenc', 'compatib', 'backward',
                     'regression', 'not-our-bug', 'backport', 'external',
                     'upstream']


def _filter_relevant_issues(issue_labels):
    for label in issue_labels:
        for irrelevant_label_token in IRRELEVANT_LABELS:
            if irrelevant_label_token in label.lower():
                return True
    return False


def _parse_api_results(api_data):
    return json_normalize(api_data['page_data'], 'edges')


def _extract_bug_reports(issues_dataset):
    df = issues_dataset.copy()
    df.rename(columns={'bodyText': 'bug report'}, inplace=True)
    df['source code and errors'] = df['bodyHTML'].apply(get_source_code_n_error_messages)
    return df


def _extract_issue_labels(labels_record):
    if not labels_record:
        return []
    return [label_record['node']['name'] for label_record in labels_record]


def _extract_referencing_commits(fixes_record,
                                 linked_to_PRs=False):
    if not fixes_record:
        return []
    if linked_to_PRs:
        return [fix_record['node']['commit'] for fix_record in fixes_record
                if (fix_record and fix_record['node'] and ('commit' in fix_record['node']) and
                    fix_record['node']['commit'] and fix_record['node']['commit']['associatedPullRequests']['edges'])]
    else:
        return [fix_record['node']['commit'] for fix_record in fixes_record
                if (fix_record and fix_record['node'] and ('commit' in fix_record['node']) and
                    fix_record['node']['commit'] and (not fix_record['node']['commit']['associatedPullRequests']['edges']))]


def _extract_closing_commits(fixes_record,
                             linked_to_PRs=False):
    if not fixes_record:
        return []
    if linked_to_PRs:
        return [fix_record['node']['closer'] for fix_record in fixes_record
                if (fix_record and fix_record['node'] and ('closer' in fix_record['node']) and
                    fix_record['node']['closer'] and ('associatedPullRequests' in fix_record['node']['closer']) and
                    fix_record['node']['closer']['associatedPullRequests']['edges'])]
    else:
        return [fix_record['node']['closer'] for fix_record in fixes_record
                if (fix_record and fix_record['node'] and ('closer' in fix_record['node']) and
                    fix_record['node']['closer'] and ('associatedPullRequests' in fix_record['node']['closer']) and
                    (not fix_record['node']['closer']['associatedPullRequests']['edges']))]


def _extract_closing_PRs(fixes_record):
    if fixes_record:
        return [fix_record['node']['closer'] for fix_record in fixes_record
                if (fix_record and fix_record['node'] and ('closer' in fix_record['node']) and
                    fix_record['node']['closer'] and ('merged' in fix_record['node']['closer']))]
    else:
        return []


def _extract_related_PRs(fixes_record,
                         linked_PR=False):
    if not fixes_record:
        return []
    if linked_PR:
        return [fix_record['node']['subject'] for fix_record in fixes_record
                if (fix_record and fix_record['node'] and ('subject' in fix_record['node']) and
                    fix_record['node']['subject'])]
    else:
        return [fix_record['node']['source'] for fix_record in fixes_record
                if (fix_record and fix_record['node'] and ('source' in fix_record['node']) and
                    fix_record['node']['source'])]


def _extract_PRs_for_referencing_commits(fixes_record):
    if not fixes_record:
        return []

    PRs_for_ref_commits = []
    for fix_record in fixes_record:
        if (fix_record and fix_record['node'] and ('commit' in fix_record['node']) and
                fix_record['node']['commit'] and ('associatedPullRequests' in fix_record['node']['commit'])):
            PRs_for_ref_commits.extend(fix_record['node']['commit']['associatedPullRequests']['edges'])
    return [PR_info['node'] for PR_info in PRs_for_ref_commits]


def _is_issue_irrelevant(labels):
    for label in labels:
        for irrelevant_label in IRRELEVANT_LABELS:
            if irrelevant_label in label.lower():
                return True
    return False


def _create_raw_dataset_for_date_range_api4(repo_name,
                                            date_range,
                                            dataset_type,
                                            bug_label):
    params = {'token': GITHUB_TOKENS[0],
              'starting_date': date_range['starting_date'],
              'ending_date': date_range['ending_date'],
              'query_type': dataset_type}
    if dataset_type == 'issue':
        params['issue_label'] = bug_label
    else:
        params['pull_request_label'] = bug_label
    api_data = fetch_github_paged_graphql_api_data(repo_name,
                                                   params=params)
    dataframes = [_parse_api_results(api_data), ]
    total_number_of_pages = api_data['page_info']['total_pages']
    #print(total_number_of_pages)

    for p in range(2, total_number_of_pages + 1):
        params['cursor'] = api_data['page_info']['cursor']
        params['token'] = GITHUB_TOKENS[(p - 1) % len(GITHUB_TOKENS)]
        api_data = fetch_github_paged_graphql_api_data(repo_name,
                                                       params=params)
        dataframes.append(_parse_api_results(api_data))
        p += 1
        time.sleep(1)
    return pd.concat(dataframes,
                     axis=0,
                     ignore_index=True)


def _create_raw_dataset_api4(repo_name,
                             repo_creation_date,
                             dataset_type='issue'):
    def dates_ranges_iterator(initial_date,
                              date_due):
        for n in range(TIME_PERIOD_FOR_SINGLE_API_QUERY[dataset_type],
                       int((date_due - initial_date).days) + TIME_PERIOD_FOR_SINGLE_API_QUERY[dataset_type],
                       TIME_PERIOD_FOR_SINGLE_API_QUERY[dataset_type]):
            a_starting_date = initial_date + timedelta(n - TIME_PERIOD_FOR_SINGLE_API_QUERY[dataset_type])
            a_ending_date = initial_date + timedelta(n - 1)
            yield a_starting_date.strftime('%Y-%m-%d'), a_ending_date.strftime('%Y-%m-%d')

    bug_labels = infer_bug_label_api4(repo_name)
    print(f'Inferred issues labels for {repo_name}: {bug_labels}')

    dataframes = []
    now_date = date.today()
    for starting_date, ending_date in dates_ranges_iterator(repo_creation_date,
                                                            now_date):
        for bug_label in bug_labels:
            #print("date range is ", starting_date, " through ", ending_date)
            res = _create_raw_dataset_for_date_range_api4(repo_name,
                                                          {'starting_date': starting_date,
                                                           'ending_date': ending_date},
                                                          dataset_type=dataset_type,
                                                          bug_label=bug_label)
            dataframes.append(res)
    return pd.concat(dataframes,
                     axis=0,
                     ignore_index=True).drop_duplicates(subset='node.url') if dataframes else pd.DataFrame([])


def _extract_commits_n_PRs_info(raw_issues_dataset,
                                original_issues_dataset):
    issues_dataset = original_issues_dataset.copy()
    columns_to_extracting_func_map = {
        'referencing commits not linked to PRs': {'column_extracting_func': _extract_referencing_commits,
                                                  'func_keyword_args': {'linked_to_PRs': False}},
        'referencing commits linked to PRs': {'column_extracting_func': _extract_referencing_commits,
                                              'func_keyword_args': {'linked_to_PRs': True}},
        'closing commits not linked to PRs': {'column_extracting_func': _extract_closing_commits,
                                              'func_keyword_args': {'linked_to_PRs': False}},
        'closing commits linked to PRs': {'column_extracting_func': _extract_closing_commits,
                                          'func_keyword_args': {'linked_to_PRs': True}},
        'closing PRs': {'column_extracting_func': _extract_closing_PRs,
                        'func_keyword_args': {}},
        'linked PRs': {'column_extracting_func': _extract_related_PRs,
                       'func_keyword_args': {'linked_PR': True}},
        'mentioning PRs': {'column_extracting_func': _extract_related_PRs,
                           'func_keyword_args': {'linked_PR': False}},
        'PRs for referencing commits': {'column_extracting_func': _extract_PRs_for_referencing_commits,
                                        'func_keyword_args': {}}
    }

    for column_name, column_extracting_func_info in columns_to_extracting_func_map.items():
        extracting_func = column_extracting_func_info['column_extracting_func']
        func_keyword_args = column_extracting_func_info['func_keyword_args']
        issues_dataset[column_name] = \
            raw_issues_dataset['node.timelineItems.edges'].apply(lambda x: extracting_func(x, **func_keyword_args))

    return issues_dataset


def _extract_additional_bug_fixing_info(original_issues_dataset):
    issues_dataset = original_issues_dataset.copy()
    issues_dataset['irrelevant'] = issues_dataset['labels'].apply(_is_issue_irrelevant)
    issues_dataset['has mentioning, linked or closing PRs'] = \
        issues_dataset[['mentioning PRs',
                        'linked PRs',
                        'closing PRs']].apply(lambda x: (len(x['mentioning PRs']) +
                                                         len(x['linked PRs']) +
                                                         len(x['closing PRs'])) > 0,
                                              axis=1)
    issues_dataset['has related commits and PRs'] = \
        (issues_dataset['has mentioning, linked or closing PRs'] |
         issues_dataset['referencing commits not linked to PRs'].apply(lambda x: len(x) > 0) |
         issues_dataset['referencing commits linked to PRs'].apply(lambda x: len(x) > 0))
    return issues_dataset


def infer_bug_label_api4(repo_name):
    return [r"\"" + bug_label + r"\"" for bug_label in infer_bug_label(repo_name)]


def create_issues_dataset_api4(repo_name,
                               repo_creation_date,
                               remove_irrelevant_issues=False):
    repo_link = 'https://github.com/' + repo_name
    print(f'Processing repo {repo_name} created at {repo_creation_date} to get info about its issues...')
    raw_issues_dataset = _create_raw_dataset_api4(repo_name,
                                                  repo_creation_date)
    issues_dataset_columns = ['title', 'url', 'bodyHTML', 'bodyText', 'closedAt',
                              'createdAt', 'publishedAt', 'author', 'labels',
                              'referencing commits not linked to PRs',
                              'referencing commits linked to PRs',
                              'closing commits not linked to PRs',
                              'closing commits linked to PRs', 'closing PRs',
                              'linked PRs', 'mentioning PRs', 'PRs for referencing commits',
                              'irrelevant', 'has mentioning, linked or closing PRs',
                              'has related commits and PRs']

    if raw_issues_dataset.empty:
        issues_dataset_columns[3] = 'bug report'
        return pd.DataFrame([], columns=issues_dataset_columns), repo_link

    issues_dataset = pd.DataFrame(columns=issues_dataset_columns)
    issues_dataset[issues_dataset_columns[:7]] = raw_issues_dataset[['node.' + col
                                                                     for col in issues_dataset_columns[:7]]]
    issues_dataset['author'] = raw_issues_dataset['node.author.login']
    issues_dataset['labels'] = raw_issues_dataset['node.labels.edges'].apply(_extract_issue_labels)

    issues_dataset = _extract_commits_n_PRs_info(raw_issues_dataset,
                                                 issues_dataset)
    issues_dataset = _extract_additional_bug_fixing_info(issues_dataset)
    if remove_irrelevant_issues:
        issues_dataset = issues_dataset.loc[(issues_dataset['has related commits and PRs']) &
                                            ~issues_dataset['irrelevant'], :]
    else:
        issues_dataset = issues_dataset.loc[issues_dataset['has related commits and PRs'], :]
    return _extract_bug_reports(issues_dataset), repo_link


def create_pull_requests_dataset_api4(repo_name,
                                      repo_creation_date):
    print(f'Processing repo {repo_name} created at {repo_creation_date} to get info about its pull requests...')
    df = _create_raw_dataset_api4(repo_name, repo_creation_date, dataset_type='pull request')

    pull_requests_dataset_columns = ['headRefOid', 'baseRefOid', 'title', 'url', 'createdAt', 'closed', 'closedAt',
                                     'state', 'merged', 'mergedAt', 'mergedBy', 'milestone title', 'bodyHTML',
                                     'milestone number', 'author', 'changedFiles', 'commits',
                                     'isCrossRepository', 'labels', 'mergeCommit', 'associated with issue']
    pull_requests_dataset = pd.DataFrame(columns=pull_requests_dataset_columns,
                                         index=range(df.shape[0]))
    return df





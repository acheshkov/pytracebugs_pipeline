import os
import re
import pandas as pd
import itertools
from get_issues.src.extract_bug_fixing_info_from_pull_request_text import _extract_issues_web_links


PATH_TO_DIR_WITH_PICKLE_DATA = os.getenv("HOME") + '/zephyr_data/'
RELEVANT_BUG_FIXING_TOKENS = [{'contained': 'solv',
                               'not contained': ['resolver', 'resolve_', 'solver', 'unresolved',
                                                 'resolv.', 'solve()', 'solveset', 'resolvable',
                                                 'resolve(', 'spsolve', 'solve/']},
                              {'contained': 'fix',
                               'not contained': ['prefix', '(fixed)', 'fix(guard):', 'implement/fix?',
                                                 'fix(media_player):', 'suffix', 'fixtures', 'fixture',
                                                 'fixme', 'unfixed.', 'webpack/bugfix', 'fix_',
                                                 'fixmes/', 'fix(', 'fix-', '_fix', '/fixes/',
                                                 'fix:dynamodbstreams-', 'fixing_', 'fixkrack',
                                                 'fixable', r'\ufefffixes', '.fix', 'fixedoffsettimezone',
                                                 'affix', 'infix', 'unfixe', 'formatter-fix', 'receivefixedmessage',
                                                 'fixers', '--fix', '(e622497)(fixes']},
                              {'contained': 'clos',
                               'not contained': ['closer', 'closely', 'closing-issues-using-keywords',
                                                 'closest', 'close()', 'enclos', 'closure',
                                                 'unclosed', 'close_', 'closed=', 'isclose',
                                                 '_clos', '@wclose', 'isclose', 'streamclosederror',
                                                 'closedpoolerror']},
                              {'contained': 'addres',
                               'not contained': ['ipaddress', 'mac_address', '_address', 'addressinput',
                                                 'shippingaddress', 'accountaddress', 'walletaddres',
                                                 'address=', '-addres', 'type(address)', 'macaddresses']},
                              {'contained': 'adres',
                               'not contained': []},
                              {'contained': 'linked',
                               'not contained': []},
                              {'contained': 'relate',
                               'not contained': []},
                              {'contained': 'referenc',
                               'not contained': []},
                              {'contained': 'refs',
                               'not contained': []},
                              {'contained': 'associated',
                               'not contained': []}]
IRRELEVANT_PR_ISSUE_n_COMMIT_MESSAGE_TOKENS = ['dependenc', 'compatib', 'regression', 'backport']

# add backport
# {'contained': 'handl',
#  'not contained': ['handler', 'unhandled', 'mishandl', 'error-handling',
#                    'draghandle', 'filehandles', 'selection-handling',
#                    '.handl', 'textinfos,handl', '_handl', 'flow—handling',
#                    'actorhandle', '@handl', 'handleset', 'forhandle',
#                    'resizehandl', 'are-handled', 'handle_', 'the-handle-is',
#                    ]}

PREDEFINED_KEYWORDS_FOR_CLOSING_ISSUES = ['close', 'closes', 'closed', 'fix',
                                          'fixes', 'fixed', 'resolve', 'resolves',
                                          'resolved']
# https://docs.github.com/en/github/managing-your-work-on-github/linking-a-pull-request-to-an-issue#linking-a-pull-request-to-an-issue-using-a-keyword


def _check_token_relevance(token,
                           relevant_token,
                           irrelevant_antitokens):
    return (relevant_token in token) and all(antitoken not in token
                                             for antitoken in irrelevant_antitokens)


def _eval_string_columns(issues_dataset):
    processed_issues_dataset = issues_dataset.copy()
    issues_cols = ['labels', 'referencing commits not linked to PRs',
                   'referencing commits linked to PRs', 'closing commits not linked to PRs',
                   'closing commits linked to PRs', 'closing PRs', 'linked PRs', 'mentioning PRs',
                   'PRs for referencing commits', 'source code and errors']
    for col in issues_cols:
        processed_issues_dataset[col] = processed_issues_dataset[col].apply(eval)
    return processed_issues_dataset


def _extract_commits_referencing_given_issue(commits_infos,
                                             issue_url):
    issue_id_token = '#' + issue_url.split('/')[-1]
    return [commit_info for commit_info in commits_infos
            if (issue_url in commit_info['linked_issues']) or
            bool(re.match('.*?' + issue_id_token + '[^0-9]+',
                          commit_info['messageHeadline'])) or
            (commit_info['messageHeadline'].endswith(issue_id_token))]


def _extract_issues_linked_in_commits_messages(commits_infos,
                                               return_preceding_tokens,
                                               number_of_preceding_tokens_to_consider):
    updated_commits_infos = []
    for commit_info in commits_infos:
        linked_issues_data = _extract_issues_web_links(commit_info['messageBodyHTML'],
                                                       return_preceding_tokens=return_preceding_tokens,
                                                       number_of_preceding_tokens_to_consider=number_of_preceding_tokens_to_consider)
        commit_info.pop('linked_issues', None)
        updated_commits_infos.append(dict(**commit_info,
                                     linked_issues=linked_issues_data))
    return updated_commits_infos


def _extract_additional_closing_commits(closing_commits_not_linked_infos,
                                        closing_commits_linked_infos,
                                        referencing_commits_not_linked_infos,
                                        referencing_commits_linked_infos,
                                        issue_url):
    set_of_closing_commits_links = set(commit_info['commitUrl'] for commit_info in closing_commits_not_linked_infos +
                                       closing_commits_linked_infos)
    non_closing_commits = [commit_info for commit_info in referencing_commits_not_linked_infos +
                           referencing_commits_linked_infos
                           if commit_info['commitUrl'] not in set_of_closing_commits_links]
    return [commit_info for commit_info in non_closing_commits
            if any(closing_keyword == preceding_tokens_list[-1]
                   for closing_keyword in PREDEFINED_KEYWORDS_FOR_CLOSING_ISSUES
                   for preceding_tokens_list in (commit_info['linked_issues'][issue_url]
                                                 if issue_url in commit_info['linked_issues'] else [])
                   if preceding_tokens_list)]


def _update_commits_info_with_linked_issues_data(issues_dataset,
                                                 return_preceding_tokens=True,
                                                 number_of_preceding_tokens_to_consider=10):
    updated_issues_dataset = issues_dataset.copy()
    for commit_col in ['referencing commits not linked to PRs',
                       'referencing commits linked to PRs',
                       'closing commits not linked to PRs',
                       'closing commits linked to PRs']:
        updated_issues_dataset[commit_col] = \
            updated_issues_dataset[commit_col].apply(lambda x:
                                                     _extract_issues_linked_in_commits_messages(x, return_preceding_tokens,
                                                                                                number_of_preceding_tokens_to_consider))
    return updated_issues_dataset


def _extract_non_closing_commits(closing_commits_not_linked_infos,
                                 closing_commits_linked_infos,
                                 referencing_commits_not_linked_infos,
                                 referencing_commits_linked_infos,
                                 keyword_closing_commits_infos):
    set_of_closing_commits_links = set(commit_info['commitUrl']
                                       for commit_info in closing_commits_not_linked_infos +
                                       closing_commits_linked_infos + keyword_closing_commits_infos)
    return [commit_info for commit_info in referencing_commits_not_linked_infos + referencing_commits_linked_infos
            if commit_info['commitUrl'] not in set_of_closing_commits_links]


def _extract_relevant_non_closing_commits(commits_infos,
                                          issue_url,
                                          history_to_consider_threshold,
                                          history_length_threshold):
    issue_id_token = '#' + issue_url.split('/')[-1]
    return [commit_info for commit_info in commits_infos
            if bool(re.match('.*?' + issue_id_token + '[^0-9]+',
                             commit_info['messageHeadline'])) or
            (commit_info['messageHeadline'].endswith(issue_id_token)) or
            any(_check_token_relevance(preceding_token,
                                       relevance_token_pairs['contained'],
                                       relevance_token_pairs['not contained']) or
                (len(preceding_tokens_list) <= history_length_threshold)
                for preceding_tokens_list in (commit_info['linked_issues'][issue_url]
                                              if issue_url in commit_info['linked_issues'] else [])
                for preceding_token in preceding_tokens_list[-history_to_consider_threshold:]
                for relevance_token_pairs in RELEVANT_BUG_FIXING_TOKENS)]


def _extract_merged_PRs(PRs_infos):
    return [PR_info for PR_info in PRs_infos if PR_info['state'] == 'MERGED']


def _extract_issues_linked_in_PRs_messages(PRs_infos,
                                           return_preceding_tokens,
                                           number_of_preceding_tokens_to_consider):
    updated_PRs_infos = []
    for PR_info in PRs_infos:
        linked_issues_data = _extract_issues_web_links(PR_info['bodyHTML'],
                                                       return_preceding_tokens=return_preceding_tokens,
                                                       number_of_preceding_tokens_to_consider=number_of_preceding_tokens_to_consider)
        PR_info.pop('linked_issues', None)
        updated_PRs_infos.append(dict(**PR_info,
                                      linked_issues=linked_issues_data))
    return updated_PRs_infos


def _extract_additional_closing_PRs(closing_PRs_infos,
                                    mentioning_PRs_infos,
                                    linked_PRs_infos,
                                    issue_url):
    set_of_closing_PRs_links = set(PR_info['url'] for PR_info in closing_PRs_infos)
    non_closing_PRs = [PR_info for PR_info in linked_PRs_infos + mentioning_PRs_infos
                       if PR_info['url'] not in set_of_closing_PRs_links]
    return [PR_info for PR_info in non_closing_PRs
            if any(closing_keyword == preceding_tokens_list[-1]
                   for closing_keyword in PREDEFINED_KEYWORDS_FOR_CLOSING_ISSUES
                   for preceding_tokens_list in (PR_info['linked_issues'][issue_url]
                                                 if issue_url in PR_info['linked_issues'] else [])
                   if preceding_tokens_list)]


def _extract_PRs_referencing_given_issue(PRs_infos,
                                         issue_url):
    issue_id_token = '#' + issue_url.split('/')[-1]
    return [PR_info for PR_info in PRs_infos
            if (issue_url in PR_info['linked_issues']) or
            bool(re.match('.*?' + issue_id_token + '[^0-9]+', PR_info['title'])) or
            (PR_info['title'].endswith(issue_id_token))]


def _extract_non_closing_PRs(closing_PRs_infos,
                             mentioning_PRs_infos,
                             linked_PRs_infos,
                             keyword_closing_PRs_infos):
    set_of_closing_PRs_links = set(PR_info['url']
                                   for PR_info in closing_PRs_infos + keyword_closing_PRs_infos)
    return [PR_info for PR_info in linked_PRs_infos + mentioning_PRs_infos
            if PR_info['url'] not in set_of_closing_PRs_links]


def _extract_relevant_non_closing_PRs(PRs_infos,
                                      issue_url,
                                      history_to_consider_threshold,
                                      history_length_threshold):
    issue_id_token = '#' + issue_url.split('/')[-1]
    return [PR_info for PR_info in PRs_infos
            if bool(re.match('.*?' + issue_id_token + '[^0-9]+', PR_info['title'])) or
            (PR_info['title'].endswith(issue_id_token)) or
            any(_check_token_relevance(preceding_token,
                                       relevance_token_pairs['contained'],
                                       relevance_token_pairs['not contained']) or
                (len(preceding_tokens_list) <= history_length_threshold)
                for preceding_tokens_list in (PR_info['linked_issues'][issue_url]
                                              if issue_url in PR_info['linked_issues'] else [])
                for preceding_token in preceding_tokens_list[-history_to_consider_threshold:]
                for relevance_token_pairs in RELEVANT_BUG_FIXING_TOKENS)]


def _update_PRs_info_with_linked_issues_data(issues_dataset,
                                             return_preceding_tokens=True,
                                             number_of_preceding_tokens_to_consider=10):
    updated_issues_dataset = issues_dataset.copy()
    for PR_col in ['closing PRs', 'mentioning PRs', 'linked PRs']:
        updated_issues_dataset[PR_col] = \
            updated_issues_dataset[PR_col].apply(lambda x:
                                                 _extract_issues_linked_in_PRs_messages(x, return_preceding_tokens,
                                                                                        number_of_preceding_tokens_to_consider))
    return updated_issues_dataset


def _filter_out_merged_PRs(issues_dataset):
    updated_issues_dataset = issues_dataset.copy()
    for PR_col_name in ['closing PRs', 'mentioning PRs', 'linked PRs']:
        updated_issues_dataset[PR_col_name] = updated_issues_dataset[PR_col_name].apply(_extract_merged_PRs)
    return updated_issues_dataset


def _aggregate_selected_columns(issues_dataset,
                                columns):
    return issues_dataset[columns].apply(lambda x:
                                         list(itertools.chain.from_iterable([x[col] for col in columns])),
                                         axis=1)


def filter_PRs(issues_dataset,
               history_to_consider_threshold=5,
               history_length_threshold=3):
    if issues_dataset.empty:
        updated_issues_dataset = pd.DataFrame(columns=list(issues_dataset.columns) +
                                              ['keyword closing PRs', 'non-closing PRs',
                                               'relevant non-closing PRs', 'all relevant PRs',
                                               'most relevant PRs'])
        return updated_issues_dataset

    updated_issues_dataset = _update_PRs_info_with_linked_issues_data(_filter_out_merged_PRs(issues_dataset))
    for PR_col_name in ['mentioning PRs', 'linked PRs']:
        updated_issues_dataset[PR_col_name] = \
            updated_issues_dataset[[PR_col_name, 'url']].apply(lambda x:
                                                               _extract_PRs_referencing_given_issue(x[PR_col_name],
                                                                                                    x['url']),
                                                               axis=1)
    PRs_columns_names = ['closing PRs', 'mentioning PRs', 'linked PRs']
    cols = PRs_columns_names + ['url']
    updated_issues_dataset['keyword closing PRs'] = \
        updated_issues_dataset[cols].apply(lambda x:
                                           _extract_additional_closing_PRs(*(x[col] for col in cols)),
                                           axis=1)
    cols = PRs_columns_names + ['keyword closing PRs']
    updated_issues_dataset['non-closing PRs'] = \
        updated_issues_dataset[cols].apply(lambda x:
                                           _extract_non_closing_PRs(*(x[col] for col in cols)),
                                           axis=1)
    updated_issues_dataset['relevant non-closing PRs'] = \
        updated_issues_dataset[['non-closing PRs',
                                'url']].apply(lambda x:
                                              _extract_relevant_non_closing_PRs(x['non-closing PRs'],
                                                                                x['url'],
                                                                                history_to_consider_threshold=history_to_consider_threshold,
                                                                                history_length_threshold=history_length_threshold),
                                              axis=1)
    updated_issues_dataset['all relevant PRs'] = _aggregate_selected_columns(updated_issues_dataset,
                                                                             ['closing PRs', 'keyword closing PRs',
                                                                              'non-closing PRs'])
    updated_issues_dataset['most relevant PRs'] = _aggregate_selected_columns(updated_issues_dataset,
                                                                              ['closing PRs', 'keyword closing PRs',
                                                                               'relevant non-closing PRs'])
    return updated_issues_dataset


def filter_commits(issues_dataset,
                   history_to_consider_threshold=50,
                   history_length_threshold=3):
    if issues_dataset.empty:
        updated_issues_dataset = pd.DataFrame(columns=list(issues_dataset.columns) +
                                                      ['keyword closing commits', 'non-closing commits',
                                                       'relevant non-closing commits', 'all relevant commits',
                                                       'most relevant commits'])
        return updated_issues_dataset

    updated_issues_dataset = _update_commits_info_with_linked_issues_data(issues_dataset)

    closing_commits_cols = ['closing commits not linked to PRs',
                            'closing commits linked to PRs']
    commits_cols = closing_commits_cols + ['referencing commits not linked to PRs',
                                           'referencing commits linked to PRs']

    cols = commits_cols + ['url']
    updated_issues_dataset['keyword closing commits'] = \
        updated_issues_dataset[cols].apply(lambda x: _extract_additional_closing_commits(*(x[col] for col in cols)),
                                           axis=1)
    cols = commits_cols + ['keyword closing commits']
    updated_issues_dataset['non-closing commits'] = \
        updated_issues_dataset[cols].apply(lambda x: _extract_non_closing_commits(*(x[col] for col in cols)),
                                           axis=1)
    updated_issues_dataset['relevant non-closing commits'] = \
        updated_issues_dataset[['non-closing commits',
                                'url']].apply(lambda x:
                                              _extract_relevant_non_closing_commits(x['non-closing commits'],
                                                                                    x['url'],
                                                                                    history_to_consider_threshold=history_to_consider_threshold,
                                                                                    history_length_threshold=history_length_threshold),
                                              axis=1)
    updated_issues_dataset['all relevant commits'] = _aggregate_selected_columns(updated_issues_dataset,
                                                                                 closing_commits_cols +
                                                                                 ['keyword closing commits',
                                                                                  'non-closing commits'])
    updated_issues_dataset['most relevant commits'] = _aggregate_selected_columns(updated_issues_dataset,
                                                                                  closing_commits_cols +
                                                                                  ['keyword closing commits',
                                                                                   'relevant non-closing commits'])
    return updated_issues_dataset


def merge_data_files_into_frame(path_to_dir_with_data,
                                file_type='pickle',
                                filter_commits_n_PRs=True,
                                return_result=['issues', 'bugfixes']):
    path_to_dir_with_issues_data = path_to_dir_with_data + 'issues/'
    path_to_dir_with_bugfixes_data = path_to_dir_with_data + 'bugfixes/'
    pandas_func_to_read_data = {'csv': pd.read_csv,
                                'pickle': pd.read_pickle}

    issues_dataframes, bugfixes_dataframes = [], []
    for issue_data_filename, bugfix_data_filename in zip(os.listdir(path_to_dir_with_issues_data),
                                                         os.listdir(path_to_dir_with_bugfixes_data)):
        if 'issues' in return_result:
            issues_dataframes.append(pandas_func_to_read_data[file_type](path_to_dir_with_issues_data +
                                                                         issue_data_filename))
        if 'bugfixes' in return_result:
            bugfixes_dataframes.append(pandas_func_to_read_data[file_type](path_to_dir_with_bugfixes_data +
                                                                           bugfix_data_filename,
                                                                           **({'sep': '\t'} if file_type == 'csv' else {})))
    if 'issues' in return_result:
        whole_issues_data = pd.concat(issues_dataframes,
                                      axis=0,
                                      ignore_index=True)
        if filter_commits_n_PRs:
            whole_issues_data = filter_PRs(whole_issues_data)
            whole_issues_data = filter_commits(whole_issues_data)

    if ('issues' in return_result) and ('bugfixes' in return_result):
        return {'issues': whole_issues_data if file_type == 'pickle' else _eval_string_columns(whole_issues_data),
                'bugfixes': pd.concat(bugfixes_dataframes,
                                      axis=0,
                                      ignore_index=True)}
    elif 'issues' in return_result:
        return {'issues': whole_issues_data if file_type == 'pickle' else _eval_string_columns(whole_issues_data)}
    elif 'bugfixes' in return_result:
        return {'bugfixes': pd.concat(bugfixes_dataframes,
                                      axis=0,
                                      ignore_index=True)}
    else:
        return {}

import pandas as pd
from requests_html import HTMLSession
from .utils import fetch_github_paged_api_data
import get_issues.src.extract_bug_fixing_info_from_issue_text as piwp
from .local_settings import *
import time

MAX_NUMBER_OF_TRIAL_QUERIES = 20
TIMEOUT_TIME_ = 60


def _get_issue_commits_pull_requests_n_bug_reports(issue_html_url,
                                                   web_session):
    print('Extracting information about issues and pull requests from the following issue web page:')
    print(issue_html_url)

    for number_of_queries in range(MAX_NUMBER_OF_TRIAL_QUERIES):
        issue_webpage_content = web_session.get(issue_html_url).text
        if len(issue_webpage_content) > 2000:
            break
        elif 'rate limit' in issue_webpage_content.lower():
            print('Rate limit exceeded for web scraping of the issue page. Will retry to query again after 1 min.')

        if number_of_queries < MAX_NUMBER_OF_TRIAL_QUERIES - 1:
            time.sleep(TIMEOUT_TIME_)
        else:
            raise RuntimeError

    time.sleep(1)
    return {'commits_n_pull_requests': piwp.get_commits_n_pull_requests_refs(issue_webpage_content.lower()),
            'source_code_n_error_messages': piwp.get_source_code_n_error_messages(issue_webpage_content)}


def _get_all_issues_commits_pull_requests_n_bug_reports(issues,
                                                        web_session):
    issues_with_bug_fixing_info = issues.copy()
    commits_pull_requests_n_bug_reports = \
        pd.Series(issues_with_bug_fixing_info['html_url'].apply(lambda issue_url:
                                                                _get_issue_commits_pull_requests_n_bug_reports(issue_url,
                                                                                                               web_session)))
    issues_with_bug_fixing_info['commits_n_pull_requests'] = \
        commits_pull_requests_n_bug_reports.apply(lambda bug_fixing_info: bug_fixing_info['commits_n_pull_requests'])
    issues_with_bug_fixing_info['source_code_n_error_messages'] = \
        commits_pull_requests_n_bug_reports.apply(lambda bug_fixing_info: bug_fixing_info['source_code_n_error_messages'])
    return issues_with_bug_fixing_info


def _filter_issues_with_related_commits_n_pull_requests(issues):
    def count_commits_n_pull_requests(commits_n_pull_requests_info):
        return (len(commits_n_pull_requests_info['commits']) +
                len(commits_n_pull_requests_info['pull_requests']))

    assert 'commits_n_pull_requests' in issues.columns, 'Column "commits_n_pull_requests" is not created'
    return issues.loc[issues['commits_n_pull_requests'].apply(count_commits_n_pull_requests) > 0, :]


def _get_raw_paged_repo_info(repo_path,
                             params,
                             key_name=None):
    params['username'] = USERNAME[0]
    params['token'] = GITHUB_TOKENS[0]
    res = fetch_github_paged_api_data(repo_path,
                                      params=params,
                                      key_name=key_name)
    dataframes = [res['query_results'], ]
    if res.get("pagination"):
        pages = range(2, res.get("pagination").get("total_pages") + 1)
        for p in pages:
            params['page'] = p
            params['username'] = USERNAME[p % len(GITHUB_TOKENS)]
            params['token'] = GITHUB_TOKENS[p % len(GITHUB_TOKENS)]
            res = fetch_github_paged_api_data(repo_path,
                                              params=params,
                                              key_name=key_name)
            dataframes.append(res)
            time.sleep(1)
    return pd.concat(dataframes,
                     ignore_index=True)


def _create_raw_dataset_for_bug_label(repo_name,
                                      bug_label):
    repo_path = "repos/" + repo_name + "/issues"
    params = {'state': 'closed',
              'labels': bug_label}
    return _get_raw_paged_repo_info(repo_path,
                                    params=params)


def _get_raw_labels(repo_name):
    params = {'token': GITHUB_TOKENS[0]}
    repo_path = "repos/" + repo_name + "/labels"
    return _get_raw_paged_repo_info(repo_path,
                                    params=params,
                                    key_name='name').unique()


def infer_bug_label(repo_name):
    bug_labels = []
    possible_bug_tokens = ('bug', 'error', 'defect', 'fault', 'should fix', 'bug fix', 'fixme', 'crash')
    possible_non_bug_tokens = ('wrong', 'not', 'external', 'bugfix', 'bug-fix', 'bug_fix',
                               'upstream', 'systemd\'s-fault', 'reporting', 'selenium',
                               'default', 'test', 'message', 'documentation',
                               'bugzilla', '429', 'someone else\'s', 'user', 'docs',
                               'technical', 'config', 'build', 'download', 'language', 'irreproducible',
                               'vendor', 'pr changelog', 'bugbash', 'compile error',
                               'third-party', 'stage/bug-repro', 'msg', 'dependency',
                               'better_errors', 'dataset', 'debug', 'dep bug', 'discord bug',
                               'rpw bug', 'revit bug')
    for label in _get_raw_labels(repo_name):
        if any(bug_token in label.lower() for bug_token in possible_bug_tokens):
            if all(non_bug_token not in label.lower() for non_bug_token in possible_non_bug_tokens):
                if ('triage' not in label.lower()) or ('triaged' in label.lower()):
                    bug_labels.append(label)
    return bug_labels


def create_issues_dataset(repo_name):
    dataframes = []
    bug_labels = infer_bug_label(repo_name)
    for bug_label in bug_labels:
        res = _create_raw_dataset_for_bug_label(repo_name,
                                                bug_label)
        dataframes.append(res)
    issues_without_bug_fixing_info = pd.concat(dataframes,
                                               ignore_index=True)
    issues_without_bug_fixing_info = \
        issues_without_bug_fixing_info.loc[issues_without_bug_fixing_info['pull_request.url'].isna()]
    issues = _get_all_issues_commits_pull_requests_n_bug_reports(issues_without_bug_fixing_info,
                                                                 HTMLSession())
    return _filter_issues_with_related_commits_n_pull_requests(issues)
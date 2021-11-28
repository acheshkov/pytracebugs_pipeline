import unittest
import pandas as pd
from get_issues.src.form_issues_datasets_api4 import create_issues_dataset_api4
import datetime


def _read_expected_issues_dataset(repo_name):
    return pd.read_csv('../data/' +
                       repo_name.replace('/', '_') +
                       '_issues.csv')


def _extract_expected_issues_commits_n_pull_requests(expected_issues_dataset):
    expected_issues = set(expected_issues_dataset['html_url'])
    expected_commits_refs, expected_pull_requests_refs = set(), set()
    for issue_commits_n_pull_requests_info in \
            expected_issues_dataset['commits_n_pull_requests'].apply(eval):
        expected_commits_refs |= {commit_ref[:-30] for commit_ref in
                                  issue_commits_n_pull_requests_info['commits']}
        expected_pull_requests_refs |= {pull_request_ref for pull_request_ref in
                                        issue_commits_n_pull_requests_info['pull_requests']}
    return expected_issues, expected_commits_refs, expected_pull_requests_refs


def _read_actual_issues_dataset(repo_name):
    test_repo_creation_date = datetime.datetime.strptime('01122008', "%d%m%Y").date()
    test_actual_issues_dataset, _ = create_issues_dataset_api4(repo_name,
                                                               test_repo_creation_date)
    return test_actual_issues_dataset


def _extract_actual_issues_commits_n_pull_requests(actual_issues_dataset):
    actual_issues = set(actual_issues_dataset['url'])
    actual_commits_refs = set()
    commits_info_columns = ['referencing commits linked to PRs',
                            'referencing commits not linked to PRs',
                            'closing commits not linked to PRs',
                            'closing commits linked to PRs']
    for commits_info_column in commits_info_columns:
        for commits_info in actual_issues_dataset[commits_info_column]:
            for commit_info in commits_info:
                actual_commits_refs.add(commit_info['commitUrl'][18:].lower())

    actual_pull_requests_refs = set()
    pull_requests_info_columns = ['closing PRs',
                                  'linked PRs',
                                  'mentioning PRs']
    for pull_requests_info_column in pull_requests_info_columns:
        for pull_requests_info in actual_issues_dataset[pull_requests_info_column]:
            for pull_request_info in pull_requests_info:
                actual_pull_requests_refs.add(pull_request_info['url'][18:].lower())

    return actual_issues, actual_commits_refs, actual_pull_requests_refs


class TestFormingIssuesDataset(unittest.TestCase):
    def test_create_issues_dataset_api4(self):
        self.maxDiff = None
        repo_names = ["pandas-dev/pandas",
                      "scikit-learn/scikit-learn"]

        for repo_name in repo_names:
            test_expected_issues_dataset = _read_expected_issues_dataset(repo_name)
            test_expected_issues_dataset = \
                test_expected_issues_dataset.loc[test_expected_issues_dataset['user.login'] != 'ghost', :]
            # GraphQL does not fetch issues authored by deleted users (named ghost)
            # Thus, those issues are excluded from test data
            # For proof one can query through GraphQL explorer https://docs.github.com/en/graphql/overview/explorer
            # query{
            #   search(first:100 type:ISSUE
            #           query:"repo:pandas-dev/pandas is:issue label:Bug is:closed") {
            #     issueCount
            #   }
            # }
            # and alternatively through pandas issue page using is:issue is:closed label:Bug
            # the first approach gives 4170 issues against 4225 issues for the second approach

            test_expected_issues, test_expected_commits_refs, test_expected_pull_requests_refs = \
                _extract_expected_issues_commits_n_pull_requests(test_expected_issues_dataset)

            test_actual_issues_dataset = _read_actual_issues_dataset(repo_name)
            test_actual_issues, test_actual_commits_refs, test_actual_pull_requests_refs = \
                _extract_actual_issues_commits_n_pull_requests(test_actual_issues_dataset)

            self.assertSetEqual(test_expected_issues - test_actual_issues, set())
            self.assertSetEqual(test_expected_commits_refs - test_actual_commits_refs, set())
            self.assertSetEqual(test_expected_pull_requests_refs - test_actual_pull_requests_refs, set())


if __name__ == '__main__':
    unittest.main()

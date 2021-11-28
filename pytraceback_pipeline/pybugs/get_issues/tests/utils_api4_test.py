import unittest
import requests
from get_issues.src.utils_api4 import _fetch_github_graphql_api_data, fetch_github_paged_graphql_api_data, GITHUB_ROOT_ENDPOINT, _form_graphql_query_for_issues
from get_issues.src.local_settings import *


class TestUtilsAPI4(unittest.TestCase):
    def test_fetch_github_graphql_api_data_on_another_webserver(self):
        self.maxDiff = None
        test_web_server_url = 'https://httpbin.org/post'
        expected_test_results = requests.post(test_web_server_url,
                                              json={},
                                              headers={"Authorization": "kobylkinks"})
        actual_test_results_status_code, _ = \
            _fetch_github_graphql_api_data(test_web_server_url,
                                           query_params={},
                                           headers={"Authorization": "kobylkinks"})
        self.assertEqual(actual_test_results_status_code,
                         expected_test_results.status_code,
                         'https://httpbin.org/ does not respond correctly on fetch_github_graphql_api_data post query.')

    def test_fetch_github_graphql_api_data(self):
        self.maxDiff = None
        test_params = {'token': GITHUB_TOKENS[0]}
        test_api_endpoint = GITHUB_ROOT_ENDPOINT + "/graphql"
        test_headers = {"Authorization": "token " + test_params['token']}

        test_query = """query {
            search(first:100 type:REPOSITORY query:"is:public sort:created-asc") {
               edges {
                  node {
                  ... on Repository {
                        url
                        name
                      }
                  }
               }
            }
        }"""
        test_query_params = {'query': test_query}
        actual_test_results_status_code, actual_test_results_data = \
            _fetch_github_graphql_api_data(test_api_endpoint,
                                           query_params=test_query_params,
                                           headers=test_headers)
        expected_test_results = requests.post(test_api_endpoint,
                                              json=test_query_params,
                                              headers=test_headers)
        self.assertEqual(expected_test_results.status_code,
                         actual_test_results_status_code,
                         test_api_endpoint + ' does not respond correctly on fetch_github_graphql_api_data post query')
        if expected_test_results.status_code == 200:
            expected_test_results_data = expected_test_results.json()
        else:
            expected_test_results_data = {}
        self.assertEqual(expected_test_results_data,
                         actual_test_results_data,
                         "fetch_github_graphql_api_data test query payload does not " +
                         "coincide with the correct GitHub API test query payload.")

    def test_fetch_github_paged_graphql_api_data(self):
        self.maxDiff = None
        test_repo_path = 'scikit-learn/scikit-learn'
        test_params = {'token': GITHUB_TOKENS[0],
                       'starting_date': '2015-12-01',
                       'ending_date': '2016-01-01',
                       'query_type': 'issue',
                       'issue_label': 'Bug',
                       'batch_size': 10,
                       'sort': True}
        test_api_endpoint = GITHUB_ROOT_ENDPOINT + "/graphql"
        test_headers = {"Authorization": "token " + test_params['token']}
        test_query = """query {
                search(first: 10  type: ISSUE, 
                       query: "repo:scikit-learn/scikit-learn sort:created-desc is:issue label:Bug state:closed closed:2015-12-01..2016-01-01 ") {
                    issueCount
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                   edges {
                       node {
                       ... on Issue {
                               title
                               url
                               author {
                                  login
                               }
                               bodyHTML
                               bodyText
                               closedAt
                               createdAt
                               publishedAt
                               labels(first:5) {
                                   edges {
                                     node {
                                       name
                                     }
                                   }
                               }
                               timelineItems(itemTypes: [CLOSED_EVENT, REFERENCED_EVENT, CROSS_REFERENCED_EVENT, CONNECTED_EVENT] first: 85) {
                                edges {
                                  node {
                                    ... on CrossReferencedEvent {
                                           isCrossRepository
                                           source {
                                             ... on PullRequest {
                                                   headRefOid 
                                                   baseRefOid
                                                   title
                                                   bodyHTML
                                                   createdAt
                                                   closed
                                                   url
                                                   state
                                                   merged
                                                   mergedAt
                                                   mergedBy {
                                                     login
                                                   }
                                                   milestone {
                                                     title
                                                     number
                                                   }
                                                   author {
                                                     login
                                                   }
                                                   changedFiles
                                                   closedAt
                                                   commits(first:20) {
                                                     edges {
                                                       node {
                                                        commit {
                                                          commitUrl
                                                          status {
                                                            state
                                                          }  
                                                        }
                                                       }
                                                     }
                                                   }
                                                   isCrossRepository
                                                   labels(first:5) {
                                                      edges {
                                                        node {
                                                          name
                                                        }
                                                      }
                                                   }
                                                   mergeCommit {
                                                     commitUrl
                                                     status {
                                                       state
                                                     }
                                                   }   
                                             }
                                           }
                                    }
                                    ... on ReferencedEvent  {
                                      isCrossRepository
                                      commit {
                                        commitUrl
                                        status {
                                          state
                                        }
                                        authoredByCommitter
                                        associatedPullRequests(first:3) {
                                          edges {
                                            node {
                                               closed
                                               url
                                               state
                                               merged
                                               author {
                                                 login
                                               }
                                            }
                                          } 
                                        }
                                      }
                                    }
                                    ... on ClosedEvent {
                                      closer {
                                        ... on Commit {
                                          commitUrl
                                          status {
                                             state
                                          }
                                          authoredByCommitter
                                          associatedPullRequests(first:3) {
                                            edges {
                                              node {
                                                 closed
                                                 url
                                                 state
                                                 merged
                                                 author {
                                                   login
                                                 }
                                              }
                                            } 
                                          }
                                        }
                                        ... on PullRequest {
                                          headRefOid 
                                          baseRefOid
                                          title
                                          bodyHTML
                                          createdAt
                                          closed
                                          url
                                          state
                                          merged
                                          mergedAt
                                          mergedBy {
                                            login
                                          }
                                          milestone {
                                            title
                                            number
                                          }
                                          author {
                                            login
                                          }
                                          changedFiles
                                          closedAt
                                          commits(first:20) {
                                            edges {
                                              node {
                                                commit {
                                                  commitUrl
                                                  status {
                                                    state
                                                  }  
                                                }
                                              }
                                            }
                                          }
                                          isCrossRepository
                                          labels(first:5) {
                                            edges {
                                               node {
                                                name
                                               }
                                            }
                                          }
                                          mergeCommit {
                                            commitUrl
                                            status {
                                              state
                                            }
                                          }
                                        }
                                      }
                                    }
                                    ... on ConnectedEvent {
                                      isCrossRepository
                                      subject {
                                        ... on PullRequest {
                                          headRefOid 
                                          baseRefOid
                                          title
                                          bodyHTML
                                          createdAt
                                          closed
                                          url
                                          state
                                          merged
                                          mergedAt
                                          mergedBy {
                                            login
                                          }
                                          milestone {
                                            title
                                            number
                                          }
                                          author {
                                            login
                                          }
                                          changedFiles
                                          closedAt
                                          commits(first:20) {
                                            edges {
                                              node {
                                                commit {
                                                  commitUrl
                                                  status {
                                                    state
                                                  }  
                                                }
                                              }
                                            }
                                          }
                                          isCrossRepository
                                          labels(first:5) {
                                            edges {
                                               node {
                                                name
                                               }
                                            }
                                          }
                                          mergeCommit {
                                            commitUrl
                                            status {
                                              state
                                            }
                                          }                               
                                        }
                                      }
                                    }
                                  }
                                }
                              }

                           }
                       }
                   }
                }
                rateLimit {
                   limit
                   cost,
                   nodeCount,
                   remaining
                   resetAt
                }
            }"""
        expected_test_results = requests.post(test_api_endpoint,
                                              json={'query': test_query},
                                              headers=test_headers)
        expected_test_results_data = (expected_test_results.json() if
                                      expected_test_results.status_code == 200 else {})

        if expected_test_results.status_code == 200:
            if 'error' not in expected_test_results_data:
                try:
                    actual_test_results = fetch_github_paged_graphql_api_data(test_repo_path,
                                                                              params=test_params)
                    self.assertEqual(test_query, _form_graphql_query_for_issues(test_repo_path,
                                                                                params=test_params))
                    self.assertEqual({'total_pages': 1,
                                      'cursor': actual_test_results['page_info']['cursor'],
                                      'hasNextPage': False},
                                     actual_test_results['page_info'], 'pagination info is incorrect')
                    self.assertEqual(expected_test_results_data['data']['search']['edges'],
                                     actual_test_results['page_data']['edges'],
                                     "fetch_github_graphql_api_data test query payload does not " +
                                     "coincide with the correct GitHub API test query payload.")
                except RuntimeError:
                    raise AssertionError("Test query response contains some data whereas " +
                                         "fetch_github_paged_graphql_api_data raises Runtime error.")
            else:
                self.assertRaises(RuntimeError,
                                  fetch_github_paged_graphql_api_data,
                                  test_repo_path,
                                  test_params)


if __name__ == '__main__':
    unittest.main()

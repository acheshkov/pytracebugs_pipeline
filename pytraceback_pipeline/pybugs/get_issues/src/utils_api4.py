import requests
import time
from datetime import datetime
from socket import gethostbyname, gaierror
from requests.exceptions import ChunkedEncodingError


GITHUB_ROOT_ENDPOINT = "https://api.github.com"
BATCH_SIZE = 25
TIMELINE_SIZE = 85
NUMBER_OF_COMMITS_WITHIN_PULL_REQUEST = 20
GRAPHQL_OPERATIONS_LIMIT = 1000
API_EXCEEDING_LIMIT_THRESHOLD_FACTOR = 3
API_LIMIT_FOR_NUMBER_OF_NODES = 500000
MAX_NUMBER_OF_TRIAL_QUERIES = 300
TIMEOUT_TIME=240


def _fetch_github_graphql_api_data(api_endpoint,
                                   query_params,
                                   headers):
    for number_of_trial_queries in range(MAX_NUMBER_OF_TRIAL_QUERIES):
        try:
            request = requests.post(api_endpoint,
                                    json=query_params,
                                    headers=headers)
            break
        except (gaierror, ChunkedEncodingError, TimeoutError) as e:
            print(e)
            time.sleep(TIMEOUT_TIME)

    if request.status_code == 200:
        return request.status_code, request.json()
    else:
        print("Query failed to run by returning code of {}. {}".format(request.status_code,
                                                                       query_params['query']))
        return request.status_code, {}


def _compute_pagination_info_from_graphql_page(api_results,
                                               first_page):
    if first_page:
        number_of_pages = api_results['data']['search']['issueCount'] / BATCH_SIZE
        total_pages = int(number_of_pages) if int(number_of_pages) == number_of_pages else int(number_of_pages) + 1
        total_pages = min(int(GRAPHQL_OPERATIONS_LIMIT / BATCH_SIZE), total_pages)
        return {'total_pages': total_pages,
                'cursor': api_results['data']['search']['pageInfo']['endCursor'],
                'hasNextPage': bool(api_results['data']['search']['pageInfo']['hasNextPage'])}
    else:
        return {'cursor': api_results['data']['search']['pageInfo']['endCursor'],
                'hasNextPage': bool(api_results['data']['search']['pageInfo']['hasNextPage'])}


def _is_approaching_api_limit(api_results):
    api_consumption_status = _get_graphql_api_limit_consumption(api_results)
    delta = (datetime.strptime(api_consumption_status['resetAt'], '%Y-%m-%dT%H:%M:%SZ') -
             datetime.utcnow()).total_seconds()
    # print(f"It is remaining {delta} seconds for current window to elapse")
    # print(f"It is remaining {api_consumption_status['remaining']} API v.4 points")
    if api_consumption_status['remaining'] < API_EXCEEDING_LIMIT_THRESHOLD_FACTOR * api_consumption_status['cost']:
        return True, delta
    else:
        return False, 0.0


def _get_graphql_api_limit_consumption(api_results):
    return {'limit': api_results['data']['rateLimit']['limit'],
            'remaining': api_results['data']['rateLimit']['remaining'],
            'resetAt': api_results['data']['rateLimit']['resetAt'],
            'cost': api_results['data']['rateLimit']['cost']}


def _form_graphql_query_for_issues(repo_path,
                                   params):
    page_info = "after:\"" + params['cursor'] + "\"" if 'cursor' in params else ""
    # https://stackoverflow.com/questions/48116781/github-api-v4-how-can-i-traverse-with-pagination-graphql
    is_to_compute_issues_count = "issueCount" if 'cursor' not in params else ""
    date_range = "closed:" + params['starting_date'] + ".." + params['ending_date']
    issue_label = "label:" + params['issue_label'] if 'issue_label' in params else ""
    batch_size = params['batch_size'] if 'batch_size' in params else BATCH_SIZE
    is_sort = "sort:created-desc" if 'sort' in params else ''

    issues_query = """query {
                search(first: """ + str(batch_size) + """ """ + page_info + """ type: ISSUE, 
                       query: "repo:""" + repo_path + """ """ + is_sort + """ is:issue """ + issue_label + """ state:closed """ + date_range + """ ") {
                    """ + is_to_compute_issues_count + """
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
                               timelineItems(itemTypes: [CLOSED_EVENT, REFERENCED_EVENT, CROSS_REFERENCED_EVENT, CONNECTED_EVENT] first: """ + str(TIMELINE_SIZE) + """) {
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
                                                   commits(first:""" + str(NUMBER_OF_COMMITS_WITHIN_PULL_REQUEST) + """) {
                                                     edges {
                                                       node {
                                                        commit {
                                                          commitUrl
                                                          messageBodyHTML
                                                          messageHeadline
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
                                                     messageBodyHTML
                                                     messageHeadline
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
                                        messageBodyHTML
                                        messageHeadline
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
                                          messageBodyHTML
                                          messageHeadline
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
                                          commits(first:""" + str(NUMBER_OF_COMMITS_WITHIN_PULL_REQUEST) + """) {
                                            edges {
                                              node {
                                                commit {
                                                  commitUrl
                                                  messageBodyHTML
                                                  messageHeadline
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
                                            messageBodyHTML
                                            messageHeadline
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
                                          commits(first:""" + str(NUMBER_OF_COMMITS_WITHIN_PULL_REQUEST) + """) {
                                            edges {
                                              node {
                                                commit {
                                                  commitUrl
                                                  messageBodyHTML
                                                  messageHeadline
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
                                            messageBodyHTML
                                            messageHeadline
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
    return issues_query


def _form_graphql_query_for_pull_requests(repo_path,
                                          params):
    page_info = "after:\"" + params['cursor'] + "\"" if 'cursor' in params else ""
    # https://stackoverflow.com/questions/48116781/github-api-v4-how-can-i-traverse-with-pagination-graphql
    is_to_compute_issues_count = "issueCount" if 'cursor' not in params else ""
    date_range = "closed:" + params['starting_date'] + ".." + params['ending_date']
    pull_request_label = "label:" + params['pull_request_label'] if 'pull_request_label' in params else ""
    batch_size = params['batch_size'] if 'batch_size' in params else BATCH_SIZE
    is_sort = "sort:created-desc" if 'sort' in params else ''

    pull_requests_query = """query {
                search(first: """ + str(batch_size) + """ """ + page_info + """ type: ISSUE, 
                       query: "repo:""" + repo_path + """ """ + is_sort + """ is:pr """ + pull_request_label + """ 
                       state:closed """ + date_range + """ ") {
                    """ + is_to_compute_issues_count + """ 
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    edges {
                      node {
                        ... on PullRequest {
                          headRefOid 
                          baseRefOid
                          title
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
                          commits(first:""" + str(NUMBER_OF_COMMITS_WITHIN_PULL_REQUEST) + """) {
                            edges {
                              node {
                                  commit {
                                    commitUrl
                                    messageBodyHTML
                                    messageHeadline
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
                            messageBodyHTML
                            messageHeadline
                            status {
                               state
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
                  resetAt
                  remaining
                }
            }"""
    return pull_requests_query


def _form_graphql_query_for_repos_info(repo_path,
                                       params):
    repo_owner, repo_name = repo_path.split('/')
    repo_query = """query {
            repository(owner:\"""" + repo_owner + """\", name:\"""" + repo_name + """\") {
              refs(refPrefix: "refs/tags/") {
                 totalCount
              }
              milestones {
                 totalCount
              }
              rebaseMergeAllowed
              repositoryTopics(first:20) {
                 edges {
                    node {
                       topic {
                         name
                       }
                    }
                 }
              }
              squashMergeAllowed
            }
            rateLimit {
                  limit
                  cost,
                  nodeCount,
                  resetAt
                  remaining
            }
    }"""
    return repo_query


def _form_graphql_query_for_repo_pull_requests_count(repo_path,
                                                     params):
    date_range = "created:" + params['starting_date'] + ".." + params['ending_date']

    pull_requests_count_query = """query {
                    search(type: ISSUE query: "repo:""" + repo_path + """ is:pr """ + date_range + """ ") {
                        issueCount
                    }
                    rateLimit {
                      limit
                      cost,
                      nodeCount,
                      resetAt
                      remaining
                    }
                }"""
    return pull_requests_count_query


def fetch_github_paged_graphql_api_data(repo_path,
                                        params):
    query_former = {'issue': _form_graphql_query_for_issues,
                    'pull_request': _form_graphql_query_for_pull_requests,
                    'repository': _form_graphql_query_for_repos_info,
                    'repository_pull_requests_count': _form_graphql_query_for_repo_pull_requests_count}
    api_endpoint = GITHUB_ROOT_ENDPOINT + "/graphql"
    headers = {"Authorization": "token " + params['token']}
    if params['query_type'] in query_former:
        query_params = {'query': query_former[params['query_type']](repo_path,
                                                                    params=params)}
    else:
        raise RuntimeError("query_type is not specified")

    for number_of_trial_queries in range(MAX_NUMBER_OF_TRIAL_QUERIES):
        api_request_status_code, api_results = _fetch_github_graphql_api_data(api_endpoint,
                                                                              query_params=query_params,
                                                                              headers=headers)

        if api_request_status_code != 200:
            if number_of_trial_queries < MAX_NUMBER_OF_TRIAL_QUERIES - 1:
                time.sleep(TIMEOUT_TIME)
            else:
                raise RuntimeError('API data could not be fetched')
        else:
            if 'errors' in api_results:
                print(f'Error when processing repo {repo_path}:', api_results['errors'])
                if number_of_trial_queries < MAX_NUMBER_OF_TRIAL_QUERIES - 1:
                    time.sleep(TIMEOUT_TIME)
                else:
                    raise RuntimeError('API data could not be fetched. All trials were unsuccessful')
            else:
                break

    close_to_be_exceeding_limit, delay_to_wait_for_next_window = _is_approaching_api_limit(api_results)
    if close_to_be_exceeding_limit:
        print('API limit is about to be exceeded. Wait for next time window to open.')
        time.sleep(int(delay_to_wait_for_next_window) + 2)

    if api_results['data']['rateLimit']['nodeCount'] > 0.95 * API_LIMIT_FOR_NUMBER_OF_NODES:
        print('Maximal limit on the number of query nodes is about to be exceeded.')
        print('Please decrease either query batch size or length of the timeline')

    if params['query_type'] in ['repository', 'repository_pull_requests_count']:
        return api_results['data']['repository' if params['query_type'] == 'repository' else 'search']
    else:
        return {
                  'page_data': api_results['data']['search'],
                  'page_info': _compute_pagination_info_from_graphql_page(api_results,
                                                                          first_page='cursor' not in params)
               }

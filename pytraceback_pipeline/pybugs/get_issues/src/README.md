# Functions for collecting issues from Github repositories API



## Module `utils_api4.py`

The module contains basic functions to query Github API 4.0.
It includes the following functions:
* `_fetch_github_graphql_api_data`: core function to query Github API
* `_compute_pagination_info_from_graphql_page`: extracts a pointer to the next page if it exists and the total number of pages for the query
* `_is_approaching_api_limit`: controls approaching to API queries limit
* `_get_graphql_api_limit_consumption`: extracts consumption of API quotes
* `_form_graphql_query_for_issues`: forms GraphQL query for a repository to get its relevant issues info
* `_form_graphql_query_for_pull_requests`: forms GraphQL query for a repository to get its relevant pull requests info
* `_form_graphql_query_for_repos_info`: forms a GrapgQL query to mine repositories tags and releases counts
* `_form_graphql_query_for_repo_pull_requests_count`: forms a GrapgQL query to mine pull requests counts within a specified date period
* `fetch_github_paged_graphql_api_data`: actually queries Github API for a given purpose

## Module `utils.py`

Serves the same purpose as the module above but employs Github API 3. It includes the following functions:
* `_fetch_github_api_data`: core function to query Github API
* `_compute_pagination`: extracts total number of pages for a given query and the current page number
* `fetch_github_paged_api_data`: actually queries Github API

## Module `extract_bug_fixing_info_from_issue_text.py`

It contains function to extract bug reports, traceback error messages, 
source code pieces, closing and referencing pull requests and commits from issues web pages HTML.

* `_extract_pull_requests_refs`: extracts pull requests from issue web page HTML
* `_extract_commits_refs`: the same as above but for commits
* `_remove_unnecessary_symbols`: filters irrelevant symbols from HTML
* `_contains_word_reproducing`: checks a source code chunks in bug reports are error reproducing
* `_extract_source_code_n_error_messages`: extracts source code and error messages from HTML
* `_triage_source_code_n_error_messages`: sorts mined source code pieces and source code
* `_extract_source_code_from_gist_id`: extracts source code pieces from Github gists ids
* `_extract_source_code_from_gist_refs`: higher level function that extracts gists ids from issue HTML andmines source code and error messages
* `get_commits_n_pull_requests_refs`: higher level function that extracts commits and pull requests info from issue web pages
* `def get_source_code_n_error_messages(issue_bodyHTML)`: higher level function for extracting source code and error messages



## Module `form_issues_datasets_api4.py`

Forms datasets with the information about Github issues and pull requests, given repository name with owner.
It contains the following functions:
* `_filter_relevant_issues`: removes issues with irrelevant labels (dependency, compatibility etc)
* `_parse_api_results`: convetts API results from json to pandas dataframe
* `_extract_bug_reports`: extracts source code pieces (perhaps, error reproducing source code) and traceback error reports from API query results
* `_extract_issue_labels`: extracts issues labels from API query results
* `_extract_referencing_commits`: extracts an information about commits from API query results, which reference an issue
* `_extract_closing_commits`: extracts an information about commits from API query results, closing an issue
* `_extract_closing_PRs`: extracts an information about pull requests from API query results, closing an issue
* `_extract_related_PRs`: extracts an information about pull requests from API query results, mentioning or linked to an issue
* `_extract_PRs_for_referencing_commits`: extracts an information about pull requests from API query results, associated with a given commit
* `_is_issue_irrelevant`: determines if an issue has a relevant labels
* `_create_raw_dataset_for_date_range_api4`: creates a raw dataset (i.e. with uprocessed API query result json info about commits and pull requests as well as 
without bug reports and some other related info) of either issues or pull requests for a given repository, a date range and a bug label
* `_create_raw_dataset_api4`: creates a raw dataset for a given repository
* `_extract_commits_n_PRs_info`: extracts an information about commits and pull requests from API query result jsons in the raw datasets
* `_extract_additional_bug_fixing_info`: classifies and forms additional information on different types of commits and pull requests
* `infer_bug_label_api4`: extracts all possible labels of issues for a given repository issues labels page
* `create_issues_dataset_api4`: forms a final processed dataset of repository issues
* `create_pull_requests_dataset_api4`: forms a final processed dataset of repository pull requests

## Module `form_issues_datasets.py`

Serves an analogous purpose to the one the module `form_issues_datasets_api4.py` does.
It does not provide any additional info about commits and pull requests. 
Contains the following functions:
* `_get_issue_commits_pull_requests_n_bug_reports`: crawls the issue web page for bug reports, source code pieces, 
related commits and pull requests given an issue web page HTML
* `_get_all_issues_commits_pull_requests_n_bug_reports`: extracts all the above info from many issues
* `_filter_issues_with_related_commits_n_pull_requests`: forms a filtered dataset with issues, containing additional information about linked commits and pull requests
The other functions are analogous to the ones from `form_issues_datasets_api4.py`.





## Description of buggy dataset

The buggy dataset includes three pickle-files, containing buggy snippets from training, validation and test sets as well as 
a folder with source code of all its snippets. Each training or validation pickle-file contains a pandas dataframe with the following columns:
* `before_merge` - implementation of a snippet, containing a bug;
* `after_merge` - implementation of a snippet, being an immediate fix of bugs in the corresponding snippet in the column `before_merge`;
* `filename` - filename where buggy and its corresponding fixed snippets reside;
* `full_file_code_before_merge` - source code of the module, containing the buggy snippet;
* `full_file_code_after_merge` - source code of the module, containing the fixed snippet;
* `function_name` - a complete function/method name;
* `url` - issue url, where bugs are reported in the buggy snippet;
* `source code and errors` - contains parsed source code and error messages from the issue report; 
* `full_traceback` - complete traceback report;
* `traceback_type` - exception type in the traceback report;
* `before_merge_without_docstrings` - implementation of the buggy snippet without its comments and docstrings;
* `after_merge_without_docstrings` - implementation of the fixed snippet without its comments and docstrings;
* `before_merge_docstrings` - docstrings in the buggy snippet;
* `after_merge_docstrings` - docstrings in the fixed snippet;
* `path_to_snippet_before_merge` - path to the file with source code of the buggy snippet; 
* `path_to_snippet_after_merge` - path to the file with source code of the fixed snippet.

Its test pickle-file contains a table with the following columns:
* `before_merge` - as above;
* `after_merge` - as above; 
* `url` - as above 
* `bug type` - a type of a bug ib the snippet according to the known classification of bugs from https://cwe.mitre.org/ 
* `bug description` - textual description of the bug;
* `bug filename` - a filename where the buggy snippet resides;
* `bug function_name` - a complete function/method name;
* `bug lines` - lines ranges in the snippet source code where the bug is supposed to be located;
* `full_traceback` - as above;
* `traceback_type` - as above;
* `path_to_snippet_before_merge` - as above;
* `path_to_snippet_after_merge` - as above.

## Description of correct dataset

The correct dataset is similarly structured. In distinction to the buggy dataset, source code of the modules, containing snippets, is located
in a separate folder.

The dataset tables have the following columns:
* `before_merge` - implementation of a snippet without bugs, a stable snippet;
* `repo_name` - the repository name with owner where the snippet resides;
* `filename` - as above; 
* `function_name` - as above;
* `path_to_source_file` - path to the file with source code of the module where the snippet is located; 
* `commit` - the last commit where the snippet was changed; 
* `path_to_snippet_before_merge` - path to the file with source code of the snippet.

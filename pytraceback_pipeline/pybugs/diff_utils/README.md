# Utilities for git differences.

There presented files for git differences handling.

For pd.DataFrame with columns: 
```
[    
    'url',
    'all relevant PRs',
    'most relevent PRs',
    'all relevant commits',
    'most relevant commits',
] 
```
where 
- `url` is an URL to github issue for specific repository;
- `pr_type` is a type of pull request which can take one of following values:
    'all relevant PRs' for all pull requests mentioned in the issue and
    'most relevant PRs' for pull requests closing the issue;
- {`all relevant PRs`, `most relevent PRs`} is a list of dictionaries that must contains following keys:
    1. 'url' -- a github pull request URL.
    2. 'merged' -- a flag if the pull request is merged.
    3. 'mergeCommit' -- dictionary with a key 'commitUrl' which is a merge commit URL of the pull request.
- {`all relevant commits`, `most relevant commits`} is a list of dictionaries that must contains following keys:
    1. 'commitUrl' -- a github commit URL.
 
you can get a pandas.DataFrame where each row is associated with one of functions that changed in github issue. 
That row contains following columns:
```
[
    'issue_url',
    'pr_type' (Optional, presented if issues dataframe contains issues resolved in pull requests),
    'pr_url' (Optional, presented if issues dataframe contains issues resolved in pull requests),
    'merge_commit_sha (Optional, presented if issues dataframe contains issues resolved in pull requests)',
    'commit_type' (Optional, presented if issues dataframe contains issues resolved in single commit)',
    'commit_sha' (Optional, presented if issues dataframe contains issues resolved in single commit)',
    'filename',
    'function_name',
    'before_merge',
    'after_merge',
    'full_file_code_before_merge',
    'full_file_code_after_merge',
]
```
where 
- `issue_url` is an URL to github issue for specific repository;
- `pr_type` is a type of pull request associated with function changes, 
    it can take the values 'all relevant PRs' or 'most relevant PRs'. 
    It also can be None if changes of a function was made in a single commit rather than in a pull request;
- `pr_url` is a URL of an associated pull request. It can be None of `pr_type` is None; 
- `merge_commit_sha` is a SHA of a merge commit of an associated pull request. 
    It can be None of `pr_type` is None;
- `commit_type` is a type of commit associated with function changes,
    it can take the values 'all relevant commits', 'most relevant commits'.
    It also can be None if changes of a function was made in a pull request rather than in a single commit;
- `commit_sha`is a SHA of a merge commit of an associated pull request. 
    It can be None of `commit_type` is None;
- `filename` is a name of file where changed function is located; 
- `function_name` is a name of changed function;
- `before_merge` is a function source code before changes; 
- `after_merge` is a function source code after changes;
- `full_file_code_before_merge` is a source code of a full file (where changed function is located) before changes;
- `full_file_code_after_merge` is a source code of a full file (where changed function is located) after changes;
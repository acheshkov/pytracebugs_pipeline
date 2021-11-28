from tokenize import tokenize, untokenize, TokenError
from io import BytesIO
import os
import re
from get_issues.src.form_issues_datasets_api4 import _is_issue_irrelevant
from get_issues.src.extract_bug_fixing_info_from_issue_text import _remove_unnecessary_symbols
from collect_snippets.src.analyze_issues import IRRELEVANT_PR_ISSUE_n_COMMIT_MESSAGE_TOKENS
import pandas as pd

DATA_DIR = os.getenv("HOME") + '/zephyr_data/stable_code/'


def checkSourceCodeSyntax(snippet,
                          print_snippet=False):
    result = []
    try:
        for tok in tokenize(BytesIO(snippet.encode('utf-8')).readline):
            result.append(tok)
        untokenize(result).decode('utf-8')
        return True
    except (TokenError, IndentationError, ValueError) as e:
        print(e)
        if print_snippet:
            print(snippet)
        return False


def compileSourceCode(snippet,
                      print_snippet=False):
    try:
        compile(snippet.strip(), 'file', 'exec')
        return True
    except SyntaxError as e:
        if ('no binding' not in e.msg) and ('unexpected indent' not in e.msg) and ('unindent' not in e.msg):
            print(e)
            if print_snippet:
                print(snippet)
            return False
        else:
            return True


def snippetNameContainsTestToken(snippet):
    func_definition_pattern = 'def[\s\\\\]+[\w]+'
    try:
        return 'test' in re.search(func_definition_pattern, snippet.strip()).group(0)[4:]
    except AttributeError:
        print(snippet)
        return False


def filenameContainsTestToken(filename):
    return 'test' in filename


def isSnippetIrrelevant(pr_url,
                        issue_most_relevant_PRs,
                        issue_most_relevant_commits,
                        commit_message,
                        commit_summary,
                        commit_sha,
                        issue_title,
                        issue_labels):

    if _is_issue_irrelevant(issue_labels):
        return True

    for irrelevant_token in IRRELEVANT_PR_ISSUE_n_COMMIT_MESSAGE_TOKENS:
        if (irrelevant_token in commit_message) or (irrelevant_token in commit_summary): # or  \ (irrelevant_token in issue_title):
            return True

    for pr_info in issue_most_relevant_PRs:
        if pr_info['url'] == pr_url:
            for irrelevant_token in IRRELEVANT_PR_ISSUE_n_COMMIT_MESSAGE_TOKENS:
                if (irrelevant_token in pr_info['title']) or ( irrelevant_token in _remove_unnecessary_symbols(pr_info['bodyHTML'])):
                    return True
            if len(pr_info['linked_issues']) > 2:
                return True

    #if len(str(commit_sha)) > 0:
    #    for commit_info in issue_most_relevant_commits:
    #        if str(commit_sha) in commit_info['commitUrl']:
    #            if len(commit_info['linked_issues']) > 1:
    #                return True

    return False


if __name__ == '__main__':
    chunk_size = 10 ** 6
    i = 0

    for data in pd.read_csv(DATA_DIR + 'top_proj_code_samples.csv',
                            chunksize=chunk_size):
        data['syntax_correct'] = data['before_merge'].apply(compileSourceCode)
        data.to_pickle(DATA_DIR + 'stable_code_' + str(i) + '.pickle')
        i += 1

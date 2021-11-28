import re
import string
from .extract_bug_fixing_info_from_issue_text import _remove_unnecessary_symbols


def _extract_issues_web_links(bodyHTML,
                              return_preceding_tokens,
                              number_of_preceding_tokens_to_consider):
    issues_links_to_preceding_tokens = dict()

    any_symbol_pattern = '.+?'
    first_raw_issues_link_pattern = ('(<a class="issue-link js-issue-link"' + any_symbol_pattern +
                                     'href="https://github.com/[\\w' + string.punctuation + ']+' +
                                     '/issues/[\\d]+"' + any_symbol_pattern + '</a>)')
    second_raw_issues_link_pattern = ('(<a href="https://github.com/[\\w' + string.punctuation + ']+' +
                                      '/issues/[\\d]+"' + any_symbol_pattern + '</a>)')
    raw_issues_link_pattern = first_raw_issues_link_pattern + '|' + second_raw_issues_link_pattern
    issue_link_pattern = 'href="https://github.com/[\\w' + string.punctuation + ']+' + '/issues/[\\d]+"'

    try:
        starting_position_of_text = 0
        for content in re.finditer(raw_issues_link_pattern,
                                   bodyHTML):
            raw_issue_link = content.group(0)
            #print('*** ' + raw_issue_link)
            cleaned_preceding_text = _remove_unnecessary_symbols(bodyHTML[max(0, starting_position_of_text - 2000):
                                                                          content.start(0)].lower())
            tokens_preceding_issues_link = cleaned_preceding_text.split()
            close_tokens_preceding_issues_link = tokens_preceding_issues_link[-number_of_preceding_tokens_to_consider:]
            for issue_link in re.finditer(issue_link_pattern,
                                          raw_issue_link):
                cleaned_issue_link = issue_link.group(0)[6:-1]
                if cleaned_issue_link in issues_links_to_preceding_tokens:
                    issues_links_to_preceding_tokens[cleaned_issue_link].append(close_tokens_preceding_issues_link)
                else:
                    issues_links_to_preceding_tokens[cleaned_issue_link] = [close_tokens_preceding_issues_link]
            # print(tokens_preceding_issues_link)

            starting_position_of_text = content.end(0)
    except AttributeError as e:
        print(e)

    if return_preceding_tokens:
        return issues_links_to_preceding_tokens
    else:
        return {'issues links': issues_links_to_preceding_tokens.keys()}

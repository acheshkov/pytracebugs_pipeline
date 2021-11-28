import re
import string
from .local_settings import *
from .utils import fetch_github_paged_api_data


def _extract_pull_requests_refs(issue_bodyHTML):
    pull_requests_info = []

    any_symbol_pattern = '.+?'
    string_pattern = '[\\w' + string.punctuation + ']+'
    web_link_pattern = 'href="' + string_pattern + '"'

    try:
        closing_pull_requests_pattern = ('successfully merging a pull request may close this issue' +
                                         any_symbol_pattern + 'form')
        closing_pull_requests_raw_info = re.search(closing_pull_requests_pattern,
                                                   issue_bodyHTML,
                                                   flags=re.DOTALL).group(0)
        for raw_web_link in re.finditer(web_link_pattern,
                                        closing_pull_requests_raw_info):
            pull_requests_info.append(raw_web_link.group(0)[6:-1])
    except AttributeError as e:
        print(e)
    return pull_requests_info


def _extract_commits_refs(issue_bodyHTML):
    commits_info = []

    any_symbol_pattern = '.+?'
    string_pattern = '[\\w' + string.punctuation + ']+'
    web_link_pattern = 'href="' + string_pattern + '"'

    first_commit_subpattern = '([\\s]+to' + any_symbol_pattern + ')'
    second_commit_subpattern = '([\\s]+)'
    short_commit_pattern = ('a commit(' + first_commit_subpattern +
                            '|' + second_commit_subpattern + ')' +
                            'that referenced[\\s]+this issue' +
                            any_symbol_pattern + web_link_pattern)
    try:
        for commit_raw_info in re.finditer(short_commit_pattern,
                                           issue_bodyHTML,
                                           flags=re.DOTALL):
            commit_short_link = re.search(web_link_pattern,
                                          commit_raw_info.group(0)).group(0)[18:-1]
            commit_pattern = ('data-url=' + string_pattern +
                              'commit/' + commit_short_link +
                              string_pattern + '"')
            commit_web_link = re.search(commit_pattern,
                                        issue_bodyHTML).group(0)[10:-1]
            commits_info.append(commit_web_link)
    except AttributeError as e:
        print(e)
    return commits_info


def _remove_unnecessary_symbols(html_text):
    compiled_html_pattern = re.compile('<.*?>')
    text = re.sub(compiled_html_pattern, '', html_text).strip()

    cleaned_text = re.sub('&lt;', '<', text)
    cleaned_text = re.sub('&gt;', '>', cleaned_text)

    processed_text_lines = []
    command_prompt_symbol = ">"
    for line in cleaned_text.split('\n'):
        processed_text_lines.append(line.lstrip(command_prompt_symbol).strip())
    return '\n'.join(processed_text_lines)


def _contains_word_reproducing(text_tokens):
    number_of_preceding_tokens_to_consider = 15
    for token in text_tokens[-number_of_preceding_tokens_to_consider:]:
        if ('reproduc' in token.lower()) or ('replicat' in token.lower()):
            return True
    return False


def _extract_source_code_n_error_messages(issue_bodyHTML):
    source_code_error_messages_n_other = []
    any_symbol_pattern = '.+?'
    source_code_n_error_message_pattern = ('(<div class="highlight highlight-source-python">' +
                                           any_symbol_pattern +
                                           '/div>)')
    error_message_n_code_output_pattern = ('(<pre><code>' +
                                           any_symbol_pattern +
                                           '</code></pre>)')
    error_message_pattern = ('(<div class="highlight highlight-text-python-traceback">' +
                             any_symbol_pattern +
                             '/div>)')
    another_source_code_pattern = (r'(<pre lang="\[python\]"><code>' +
                                   any_symbol_pattern +
                                   r'</code></pre>)')
    try:
        code_n_error_n_output_pattern = (source_code_n_error_message_pattern +
                                         '|' +
                                         error_message_n_code_output_pattern +
                                         '|' +
                                         error_message_pattern +
                                         '|' +
                                         another_source_code_pattern)
        starting_position_of_text = 0
        for content in re.finditer(code_n_error_n_output_pattern,
                                   issue_bodyHTML,
                                   flags=re.DOTALL):
            code_n_error_n_output = content.group(0)
            if (code_n_error_n_output.startswith('<div class="highlight highlight-source-python') or
                    code_n_error_n_output.startswith('<pre lang="[python]"')):
                processed_piece = {
                    'piece_type': 'source code',
                    'piece_content': _remove_unnecessary_symbols(code_n_error_n_output)
                                   }
            elif code_n_error_n_output.startswith('<div class="highlight highlight-text-python-traceback'):
                processed_piece = {
                    'piece_type': 'error message',
                    'piece_content': _remove_unnecessary_symbols(code_n_error_n_output)
                                   }
            else:
                processed_piece = {
                    'piece_type': 'other',
                    'piece_content': _remove_unnecessary_symbols(code_n_error_n_output[11:-13].strip())
                                   }
            is_reproducing_code_piece = \
                _contains_word_reproducing(_remove_unnecessary_symbols(issue_bodyHTML[starting_position_of_text:
                                                                                      content.start(0)]).split())
            starting_position_of_text = content.end(0)
            if is_reproducing_code_piece and (processed_piece['piece_type'] == 'source code'):
                processed_piece['piece_type'] = 'reproducing source code'
            source_code_error_messages_n_other.append(processed_piece)
    except AttributeError as e:
        print(e)
    return source_code_error_messages_n_other


def _triage_source_code_n_error_messages(source_code_error_messages_n_other):
    triaged_source_code_error_messages_n_other = []
    for piece in source_code_error_messages_n_other:
        if 'traceback (most recent call last)' in piece['piece_content'].lower():
            triaged_source_code_error_messages_n_other.append({'piece_type': 'error message',
                                                               'piece_content': piece['piece_content']})
        else:
            triaged_source_code_error_messages_n_other.append(piece)
    return triaged_source_code_error_messages_n_other


def _extract_source_code_from_gist_id(gist_id):
    params = {'username': USERNAME[0],
              'token': GITHUB_TOKENS[0],
              'scope': 'gist'}
    gist_path = "gists/" + gist_id
    gist_info = fetch_github_paged_api_data(gist_path,
                                            params=params,
                                            key_name=None)['query_results']
    gist_source_code_content_columns = [col for col in gist_info.columns
                                        if col.startswith('files') and col.endswith('.py.content')]
    gist_source_code = [{'piece_type': 'source code',
                         'piece_content': gist_info.loc[0, col]} for col in gist_source_code_content_columns]

    gist_files_content_columns = [col for col in gist_info.columns
                                  if col.startswith('files') and col.endswith('.content')]
    gist_error_messages = [{'piece_type': 'error message',
                            'piece_content': gist_info.loc[0, col]} for col in gist_files_content_columns
                           if 'traceback (most recent call last)' in gist_info.loc[0, col].lower()]
    return gist_source_code + gist_error_messages


def _extract_source_code_from_gist_refs(issue_bodyHTML):
    gist_source_code = []
    any_symbol_pattern = '.+?'
    gist_reference_pattern = ("href=\"https://gist.github.com/" +
                              any_symbol_pattern + "\"")
    try:
        starting_position_of_text = 0
        for content in re.finditer(gist_reference_pattern,
                                   issue_bodyHTML,
                                   flags=re.DOTALL):
            gist_id = content.group(0).split('/')[-1].strip("\"")
            source_code_from_gist_id = _extract_source_code_from_gist_id(gist_id)

            is_reproducing_code_piece = \
                _contains_word_reproducing(_remove_unnecessary_symbols(issue_bodyHTML[starting_position_of_text:
                                                                                      content.start(0)]).split())
            starting_position_of_text = content.end(0)
            if is_reproducing_code_piece:
                for source_code_piece in source_code_from_gist_id:
                    gist_source_code.append(
                        {
                            'piece_type': 'reproducing source code',
                            'piece_content': source_code_piece['piece_content']
                        }
                    )
            else:
                gist_source_code.extend(source_code_from_gist_id)
    except AttributeError as e:
        print(e)
    return gist_source_code


def get_commits_n_pull_requests_refs(issue_bodyHTML):
    return {'pull_requests': _extract_pull_requests_refs(issue_bodyHTML),
            'commits': _extract_commits_refs(issue_bodyHTML)}


def get_source_code_n_error_messages(issue_bodyHTML):
    return (_triage_source_code_n_error_messages(_extract_source_code_n_error_messages(issue_bodyHTML)) +
            _extract_source_code_from_gist_refs(issue_bodyHTML))

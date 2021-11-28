import unittest
from requests_html import HTMLSession
from get_issues.src.extract_bug_fixing_info_from_issue_text import get_source_code_n_error_messages, \
    _extract_pull_requests_refs, _extract_commits_refs


class TestParsingIssueText(unittest.TestCase):
    def test__extract_pull_requests_refs(self):
        test_issue_web_links = [
            'https://github.com/scikit-learn/scikit-learn/issues/18815',
            'https://github.com/scikit-learn/scikit-learn/issues/19400',
            'https://github.com/scikit-learn/scikit-learn/issues/19228'
        ]
        test_expected_results = [
                                 ['/scikit-learn/scikit-learn/pull/18820'],
                                 ['/scikit-learn/scikit-learn/pull/19407'],
                                 ['/scikit-learn/scikit-learn/pull/19234', '/scikit-learn/scikit-learn/pull/19232']
                                ]
        web_session = HTMLSession()
        for test_issue_web_link, test_expected_result in zip(test_issue_web_links,
                                                             test_expected_results):
            issue_bodyHTML = web_session.get(test_issue_web_link).text
            test_actual_result = _extract_pull_requests_refs(issue_bodyHTML.lower())
            self.assertEqual(set(test_expected_result),
                             set(test_actual_result))

    def test__extract_commits_refs(self):
        test_issue_web_links = [
            'https://github.com/pandas-dev/pandas/issues/38714',
            'https://github.com/pandas-dev/pandas/issues/38906'
        ]
        test_expected_results = [
            ['/simonjayhawkins/pandas/commit/1f3fa0cb0de5b459b8a0d29e7c8d2ca78dce0e5e/_render_node/commit/condensed'],
            ['/batterseapower/pandas/commit/5d8cc7a5a74ac366178ef79033af47ebd7a1a7ba/_render_node/commit/condensed',
             '/batterseapower/pandas/commit/66be3eb330f0a357e4dbf7d327d050078a2cc383/_render_node/commit/condensed',
             '/batterseapower/pandas/commit/fdb6a5af1eea1a4c0c5d1d1c9d85470af6bf34ed/_render_node/commit/condensed',
             '/batterseapower/pandas/commit/f4eb93ca9cc8ae440e2f32cf39707e16f81b67fd/_render_node/commit/condensed',
             '/batterseapower/pandas/commit/497dcbb34e9a1e9092b0cd4f31364907e354deea/_render_node/commit/condensed']
        ]
        web_session = HTMLSession()
        for test_issue_web_link, test_expected_result in zip(test_issue_web_links,
                                                             test_expected_results):
            issue_bodyHTML = web_session.get(test_issue_web_link).text
            test_actual_result = _extract_commits_refs(issue_bodyHTML.lower())
            self.assertEqual(set(test_expected_result),
                             set(test_actual_result))

    def test_get_source_code_n_error_messages(self):
        test_issue_web_links = [
            'https://github.com/pandas-dev/pandas/issues/38714',
            'https://github.com/pandas-dev/pandas/issues/38906'
        ]
        test_expected_results = [
                                 [
                                  {
                                      'piece_type': 'source code',
                                      'piece_content': ("""d = pd.DataFrame({'a':[1]*2188})\n""" +
                                                        """p = R"T:\\test.csv.zip"  # replace with available path\n""" +
                                                        """d.to_csv(p)\npd.read_csv(p)""")
                                  },
                                  {
                                      'piece_type': 'source code',
                                      'piece_content': ("""import pandas as pd\nimport io\nf = io.BytesIO()\n""" +
                                                        """d = pd.DataFrame({'a':[1]*5000})\n""" +
                                                        """d.to_csv(f, compression='zip')\nf.seek(0)\n""" +
                                                        """pd.read_csv(f, compression='zip')""")
                                  },
                                  {
                                      'piece_type': 'source code',
                                      'piece_content': ("""import pandas as pd\nimport io\nf = io.BytesIO()\n""" +
                                                        """d = pd.DataFrame({'a':[1]*5000})\n""" +
                                                        """d.to_csv(f, compression='zip')\nf.seek(0)\n"""
                                                        """pd.read_csv(f, compression='zip')""")
                                  }
                                 ],
                                 [
                                  {
                                     'piece_type': 'source code',
                                     'piece_content': ("""pd.DataFrame(columns=pd.CategoricalIndex([]), """ +
                                                       """index=['K']).reindex""" +
                                                       """(columns=pd.CategoricalIndex(['A', 'A']))""")
                                  },
                                  {
                                      'piece_type': 'source code',
                                      'piece_content': ("""pd.DataFrame(columns=pd.Index([]), """ +
                                                        """index=['K']).reindex""" +
                                                        """(columns=pd.CategoricalIndex(['A', 'A']))\n""" +
                                                        """pd.DataFrame(columns=pd.CategoricalIndex([]), """ +
                                                        """index=['K']).reindex""" +
                                                        """(columns=pd.CategoricalIndex(['A', 'B']))\n""" +
                                                        """pd.DataFrame(columns=pd.CategoricalIndex([]), """ +
                                                        """index=['K']).reindex(columns=pd.CategoricalIndex([]))""")
                                  },
                                  {
                                      'piece_type': 'error message',
                                      'piece_content': r"""Traceback (most recent call last):
File "<stdin>", line 1, in <module>
File "C:\Users\mboling\Anaconda3\envs\pandastest\lib\site-packages\pandas\util\_decorators.py", line 312, in wrapper
return func(*args, **kwargs)
File "C:\Users\mboling\Anaconda3\envs\pandastest\lib\site-packages\pandas\core\frame.py", line 4173, in reindex
return super().reindex(**kwargs)
File "C:\Users\mboling\Anaconda3\envs\pandastest\lib\site-packages\pandas\core\generic.py", line 4806, in reindex
return self._reindex_axes(
File "C:\Users\mboling\Anaconda3\envs\pandastest\lib\site-packages\pandas\core\frame.py", line 4013, in _reindex_axes
frame = frame._reindex_columns(
File "C:\Users\mboling\Anaconda3\envs\pandastest\lib\site-packages\pandas\core\frame.py", line 4055, in _reindex_columns
new_columns, indexer = self.columns.reindex(
File "C:\Users\mboling\Anaconda3\envs\pandastest\lib\site-packages\pandas\core\indexes\category.py", line 448, in reindex
new_target, indexer, _ = result._reindex_non_unique(np.array(target))
File "C:\Users\mboling\Anaconda3\envs\pandastest\lib\site-packages\pandas\core\indexes\base.py", line 3589, in _reindex_non_unique
new_indexer = np.arange(len(self.take(indexer)))
File "C:\Users\mboling\Anaconda3\envs\pandastest\lib\site-packages\pandas\core\indexes\base.py", line 751, in take
taken = algos.take(
File "C:\Users\mboling\Anaconda3\envs\pandastest\lib\site-packages\pandas\core\algorithms.py", line 1657, in take
result = arr.take(indices, axis=axis)
IndexError: cannot do a non-empty take from an empty axes."""
                                  }
                                 ]
        ]
        web_session = HTMLSession()
        for test_issue_web_link, test_expected_result in zip(test_issue_web_links,
                                                             test_expected_results):
            issue_bodyHTML = web_session.get(test_issue_web_link).text
            test_actual_result = get_source_code_n_error_messages(issue_bodyHTML)
            self.assertEqual(sorted(test_expected_result, key=lambda x: x['piece_content']),
                             sorted(test_actual_result, key=lambda x: x['piece_content']))


if __name__ == '__main__':
    unittest.main()

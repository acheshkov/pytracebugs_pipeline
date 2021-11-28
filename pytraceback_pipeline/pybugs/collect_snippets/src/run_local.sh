#!/bin/bash
cat $HOME/zephyr_local/filter_buggy_repos/selected_repos/big_list_of_repos_names.csv | xargs -n 2 -P 1 python $HOME/zephyr_local/collect_snippets/src/collect_snippets_for_single_repo.py

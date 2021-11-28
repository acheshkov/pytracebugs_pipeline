#!/bin/bash
#SBATCH --time=20:00:00 -n 6 --mem-per-cpu 4000
cat $HOME/zephyr/filter_buggy_repos/selected_repos/big_list_of_repos_names.csv | xargs -n 2 -P 6 srun -t 10:00:00 -n 1 --mem=4000 python $HOME/zephyr/collect_snippets/src/collect_snippets_for_single_repo.py

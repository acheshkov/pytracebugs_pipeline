#!/bin/bash
#SBATCH --time=20:00:00 -n 36 --mem-per-cpu 4000
cat python_repos_interesting_top.txt | xargs -n 1 -P 36 srun -t 10:00:00 -n 1 --mem=4000 /home/u1333/python3.9/bin/python3.9 repo_get_raw_files.py

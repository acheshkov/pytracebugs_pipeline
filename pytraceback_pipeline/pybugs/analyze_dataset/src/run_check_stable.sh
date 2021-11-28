#!/bin/bash
#SBATCH --time=20:00:00 -n 6 --mem-per-cpu 4000
srun -t 10:00:00 -n 1 --mem=4000 python $HOME/zephyr/analyze_dataset/src/check_snippets.py

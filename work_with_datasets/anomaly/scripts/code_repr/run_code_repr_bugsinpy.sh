sbatch --mem=30000 -t 06:00:00 --wrap="srun -u python -u code_representation.py --data bugsinpy --repr gcb"

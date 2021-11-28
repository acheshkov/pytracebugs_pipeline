sbatch --gres=gpu:k40m:1 --mem=30000 -t 01:00:00 --wrap="srun -u python -u code_representation.py --data pytest --limit 10"

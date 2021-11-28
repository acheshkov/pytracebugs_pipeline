sbatch -p v100 --gres=gpu:v100:1 --mem=30000 -t 00:10:00 --wrap="srun -u python -u code_representation.py --data pytest --gpu --limit 10"
# srun -p v100 --gres=gpu:v100:1 --mem=30000 -t 00:10:00 -o _repr_test.out -e _repr_test.err python -u code_representation.py --data pytest --gpu --limit 10

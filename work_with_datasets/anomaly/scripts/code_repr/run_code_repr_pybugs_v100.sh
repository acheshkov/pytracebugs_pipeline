sbatch -p v100 --gres=gpu:v100:1 --mem=30000 -t 06:00:00 --wrap="srun -u python -u code_representation.py --data pybugs --gpu --repr gcb"
#srun -p v100 --gres=gpu:v100:1 --mem=30000 -t 20:00:00 -o _repr.out -e _repr.err python -u code_representation.py --gpu

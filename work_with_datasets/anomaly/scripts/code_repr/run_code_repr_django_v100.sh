sbatch -p v100 --gres=gpu:v100:1 --mem=30000 -t 06:00:00 --wrap="srun -u python -u /home/u1018/zephyr/anomaly/code_representation.py --data django --fragment_type function --gpu --repr gcb"

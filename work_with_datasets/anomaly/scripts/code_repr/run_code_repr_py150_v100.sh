sbatch -p v100 --gres=gpu:v100:1 --mem=30000 -t 06:00:00 --wrap="srun -u python -u /home/u1018/zephyr/anomaly/code_representation.py --data py150 --fragment_type function --fragment_wsize 9 --fragment_overlap --gpu --repr gcb"

# TEST
#sbatch --gres=gpu:k40m:1 --mem=30000 -t 00:30:00 --wrap="srun -u python -u /home/u1018/zephyr/anomaly/code_representation.py --data py150 --fragment_type function --fragment_wsize 9 --fragment_overlap --repr gcb --limit 100"

sbatch --mem=30000 -t 06:00:00 --wrap="srun -u python -u /home/u1018/zephyr/anomaly/dataloader.py --data bugsinpy"

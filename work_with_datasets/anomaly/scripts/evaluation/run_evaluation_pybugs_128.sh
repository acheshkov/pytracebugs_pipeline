sbatch --mem=30000 -t 12:00:00 --wrap="srun -u python -u /home/u1018/zephyr/anomaly/anomalist.py --data pybugs --aux_size 314 --hidden_size 128 --checkpoint /home/u1018/zephyr/anomaly/data/model/20210519_205501_128/vae_278_961169.pth"

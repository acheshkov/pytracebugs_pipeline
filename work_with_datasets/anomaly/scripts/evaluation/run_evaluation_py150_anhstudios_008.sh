sbatch --mem=30000 -t 12:00:00 --wrap="srun -u python -u /home/u1018/zephyr/anomaly/anomalist.py --data py150 --rep anhstudios --split 2 --aux_size 78 --hidden_size 8 --checkpoint /home/u1018/zephyr/anomaly/data/model/20210815_171230_008/vae_467_50826.pth"
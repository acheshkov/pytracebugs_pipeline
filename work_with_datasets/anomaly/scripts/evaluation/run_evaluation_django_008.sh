sbatch --mem=30000 -t 12:00:00 --wrap="srun -u python -u /home/u1018/zephyr/anomaly/anomalist.py --data django --split 2 --aux_size 78 --hidden_size 8 --checkpoint /home/u1018/zephyr/anomaly/data/model/django/20210824_150623_008/vae_364_64521.pth"
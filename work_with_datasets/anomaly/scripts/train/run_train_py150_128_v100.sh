sbatch -p v100 --gres=gpu:v100:1 --mem=30000 -t 12:00:00 --wrap="srun -u python -u /home/u1018/zephyr/anomaly/vae_trainer.py --data py150 --label None --split 0 --aux_size 314 --hidden_size 128 --epochs 999 --lr 0.001 --gpu --prefix 128"
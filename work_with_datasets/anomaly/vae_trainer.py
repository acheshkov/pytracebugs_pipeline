import torch
import pickle
import argparse
import numpy as np
from pathlib import Path
import torch.optim as optim
from torch.optim.lr_scheduler import LambdaLR

import utils
from ml_utils import calculate_mean_std, normalize
from dataloader import Dataloader
from vae import VAESimplex, loss_function


class VAETrainer:

    def __init__(self, device_id, input_size=768, aux_size=400, hidden_size=20, lr=1e-3, prefix='', verbose=True):
        self.device = torch.device(device_id)
        self.verbose = verbose

        self.model = VAESimplex(input_size=input_size, aux_size=aux_size, hidden_size=hidden_size).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self.mean = None
        self.std = None

        self.prefix = prefix
        self.checkpoint_dir = None

    def load_checkpoint(self, scaler_path, vae_path, verbose):
        self.model.load_state_dict(torch.load(vae_path, map_location=self.device))
        with open(scaler_path, 'rb') as f:
            self.mean, self.std = pickle.load(f)

    def run(self, dataloader, epochs):
        self.prefix = utils.now() + f'_{self.prefix}' if self.prefix else ''
        utils.log(label='run', message=f'beg {self.prefix}', enable=self.verbose)

        self.checkpoint_dir = Path(self.prefix)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        utils.log(label='run', message=f'checkpoint dir: {self.checkpoint_dir}', enable=self.verbose)

        X_train = self.preprocess_data(dataloader)
        self.mean, self.std = calculate_mean_std(X_train)

        X_train_norm = normalize(X_train, self.mean, self.std)
        #X_test_norm = normalize(X_test, mean, std)

        train_dataloader = torch.utils.data.DataLoader(X_train_norm, batch_size=128, shuffle=True,  num_workers=1, pin_memory=True)
        #train_dataloader = torch.utils.data.DataLoader(X_train_norm, batch_size=128, shuffle=True,  num_workers=4, pin_memory=True)
        #test_dataloader = torch.utils.data.DataLoader(X_test_norm , batch_size=32 , shuffle=False, num_workers=4)

        loss = self.train(train_dataloader, epochs, save=True)
        return loss

    def train(self, train_dataloader, epochs, save=True):
        utils.log(label='train', message=f'beg, epochs: {epochs}', enable=self.verbose)

        #lambda1 = lambda epoch: epoch // 30
        #lambda2 = lambda epoch: 0.95 ** epoch
        #scheduler = LambdaLR(self.optimizer, lr_lambda=[lambda1, lambda2])

        lambda1 = lambda epoch: 0.95 ** epoch
        scheduler = LambdaLR(self.optimizer, lr_lambda=lambda1)


        for epoch in range(epochs):
            self.model.train()
            loss = 0
            for batch in train_dataloader: 
                batch = batch.float().to(self.device)
        
                self.optimizer.zero_grad()
        
                reconstructed_batch, mu, logvar = self.model(batch)
        
                train_loss = loss_function(reconstructed_batch, batch, mu, logvar)
                train_loss.backward()
                self.optimizer.step()
        
                loss += train_loss.item()
       
            loss = loss / len(train_dataloader)
            utils.log(label='train', message=f'{epoch}/{epochs}, lr: {self.optimizer.param_groups[0]["lr"]}, loss: {loss:.6f}', enable=self.verbose)

            self.save(f'{epoch:03d}_{int(loss)}')

            scheduler.step()
        return loss

    def preprocess_data(self, dataloader):
        X_train = dataloader
        return X_train

    def save(self, label=''):
        scaler_path = self.checkpoint_dir / Path(f'scaler_{label}.pickle')
        pickle.dump((self.mean, self.std), open(scaler_path, 'wb'))
        utils.log(label='save', message=f'save scaler: {scaler_path}', enable=self.verbose)

        vae_path = self.checkpoint_dir / Path(f'vae_{label}.pth')
        torch.save(self.model.state_dict(), vae_path)
        utils.log(label='save', message=f'save vae: {vae_path}', enable=self.verbose)

        return scaler_path, vae_path


def main():

    parser = argparse.ArgumentParser(description='')                                                                                                                     
    parser.add_argument('--data', help='choose data', type=str, choices=['py150', 'bugsinpy', 'pybugs', 'django'], required=True)
    parser.add_argument('--rep',  help='choose repository', type=str, default='', required=False)
    parser.add_argument('--label', help='label', type=str, choices=['None', 'before', 'after'], default='None')
    parser.add_argument('--split', help='split', type=int, choices=[0, 1, 2], required=True)
    parser.add_argument('--aux_size', help='vae aux_size', type=int, choices=range(1000), default=400)
    parser.add_argument('--hidden_size', help='vae hidden_size', type=int, choices=range(400), default=20)
    parser.add_argument('--lr', help='learning rate', type=float, default=1e-3)
    parser.add_argument('--epochs', help='epochs', type=int, choices=range(1000), default=100)
    parser.add_argument('--gpu', help='use gpu', action='store_true')
    parser.add_argument('--checkpoint', help='checkpoint', type=str, default='')
    parser.add_argument('--prefix', help='checkpoint', type=str, default='')
 
    args = parser.parse_args()
    label = args.label if args.label != 'None' else None
    split = args.split

    data_dir = Path('/home/u1018/zephyr/anomaly/data')
    # line-level
    #prefices = {'py150'   : str(data_dir / Path('py150_gcb_lines')/ Path('20210706_023937_py150_')),
    # fragment-level
    prefices = {'py150'   : str(data_dir / Path('py150_gcb')    / Path('20210512_121352_py150_')),
                'pybugs'  : str(data_dir / Path('pybugs_gcb')   / Path('20210512_121239_pybugs_')),
                'bugsinpy': str(data_dir / Path('bugsinpy_gcb') / Path('20210512_121228_bugsinpy_')),
                'django'  : str(data_dir / Path('django_gcb')   / Path('20210824_105519_django_')),
               }
    device_id = 'cpu' if not args.gpu else 'cuda:0'
    checkpoint = Path(args.checkpoint) if args.checkpoint else ''

    verbose = True
    
    utils.log(label='main', message=f'sha : {utils.githash()}', enable=verbose)
    utils.log(label='main', message=f'args: {parser.parse_args()}', enable=verbose)

    utils.log(label='main', message=f'beg dataloader: {args.data} | {args.rep} | {label} | {split}', enable=verbose)
    dataloader = Dataloader(prefix=prefices[args.data], path_prefix=args.rep, label=label, split=split, skip_truncated=True, embeddings_only=True)
    utils.log(label='main', message=f'end, size: {len(dataloader)}', enable=verbose)

    if len(dataloader) == 0:
        utils.log(label='main', message=f'FATAL ERROR, empty dataloader', enable=verbose)
        return

    utils.log(label='main', message=f'beg init VAETrainer', enable=verbose)
    trainer = VAETrainer(device_id=device_id, aux_size=args.aux_size, hidden_size=args.hidden_size, lr=args.lr, prefix=args.prefix, verbose=verbose)
    utils.log(label='main', message=f'end init VAETrainer', enable=verbose)

    if checkpoint:
        utils.log(label='main', message=f'beg load checkpoint: {checkpoint}', enable=verbose)
        vae_path = checkpoint
        if vae_path.is_file():
            entries = checkpoint.stem.split('_')
            scaler_path = checkpoint.parents[0] / Path(f'scaler_{entries[1]}_{entries[2]}.pickle')
            if scaler_path.is_file():
                utils.log(label='main', message=f'vae    file: {vae_path   }', enable=verbose)
                utils.log(label='main', message=f'scaler file: {scaler_path}', enable=verbose)

                trainer.load_checkpoint(scaler_path=scaler_path, vae_path=vae_path, verbose=verbose)

                utils.log(label='main', message=f'end', enable=verbose)
            else:
                utils.log(label='main', message=f'ERROR, scaler file not found: {scaler_path}', enable=verbose)
        else:
            utils.log(label='main', message=f'ERROR, vae file not found: {vae_path}', enable=verbose)

    utils.log(label='main', message=f'beg training, epochs: {args.epochs}', enable=verbose)
    loss = trainer.run(dataloader, epochs=args.epochs)
    utils.log(label='main', message=f'end training, loss: {loss}', enable=verbose)

    scaler_path, model_path = trainer.save()
    utils.log(label='main', message=f'saved model: {model_path} {scaler_path}', enable=verbose)


if __name__ == '__main__':
    main()       

    #data/anhstudios/swganh

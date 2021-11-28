import torch
import pickle
import argparse
import numpy as np
from pathlib import Path
import torch.nn.functional as F

import utils
from ml_utils import calculate_mean_std, normalize
from dataloader import Dataloader, data_alignment, bugsinpy_alignment_filtering
from code_item import CodeItem
from code_representation import CodeRepresentation
from vae import VAESimplex


class Anomalist:

    def __init__(self, aux_size, hidden_size, scaler_path,  vae_path, device_id, verbose=True):
        assert scaler_path.is_file(), f'file {scaler_path} does not exist'
        assert vae_path.is_file(), f'file {vae_path} does not exist'

        self.device = torch.device(device_id)
        self.verbose = verbose

        INPUT_SIZE = 768
        self.model = VAESimplex(input_size=INPUT_SIZE, aux_size=aux_size, hidden_size=hidden_size).to(self.device)
        self.model.load_state_dict(torch.load(vae_path, map_location=self.device))
        self.model.eval()

        self.mean = None
        self.std = None
        with open(scaler_path, 'rb') as f:
            self.mean, self.std = pickle.load(f)

    def run_repr(self, X):
        #prefix = utils.now()                                                                                                                                    
        #utils.log(label='run', message=f'beg {prefix}', enable=self.verbose)

        #checkpoint_dir = Path(prefix)
        #checkpoint_dir.mkdir(parents=True, exist_ok=True)
        #utils.log(label='run', message=f'checkpoint dir: {checkpoint_dir}', enable=self.verbose)

        X_norm = normalize(X, self.mean, self.std)

        # reconstruction
        reconstructions = []
        reconstruction_losses = []
        for x in X_norm:
            normalized = torch.Tensor(x).float().to(self.device)
            reconstruction, _, _ = self.model(normalized)
            reconstruction_loss = F.pairwise_distance(normalized, reconstruction, 2).detach().cpu().numpy()

            reconstructions.append(reconstruction)
            reconstruction_losses.append(reconstruction_loss)

        return reconstructions, reconstruction_losses

    '''
    def run(self, code, lang=None):
        if lang is None and isinstance(code, CodeItem):
           lang = code._lang
        assert lang is not None

        code_item = Anomalist._load(code, lang)
        fragments = code_item.extract_fragments()

        # representation
        # TODO batch mode
        representations = []
        for fragment in fragments:
            with torch.no_grad():
                tokens_tensor, segments_tensors = code_to_tokens_segments(fragment.get_text(), self._repr_tokenizer)
                if tokens_tensor.shape[1] > self._repr_max_tokens:
                    representations.append(None)
                    continue

                tokens_tensor = tokens_tensor.to(self._device)
                segments_tensors = segments_tensors.to(self._device)

                outputs = self._repr_model(tokens_tensor, segments_tensors)
                hidden_states = outputs[2]

                embedding = get_code_embedding(hidden_states, penultimate=True)
                representations.append( embedding.cpu().detach().numpy().astype(np.half) )

        # reconstruction
        # TODO batch mode
        reconstructions = []
        reconstruction_losses = []
        for representation in representations:
            if representation is None:
                reconstructions.append(None)
                reconstruction_losses.append(None)
                continue

            normalized = torch.Tensor((representation - self._scaler_mean) / self._scaler_std).float().to(self._device)
            reconstruction, _, _ = self._vae_model(normalized)
            reconstruction_loss = F.pairwise_distance(normalized, reconstruction, 2).detach().cpu().numpy()

            reconstructions.append(reconstruction)
            reconstruction_losses.append(reconstruction_loss)
 
        return fragments, representations, reconstructions, reconstruction_losses

    @staticmethod
    def _load(code, lang):
        if isinstance(code, str) or isinstance(code, Path):
            return Anomalist._load_from_path(code, lang)
        elif isinstance(code, list):
            return Anomalist._load_from_lines(code, lang)
        elif isinstance(code, CodeItem):
            return code
        assert False, f'unexpected type {type(code)}'

    @staticmethod
    def _load_from_path(code_path, lang):
        assert os.path.isfile, f'file {code_path} does not exist'
        return CodeItem(lang=lang).load_from_file(code_path)

    @staticmethod
    def _load_from_lines(self, code_lines, lang):
        return CodeItem(lang=lang).load_from_lines(code_lines)
    '''

def eval_pairs(anomalist, alignment, verbose):
    result = []
    for index, (path, value) in enumerate(alignment.items()):
        #utils.log(label='main', message=f'{index} {path}', enable=verbose)
        for fragment_index, rs in value.items():
            #utils.log(label='main', message=f'\t{fragment_index} {len(rs)}', enable=verbose)
            if len(rs) == 1:
                continue
            assert len(rs) == 2
            #r_before, r_after = rs[0], rs[1]
            reconstructions, reconstruction_losses = anomalist.run_repr(rs)
            assert len(reconstruction_losses) == 2
            loss_before, loss_after = reconstruction_losses[0], reconstruction_losses[1]
            shift = (loss_after - loss_before)[0]
            utils.log(label='eval_pairs', message=f'shift: {shift}', enable=verbose)

            result.append(shift)
    return result
 

def eval_ones(anomalist, dataloader, verbose):
    result = []
    for path, fragment_index, r in dataloader:
        reconstruction, reconstruction_loss = anomalist.run_repr([r])
        loss = reconstruction_loss[0][0]
        utils.log(label='eval_ones', message=f'loss: {loss}', enable=verbose)

        result.append((path, fragment_index, loss))
    return result


def get_code(path, fragment_index, parser):
    code = CodeItem(lang='py')
    code.load_from_file(path)
    fragments = code.extract_fragments(parser)
    assert fragment_index < len(fragments)
    return fragments[fragment_index]


def main():

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--checkpoint', help='checkpoint', type=str, default='')
    parser.add_argument('--data', help='choose data', type=str, choices=['py150', 'bugsinpy', 'pybugs', 'django'], required=True)
    parser.add_argument('--rep',  help='choose repository', type=str, default='', required=False)
    #parser.add_argument('--label', help='label', type=str, choices=['None', 'before', 'after'], default='None')
    parser.add_argument('--split', help='split', type=int, choices=[0, 1, 2])
    parser.add_argument('--aux_size', help='vae aux_size', type=int, choices=range(2, 1000, 2), default=400)
    parser.add_argument('--hidden_size', help='vae hidden_size', type=int, choices=range(2, 400, 2), default=20)
    parser.add_argument('--gpu', help='use gpu', action='store_true')
 
    args = parser.parse_args()
    #label = args.label if args.label != 'None' else None
    split = args.split
    data_dir = Path('/home/u1018/zephyr/anomaly/data')
    prefices = {'py150'   : str(data_dir / Path('py150_gcb')    / Path('20210512_121352_py150_')),
                'pybugs'  : str(data_dir / Path('pybugs_gcb')   / Path('20210512_121239_pybugs_')),
                'bugsinpy': str(data_dir / Path('bugsinpy_gcb') / Path('20210512_121228_bugsinpy_')),
                'django'  : str(data_dir / Path('django_gcb')   / Path('20210824_105519_django_'))}
    device_id = 'cpu' if not args.gpu else 'cuda:0'
    checkpoint = Path(args.checkpoint)
    verbose = True

    utils.log(label='main', message=f'sha : {utils.githash()}', enable=verbose)
    utils.log(label='main', message=f'args: {parser.parse_args()}', enable=verbose)

    if args.data in ['bugsinpy', 'pybugs']:
        split = [0, 1, 2]

        utils.log(label='main', message=f'beg load data', enable=verbose)
        data_before = Dataloader(prefix=prefices[args.data], label='before', split=split, skip_truncated=True, embeddings_only=False)
        utils.log(label='main', message=f'end, before: {len(data_before)}', enable=verbose)
        data_after  = Dataloader(prefix=prefices[args.data], label='after' , split=split, skip_truncated=True, embeddings_only=False)
        utils.log(label='main', message=f'end, after : {len(data_after)}', enable=verbose)

        utils.log(label='main', message=f'beg alignment', enable=verbose)
        alignment = data_alignment(data_before, data_after)
        if args.data == 'bugsinpy':
            tree_sitter_lib_path = f'/home/u1018/zephyr/anomaly/tree_sitter/langs_py_java_csharp.so'
            code_parser = CodeRepresentation.create_parser(tree_sitter_lib=tree_sitter_lib_path, lang='python', verbose=verbose)
            data_dir = Path('/home/u1018/zephyr/anomaly/data/bugsinpy/')
            alignment = bugsinpy_alignment_filtering(alignment, data_dir, code_parser, verbose)
        utils.log(label='main', message=f'end alignment: {len(alignment)}', enable=verbose)

    if args.data in ['py150', 'django']:
        utils.log(label='main', message=f'beg dataloader: {args.data} | {args.rep} | {split}', enable=verbose)
        dataloader = Dataloader(prefix=prefices[args.data], path_prefix=args.rep, label='None', split=split, skip_truncated=True, embeddings_only=False)
        utils.log(label='main', message=f'end, size: {len(dataloader)}', enable=verbose)

    utils.log(label='main', message=f'beg load Anomalist', enable=verbose)
    vae_path = checkpoint
    scaler_path = None
    if not vae_path.is_file():
        utils.log(label='main', message=f'ERROR, vae file not found: {vae_path}', enable=verbose)
        return False
    entries = checkpoint.stem.split('_')
    scaler_path = checkpoint.parents[0] / Path(f'scaler_{entries[1]}_{entries[2]}.pickle')
    if not scaler_path.is_file():
        utils.log(label='main', message=f'ERROR, scaler file not found: {scaler_path}', enable=verbose)
        return False
    utils.log(label='main', message=f'vae    file: {vae_path   }', enable=verbose)
    utils.log(label='main', message=f'scaler file: {scaler_path}', enable=verbose)
    anomalist = Anomalist(aux_size=args.aux_size, hidden_size=args.hidden_size, scaler_path=scaler_path, vae_path=vae_path, device_id=device_id, verbose=verbose)
    utils.log(label='main', message=f'end load Anomalist', enable=verbose)

    if args.data in ['bugsinpy', 'pybugs']:
        utils.log(label='main', message=f'beg evaluation', enable=verbose)
        result = eval_pairs(anomalist, alignment, verbose)
        utils.log(label='main', message=f'end evaluation', enable=verbose)

        thresholds = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9] + list(range(1, 20)) + list(range(20, 60, 5))
        for threshold in thresholds:
            neg = len(list(filter(lambda x: (x < -threshold), result)))
            mid = len(list(filter(lambda x: (abs(x) <=  threshold), result)))
            pos = len(list(filter(lambda x: (x >  threshold), result)))

            total = neg + pos + mid
            neg_ = neg / total
            mid_ = mid / total
            pos_ = pos / total

            neg__ = neg / (neg + pos) if neg+pos else 0
            pos__ = pos / (neg + pos) if neg+pos else 0

            utils.log(label='main', message=f'thresh: {threshold}, NEG: {neg}, pos: {pos} \t{neg_:.2%} / {mid_:.2%} / {pos_:.2%} \t{neg__:.2%} / {pos__:.2%}', enable=verbose)

    if args.data in ['py150', 'django']:
        utils.log(label='main', message=f'beg evaluation', enable=verbose)
        result = eval_ones(anomalist, dataloader, verbose)
        utils.log(label='main', message=f'end evaluation', enable=verbose)

        top = sorted(result, key=lambda tup: tup[2], reverse=True)[:1000]
        tree_sitter_lib_path = f'/home/u1018/zephyr/anomaly/tree_sitter/langs_py_java_csharp.so'
        code_parser = CodeRepresentation.create_parser(tree_sitter_lib=tree_sitter_lib_path, lang='python', verbose=verbose)
        for index, (p, f, x) in enumerate(top):
            code = get_code(Path('/home/u1018/zephyr/anomaly/') / Path(p), f, code_parser)

            test = '#' if ('test' in str(p).lower()) or ('test' in code.get_text().lower()) else '$'

            print(f'{index}\t{test}\t{x}')
            print('-' * 32)
            print('\n'.join(code.lines()))
            print('*' * 32)


    utils.log(label='main', message=f'END', enable=verbose)

if __name__ == '__main__':
    main()

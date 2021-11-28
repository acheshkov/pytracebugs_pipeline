import pickle
import argparse
from pathlib import Path
from operator import itemgetter
from torch.utils.data import Dataset, DataLoader

import utils
from code_item import CodeItem


class Dataloader(Dataset):

    def __init__(self, prefix, path_prefix='', label=None, split=None, skip_truncated=True, embeddings_only=False):
        self.label = label
        self.split = split
        self.data = []

        paths = Dataloader.get_paths(prefix, label, split)
        self._load_data(paths, path_prefix, skip_truncated, embeddings_only)

    @staticmethod
    def get_paths(prefix, label=None, split=None):
        prefix = Path(prefix)
        paths = Path(prefix.parents[0]).glob(f'{prefix.name}*')

        def is_appropriate(path):
            entries = (path.stem).split('_')
            if entries[3] == 'error':
                return False
            if label is not None:
                if entries[3] != label:
                    return False
            if split is not None:
                spl = int(entries[4])
                if type(split) == int  and spl != split:
                    return False
                if type(split) == list and spl not in split:
                    return False
            return True

        return [path for path in paths if is_appropriate(path)]

    def _load_data(self, paths, path_prefix, skip_truncated, embeddings_only):
        for data_path in paths:
            with (open(data_path, 'rb')) as fin:
                data = pickle.load(fin)
            for label, split, corpus_index, path, fragment_index, fragment, r, b in data:
                if str(path_prefix) not in str(path):
                    continue
                if skip_truncated and b == 512:
                    continue
                if embeddings_only:
                    self.data.append(r)
                else:
                    self.data.append((path, fragment_index, r))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]

def data_alignment(data0, data1):
    alignment = {}
    for path, fragment_index, r in data0:
        p = Path(path).stem
        if p not in alignment:
            alignment[p] = {fragment_index: [r] }
        else:
            alignment[p][fragment_index] = [r]

    for path, fragment_index, r in data1:
        p = Path(path).stem
        if p not in alignment:
            continue
        if fragment_index not in alignment[p]:
            continue
        alignment[p][fragment_index].append(r)

    '''
    for path, value in list(alignment.items()):
        for fragment_index, rs in list(value.items()):
            if len(rs) == 1:
                del alignment[path][fragment_index]
    '''
    return alignment

def bugsinpy_alignment_filtering(alignment, data_dir,  parser, verbose):
    new_alignment = {}
    for index, (path, value) in enumerate(alignment.items()):
        path_before = data_dir / Path(f'{path}.old')
        path_after  = data_dir / Path(f'{path}.new')

        code_before = CodeItem(lang='py')
        code_before.load_from_file(path_before)
        code_after  = CodeItem(lang='py')
        code_after .load_from_file(path_after)

        fragments_before = code_before.extract_fragments(parser)
        fragments_after  = code_after .extract_fragments(parser)
        if len(fragments_before) != len(fragments_after):
            utils.log(label='filtering', message=f'WARN: {index} {len(fragments_before)}!={len(fragments_after)} : {path}', enable=verbose)
            continue
        fragments = zip(fragments_before, fragments_after)
        masks = [before.get_text() != after.get_text() for before, after in fragments]
        if sum(masks) != 1:
            utils.log(label='filtering', message=f'WARN: {index} sum={sum(masks)} : {path}', enable=verbose)
            continue
        fragment_index, _ = max(enumerate(masks), key=itemgetter(1))
        utils.log(label='filtering', message=f'{index} fragment_index={fragment_index} : {path}', enable=verbose)
        if fragment_index not in value: 
            utils.log(label='filtering', message=f'WARN: {index} fragment_index={fragment_index} not found: {path}', enable=verbose)
            continue

        new_alignment[path] = {fragment_index: alignment[path][fragment_index]}

    return new_alignment        


def main():

    parser = argparse.ArgumentParser(description='')                                                                                                                 
    parser.add_argument('--data', help='choose data', type=str, choices=['py150', 'bugsinpy', 'pybugs'], required=True)
    #parser.add_argument('--label', help='label', type=str, choices=['None', 'before', 'after'], default='None')
    #label = args.label if args.label != 'None' else None
    #parser.add_argument('--split', help='split', type=int, choices=[0, 1, 2], required=True)
 
    args = parser.parse_args()
    data_dir = Path('/home/u1018/zephyr/anomaly/data')
    prefices = {'py150'   : str(data_dir / Path('py150_gcb')    / Path('20210512_121352_py150_')),
                'pybugs'  : str(data_dir / Path('pybugs_gcb')   / Path('20210512_121239_pybugs_')),
                'bugsinpy': str(data_dir / Path('bugsinpy_gcb') / Path('20210512_121228_bugsinpy_'))}

    labels = ['before', 'after'] if args.data in ['bugsinpy', 'pybugs'] else ['None']
    splits = [0, 1, 2]

    print(f'{parser.parse_args()}')

    for label in labels:
        for split in splits:
            dl = Dataloader(prefix=prefices[args.data], label=label, split=split)
            print(f'label={label} split={split} size={len(dl)}')


if __name__ == '__main__':
    main()  

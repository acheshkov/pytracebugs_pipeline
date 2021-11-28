import os
import pickle
import numpy as np
from pathlib import Path

import torch
import torch.nn.functional as F
from transformers import RobertaTokenizer, RobertaModel

from code_item import CodeItem
from transformer_utils import code_to_tokens_segments, get_code_embedding
from variational_autoencoder import VariationalAutoencoder, loss_function


class Anomalist:

    def __init__(self, scaler_path,  vae_path, code=None, device_id='cpu'):
        assert os.path.isfile(scaler_path), f'file {scaler_path} does not exist'
        assert os.path.isfile(vae_path), f'file {vae_path} does not exist'

        #torch.manual_seed(0)
        self._device = torch.device(device_id)

        self._repr_model_name = 'microsoft/codebert-base'
        self._repr_size = 768
        self._repr_max_tokens = 512
        self._repr_tokenizer = RobertaTokenizer.from_pretrained(self._repr_model_name)
        self._repr_model = RobertaModel.from_pretrained(self._repr_model_name, output_hidden_states=True)
        self._repr_model.to(self._device)
        self._repr_model.eval()

        with open(scaler_path, 'rb') as f:
            self._scaler_mean, self._scaler_std = pickle.load(f)

        self._vae_model = VariationalAutoencoder(input_size=self._repr_size, aux_size=400, hidden_size=20)
        self._vae_model.load_state_dict(torch.load(vae_path))
        self._vae_model.to(self._device)
        self._vae_model.eval()

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

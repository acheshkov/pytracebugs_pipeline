import numpy as np
import torch
from transformers import RobertaTokenizerFast, RobertaModel


class Representator:
    def __init__(self, model_name='microsoft/codebert-base', max_size=512, dim=768, device_id='cpu'):
        self._model_name = model_name
        self._max_size = max_size
        self._dim = dim
        self._device_id = device_id
        self._device = torch.device(device_id)

        self._tokenizer = RobertaTokenizerFast.from_pretrained(self._model_name)
        self._model = RobertaModel.from_pretrained(self._model_name, return_dict=True, output_hidden_states=True)
        self._model.to(self._device)
        self._model.eval()

    def run(self, sources, padding=True, truncation=False):
        with torch.no_grad():
            tokens_pt = self._tokenizer(sources, padding=padding, truncation=truncation, return_tensors='pt')
            if len(tokens_pt['input_ids'][0]) > 512:
                return f"Fragment is too long"
            input_ids = tokens_pt['input_ids'].to(self._device)
            attention_masks = tokens_pt['attention_mask'].to(self._device)

            output = self._model(input_ids=input_ids, attention_mask=attention_masks)
            hidden_states = output[2]

            # (batch_size, max_tokens_length_in_batch, embedding_dimension)
            embeddings = (hidden_states[-1] * attention_masks.unsqueeze(-1))

            # (batch_size, embedding_dimension)
            embeddings = embeddings.sum(axis=1) / attention_masks.sum(axis=1).unsqueeze(-1)

            return embeddings.detach().cpu().numpy().astype(np.half)


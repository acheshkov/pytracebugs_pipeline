import torch
import numpy as np
from random import randrange
from transformers import pipeline
from transformers import RobertaTokenizer, RobertaForMaskedLM

def softmax(x, axis=None):
    x = x - x.max(axis=axis, keepdims=True)
    y = np.exp(x)
    return y / y.sum(axis=axis, keepdims=True)


class Representator:

    def __init__(self, model_name='microsoft/graphcodebert-base', max_size=512, dim=768, device_id='cpu'):
        self._model_name = model_name
        self._max_size = max_size
        self._dim = dim
        self._device_id = device_id
        self._device = torch.device(device_id)

        self._tokenizer = RobertaTokenizer.from_pretrained(self._model_name)
        self._model = RobertaForMaskedLM.from_pretrained(self._model_name)
        self._model.to(self._device)
        self._model.eval()

        self._pipe = pipeline('fill-mask', model=self._model, tokenizer=self._tokenizer)

    def run(self, sources, padding=True, truncation=True):
        with torch.no_grad():
            tokens_pt = self._tokenizer(sources, padding=padding, truncation=truncation, return_tensors='pt')
            input_ids = tokens_pt['input_ids']
            attention_mask = tokens_pt['attention_mask']

            output = self._pipe.model.roberta(input_ids=input_ids.to(self._device),
                                              attention_mask=attention_mask.to(self._device))
            hidden_states = output.last_hidden_state
            attention_mask.unsqueeze_(-1)
            attention_mask_big = attention_mask.expand(attention_mask.shape[0], attention_mask.shape[1], hidden_states.shape[2]).to(self._device)
            masked_summa = torch.sum(hidden_states * attention_mask_big, dim=1)

            embeddings = masked_summa / torch.sum(attention_mask_big, dim=1)
            bounds = torch.count_nonzero(attention_mask, dim=1)

            return embeddings.detach().cpu().numpy().astype(np.half), bounds.detach().cpu().numpy()

    def run_depricated(self, sources, padding=True, truncation=True):
        '''
        if padding then pad sequence (necessary in case axis0 != 1)
        if truncation then truncate sequence to max_size
        '''
        with torch.no_grad():
            tokens_pt = self._tokenizer(sources, padding=padding, truncation=truncation, return_tensors='pt')
            input_ids = tokens_pt['input_ids']
            attention_mask = tokens_pt['attention_mask']

            output = self._pipe.model.roberta(input_ids=input_ids.to(self._device), attention_mask=attention_mask.to(self._device))

            embeddings = output.last_hidden_state.detach().cpu().numpy().astype(np.half)
            return embeddings, torch.count_nonzero(attention_mask, dim=1)


    @staticmethod
    def pad(embedding, pad=0, random=False):
        '''
        embedding --- tensor of shape(batch_size, hei, wid=768)
        pad --- new hei (axis=1) of the output tensor; do pad if pad != 0
        random --- whether use random padding or not

        return padded tensor
        '''
        if not pad:
            return embedding
        assert embeddings.shape[1] <= pad, f'pad={pad} axis1={embeddings.shape[1]}'
        target = torch.zeros(embeddings.shape[0], pad, embeddings.shape[2])
        beg = randrange(0, pad-embeddings.shape[1]) if random else 0
        target[:, beg:beg+embeddings.shape[1], :] = embeddings
        assert target.shape[0] == embeddings.shape[0] and target.shape[1] == pad and target.shape[2] == embeddings.shape[2], target.shape
        return target

    def back(self, embeddings):
        lm_head_output = self._pipe.model.lm_head(embeddings)
        result = []
        for i in range(lm_head_output.shape[0]):
            res = []
            for j in range(lm_head_output.shape[1]):
                probs = softmax(lm_head_output[i][j].detach().cpu().numpy())
                indices = probs.argsort()[-1:][::-1]
                idx = indices[0]
                res.append((self._tokenizer.decode(int(idx)), probs[idx]))
            result.append(res)
        return result

    def to_text(self, tokens_with_score):
        texts = []
        for x in tokens_with_score:
            texts.append(''.join([t for t, _ in x]))
        return texts

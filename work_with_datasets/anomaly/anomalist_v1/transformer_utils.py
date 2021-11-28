import torch
from scipy.spatial.distance import cosine


def code_to_tokens_segments(code, tokenizer):
    marked_code = f'{code}'
    tokenized_code = tokenizer.tokenize(marked_code)
    indexed_tokens = tokenizer.convert_tokens_to_ids(tokenized_code)
    #for tup in zip(tokenized_code, indexed_tokens):
    #    print(f'{tup[0]:<12} {tup[1]:>6}')
    segments_ids = [1] * len(tokenized_code)
    tokens_tensor = torch.tensor([indexed_tokens])
    segments_tensors = torch.tensor([segments_ids])
    return tokens_tensor, segments_tensors


def get_code_embedding(hidden_states, penultimate=True):
    if penultimate:
        return torch.mean(hidden_states[-2][0], dim=0)

    return torch.cat([torch.mean(state[0], dim=0) for state in hidden_states[1:]], 0)

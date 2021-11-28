import hashlib
import bisect
import numpy as np


def chunks(data, n):
    return [data[x: min(x+n, len(data))] for x in range(0, len(data), n)]

def str_to_probability(s):
    Hash = hashlib.sha512
    MAX_HASH_PLUS_ONE = 2**(Hash().digest_size * 8)

    seed = s.encode()
    hash_digest = Hash(seed).digest()
    # Uses explicit byteorder for system-agnostic reproducibility
    hash_int = int.from_bytes(hash_digest, 'big')
    return hash_int / MAX_HASH_PLUS_ONE

def splitter(s, boundaries=[0.5, 0.7]):
    return bisect.bisect_left(boundaries, str_to_probability(s))

def calculate_mean_std(X):
    # https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html
    mean = np.mean(X, axis=0)
    std  = np.std (X, axis=0)
    return mean, std

def normalize(X, mean, std):
    return (X - mean) / std

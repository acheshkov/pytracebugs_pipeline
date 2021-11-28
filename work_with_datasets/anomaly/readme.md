# Anomaly

## Create embeddings
- `representator.py`
- `code_representation.py`

## Train VAE
- `vae.py`
- `vae_trainer.py`

## Inference
- `anomalist.py`

## Evaluation
- `anomalist.py`


## Usage

### Docker

Build Docker container:
```bash
docker build -t anomaly .
```

Run #1:
```bash
docker run anomaly python3 prototype.py 'https://github.com/tensorflow/tensorflow/pull/50949' json
```

Output in json format:
```json
[
  {
    "a-index": "75.85",
    "path": "tensorflow/python/keras/losses.py",
    "first_line": "__init__",
    "fragment_range":
    {
      "beg": 86,
      "end": 108
    },
    "fragment_index": 0
  },
  ...
]
```

or run #2:
```bash
docker run anomaly python3 prototype.py 'https://github.com/tensorflow/tensorflow/pull/50949' man
```

Output in a human format:
```
tensorflow/python/keras/losses.py 2069:2077	A-INDEX=129.80, NAME=is_categorical_crossentropy
tensorflow/python/keras/losses.py 1349:1352	A-INDEX=127.95, NAME=_ragged_tensor_mae
tensorflow/python/keras/losses.py 2080:2090	A-INDEX=118.86, NAME=serialize
tensorflow/python/keras/losses.py 170:173	A-INDEX=107.50, NAME=get_config
tensorflow/python/keras/losses.py 1526:1557	MESSAGE=truncated to 512, NAME=categorical_hinge
tensorflow/python/keras/losses.py 1322:1346	A-INDEX=102.54, NAME=mean_absolute_error
tensorflow/python/keras/losses.py 1302:1316	A-INDEX=102.19, NAME=_ragged_tensor_mse
tensorflow/python/keras/losses.py 1949:1982	A-INDEX=102.10, NAME=cosine_similarity
tensorflow/python/keras/losses.py 1191:1218	A-INDEX=101.87, NAME=mean_squared_error
tensorflow/python/keras/losses.py 1494:1522	A-INDEX=101.10, NAME=hinge
tensorflow/python/keras/losses.py 1869:1902	A-INDEX=100.21, NAME=kl_divergence
tensorflow/python/keras/losses.py 1461:1490	A-INDEX=99.59, NAME=squared_hinge
tensorflow/python/keras/losses.py 1392:1396	A-INDEX=99.52, NAME=_ragged_tensor_mape
tensorflow/python/keras/losses.py 1906:1937	A-INDEX=98.64, NAME=poisson
```

The interpretation of the A-index value depends on the repositories that were used for training.
For simplicity, one can assume that if the A-index value is more than 160.0, then this is a reason to analyze the source code.


### Jupyter

Sample Jupyter notebook: `anomalist_test.ipynb`

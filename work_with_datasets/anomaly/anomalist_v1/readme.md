# Anomaly detection

- 1. Dataset
- 2. Embeddings
- 3. Visualization
- 4. Anomaly detection
- 5. Conclusion

## 1. Dataset

- Source files: [Py150](https://huggingface.co/datasets/eth_py150_open)
- Granulation: fragment equals method (`ast.FunctionDef`, `ast.AsyncFunctionDef`)
- Number of fragments: 1053690

## 2. Embeddings

- Use `microsoft/codebert-base` pretrained `RobertaModel` from `huggingface`
- Skip 99377 fragments with more than 512 tokens
- Embedding is an averaged 768-dimensional vector from the penultimate layer

## 3. Visualization

- Detect one-liners using 2D mapping:

![PCA, 100K](res/readme_pca_04.png 'PCA, 100K')

## 4. Anomaly detection

- Autoencoder with 64-dimensional hidden state vector (Adam, MSE, lr=1e-3)
- Loss distribution:

![AE, 64](res/readme_ae_64_losses.png 'AE, 64')


- Found anomalies:

![sample](res/readme_sample_64_1.png 'sample')
![sample](res/readme_sample_64_2.png 'sample')
![sample](res/readme_sample_64_3.png 'sample')
![sample](res/readme_sample_64_4.png 'sample')
![sample](res/readme_sample_64_5.png 'sample')
![sample](res/readme_sample_64_6.png 'sample')
![sample](res/readme_sample_64_7.png 'sample')

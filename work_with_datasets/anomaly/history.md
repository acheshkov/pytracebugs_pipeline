# Anomaly detection

## Plan

|   |           description           |                 deliverables                 |                              risks                             |          dates         |
|---|:-------------------------------:|:--------------------------------------------:|:--------------------------------------------------------------:|:----------------------:|
| 1 | get an evaluation dataset       | language and dataset are fixed and available | ! no good evaluation dataset                                   | 2021.04.24--2021.04.25 |
| 2 | get a dataset for VAE training  | dataset is available                         |                                                                | 2021.04.26--2021.05.02 |
| 3 | calculate embeddings            | splitting; emebddings are available          | ? CB, GCB, fine-tuned GCB ? batches ? CLS, output_hidden_layer | 2021.05.03--2021.05.09 |
| 4 | VAE training                    | model is ready                               |                                                                | 2021.05.10--2021.05.16 |
| 5 | model evaluation                | good evaluation                              | ! no good evaluation                                           | 2021.05.17--2021.05.23 |
| 6 | write a paper                   | paper is written                             |                                                                | 2021.05.24--2021.05.30 |


## 1. Datasets

[a list](https://github.com/dspinellis/awesome-msr#data-sets)

#### EVALUATION

- [CROP](https://crop-repo.github.io/) provides data for 11 software systems, accounting for a total of 50,959 code reviews and 144,906 revisions.
Data [contains](https://crop-repo.github.io/#details) reviews in Java, Python, etc. [Paper](https://mhepaixao.github.io/homepage/files/crop.pdf), [download](https://zenodo.org/record/3599150#.YIPEo65S_eM), [replication scripts](https://github.com/crop-repo/crop).

- [CodeReviewsDataset SEAA2018](https://figshare.com/articles/dataset/Rev-rec_Source_-_Code_Reviews_Dataset_SEAA2018_/6462380) contains source code reviews of 51 projects mined from Gerrit (14 projects, ~133K pull requests) and GitHub (37 projects, ~159K pull requests). [Paper](https://arxiv.org/pdf/1806.07619.pdf).

- [QScored](https://zenodo.org/record/4468361#.YJOxD65S_eM) --- smells, metrics

- [Code Review Data](https://zenodo.org/record/938694#.YJO2Ra5S_eM) --- review pages, diffs, line comments

- [code reviews](http://kin-y.github.io/miningReviewRepo/) --- SQL

#### CORPORA

- [Py150](https://huggingface.co/datasets/eth_py150_open)

#### LABELLED

- [pybugs]
- [BugsInPy]

- [ManySStuBs4J](https://zenodo.org/record/3653444#.YIQzua5S_eM)
- [Defects4J](https://github.com/rjust/defects4j)
- [QuixBugs](https://github.com/jkoppel/QuixBugs)
- [BFP](https://github.com/micheletufano/NeuralCodeTranslator/tree/master/dataset)
- [Bug Database](http://www.inf.u-szeged.hu/~ferenc/papers/GitHubBugDataSet/)
- [Unified Bug Dataset](http://www.inf.u-szeged.hu/~ferenc/papers/UnifiedBugDataSet/)
- [ManySStuBs4J Dataset](https://zenodo.org/record/3653444#.YJO0XK5S_eM)
- [Lines](https://github.com/awsm-research/line-level-defect-prediction/tree/master/Dataset)


## 2. Embeddings

- Use `microsoft/graphcodebert-base` pretrained `RobertaModel` from `huggingface`
- Embedding is an averaged 768-dimensional vector from the last layer

- py150: train=766181, test=377923
- pybugs:
  - before: 6721/2603/3890
  - after : 6419/2520/3722
- bugsinpy:
  - before: 8172/5602/4974
  - after : 8167/5581/4977

## 3. Model

- ~~Autoencoder with 64-dimensional hidden state vector (Adam, MSE, lr=1e-3)~~
- ~~Loss distribution~~

## 4. Paper

- [defects](https://arxiv.org/pdf/2003.07914.pdf)
- [naturalness](Buratti et al - Exploring software naturalness through neural language models 2020)
- [C-BERT](Buratti et al - Exploring software naturalness through neural language models 2020)
- [char-based Transformer](Buratti et al - Exploring software naturalness through neural language models 2020)
- [anonymize](Chirkova Troshin - Empirical study of Transformers for source code 2020)
- [anomaly, review](Dosea et al - A survey of software code review practices in Brazil 2020)
  1. Software code review aims to early find code anomalies and to perform code improvements when they are less expensive. However, issues and challenges faced by developers who do not apply code review practices regularly are unclear.
  2. The main objectives of code review are finding code anomalies (code smells), and performing code improvements in terms of readability, commenting, consistency, and dead code removal.
  3. Surveys conducted with developers who regularly use code review practices indicate that developers spend 10-15 percent of their time in code reviews.
  4. What is the best moment to warn software developers regarding code anomalies?
  5. Practitioners’ perception is that multiple metric thresholds should be used in source code quality analysis. Current static analysis tools use a single metric threshold value for each metric. Metric thresholds are used by detection strategies to identify code anomalies. However, our results showed that only 9.14% of the respondents declared to agree with a single metric threshold to evaluate all system classes
- [malware](Gonzalez et al - Anomalicious Automated detection of anomalous and potentially malicious commits on GitHub 2021)
- [logs](Hashemi Mantyla - Detecting anomalies in software execution logs with Siamese network 2021)
- [logs](Hashemi Mantyla - OneLog Towards end-to-end training in software log anomaly detection 2021)
- [logs, synthetic evaluation](Ott et al - Robust and transferable anomaly detection in log data using pre-trained language models 2021)
- [defect prediction](Hosseini Turhan - A comparison of similarity based instance selection methods for cross project defect prediction 2021)
- [semantic outlier](Lee Lee - Identifying semantic outliers of source code artifacts and their application to software architecture recovery 2020)
- [ml vs dl](Lomio et al - Fault prediction based on software metrics and SonarQube rules Machine or deep learning 2021)

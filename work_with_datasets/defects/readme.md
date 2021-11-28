# Experiments

## 0. Embeddings

## 1. CodeBERT on PyBugs
  1. **bug** vs **fix** (best result, CodeBert embeddings + LightGBM classifier):

| class | precision | recall | f1  | support |
| ----- | --------- | ------ | --- | ------- |
| stable code | 0.51 | 0.65 | 0.57 | 48184 |
| bug         | 0.52 | 0.39 | 0.44 | 48184 |

accuracy: 0.52

  3. **bug** vs **stable code** (best result, CodeBert embeddings + LightGBM classifier):

| class | precision | recall | f1  | support |
| ----- | --------- | ------ | --- | ------- |
| stable code | 0.91 | 0.84 | 0.88 | 32000 |
| bug         | 0.90 | 0.95 | 0.92 | 48184 |

accuracy: 0.91

  3. **fix** vs **stable code** (best result, CodeBert embeddings + LightGBM classifier):

| class | precision | recall | f1  | support |
| ----- | --------- | ------ | --- | ------- |
| stable code | 0.92 | 0.85 | 0.88 | 32000 |
| fix         | 0.90 | 0.95 | 0.93 | 48184 |

accuracy: 0.91


## 2. CodeBERT on pairs of PyBugs (bug-fix and fix-bug, bugfix and fixbug)
  1. **bug-fix** vs **fix-bug** (best result, CodeBert embeddings + LightGBM classifier):

| class | precision | recall | f1  | support |
| ----- | --------- | ------ | --- | ------- |
| fix-bug  | 0.62 | 0.71 | 0.66 | 24092 |
| bug-fix  | 0.66 | 0.57 | 0.62 | 24092 |

accuracy: 0.64

  3. **concat(bug, fix)** vs **concat(fix, bug)** (best result, CodeBert embeddings + LightGBM classifier):

| class | precision | recall | f1  | support |
| ----- | --------- | ------ | --- | ------- |
| concat(fix, bug)  | 0.60 | 0.62 | 0.61 | 24092 |
| concat(bug, fix)  | 0.61 | 0.60 | 0.60 | 24092 |

accuracy: 0.61

## 3. CodeBERT on bfp
  1. **bug** vs **fix**, **"small"** part (best result, CodeBert embeddings + LightGBM classifier):

| class | precision | recall | f1  | support |
| ----- | --------- | ------ | --- | ------- |
| fix  | 0.61 | 0.54 | 0.57 | 5835 |
| bug  | 0.59 | 0.66 | 0.62 | 5835 |

accuracy: 0.60

  3. **bug** vs **fix**, **"medium"** part (best result, CodeBert embeddings + LightGBM classifier):

| class | precision | recall | f1  | support |
| ----- | --------- | ------ | --- | ------- |
| fix  | 0.54 | 0.61 | 0.57 | 6545 |
| bug  | 0.55 | 0.47 | 0.51 | 6545 |

accuracy: 0.54

## 4. CodeBERT on BugHunter [PAUSED]

## 5. CodeBERT on BugsInPy

## 6. CodeBERT on pairs of BugsInPy (bug-fix and fix-bug, bugfix and fixbug)

## 7. CodeBERT on separate projects of PyBugs

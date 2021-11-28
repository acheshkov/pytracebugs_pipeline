## Usage

### Docker

Build Docker container:
```bash
docker build -t bug_detection .
```

Run:
```bash
docker run bug_detection python3 prototype.py 'https://github.com/tensorflow/tensorflow/pull/50949'
```

Output:
```json
[
    {
        "bugginess_probability": 0.06868967334743603,
        "first_line": "  def __init__(self, reduction=losses_utils.ReductionV2.AUTO, name=None):",
        "fragment_range": {
            "beg": 86,
            "end": 108
        },
        "path": "tensorflow/python/keras/losses.py"
    },
  ...
]
```

### Result interpretation

If `bugginess_probability` is greater or equal to 0.5 then we assume that fragment contains buggy code. Otherwise we assume that fragment is correct.

import requests
import json
import random
import time
import tempfile
import os
import gzip
import sys

from requests.auth import HTTPBasicAuth

sess = requests.session()

REPOS_PER_BUCKET = 100000
MAX_ID = 1_000_000_000
START_AT = int(sys.argv[1])

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
}

TOKENS = [
    ("username", "1111111111111111111111111111111111111111"),
]

def get_repos_from(start, end):
    while start < end:
        print(f"getting since {start}")
        params = {"since": start}
        resp = sess.get("https://api.github.com/repositories", headers=HEADERS, params=params, auth=random.choice(TOKENS))
        print("Remaining", resp.headers["X-RateLimit-Remaining"])

        repos = resp.json()
        if not isinstance(repos, list):
            print(f"wrong ans", repos)
            time.sleep(5)
            continue
        elif not repos:
            print(f"end has reached")
            break

        for repo in repos:
            start = max(start, repo["id"])
            if repo["id"] < end:
                yield repo




for start in range(START_AT, MAX_ID, REPOS_PER_BUCKET):
    filename = f"pub_repos_{start}.json.gz"
    if os.path.exists(filename):
        continue

    fd, tempname = tempfile.mkstemp(prefix=f"{filename}-unfinished-", dir="")
    print(tempname)
    os.chmod(tempname, 0o755)

    #print(fd, dir(fd))
    # with open(fd, 'w', newline='') as out_file:
    with gzip.open(open(fd, "wb"), 'wb') as out_file:
        print("getting from", start)
        for obj in get_repos_from(start, start+REPOS_PER_BUCKET):
            out_file.write((json.dumps(obj, ensure_ascii=False) + "\n").encode())

    os.rename(tempname, filename)

import os
import glob
import re
import gzip
import json

from collections import Counter

langs = Counter()

output = open("python_repos_interesting_top.json", "w")

repos = []

num = 0
good = 0
for line in open("python_repos_interesting.json"):
    obj = json.loads(line)
    if obj["pullRequests"]["totalCount"] < 25:
        continue
    if obj["stargazerCount"] < 25:
        continue
    if obj["forkCount"] < 25:
        continue
    # if obj["issues"]["totalCount"] < 25:
    #     continue
    repos.append(obj)

repos.sort(key=lambda o:
    o["pullRequests"]["totalCount"] + o["stargazerCount"] + o["forkCount"] + o["issues"]["totalCount"], reverse=True)

for repo in repos:
    print(repo["nameWithOwner"], file=output)
    print(repo["pullRequests"]["totalCount"])
    # output.write(f"{json.dumps(repo, ensure_ascii=False)}\n")

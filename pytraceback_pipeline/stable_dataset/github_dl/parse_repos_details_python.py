import os
import glob
import re
import gzip
import json

from collections import Counter

langs = Counter()

output = open("python_repos_interesting.json", "w")

num = 0
good = 0
for line in open("python_repos.json"):
    obj = json.loads(line)
    num += 1

    if (num % 100000) == 0:
        print(num, good)

    if obj["isFork"]: # and obj["issues"]["totalCount"] # and obj["parent"] and obj["stargazerCount"] > obj["parent"]["stargazerCount"]:
        continue

    if not obj["stargazerCount"]:
        continue

    if not obj["forkCount"]:
        continue

    if not obj["pullRequests"]["totalCount"]:
        continue

    #if not obj["issues"]["totalCount"]:
        #continue
        # fork_is_better += 1

    good += 1

    output.write(line)



    # print(lang)

# print("finish", f, num, langs)

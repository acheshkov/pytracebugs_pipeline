import os
import glob
import re
import gzip
import json

from collections import Counter

langs = Counter()

output = open("python_repos.json", "wb")

num = 0
fork_is_better = 0
for f in sorted(glob.glob("github_repos_details/*"), key=lambda k: int(re.search(r"\d+", k)[0])):
    for line in gzip.open(f):
        obj = json.loads(line)
        num += 1

        # if obj["isFork"] and obj["parent"] and obj["stargazerCount"] > obj["parent"]["stargazerCount"]:
            # fork_is_better += 1
        lang = "Unknown"
        if obj.get("primaryLanguage"):
            lang = obj.get("primaryLanguage").get("name", "unknown")
            langs[lang] += 1

        if lang == "Python":
            output.write(line)



        # print(lang)

    print("finish", f, num, langs)

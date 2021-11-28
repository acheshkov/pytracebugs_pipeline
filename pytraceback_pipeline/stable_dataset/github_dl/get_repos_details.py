import requests
import json
import random
import time
import tempfile
import os
import gzip
import re
import socket

IGNORE_NODE_IDS = set([
    "MDEwOlJlcG9zaXRvcnkzMDA0NjA3OTc=", "MDEwOlJlcG9zaXRvcnkzMDU2NDk0MDE=", "MDEwOlJlcG9zaXRvcnkzMDA0NjEwNjE=",
    "MDEwOlJlcG9zaXRvcnkzMDMzNTc2ODM=", "MDEwOlJlcG9zaXRvcnkzMDMwODg1OTM=", "MDEwOlJlcG9zaXRvcnkyOTU4NDAzOTU=",
    "MDEwOlJlcG9zaXRvcnkzMDA0NjEyOTg=", "MDEwOlJlcG9zaXRvcnkxOTY1OTc1MDU=", "MDEwOlJlcG9zaXRvcnkzMDA0NjE1NjE=",
    "MDEwOlJlcG9zaXRvcnkzMDA0NjEyOTg=", "MDEwOlJlcG9zaXRvcnkxMzIwMTQxNzY=", "MDEwOlJlcG9zaXRvcnkyODcwOTk4OTA=",
    "MDEwOlJlcG9zaXRvcnkxODM1MzQ0NzQ=", "MDEwOlJlcG9zaXRvcnkyODY3NDgwMjk=", "MDEwOlJlcG9zaXRvcnkyODY3NDgwMDY=",
    "MDEwOlJlcG9zaXRvcnkyOTg4MDA5MDM=", "MDEwOlJlcG9zaXRvcnkxODAxNzA3OTY=", "MDEwOlJlcG9zaXRvcnkyODY3NDgxMDM=",
    "MDEwOlJlcG9zaXRvcnkyODY3NDgxMDk=", "MDEwOlJlcG9zaXRvcnkyODY3NDgwNTQ=", "MDEwOlJlcG9zaXRvcnkyODY3NDgwNDQ=",
    "MDEwOlJlcG9zaXRvcnkyODY3NDgwNjY=", "MDEwOlJlcG9zaXRvcnkyODY3NDgwNzU=", "MDEwOlJlcG9zaXRvcnkyODY3NDgwODk=",
    "MDEwOlJlcG9zaXRvcnkyODY3NDgwOTU=", "MDEwOlJlcG9zaXRvcnkyODY3NDgyMTY=", "MDEwOlJlcG9zaXRvcnkyODY3NDgyMjQ=",
    "MDEwOlJlcG9zaXRvcnkyODY3NDgyMzQ=", "MDEwOlJlcG9zaXRvcnkyODY3NDgyNDM=", "MDEwOlJlcG9zaXRvcnkyODY3NDgyNDc=",
    "MDEwOlJlcG9zaXRvcnkyODY3NDgyNTI=", "MDEwOlJlcG9zaXRvcnkxODAxNzA3OTY=", "MDEwOlJlcG9zaXRvcnkyODQ5OTk5NzA=",
    "MDEwOlJlcG9zaXRvcnkyODMxMTIwMTc=", "MDEwOlJlcG9zaXRvcnkyNjY1OTYzOTg=", "MDEwOlJlcG9zaXRvcnkyODMxMTIwMTc=",
    "MDEwOlJlcG9zaXRvcnkyNTc5NjY0OTk=", "MDEwOlJlcG9zaXRvcnkyODMxMTI5NjA=", "MDEwOlJlcG9zaXRvcnkyOTg4MDU5MTY=",
    "MDEwOlJlcG9zaXRvcnkyODMxMTM1NDA=", "MDEwOlJlcG9zaXRvcnkyODMxMTQyMjU=", "MDEwOlJlcG9zaXRvcnkyODMxNDgxNzg="

    ])



RETRY_STRATEGY = requests.packages.urllib3.util.retry.Retry(
    total=10,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS"]
)
sess = requests.session()
adapter = requests.adapters.HTTPAdapter(max_retries=RETRY_STRATEGY)
sess.mount("https://", adapter)
sess.mount("http://", adapter)

hostname = socket.gethostname()

TOKENS = [
    ("tokenname", "1111111111111111111111111111111111111111")
]


def get_repos_detail(node_ids):
    node_ids = [node_id for node_id in node_ids if node_id not in IGNORE_NODE_IDS]

    query = """query {
  nodes(ids:""" + json.dumps(node_ids) + """) {
    ... on Repository {
      databaseId,
      nameWithOwner,
      description,
      mirrorUrl,
      createdAt,
      pushedAt,
      updatedAt,
      forkCount,
      stargazerCount,
      hasIssuesEnabled,
      isArchived,
      isDisabled,
      isFork,
      isMirror,
      diskUsage,
      defaultBranchRef {
        name
      },
      commitComments {
        totalCount
      },
      licenseInfo {
        name,
      },
      watchers {
        totalCount
      },
      issues {
        totalCount
      },
      pullRequests {
        totalCount
      },
      primaryLanguage {
        name
      },
      releases {
        totalCount
      }
      languages(first:100) {
        edges {
          node {
            name
          }
          size
        }
      },
      parent {
        databaseId,
        nameWithOwner,
        isFork,
        forkCount,
        stargazerCount,
        watchers {
          totalCount
        },
        issues {
          totalCount
        },
        pullRequests {
          totalCount
        },
      }
    }
  },
  rateLimit {
    cost,
    nodeCount,
    remaining
  }

}"""

    while True:
        token = random.choice(TOKENS)[1]
        headers = {"Authorization": f"bearer {token}"}
        try:
            resp = sess.post("https://api.github.com/graphql",
                data=json.dumps({"query": query}),
                headers=headers)
            repos = resp.json()
            # print("Remaining", resp.headers["X-RateLimit-Remaining"])

            # print(repos)
            if not repos.get("data", {}) or not repos["data"].get("rateLimit", None) :
                print(f"wrong ans", node_ids, repos)
                raise Exception("Bad data format")

            # if "rateLimit" in repos["data"]:
            print("Remaining from ans:", repos["data"]["rateLimit"])

        except Exception as E:
            print(f"exception on post", E)
            time.sleep(5)
            continue

        return repos



files = os.listdir()
random.shuffle(files)

for filename in files:
    m = re.fullmatch(r"pub_repos_(\d+).json.gz", filename)
    if not m:
        continue

    data_filename = f"pub_repos_details_{m[1]}.json.gz"
    error_filename = f"pub_repos_details_errors_{m[1]}.json"

    if os.path.exists(data_filename):
        continue

    fd, tempname = tempfile.mkstemp(prefix=f"{data_filename}-unfinished-", dir="")
    print(tempname)
    os.chmod(tempname, 0o755)

    node_ids = []

    with gzip.open(open(filename, "rb"), "rb") as in_file:
        for line in in_file:
            obj = json.loads(line)

            if "node_id" not in obj:
                print("Strange: node_id not in obj")
                continue
            node_ids.append(obj["node_id"])
            # print(obj)

    CHUNK_LEN = 100
    CHUNKS = (len(node_ids) + (CHUNK_LEN-1)) // CHUNK_LEN

    written = 0
    with open(error_filename, "a") as error_file:
        with gzip.open(open(fd, "wb"), 'wb') as out_file:
            for chunk in range(CHUNKS):
                chunk_node_ids = node_ids[chunk*CHUNK_LEN: chunk*CHUNK_LEN+CHUNK_LEN]
                # print(chunk_node_ids)

                print(f"chunk {chunk}/{CHUNKS}")

                repo_details = get_repos_detail(chunk_node_ids)

                if "errors" in repo_details:
                    error_file.write(json.dumps(repo_details["errors"], ensure_ascii=False) + "\n")

                # print(len(repo_details.get("data", []))
                for node in repo_details.get("data", {}).get("nodes", []):
                    if not node:
                        continue
                    out_file.write((json.dumps(node, ensure_ascii=False) + "\n").encode())
                    written += 1
                print(f"got {written}/{len(node_ids)} repos")
            os.rename(tempname, data_filename)
#     # with open(fd, 'w', newline='') as out_file:
#         print("getting from", start)
#         for obj in get_repos_from(start, start+REPOS_PER_BUCKET):
#             out_file.write((json.dumps(obj, ensure_ascii=False) + "\n").encode())

#     os.rename(tempname, filename)

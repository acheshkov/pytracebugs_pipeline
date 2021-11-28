import os
import ast
import hashlib
import itertools
import sys
import copy
import pickle

from collections import defaultdict

from git import Repo
from git import RemoteProgress

# URL = "https://github.com/alexbers/mtprotoproxy"
# DIR = "alexbers_mtprotoproxy"

R = sys.argv[1]
URL = f"https://github.com/{R}"
DIR = R.replace("/", "_")
OUT_DIR = f"python_top_code"
REPO_DIR = f"repo"

REPO_FULL_DIR = REPO_DIR + "/" + DIR
OUT_FULL_DIR = OUT_DIR + "/" + DIR

def make_dir_ignore_exists(d):
    try:
        return os.mkdir(d)
    except FileExistsError as E:
        pass

make_dir_ignore_exists(REPO_DIR)
make_dir_ignore_exists(OUT_DIR)
make_dir_ignore_exists(OUT_FULL_DIR)

if not os.path.exists(REPO_FULL_DIR):
    repo = Repo.clone_from(URL, REPO_FULL_DIR, multi_options=["--bare"], branch=None)
else:
    repo = Repo(REPO_FULL_DIR)

print(f"Repo {URL} opened")

for obj in repo.head.commit.tree.list_traverse():
    if obj.type != "blob":
        continue

    if not obj.path.endswith(".py"):
        continue

    obj_dir = os.path.dirname(obj.path)

    try:
        content = obj.data_stream.read()

        with open(f"{OUT_FULL_DIR}/" + f"{obj.path}".replace("+", "_").replace("/", "+"), "wb") as out:
            out.write(content)

    except Exception as E:
        print(f"skipping file {obj.path} because of exception {type(E)} {E}", file=sys.stderr)

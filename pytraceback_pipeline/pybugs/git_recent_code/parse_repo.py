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
OUT_DIR = f"stat"
REPO_DIR = f"repo"
CACHE_DIR = f"cache"

REPO_FULL_DIR = REPO_DIR + "/" + DIR
OUT_FULL_DIR = OUT_DIR + "/" + DIR

def make_dir_ignore_exists(d):
    try:
        return os.mkdir(d)
    except FileExistsError as E:
        pass

make_dir_ignore_exists(REPO_DIR)
make_dir_ignore_exists(CACHE_DIR)
make_dir_ignore_exists(OUT_DIR)
make_dir_ignore_exists(OUT_FULL_DIR)


# URL = "https://github.com/tensorflow/tensorflow"
# DIR = "tensorflow_tensorflow"


def gen_ast_subnodes(ast_node):
    for child in ast.iter_child_nodes(ast_node):
        if not isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.Lambda, ast.AsyncFunctionDef)):
            continue

        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # if "test" not in child.name:
            yield child
        yield from gen_ast_subnodes(child)


def gen_ast_nodes(text):
    try:
        ast_parsed = ast.parse(text)
        yield from gen_ast_subnodes(ast_parsed)
    except Exception as e:
        print("Parsing error", e, file=sys.stderr)

def gen_python_funcs_texts(text):
    for ast_node in gen_ast_nodes(text):
        yield ast.unparse(ast_node)


def calc_dir_to_func_checksums(repo):
    # checksum_to_times = defaultdict(int)

    try:
        return pickle.load(open(f"{CACHE_DIR}/{DIR}.pickle", "rb"))
    except FileNotFoundError:
        pass

    file_checksum_to_func_checksums = defaultdict(list)

    # commit_to_dir_change_counter = defaultdict(int)
    # prev_commit_file_checksum_to_func_checksums = defaultdict(list)

    # dir -> checksum -> times
    dir_to_func_checksums = defaultdict(dict)

    commits = [repo.head.commit] + list(repo.head.commit.iter_parents())
    commits.reverse()

    for pos, commit in enumerate(commits):
        print(f"Parsing commit {pos+1}/{len(commits)}")

        dir_checksums = defaultdict(set)

        changed_dirs = set()

        for obj in commit.tree.list_traverse():
            if obj.type != "blob":
                continue

            if not obj.path.endswith(".py"):
                continue

            if "test" in obj.path.casefold():
                continue

            obj_dir = os.path.dirname(obj.path)

            file_checksum = obj.binsha

            if file_checksum not in file_checksum_to_func_checksums:
                content = obj.data_stream.read()
                for text in gen_python_funcs_texts(content):
                    checksum = hashlib.sha1(text.encode()).digest()
                    file_checksum_to_func_checksums[file_checksum].append(checksum)

                changed_dirs.add(obj_dir)

            checksums = file_checksum_to_func_checksums[file_checksum]

            dir_checksums[obj_dir].update(checksums)

        new_dir_to_func_checksums = defaultdict(dict)
        for obj_dir, checksums in dir_checksums.items():
            for checksum in checksums:
                checksum_counter = dir_to_func_checksums[obj_dir].get(checksum, -1)
                if obj_dir in changed_dirs:
                    checksum_counter += 1
                new_dir_to_func_checksums[obj_dir][checksum] = checksum_counter

        dir_to_func_checksums = new_dir_to_func_checksums

    pickle.dump(dir_to_func_checksums, open(f"{CACHE_DIR}/{DIR}.pickle", "wb"))
    return dir_to_func_checksums


if not os.path.exists(REPO_FULL_DIR):
    repo = Repo.clone_from(URL, REPO_FULL_DIR, multi_options=["--bare"], branch=None)
else:
    repo = Repo(REPO_FULL_DIR)

print(f"Repo {URL} opened")

dir_to_func_checksums = calc_dir_to_func_checksums(repo)

for obj in repo.head.commit.tree.list_traverse():
    if obj.type != "blob":
        continue

    if not obj.path.endswith(".py"):
        continue

    obj_dir = os.path.dirname(obj.path)

    try:
        content = obj.data_stream.read()
        line_to_times = defaultdict(int)

        # print(obj)

        child_nodes = list(gen_ast_nodes(content))
        child_nodes.sort(key=lambda k:
            {ast.ClassDef: 0, ast.FunctionDef: 1, ast.Lambda:2, ast.AsyncFunctionDef: 3}.get(type(k), -1))

        for child in child_nodes:
            # print(dir(child))
            checksum = hashlib.sha1(ast.unparse(child).encode()).digest()

            times = dir_to_func_checksums[obj_dir][checksum]

            for lineno in range(child.lineno, child.end_lineno + 1):
                line_to_times[lineno] = times

        with open(f"{OUT_FULL_DIR}/" + f"{obj.path}.freq.txt".replace("/", "_"), "w") as out:
            for pos, line in enumerate(content.split(b"\n")):
                lineno = pos + 1

                out.write(f"{line_to_times.get(lineno, 0):-6d} {line.decode()}\n")
    except Exception as E:
        print(f"skipping file {obj.path} because of exception {type(E)} {E}", file=sys.stderr)


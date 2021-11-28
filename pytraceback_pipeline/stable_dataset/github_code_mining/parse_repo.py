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
DIR = R.replace("/", "+")
OUT_DIR = f"stat"
REPO_DIR = f"repo"
CACHE_DIR = f"cache"

OUT_SNIPPET_FULL_DIR = OUT_DIR + "/stable_snippets_files"
OUT_SOURCE_FULL_DIR = OUT_DIR + "/source_files"

REPO_FULL_DIR = REPO_DIR + "/" + DIR
OUT_FULL_FILE = OUT_DIR + "/" + DIR + ".pickle"

def make_dir_ignore_exists(d):
    try:
        return os.mkdir(d)
    except FileExistsError as E:
        pass

make_dir_ignore_exists(REPO_DIR)
make_dir_ignore_exists(CACHE_DIR)
make_dir_ignore_exists(OUT_DIR)
make_dir_ignore_exists(OUT_SNIPPET_FULL_DIR)
make_dir_ignore_exists(OUT_SOURCE_FULL_DIR)


# URL = "https://github.com/tensorflow/tensorflow"
# DIR = "tensorflow_tensorflow"


def gen_ast_subnodes(ast_node, prefix=""):
    for child in ast.iter_child_nodes(ast_node):
        if not isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.Lambda, ast.AsyncFunctionDef)):
            continue

        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # if "test" not in child.name:
            
            child.prefixed_name = prefix + child.name
            yield child
        yield from gen_ast_subnodes(child, prefix=child.name + "." + prefix)


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

#print(repo.head.commit.hexsha)
#exit(0)

dir_to_func_checksums = calc_dir_to_func_checksums(repo)

snippets = []

for obj in repo.head.commit.tree.list_traverse():
    if obj.type != "blob":
        continue

    if not obj.path.endswith(".py"):
        continue

    obj_dir = os.path.dirname(obj.path)
    

    try:
        content = obj.data_stream.read()
        #line_to_lineinfo = defaultdict(dict)

        content_lines = content.split(b"\n")

        # print(obj)

        child_nodes = list(gen_ast_nodes(content))
        child_nodes.sort(key=lambda k:
            {ast.ClassDef: 0, ast.FunctionDef: 1, ast.Lambda:2, ast.AsyncFunctionDef: 3}.get(type(k), -1))

        for child in child_nodes:
            if not isinstance(child, ast.FunctionDef) and not isinstance(child, ast.AsyncFunctionDef):
                continue
            # print(dir(child))
            checksum = hashlib.sha1(ast.unparse(child).encode()).digest()

            times = dir_to_func_checksums[obj_dir][checksum]
            
            if times < 20:
                continue
            
            decorators = " ".join(["@" + ast.unparse(c) for c in child.decorator_list])
            
            func_full_name = child.prefixed_name
            if decorators:
                func_full_name = decorators + " " + func_full_name
                
            


            func_text = b"\n".join(content_lines[lineno] for lineno in range(child.lineno-1, child.end_lineno + 1))
            
            func_text_sha = hashlib.sha1(func_text).hexdigest()
            
            snippet = {}
            snippet["before_merge"] = func_text
            snippet["repo_name"] = R
            snippet["filename"] = os.path.basename(obj.path)
            snippet["function_name"] = func_full_name
            snippet["syntax_correct"] = True
            snippet["path_to_source_file"] = obj.path
            snippet["commit"] = repo.head.commit.hexsha
            snippet["path_to_snippet_before_merge"] = f"{OUT_SNIPPET_FULL_DIR}/{func_text_sha}.py"
            snippet["path_to_source_file"] = f"{OUT_SOURCE_FULL_DIR}/{obj.hexsha}.py"
            snippet["times"] = times
            
            snippets.append(snippet)
            
            with open(snippet["path_to_snippet_before_merge"], "wb") as f:
                f.write(func_text)

            with open(snippet["path_to_source_file"], "wb") as f:
                f.write(content)

            
            #for lineno in range(child.lineno-1, child.end_lineno + 1):
                #print(content_lines[lineno])
            

            #for lineno in range(child.lineno, child.end_lineno + 1):
                #line_to_lineinfo[lineno]["times"] = times

        #with open(f"{OUT_FULL_DIR}/" + f"{obj.path}.freq.txt".replace("/", "+"), "w") as out:
            #for pos, line in enumerate(content.split(b"\n")):
                #lineno = pos + 1

                #out.write(f"{line_to_lineinfo.get(lineno, {}).get('times', 0):-6d} {line.decode()}\n")
    except Exception as E:
        print(f"skipping file {obj.path} because of exception {type(E)} {E}", file=sys.stderr)
    
# export to pandas
import pandas
df = pandas.DataFrame(snippets)
df.to_pickle(OUT_FULL_FILE)

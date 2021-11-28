import glob
import os

from collections import Counter

STATS_DIR = "stats"

GOOD_REPOS = [d for d in os.listdir(STATS_DIR) if os.stat(f"{STATS_DIR}/{d}/stat_ast.txt").st_size and d != "CiscoDevNet_ydk-py"]

NUM = len(GOOD_REPOS)
print(f"{NUM=}")


def read_counter_from_file(filename):
    c = Counter()

    for line in map(str.strip, open(filename)):
        v, k = line.split(" ", 1)
        c[k] = int(v)
    return c


def agregate_stats(stat_file_base_names, key_mapper=lambda k: k):
    global NUM

    cumulative_c = Counter()
    repos_sum_c = Counter()

    for repo in GOOD_REPOS:
        filepath = f"{STATS_DIR}/{repo}"
        c = Counter()
        for stat_file_base_name in stat_file_base_names:
            c.update(read_counter_from_file(f"{filepath}/{stat_file_base_name}.txt"))

        for k, v in c.items():
            cumulative_c[key_mapper(k)] += v

        repos_sum_c.update(map(key_mapper, c.keys()))

    with open(f"{stat_file_base_names[0]}_all.txt", "w") as f:
        for k, v in cumulative_c.most_common():
            print(f"{v} {k}", file=f)

    with open(f"{stat_file_base_names[0]}_repo_fract.txt", "w") as f:
        for k, v in repos_sum_c.most_common():
            print(f"{v*100 / NUM: .1f}% {v} {k}", file=f)


agregate_stats(["stat_ast"])
agregate_stats(["stat_async_func_names"])
agregate_stats(["stat_async_function_decorators"])
agregate_stats(["stat_attributes"])
agregate_stats(["stat_class_bases"])
agregate_stats(["stat_class_decorators_c"])
agregate_stats(["stat_class_keywords"])
agregate_stats(["stat_class_names"])
agregate_stats(["stat_exception_handlers"])
agregate_stats(["stat_func_names"])
agregate_stats(["stat_function_decorators_c"])
agregate_stats(["stat_module_names", "stat_from_module_names"], lambda k: k.split()[0])

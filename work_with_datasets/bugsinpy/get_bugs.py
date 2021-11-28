import os
import string
import random
import time
import datetime
import subprocess
from glob import glob
from os.path import expanduser

import whatthepatch


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


# configuration
working_dir = f'{expanduser("~")}/zephyr/datasets/bugsinpy/github.BugsInPy/framework/bin/'
projects_dir = f'{expanduser("~")}/zephyr/datasets/bugsinpy/github.BugsInPy/projects/'
#dir_for_cloned_projects = f'/temp/projects/'

projects_paths = glob(projects_dir + '*/')
print(f'number of projects: {len(projects_paths)}')

projects_names = [path.split('/')[-2] for path in projects_paths]
for name in projects_names:
    print(f' {name}')

print(f'{32 * "-"}\n')

bugs = {}
for index, name in enumerate(projects_names):
    bugs[name] = []
    bug_dir = f'{projects_dir}{name}/bugs/'
    bugid_dir = glob(bug_dir + '*/')
    for d in bugid_dir:
        bug_patch_path = f'{d}bug_patch.txt'
        with open(bug_patch_path, encoding='utf8') as f:
            text = f.read()
        diffs = list(whatthepatch.parse_patch(text))
        if len(diffs) != 1:
            continue
        for diff in diffs:
            if diff.header.old_path == diff.header.new_path:
                bugs[name].append(bug_patch_path)

    print(f'{name}\t{len(bugs[name])}')
print(f'\ntotal: {sum([len(f) for f in bugs.values()])}')

print(f'{32 * "-"}\n')

res_dir = f'{working_dir}{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}/'
print(res_dir)
os.mkdir(res_dir)

dir_for_cloned_projects = res_dir

bug_table_path = f'{res_dir}bugs.tsv'
for name, paths in bugs.items():
    for path in paths:
        bug_id = os.path.basename(os.path.dirname(path))
        with open(path) as f:
            text = f.read()
        for diff in whatthepatch.parse_patch(text):
            source_path_old = f'{dir_for_cloned_projects}{name}/{diff.header.old_path}'
            source_path_new = f'{dir_for_cloned_projects}{name}/{diff.header.new_path}'
            genid = id_generator() 
            with open(bug_table_path, 'a', encoding='utf8') as table:
                table.write(f'{name}\t{bug_id}\t{diff.header.old_path}\t{genid}\n')

            cmds = []
            # get old file
            cmds.append(f'./bugsinpy-checkout -p {name} -i {bug_id} -v 0 -w {dir_for_cloned_projects}')
            cmds.append(f'cp {source_path_old} {res_dir}{genid}.old')

            # get new file
            cmds.append(f'rm -rf {dir_for_cloned_projects}{name}/')
            cmds.append(f'./bugsinpy-checkout -p {name} -i {bug_id} -v 1 -w {dir_for_cloned_projects}')
            cmds.append(f'cp {source_path_new} {res_dir}{genid}.new')

            # get diff
            cmds.append(f'cp {path} {res_dir}{genid}.diff')

            for cmd in cmds:
                print(f'{cmd} ...')
                process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
                output, error = process.communicate()
                print(f'{cmd} ... OK\n')

            time.sleep(60)


import requests
import subprocess


false = False
true = True
null = None


def get_merge_commit_sha(repo_name, pr_number):
    r = requests.get(f'https://api.github.com/repos/{repo_name}/pulls/{pr_number}')
    assert r.status_code == 200, print(r.text)

    return eval(r.text)['merge_commit_sha']


def get_python_files_from_pull_request(repo_name, pr_number):
    r = requests.get(f'https://api.github.com/repos/{repo_name}/pulls/{pr_number}/files')
    assert r.status_code == 200, print(r.text)

    files = [f['filename'] for f in eval(r.text) if f['filename'].endswith('.py')]
    return files


def clone_repo(repo_url):
    repo_dir = 'temp_repo_dir/'
    command = f'git clone {repo_url} {repo_dir}'
    subprocess.Popen(command, shell=True).wait()
    return repo_dir

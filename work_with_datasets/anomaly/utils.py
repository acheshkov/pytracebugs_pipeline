import sys
import git
import datetime
import subprocess

def install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def now():
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

def log(label, message, enable=True):
    if enable:
        print(f'{now()} [{label}]: {message}')

def githash():
    repo = git.Repo(search_parent_directories=True)
    sha = repo.head.object.hexsha
    return sha

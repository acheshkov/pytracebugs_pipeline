import json
import os

from collections import OrderedDict

import git
import pandas
import javalang
from javalang.parser import JavaSyntaxError
from javalang.tree import ClassDeclaration, MethodDeclaration

from utyls import get_line_code_snippet, print_progress_bar

BASE_BUG_HUNTER_DIR = "./data/full/"
REPOS_DIR = "./repos/"
FILE_DIR = "./dataset_file/"


def init():
    if not os.path.exists(REPOS_DIR):
        os.makedirs(REPOS_DIR)
    if not os.path.exists(FILE_DIR):
        os.makedirs(FILE_DIR)


class BugHunterItem:
    def __init__(self, name, count_bug):
        self.name = name
        self.count_bug = count_bug


class FileCommit:
    def __init__(self, raw_data, save_path, count_bug, _hash):
        self.hash = _hash
        self.save_path = save_path
        self.raw_data = raw_data
        self.file_data = javalang.parse.parse(raw_data)
        self.count_bug = count_bug
        self.count_bug_class = 0
        self.count_bug_method = 0
        self.edit_class = []
        self.edit_method = []

    def get_all_class(self):
        return [f"{self.file_data.package.name}.{i.name}" for i in self.file_data.types if type(i) is ClassDeclaration]

    def have_method(self, method_name):
        have = False
        for item in self.file_data.types:
            if type(item) is ClassDeclaration:
                for child in item.body:
                    if type(child) is MethodDeclaration and child.name == method_name:
                        have = True
        return have

    def export_in_file(self):
        save_dir_patch = os.path.dirname(self.save_path)
        if not os.path.isdir(save_dir_patch):
            os.makedirs(save_dir_patch)
        with open(self.save_path, "w") as f:
            f.write(self.raw_data)

    def get_class_position(self, _class):
        info = {
            "name": _class.name,
            "beg": 0,
            "end": 0,
            "count_bug": _class.count_bug
        }
        for item in self.file_data.types:
            if type(item) is ClassDeclaration and f"{self.file_data.package.name}.{item.name}" == _class.name:
                info["beg"] = item.position[0]
                info["end"] = item.position[0] + get_line_code_snippet(
                    self.raw_data.split("\n"), item.position[0] - 1
                )
        return info

    def get_method_position(self, method, old_version=None):
        method_name = method.name.split('(')[0].split('.')[-1]
        info = {
            "name": method_name,
            "beg": 0,
            "end": 0,
            "count_bug": method.count_bug
        }
        for item in self.file_data.types:
            if type(item) is ClassDeclaration:
                for child in item.body:
                    if type(child) is MethodDeclaration and child.name == method_name:
                        info["beg"] = child.position[0]
                        info["end"] = child.position[0] + get_line_code_snippet(
                            self.raw_data.split("\n"), child.position[0] - 1
                        )
        if old_version is not None:
            if old_version.have_method(method_name):
                info["status"] = "edit"
            else:
                info["status"] = "add"
        return info


class File:
    def __init__(self, file_name):
        self.file_name = file_name
        self.history = OrderedDict()

    def get_list_patch(self):
        all_patch = []
        old_key = None
        for key in sorted(self.history):
            data = self.history[key]
            if old_key is None and data.count_bug != 0:
                old_key = key
            elif old_key is not None:
                old_data = self.history[old_key]
                if old_data.count_bug > data.count_bug:
                    all_patch.append({
                        'bug': old_data,
                        'fix': data
                    })
                    old_key = None
                else:
                    old_key = key
        return all_patch

    def get_list_patch_method(self):
        all_patch = []
        bug_method = {}
        for key in sorted(self.history):
            data = self.history[key]
            for method in data.edit_method:
                if method.name not in bug_method and method.count_bug > 0:
                    bug_method[method.name] = {
                        'name': method.name,
                        "hash": key,
                        "count_bug": method.count_bug
                    }
                elif method.name in bug_method and bug_method[method.name]["count_bug"] > method.count_bug:
                    bug_method_data = bug_method.pop(method.name)
                    all_patch.append({
                        'bug': bug_method_data,
                        'fix': {
                            'name': method.name,
                            "hash": key,
                            "count_bug": method.count_bug
                        },
                    })
        return all_patch

    def get_list_patch_class(self):
        all_patch = []
        bug_class = {}
        for key in sorted(self.history):
            data = self.history[key]
            for _class in data.edit_class:
                if _class.name not in bug_class and _class.count_bug > 0:
                    bug_class[_class.name] = {
                        'name': _class.name,
                        "hash": key,
                        "count_bug": _class.count_bug
                    }
                elif _class.name in bug_class and bug_class[_class.name]["count_bug"] > _class.count_bug:
                    bug_class_data = bug_class.pop(_class.name)
                    all_patch.append({
                        'bug': bug_class_data,
                        'fix': {
                            'name': _class.name,
                            "hash": key,
                            "count_bug": _class.count_bug
                        },
                    })
        return all_patch


def patches_file(files: dict):
    patches = []
    for key, file_data in files.items():
        for patch in file_data.get_list_patch():
            patch['bug'].export_in_file()
            patch['fix'].export_in_file()

            bug = {
                "file_path": patch['bug'].save_path,
                "classes": [patch['bug'].get_class_position(_class) for _class in patch['bug'].edit_class],
                "methods": [patch['bug'].get_method_position(method) for method in patch['bug'].edit_method]
            }
            fix = {
                "file_path": patch['fix'].save_path,
                "classes": [patch['fix'].get_class_position(_class) for _class in patch['fix'].edit_class],
                "methods": [patch['fix'].get_method_position(method, patch['bug']) for method in
                            patch['fix'].edit_method]
            }

            patches.append(
                {
                    "bug": bug,
                    "fix": fix,
                }
            )
    return patches


def patches_class(files: dict):
    patches = []
    for key, file_data in files.items():
        for patch in file_data.get_list_patch_class():
            bug_file = file_data.history[patch['bug']['hash']]
            fix_file = file_data.history[patch['fix']['hash']]
            bug_file.export_in_file()
            fix_file.export_in_file()
            bug = {
                "file_path": bug_file.save_path,
                "class": bug_file.get_class_position(
                    BugHunterItem(patch['bug']['name'], patch['bug']['count_bug'])
                )
            }
            fix = {
                "file_path": fix_file.save_path,
                "class": fix_file.get_class_position(
                    BugHunterItem(patch['fix']['name'], patch['fix']['count_bug'])
                )
            }

            patches.append(
                {
                    "bug": bug,
                    "fix": fix,
                }
            )
    return patches


def patches_method(files: dict):
    patches = []
    for key, file_data in files.items():
        for patch in file_data.get_list_patch_method():
            bug_file = file_data.history[patch['bug']['hash']]
            fix_file = file_data.history[patch['fix']['hash']]
            bug_file.export_in_file()
            fix_file.export_in_file()
            bug = {
                "file_path": bug_file.save_path,
                "method": bug_file.get_method_position(
                    BugHunterItem(patch['bug']['name'], patch['bug']['count_bug'])
                )
            }
            fix = {
                "file_path": fix_file.save_path,
                "method": fix_file.get_method_position(
                    BugHunterItem(patch['fix']['name'], patch['fix']['count_bug'])
                )
            }

            patches.append(
                {
                    "bug": bug,
                    "fix": fix,
                }
            )
    return patches


def export_files(files: dict):
    project_files = {}
    for file_patch, file_data in files.items():
        project_files[file_patch] = []
        for key in sorted(file_data.history):
            data = file_data.history[key]
            data.export_in_file()
            project_files[file_patch].append(
                {
                    "file_path": data.save_path,
                    "classes": [data.get_class_position(_class) for _class in data.edit_class],
                    "methods": [data.get_method_position(method) for method in data.edit_method]
                }
            )
    return project_files


def export_bug_method(files: dict):
    project_files = {}
    for file_patch, file_data in files.items():
        project_files[file_patch] = []
        for key in sorted(file_data.history):
            data = file_data.history[key]
            data.export_in_file()
            project_files[file_patch].append(
                {
                    "file_path": data.save_path,
                    "bugs_methods": [data.get_method_position(method) for method in data.edit_method if
                                     method.count_bug > 0]
                }
            )
    return project_files


def export(all_project: dict, export_file_name: str, export_type: int):
    all_data = []
    export_methods = {
        1: patches_file,
        2: patches_method,
        3: export_bug_method,
        4: export_files
    }
    project_index = 0
    for project_name, files in all_project.items():
        project_index += 1
        print_progress_bar(project_index, len(all_project.keys()), prefix="Start export dataset: ")
        data = {
            "project_name": project_name,
        }
        if export_type > 2:
            data['files'] = export_methods[export_type](files)
        else:
            data['patches'] = export_methods[export_type](files)
        all_data.append(data)
    with open(export_file_name, "w") as export_file:
        export_file.write(json.dumps(all_data))


def main(repos: list, export_file: str, export_type: int):
    all_project = {}
    repo_index = 0
    for repo_item in repos:
        repo_index += 1
        repo_name = repo_item.get('name', None)
        rep_url = repo_item.get('url', None)
        if repo_name is None or rep_url is None:
            continue
        print(f"Start load {repo_name}  {repo_index}/{len(repos)}")
        repo_dir = os.path.join(REPOS_DIR, repo_name)
        bug_hunter_dir = os.path.join(BASE_BUG_HUNTER_DIR, repo_name)
        if not os.path.exists(repo_dir):
            print(f"Clone {rep_url}")
            git.Repo.clone_from(rep_url, repo_dir)

        repo = git.Repo(repo_dir)
        files = {}
        file_data = pandas.read_csv(bug_hunter_dir + '/file.csv')
        class_data = pandas.read_csv(bug_hunter_dir + '/class.csv')
        method_data = pandas.read_csv(bug_hunter_dir + '/method-p.csv')
        for index, file_item in file_data.iterrows():
            print_progress_bar(index, len(file_data) - 1, prefix=f"Start parse dataset for {repo_name}:")
            _hash = file_item['Hash']
            file_path = file_item['LongName']
            count_bug = file_item['Number of Bugs']
            if file_path not in files:
                files[file_path] = File(file_path)
            repo.git.stash()
            repo.git.checkout(_hash)
            commit = repo.head.commit
            commit_data = str(commit.committed_datetime.astimezone())
            try:
                with open(f'{repo_dir}/{file_path}') as java_file:
                    raw_data = java_file.read()

                    file_commit = FileCommit(
                        raw_data,
                        os.path.join(FILE_DIR, repo_name, _hash, file_path),
                        count_bug,
                        _hash,
                    )
                    files[file_path].history[commit_data] = file_commit

                    for file_class in file_commit.get_all_class():
                        class_filter = class_data[(class_data.Hash == _hash) & (class_data.LongName == file_class)]
                        method_filter = method_data[(method_data.Hash == _hash) & (method_data.Parent == file_class)]
                        for class_index, class_data_item in class_filter.iterrows():
                            file_commit.count_bug_class = class_data_item['Number of Bugs']
                            file_commit.edit_class.append(
                                BugHunterItem(class_data_item.LongName, class_data_item['Number of Bugs'])
                            )
                        for method_index, method_data_item in method_filter.iterrows():
                            file_commit.count_bug_method = method_data_item['Number of Bugs']
                            file_commit.edit_method.append(
                                BugHunterItem(method_data_item.LongName, method_data_item['Number of Bugs'])
                            )
            except JavaSyntaxError:
                continue

        all_project[repo_name] = files
    export(all_project, export_file, export_type)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Generate dataset')
    parser.add_argument(
        'repositories', type=str, help='JSON со списком репозиториев в формате [{"name":"<name>","url":"<url>"},...]'
    )
    parser.add_argument(
        'export_file', type=str, help='Имя файла для сохранения экспорта'
    )
    parser.add_argument(
        'export_type', default=1, type=int,
        help='Типы JSON экспорта: \n'
             '\t 1 - bug-fix грануляциия файл\n'
             '\t 2 - bug-fix грануляциия метод\n'
             '\t 3 - bug-fix грануляциия метод\n'
             '\t 4 - экспорт методов с багом\n'
             '\t 5 - экспорт данных о файлах\n'
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")
    args = parser.parse_args()
    init()
    with open(args.repositories) as f:
        main(json.loads(f.read()), args.export_file, args.export_type)

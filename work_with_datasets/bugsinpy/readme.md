# BugsInPy

493 bugs, 17 real-world projects

Sources:
- Paper + video: https://dl.acm.org/doi/abs/10.1145/3368089.3417943
- Youtube: https://www.youtube.com/watch?v=8K1NEIONrzU
- Docker container: https://hub.docker.com/r/soarsmu/bugsinpy
- GtHub project: https://github.com/soarsmu/BugsInPy
- Reddit: https://www.reddit.com/r/ESECFSE/comments/jkbdki/bugsinpy_a_database_of_existing_bugs_in_python/

### Paper

- 17 real-world projects: they represent *the diverse domains* (machine learning, developer tools, scientific computing, web frameworks, etc) that Python is used for. These projects are Python3 open-source projects on GitHub, each with more than 10,000 stars. Constructing and manually validating the bugs and test cases for this dataset required significant effort, and took an estimated *831 man-hours*

- BugsInPy’s architecture is similar to Defects4J. It has three main components (highlighted in gray): a bug database, a database abstraction layer, and a test execution framework. The bug database contains the collected bug metadata with links to the original Git repositories. The database abstraction layer allows access to bugs without the knowledge on how the bug data is stored. It abstracts details on how to checkout and build faulty or fixed source code versions. The test execution framework allows execution of tools for testing/debugging on the collected bug data.

- bugs in BugsInPy:
  - The bug is in source code. We include only bug fixes involving changes in source code and exclude those that change configurations, build scripts, documentation, and test cases
  - The bug is reproducible. At least one of the test cases from the fixed version should fail on the faulty version
  - The bug is isolated. The faulty and fixed versions differ only by code changes required to fix the bug and no other unrelated changes are involved (e.g., refactoring or feature addition)

| Project                   | Bugs | LoC     | Test LoC  | # Tests | # Stars |
|---------------------------|------|---------|-----------|---------|---------|
| ansible/ansible           | 18   | 207.3K  | 128.8K    | 20434   | 43.6K   |
| cookiecutter/cookiecutter | 4    | 4.7K    | 3.4K      | 300     | 12.2K   |
| cool-RR/PySnooper         | 3    | 4.3K    | 3.6K      | 73      | 13.5K   |
| explosion/spaCy           | 10   | 102K    | 13K       | 1732    | 16.6K   |
| huge-success/sanic        | 5    | 14.1K   | 8.1K      | 643     | 13.9K   |
| jakubroztocil/httpie      | 5    | 5.6K    | 2.2K      | 309     | 47K     |
| keras-team/keras          | 45   | 48.2K   | 17.9K     | 841     | 48.6K   |
| matplotlib/matplotlib     | 30   | 213.2K  | 23.2K     | 7498    | 11.6K   |
| nvbn/thefuck              | 32   | 11.4K   | 6.9K      | 1741    | 53.9K   |
| pandas-dev/pandas         | 169  | 292.2K  | 196.7K    | 70333   | 25.4K   |
| psf/black                 | 15   | 96K     | 5.8K      | 142     | 16.4K   |
| scrapy/scrapy             | 40   | 30.7K   | 18.6K     | 2381    | 37.4K   |
| spotify/luigi             | 33   | 41.5K   | 20.7K     | 1718    | 13.4K   |
| tiangolo/fastapi          | 16   | 25.3K   | 16.7K     | 842     | 15.3K   |
| tornadoweb/tornado        | 16   | 27.7K   | 12.9K     | 1160    | 19.2K   |
| tqdm/tqdm                 | 9    | 4.8K    | 2.3K      | 88      | 14.9K   |
| ytdl-org/youtube-dl       | 43   | 124.5K  | 5.2K      | 2367    | 67.3K   |
| Total                     | 493  | 1253.5K | 486K      | 112602  | 470.2K  |

### Docker container

```
# docker pull soarsmu/bugsinpy
# docker images
# docker run -it soarsmu/bugsinpy /bin/bash

# ls -l BugsInPy/projects/

drwxr-xr-x 21 root root 4096 Jun 20  2020 .
drwxr-xr-x  5 root root 4096 Jun 20  2020 ..
drwxr-xr-x  3 root root 4096 Jun 20  2020 PySnooper
drwxr-xr-x  3 root root 4096 Jun 20  2020 ansible
drwxr-xr-x  3 root root 4096 Jun 20  2020 black
drwxr-xr-x  3 root root 4096 Jun 20  2020 cookiecutter
drwxr-xr-x  3 root root 4096 Jun 20  2020 fastapi
drwxr-xr-x  3 root root 4096 Jun 20  2020 glances
drwxr-xr-x  3 root root 4096 Jun 20  2020 httpie
drwxr-xr-x  3 root root 4096 Jun 20  2020 keras
drwxr-xr-x  3 root root 4096 Jun 20  2020 luigi
drwxr-xr-x  3 root root 4096 Jun 20  2020 matplotlib
drwxr-xr-x  3 root root 4096 Jun 20  2020 pandas
drwxr-xr-x  3 root root 4096 Jun 20  2020 sanic
drwxr-xr-x  3 root root 4096 Jun 20  2020 scrapy
drwxr-xr-x  3 root root 4096 Jun 20  2020 spacy
drwxr-xr-x  3 root root 4096 Jun 20  2020 thefuck
drwxr-xr-x  3 root root 4096 Jun 20  2020 tornado
drwxr-xr-x  3 root root 4096 Jun 20  2020 tqdm
drwxr-xr-x  3 root root 4096 Jun 20  2020 you-get
drwxr-xr-x  3 root root 4096 Jun 20  2020 youtube-dl

# ls -l BugsInPy/framework/bin/

-rwxr-xr-x 1 root root 5988 Jun 20  2020 bugsinpy-checkout
-rwxr-xr-x 1 root root 5843 Jun 20  2020 bugsinpy-compile
-rwxr-xr-x 1 root root 7712 Jun 20  2020 bugsinpy-coverage
-rwxr-xr-x 1 root root 2158 Jun 20  2020 bugsinpy-fuzz
-rwxr-xr-x 1 root root 3764 Jun 20  2020 bugsinpy-info
-rwxr-xr-x 1 root root 5619 Jun 20  2020 bugsinpy-mutation
-rwxr-xr-x 1 root root 4923 Jun 20  2020 bugsinpy-test
```

Command | Description
--- | ---
info | Get the information of a specific project or a specific bug
checkout	| Checkout buggy or fixed version project from dataset
compile	| Compile sources from project that have been checkout
test	| Run test case that relevant with bug, single-test case from input user, or all test cases from project
coverage |	Run code coverage analysis from test case that relevant with bug, single-test case from input user, or all test cases
mutation |	Run mutation analysis from input user or test case that relevant with bug
fuzz | Run a test input generation from specific bug

```
# cd BugsInPy/framework/bin/

# bugsinpy-info -p keras

Summary for Project keras
--------------------------------------------------------------------------------
Script dir	: /BugsInPy/framework/bin
Base dir	: /BugsInPy
Data dir	: /BugsInPy/projects/keras
--------------------------------------------------------------------------------
Project name	: keras
Status 		: OK
Github URL	: https://github.com/keras-team/keras
Number of bugs	: 91
--------------------------------------------------------------------------------

# bugsinpy-checkout -p keras -i 1 -v 1 -w /temp/projects/

PROJECT_NAME: keras
BUG_ID: 1
VERSION_ID: 1
WORK_DIR: /temp/projects
https://github.com/keras-team/keras
github_url="https://github.com/keras-team/keras"
status="OK"
Cloning into '/temp/projects/keras'...
remote: Enumerating objects: 22, done.
remote: Counting objects: 100% (22/22), done.
remote: Compressing objects: 100% (22/22), done.
remote: Total 34278 (delta 0), reused 2 (delta 0), pack-reused 34256
Receiving objects: 100% (34278/34278), 15.01 MiB | 1.97 MiB/s, done.
Resolving deltas: 100% (24784/24784), done.
HEAD is now at ecac367b Fix h5py group naming while model saving (#13477)
'/temp/projects/keras/keras/engine/saving.py' -> '/BugsInPy/projects/keras/bugs/1/saving.py'
'/temp/projects/keras/tests/keras/metrics_training_test.py' -> '/BugsInPy/projects/keras/bugs/1/metrics_training_test.py'
'/temp/projects/keras/tests/test_model_saving.py' -> '/BugsInPy/projects/keras/bugs/1/test_model_saving.py'
'/temp/projects/keras/tests/test_model_saving.py' -> '/BugsInPy/projects/keras/bugs/1/test_model_saving.py'
HEAD is now at 4d59675b Update core.py (#13472)

# bugsinpy-checkout -p youtube-dl -v 0 -i 2 -w /temp/projects

PROJECT_NAME: youtube-dl
BUG_ID: 2
VERSION_ID: 0
WORK_DIR: /temp/projects
https://github.com/ytdl-org/youtube-dl
github_url="https://github.com/ytdl-org/youtube-dl"
status="OK" 
cause="N.A."
Cloning into '/temp/projects/youtube-dl'...
remote: Enumerating objects: 43, done.
remote: Counting objects: 100% (43/43), done.
remote: Compressing objects: 100% (37/37), done.
remote: Total 101126 (delta 17), reused 18 (delta 5), pack-reused 101083
Receiving objects: 100% (101126/101126), 60.66 MiB | 2.15 MiB/s, done.
Resolving deltas: 100% (74755/74755), done.
HEAD is now at 9d6ac71c2 [extractor/common] Fix extraction of DASH formats with the same representation id (closes #15111)
'/temp/projects/youtube-dl/test/test_InfoExtractor.py' -> '/BugsInPy/projects/youtube-dl/bugs/2/test_InfoExtractor.py'
HEAD is now at 84f085d4b [aws] fix canonical/signed headers generation in python 2(closes #15102)
``` 

### Использование BugsInPy в zephyr

BugsInPy содержит 493 примера дефектного кода и исправляющие патчи:
- один пример дефектного кода может распространятся на несколько файлов,
- в одном файле дефектный код может распространятся на несколько методов.

Пока не очень понятно как работать с дефектами, которые не локализованы в одном фрагменте. Поэтому вытащим только код, который помечен как дефектный и дефект содержится в одном методе.

1. [x] выбрать патчи `projects/*/bugs/*/bug_patch.txt`, которые содержат `diff` ровно по одному файлу
2. [x] создать список таких пар `project, bug`
3. [x] собрать фрагменты кода с помощью `bugsinpy-checkout`


### Запуск

1. В контейнер лежит код с ошибкой: при скачивании имеем одинаковые версии для старого и нового исходного файла. Запускал так:
```bash
#docker pull soarsmu/bugsinpy
#docker images

docker run -v $HOME/zephyr:/zephyr -it soarsmu/bugsinpy /bin/bash

root@59ti45t:/#

apt-get update
apt-get install python3-pip
pip3 install whatthepatch

cd /zephyr/datasets/bugsinpy
python3 get_bugs.py
```

2. В репозитории `BugsInPy` эта ошибка исправлена. Скрипт `get_bugs.py` надо скопировать в папку `github.BugsInPy/framework/bin/` и запустить. Результат --- архив  `20210118_114541.zip`.

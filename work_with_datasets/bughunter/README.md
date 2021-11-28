## BugHunter

Скрипт `main.py` на вход получает файл `repositories.json`.
В датасете BugHunter нет связи bug-fix. 

Поэтому для создания таких пар bug-fix использовался следующий алгоритм:
1. Получаем все файлы, которые содержатся в датасете BugHunter
2. Сортируем данные по каждому файлу по времени коммита
3. Бежим по отсортированным коммитам и смотрим бали ли баги в файле, если да, то запоминаем этот коммит как bug
4. Продолжаем бежать по отсортированным коммитам и если кол-во багов уменьшилось, если да, то запоминаем этот коммит как fix
5. Создаем пару bug-fix и продолжаем бежать по отсортированным коммитам и возвращаемся на пункт 3

При сборе данных было обнаружено, что в датасете BugHunter существуют файлы, в которых нет багов или нет исправлений.

[comment]: <> (Скрипт `main.py` получает все файлы из BugHunter и разбирает каждый полученный файл на токены. А потом эус)

[comment]: <> (При сборе данных было обнаружено, что в датасете BugHunter существуют файлы, в которых нет багов или нет исправлений. По)

[comment]: <> (ним пары вида `['bug_hash', 'fix_hash']` получить нельзя.)

### Запуск

```bash
$ curl https://md-datasets-public-files-prod.s3.eu-west-1.amazonaws.com/50be6c77-7146-485e-91b6-83e84668982c -o BugHunterDataset.zip
$ mkdir data
$ unzip BugHunterDataset.zip -d data
$ python3 -m venv env
$ source env/bin/activate
$ pip install -r requirements.txt
$ python main repositories.json export.json <type_export>
```

Скрипт автоматически скачивает все репозитори которые есть в repositories.json

### repositories.json

Файл служит для связи имени проекта и url-адреса репозитория. Данный файл имеет следующий формат:

```json
[
  {
    "name": "<name>",
    "url": "<repo-url>"
  },
  ...
]

```

### Экспорт

Экспорт происходит в json файл и имеет следующие форматы:

* Экспорт патчей по файлам:

```json
[
  {
    "project_name": "<project_name>",
    "patch": [
      {
        "bug": {
          "file_path": "<file_path>",
          "classes": [
            {
              "name": "<class_name>",
              "beg": "<number_start_line>",
              "end": "<number_end_line>"
            },
            ...
          ],
          "method": [
            {
              "name": "<method_name>",
              "beg": "<number_start_line>",
              "end": "<number_end_line>"
            },
            ...
          ]
        },
        "fix": {
          "file_path": "<file_path>",
          "classes": [
            {
              "name": "<class_name>",
              "beg": "<number_start_line>",
              "end": "<number_end_line>"
            },
            ...
          ],
          "method": [
            {
              "name": "<method_name>",
              "beg": "<number_start_line>",
              "end": "<number_end_line>",
              "status": "<add|edit>"
            },
            ...
          ]
        }
      }
    ]
  },
  ....
]

```

* Экспорт патчей по классам:
  
```json
[
  {
    "project_name": "<project_name>",
    "patch": [
      {
        "bug": {
          "file_path": "<file_path>",
          "class": {
            "name": "<class_name>",
             "beg": <number_begin_line>,
            "end": <number_end_line>,
            "count_bug": <count_bug>
          }
        },
        "fix": {
          "file_path": "<file_path>",
          "class": {
            "name": "<class_name>",
             "beg": <number_begin_line>,
            "end": <number_end_line>,
            "count_bug": <count_bug>
          }
        }
      },
      ...
    ]
  },
  ...
]
```

* Экспорт патчей по методам:

```json
[
  {
    "project_name": "<project_name>",
    "patch": [
      {
        "bug": {
          "file_path": "<file_path>",
          "method": {
            "name": "<method_name>",
             "beg": <number_begin_line>,
            "end": <number_end_line>,
            "count_bug": <count_bug>
          }
        },
        "fix": {
          "file_path": "<file_path>",
          "method": {
            "name": "<method_name>",
             "beg": <number_begin_line>,
            "end": <number_end_line>,
            "count_bug": <count_bug>
          }
        }
      },
      ...
    ]
  },
  ...
]
```

* Экспорт методов с багами:

```json
{
  "project_name": "antlr4",
  "files": {
    "<file_path>": [
      {
        "file_path": "<file_path>",
        "bugs_methods": [
          {
            "name": "<method_name>",
            "beg": <number_begin_line>,
            "end": <number_end_line>,
            "count_bug": <count_bug>
          },
          ...
        ]
      },
      ...
    ]
  }
}
```

* Экспорт данных о том какие методы, классы изменены в файле и содержат ли они баги:

```json
[
  {
    "project_name": "<project_name>",
    "files": {
      "<file_path>": [
        {
          "file_path": "<file_path>",
          "classes": [
            {
              "name": "<class_name>",
              "beg": <number_begin_line>,
              "end": <number_end_line>,
              "count_bug": <count_bug>
            },
            ...
          ],
          "methods": [
            {
              "name": "<method_name>",
              "beg": <number_begin_line>,
              "end": <number_end_line>,
              "count_bug": <count_bug>
            },
            ...
          ]
        },
        ...
      ]
    }
  }
]
```

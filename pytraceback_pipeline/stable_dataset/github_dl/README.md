Данный код нужен, чтобы среди всех репозиториев гитхаба отобрать самые интересные для проекта.

# get_repos.py #

Скачивает список всех публичных репозиториев гитхаба, используя API

Скачивание ведётся по 100 000 штук (константа REPOS_PER_BUCKET в коде).

Пример запуска: python3 get_repos.py <bucket_id>, bucket_id номер группы из 100000 штук которую следует скачать.

Константа TOKENS содержит токен для доступа к API гитхаба, перед запуском следует указать валидный токен.

В результате получаются файлы pub_repos_X.json.gz содержащие информацию о публичных репозиториях в формате json, сжатый gz. Примерный размер выходных файлов - 50ГБ.


# get_repos_details.py #

Скачивает детальную информацию о публичных репозиториях гитхаба, используя GraphQL-API. Информация включает в себя количество звёздочек в проекте, языки на которых он написан, количество форков, информацию о лицензии, количество человек, которые следят за проектом (watchers), количество пулл-реквестов, количество релизов, и т.д. Если репозиторий является форком, то дополнительно сохраняется информация о родительском репозитории. Дополнительно удаляется информация о репозитории, которая не представляет потенциальной ценности для проекта.

Константа TOKENS содержит токен для доступа к API гитхаба, перед запуском следует указать валидный токен.

Константа IGNORE_NODE_IDS содержит те репозитории, при попытке загрузить которые, гитхаб возвращает фатальную ошибку.

Запускается без параметров, ищет в текущем каталоге файлы, созданные скриптом get_repos.py, которые ещё не обрабатывались.

Информация об репозиториях записывается в файл pub_repos_details_X.json.gz в формате json, сжатый gz. Примерный размер выходных файлов - 15гб.

Информация о возникших нефатальных ошибках попадает в файл pub_repos_details_errors_X.json.

# parse_repos_details.py #

Фильтрует информацию содержащуюся в файлах pub_repos_details_X.json.gz, оставляя только репозитории у которых основной язык - Python.

Файлы pub_repos_details_X.json.gz, генерируемые скриптом get_repos_details.py ищутся в подкаталоге github_repos_details, перед запуском нужно переместить интересующие файлы в этот каталог.

На выходе генерируется файл python_repos.json, содержащий отфильтрованную информацию. Его размер - приблизительно 13ГБ

# parse_repos_details_python.py #

Принимает в качестве входа файл python_repos.json, сгенерированный скриптом parse_repos_details.py и дополнительно фильтрует репозитории по следующим критериям: не форк, есть хотя бы 1 звёздочка, есть хотя бы 1 форк, есть хотя бы 1 pull-реквест.

На выходе генерируется файл python_repos_interesting.json, содержащий информацию о репозиториях, которые удовлетворяют вышеуказанным критериям, его размер 192МБ

# parse_repos_details_python_top.py #

Принимает в качестве входа файл python_repos_interesting.json, сгенерированный скриптом parse_repos_details_python.py и дополнительно фильтрует репозитории по следующим критериям: есть хотя бы 25 звёздочек, хотя бы 25 форков и хотя бы 25 pull-реквестов.

На выходе генерируется файл python_repos_interesting_top.json, содержащий информацию об именах репозиториев, которые удовлетворяют вышеуказанным критериям, его размер 240КБ

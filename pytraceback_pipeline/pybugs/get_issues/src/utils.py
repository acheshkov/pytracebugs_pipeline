# import os

# from git import Repo
from urllib.parse import urlparse, parse_qs

import requests
from pandas import json_normalize
from .local_settings import *

GITHUB_ROOT_ENDPOINT = "https://api.github.com"


def _fetch_github_api_data(url,
                           accept_header,
                           params,
                           key_name,
                           first_page):
    headers = {"Accept": accept_header}
    r = requests.get(url,
                     auth=(params['username'], params['token']),
                     headers=headers,
                     params=params)
    data = json_normalize(r.json())
    data = data if not key_name else data[key_name]
    if not first_page:
        return data
    else:
        return {'query_results': data,
                'pagination': _compute_pagination(r)}


def _compute_pagination(api_results):
    last_url = api_results.links.get('last')
    if last_url:
        p = urlparse(last_url.get('url'))
        try:
            pages = int(parse_qs(p.query).get('page')[0])
        except ValueError:
            pages = 1
        pagination = {'page': 1, 'total_pages': pages}
    else:
        pagination = {}
    return pagination


def fetch_github_paged_api_data(api_path,
                                params,
                                key_name,
                                accept_header=None):
    api_path = api_path.strip("/")
    url = "{}/{}".format(GITHUB_ROOT_ENDPOINT, api_path)
    if not accept_header:
        accept_header = "application/vnd.github.v3+json"
    return _fetch_github_api_data(url,
                                  accept_header,
                                  params,
                                  key_name,
                                  first_page='page' not in params.keys())


# def search_github(resource, search_query, page=None):
#     params = {"q": search_query, "per_page": 100}
#     if page:
#         params["page"] = page
#
#     search_res = fetch_github_api_data(
#         "/search/{}".format(resource),
#         accept_header="application/vnd.github.mercy-preview+json",
#         params=params,
#         raw_response=True)
#
#     res = search_res.json()
#
#     if not page:
#         last_url = search_res.links.get("last")
#         if last_url:
#             p = urlparse(last_url.get("url"))
#             try:
#                 pages = int(parse_qs(p.query).get("page")[0])
#             except ValueError as ve:
#                 pages = 1
#
#             pagination = {
#                 "page": 1,
#                 "total_pages": pages,
#             }
#             res["pagination"] = pagination
#     return res
#
#
# def clone_git_repo(full_name, repo_url, repos_dir="./repos"):
#     pdir_name = full_name.replace("/", "_")
#     prepo_path = os.path.join(repos_dir, pdir_name)
#
#     if not os.path.exists(repos_dir):
#         os.makedirs(repos_dir)
#
#     if os.path.exists(prepo_path):
#         print("Repo exists in {}, not going to clone.".format(
#             pdir_name))
#     else:
#         os.makedirs(prepo_path)
#         print(" cloning {} please wait ...".format(repo_url))
#         Repo.clone_from(repo_url, prepo_path)
#         print("finished cloning in {}.".format(prepo_path))

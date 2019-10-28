#!/usr/bin/env python

import gitUtil
import requests
import yaml
import urllib.request
import os
import json
import sys
from os.path import expanduser
from github import Github
from git import Repo, GitCommandError, RemoteProgress, Git
import logging
import logging.handlers

logger = logging.getLogger()
# handler = logging.handlers.WatchedFileHandler(path_log)
handler = logging.StreamHandler()
# formatter = logging.Formatter(logging.BASIC_FORMAT)
formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - %(message)s')

handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class Error(Exception):
    """An error that is not a bug in this script."""


def ensure_dir(dir):
    if not os.path.isdir(dir):
        os.makedirs(dir)


def get_json_and_headers(url):
    """Perform HTTP GET for a URL, return deserialized JSON and headers.
    Returns a tuple (json_data, headers) where headers is an instance
    of email.message.Message (because that's what urllib gives us).
    """
    with requests.get(url) as r:
        # We expect Github to return UTF-8, but let's verify that.
        content_type = r.headers['Content-Type'].lower()
        if content_type not in ('application/json; charset="utf-8"',
                                'application/json; charset=utf-8'):
            raise Error('Did not get UTF-8 JSON data from {0}, got {1}'
                        .format(url, content_type))
        return r.json(), r.headers


def get_github_list(url, batch_size=100):
    """Perform (a series of) HTTP GETs for a URL, return deserialized JSON.
    Format of the JSON is documented at
    http://developer.github.com/v3/repos/#list-organization-repositories
    Supports batching (which Github indicates by the presence of a Link header,
    e.g. ::
        Link: <https://api.github.com/resource?page=2>; rel="next",
              <https://api.github.com/resource?page=5>; rel="last"
    """
    # API documented at http://developer.github.com/v3/#pagination
    res, headers = get_json_and_headers(
        '{0}?per_page={1}'.format(url, batch_size))

    page = 1
    while 'rel="next"' in headers.get('Link', ''):
        page += 1
        more, headers = get_json_and_headers('{0}?page={1}&per_page={2}'.format(
            url, page, batch_size))
        res += more
    return res


def pull():
    logger.info()


def run():
    config = yaml.load(open('repos.yml'))
    repo_dir = os.path.join('./', config['local-path'])
    organization = config['organization'] or ''
    branch_name = config['branch-name'] or ''
    commit_message = config['commit-message'] or ''
    
    f = open(expanduser("~/.github"), "r")
    token = f.readline()[len("oauth="):].lstrip().rstrip()
    
    g = Github(token)
    user = g.get_user()
    org = g.get_organization(organization)

    if 'repos-configs-map' in config:
        for item in config['repos-configs-map']:
            config_file = item['config-file'] or 'mergify.yml'
            repos = item['repos'] or []

            for repo in repos:

                repository = org.get_repo(repo)
                gitUtil.fork_and_clone(org=org, repo=repository, user=user, dir=repo_dir)
                
                gitUtil.update(org=org, repo=repository, user=user,
                       dir=repo_dir, branch=branch_name, message=commit_message, configFile=config_file)

                # gitUtil.clean_up(gh=g, repo_full_name='{}/{}'.format(user.login, repo))


run()

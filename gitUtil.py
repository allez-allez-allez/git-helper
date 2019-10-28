from github import Github
import sys
from os.path import expanduser
import os
from git import Repo, GitCommandError
import logging
import json
import shutil

logger = logging.getLogger()
# f = open(expanduser("~/.github"), "r")
# token = f.readline()[len("oauth="):].lstrip().rstrip()
# g = Github(token)
# user = g.get_user()
# url = str(sys.argv[1]).replace("https://github.com/", "").split("/")
# org = g.get_organization(url[0])
# repo = org.get_repo(url[1])
# my_fork = user.create_fork(repo)
# try:
#     local_repo = Repo.clone_from("git@github.com:" + str(user.login) + "/" + str(repo.name) + ".git",
#                                  os.getcwd() + "/" + str(repo.name), branch="master")
#     Repo.create_remote(local_repo, "upstream", "git@github.com:" + url[0] + "/" + url[1] + ".git")
# except GitCommandError:
#     print("Directory already exists and is not empty. Not cloning.")
#     pass


def print_message():
    logger.error("Missing parameters...")


def fork_and_clone(**kwargs):

    ('org' in kwargs and 'repo' in kwargs and 'user' in kwargs and 'dir' in kwargs) or print_message()
    
    org = kwargs['org'] or None
    repo = kwargs['repo'] or None
    user = kwargs['user'] or None
    my_fork = user.create_fork(repo)
    logger.info('Repo forked.')
    try:
        branch = "master"
        if repo.name == "watchmaker":
            branch = "develop"

        local_repo = Repo.clone_from("git@github.com:" + str(user.login) + "/" + str(repo.name) + ".git",
                                     os.path.join(os.getcwd(), kwargs['dir'], str(user.login), str(repo.name)), branch=branch)
        Repo.create_remote(local_repo, "upstream", "git@github.com:" +
                           str(org.login) + "/" + str(repo.name) + ".git")
        logger.info('Repo cloned.')
    except GitCommandError:
        logger.info("Directory '{}/{}' already exists and is not empty. Not cloning.".format(
            kwargs['dir'], my_fork.full_name))
        pass

def update(org=None, repo=None, user=None, dir=None, branch=None, message=None, configFile=None):
    """[summary]

    Keyword Arguments:
        org {[type]} -- [description] (default: {None})
        repo {[type]} -- [description] (default: {None})
        dir {[type]} -- [description] (default: {None})
        configfile {[type]} -- [description] (default: {None})
    """
    # checkout repo
    local_repo = Repo(os.path.join(dir, user.login, repo.name))
    local_repo.create_head(branch)
    new_branch = local_repo.heads[branch]
    local_repo.head.reference = new_branch

    # copy .mergify.yml
    shutil.copy2(os.path.join(os.getcwd(), configFile),
                 os.path.join(local_repo.working_tree_dir, ".mergify.yml"))

    has_changed = False

    # add mergify
    for file in local_repo.untracked_files:
        logger.info(f'Added untracked file: {file}')
        local_repo.git.add(file)
        if has_changed is False:
            has_changed = True

    if local_repo.is_dirty() is True:
        for file in local_repo.git.diff(None, name_only=True).split('\n'):
            if file:
                logger.info(f'Added file: {file}')
                local_repo.git.add(file)
                if has_changed is False:
                    has_changed = True

    if has_changed:
        last_commit = local_repo.head.commit
        
        if last_commit.summary != message:
            # new commit
            local_repo.git.commit('-S','-m', message)
            local_repo.git.push('origin', branch)
            logger.info(f'Changes committed')
        else:
            # amend last commit
            local_repo.git.commit('--amend', '--no-edit')
            local_repo.git.push('origin', branch, '-f')
            logger.info(f'Changes ammended')

        logger.info(f'Changes pushed')
    else:
        logger.info(f'No changes')

def create_pull(**kwargs):
    ('org' in kwargs and 'repo' in kwargs and 'dir' in kwargs) or print_message()

def clean_up(gh=None, repo_full_name=None):
    if gh:
        try:
            logger.info('Cleaning up...')
            repo = gh.get_repo(repo_full_name)
            
            # deleting gh repo
            repo.delete()
            logger.info(f'Github repository {repo_full_name} deleted...')
            
            # deleting local directories
            local_dir_path = os.path.join('repos', repo_full_name)
            shutil.rmtree(local_dir_path)
            logger.info(f'Directory {local_dir_path} deleted...')
            logger.info('Cleaning up finished.')
        except Exception:
            logger.info(f'Github repository {repo_full_name} does not exit. Skip...')
            pass
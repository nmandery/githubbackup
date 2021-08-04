#!/usr/bin/env python
"""
This script clones all public repositories of a github user
to create local backups and keeps those backups up-to-date.
"""

import http.client
import json
import argparse
import sys
import os
import os.path
import subprocess


def get_repos(username):
    conn = http.client.HTTPSConnection("api.github.com")
    page = 1
    repos = []
    while True:
        conn.request("GET", f"/users/{username}/repos?page={page}", headers={'User-Agent': 'githubbackup.py'})
        response = conn.getresponse()
        if response.status == 404:
            print("no such github user found")
            sys.exit(1)
        if response.status != 200:
            raise Exception("calling github api failed with http status code %d", response.status)
        
        _repos = json.loads(response.read())
        if len(_repos) == 0:
            break
        repos.extend(_repos)
        page += 1
    return repos 

def clone_and_update(url, targetdir):
    if os.path.isdir(targetdir):
        old_working_dir=os.getcwd()
        os.chdir(targetdir)
        # http://stackoverflow.com/questions/6150188/how-to-update-a-git-clone-mirror
        rc=subprocess.call(['git', 'remote', 'update'])
        if rc!=0:
            print("could not update %s" % targetdir)
            return False
        os.chdir(old_working_dir)
    else:
        # this creates a bare repo.
        # http://stackoverflow.com/questions/67699/how-do-i-clone-all-remote-branches-with-git
        rc=subprocess.call(["git", "clone", "--mirror", url, targetdir])
        return rc==0
    return True


def run():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('username', help='github username')
    parser.add_argument('directory', help='target directory for the cloned repositories')
    parser.add_argument('--exclude-forks', action='store_const', const=True, default=False)
    args = parser.parse_args()
    if not os.path.isdir(args.directory):
        print("%s is not a directory" % args.directory)
        sys.exit(1)

    print("fetching repository list")
    success=True
    for repo in get_repos(args.username):
        if args.exclude_forks and repo.get("fork", False):
            continue

        print("creating backup from %s" % repo['name'])
        rc=clone_and_update(repo['git_url'], os.path.join(args.directory, repo['name']))
        if not rc:
            success=False

    if not success:
        print("could not backup all repositories")
        sys.exit(1)

run()

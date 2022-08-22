import os
import csv
import subprocess
import requests
import logging
import sys
import json
from retry import retry


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']
GITEE_PAT = os.environ['GITEE_PAT']

WORKDIR = os.getcwd()
repo_info_csv = 'repo_info.csv'


def read_csv(repo_info_csv):
    repo_info_list = list()
    with open(repo_info_csv) as fh:
        rd = csv.DictReader(fh, delimiter=',')
        for row in rd:
            repo_info_list.append(dict(row))
    return repo_info_list


def get_repo_name(target_repo):
    """Generate repo name from target_repo

    Args:
        target_repo (str): taget_repo

    Returns:
        str: repo name
    """
    return target_repo.split('/')[-1].replace('.git', '')


def sync_repo(source_repo, target_repo, repo_dir=None):
    logging.info('Sync {} to {}...'.format(source_repo, target_repo))
    repo_dir = repo_dir if repo_dir else source_repo.split('/')[-1]
    tmp_dir = '/home/runner/work/github_sync_to_gitee/temp'

    args = {
        'source_repo': source_repo,
        'target_repo': target_repo,
        'repo_dir': repo_dir,
        'USERNAME': USERNAME,
        'PASSWORD': PASSWORD,
        'tmp_dir': tmp_dir
    }
    command = 'rm -rf {tmp_dir} && mkdir -p {tmp_dir} && cd {tmp_dir} && git clone --bare {source_repo} {tmp_dir}/{repo_dir} && cd {tmp_dir}/{repo_dir} && git push --force --mirror https://{USERNAME}:{PASSWORD}@{target_repo}'.format(
        **args)
    logging.info(command)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    out, err = process.communicate()
    process.wait()
    logging.info(out)
    if process.returncode:
        logging.error('Return code: {}'.format(process.returncode))
    else:
        logging.info('Return code: {}'.format(process.returncode))


def get_all_repo():
    url = "https://gitee.com/api/v5/user/repos?access_token={GITEE_PAT}&sort=full_name&per_page=2000".format(
        GITEE_PAT=GITEE_PAT)
    resp = requests.get(url)
    response_text = resp.text
    all_repo_dict = json.loads(response_text)
    return [x["name"] for x in all_repo_dict]


@retry((ConnectionResetError, urllib3.exceptions.ProtocolError, requests.exceptions.ConnectionError), tries=10, delay=5, jitter=5)
def update_repo_info(source_repo, repo_name):
    url = "https://gitee.com/api/v5/repos/{}/{}".format(USERNAME, repo_name)

    json_data = {
        "access_token": GITEE_PAT,
        "name": repo_name,
        "description": "Mirror of " + source_repo,
        "has_issues": "true",
        "has_wiki": "true",
        "can_comment": "true"
    }
    resp = requests.patch(url, json=json_data)
    if resp.status_code == 200:
        logging.info('Repo {} updated successfully'.format(repo_name))
    else:
        logging.error('Repo {} update failed, return message {}'.format(
            repo_name, resp.text))


def create_repo(source_repo, repo_name):
    logging.info('Create new repo {}'.format(repo_name))
    url = "https://gitee.com/api/v5/user/repos"
    json_data = {
        "access_token": GITEE_PAT,
        "name": repo_name,
        "description": "Mirror of " + source_repo,
        "has_issues": "false",
        "has_wiki": "false",
        "can_comment": "false",
        "private": "false",
    }
    resp = requests.post(url, json=json_data)
    if resp.status_code == 200:
        logging.info('Repo {} created successfully'.format(repo_name))
    else:
        logging.error('Repo {} create failed, return message {}'.format(
            repo_name, resp.text))


def main():
    repo_info_list = read_csv(repo_info_csv)
    all_repo_list = get_all_repo()
    logging.info('All repo list: {}'.format(all_repo_list))
    for repo_info in repo_info_list:
        repo_info['target_repo_name'] = get_repo_name(repo_info['target_repo'])
        logging.info(repo_info)
        if repo_info['target_repo_name'] in all_repo_list:
            update_repo_info(repo_info['source_repo'],
                             repo_info['target_repo_name'])
        else:
            create_repo(repo_info['source_repo'],
                        repo_info['target_repo_name'])
        sync_repo(repo_info['source_repo'],
                  repo_info['target_repo'], repo_info['repo_dir'])


if __name__ == '__main__':
    main()

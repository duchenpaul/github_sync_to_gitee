import os
import csv
import subprocess

USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']

WORKDIR = os.getcwd()
repo_info_csv = 'repo_info.csv'

def read_csv(repo_info_csv):
    repo_info_list = list()
    with open(repo_info_csv) as fh:
        rd = csv.DictReader(fh, delimiter=',')
        for row in rd:
            repo_info_list.append(dict(row))
    return repo_info_list


def sync_repo(source_repo, target_repo, repo_dir=None):
    print('Sync {} to {}...'.format(source_repo, target_repo))
    repo_dir = repo_dir if repo_dir else source_repo.split('/')[-1]
    args = {
        'source_repo': source_repo,
        'target_repo': target_repo,
        'repo_dir': repo_dir,
        'USERNAME': USERNAME,
        'PASSWORD': PASSWORD,
    }
    command = 'git clone --bare {source_repo} {repo_dir} && cd {repo_dir} && git push --mirror https://{USERNAME}:{PASSWORD}@{target_repo} && cd ..'.format(**args)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    process.wait()
    print('Return code: {}'.format(process.returncode))


if __name__ == '__main__':
    repo_info_list = read_csv(repo_info_csv)
    for repo_info in repo_info_list:
        sync_repo(**repo_info)
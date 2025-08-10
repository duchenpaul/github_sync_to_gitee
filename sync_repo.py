import csv
import json
import logging
import os
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import urllib3
from retry import retry

# Replace logging setup to include thread name and configurable level
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


USERNAME = os.environ["USERNAME"]
PASSWORD = os.environ["PASSWORD"]
GITEE_PAT = os.environ["GITEE_PAT"]

WORKDIR = os.getcwd()
repo_info_csv = "repo_info.csv"


def read_csv(repo_info_csv):
    repo_info_list = list()
    with open(repo_info_csv) as fh:
        rd = csv.DictReader(fh, delimiter=",")
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
    return target_repo.split("/")[-1].replace(".git", "")


@retry((AssertionError), tries=10, delay=5, jitter=5)
def sync_repo(source_repo, target_repo, repo_dir=None):
    logging.info("Sync %s -> %s", source_repo, target_repo)
    repo_dir = repo_dir if repo_dir else source_repo.split("/")[-1]

    # Use per-task unique temp dir to avoid conflicts in parallel runs
    base_tmp_dir = "/home/runner/work/github_sync_to_gitee/temp"
    tmp_dir = os.path.join(base_tmp_dir, f"{repo_dir}_{uuid.uuid4().hex}")

    args = {
        "source_repo": source_repo,
        "target_repo": target_repo,
        "repo_dir": repo_dir,
        "USERNAME": USERNAME,
        "PASSWORD": PASSWORD,
        "tmp_dir": tmp_dir,
    }

    # Do not log the full command (contains credentials)
    logging.debug("Working directory: %s", tmp_dir)

    command = (
        "rm -rf {tmp_dir} && mkdir -p {tmp_dir} && "
        "cd {tmp_dir} && "
        "git clone --bare {source_repo} {tmp_dir}/{repo_dir} && "
        "cd {tmp_dir}/{repo_dir} && "
        "git push --force --mirror https://{USERNAME}:{PASSWORD}@{target_repo} && "
        # Clean up this task's tmp dir after push
        "cd / && rm -rf {tmp_dir}"
    ).format(**args)

    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    out, _ = process.communicate()
    process.wait()

    output = (out or b"").decode("utf-8", errors="replace")

    if process.returncode:
        logging.error(
            "Sync failed for %s (rc=%s). Output (tail):\n%s",
            repo_dir,
            process.returncode,
            output[-2000:],
        )
    else:
        logging.info("Sync succeeded for %s", repo_dir)

    assert process.returncode == 0


def get_all_repo():
    url = "https://gitee.com/api/v5/user/repos?access_token={GITEE_PAT}&sort=full_name&per_page=100".format(
        GITEE_PAT=GITEE_PAT
    )
    resp = requests.get(url)
    response_text = resp.text
    all_repo_dict = json.loads(response_text)
    return [x["name"] for x in all_repo_dict]


@retry(
    (
        ConnectionResetError,
        urllib3.exceptions.ProtocolError,
        requests.exceptions.ConnectionError,
    ),
    tries=10,
    delay=5,
    jitter=5,
)
def update_repo_info(source_repo, repo_name):
    url = "https://gitee.com/api/v5/repos/{}/{}".format(USERNAME, repo_name)

    json_data = {
        "access_token": GITEE_PAT,
        "name": repo_name,
        "description": "Mirror of " + source_repo,
        "has_issues": "true",
        "has_wiki": "true",
        "can_comment": "true",
    }
    resp = requests.patch(url, json=json_data)
    if resp.status_code in (200, 201):
        logging.info("Repo {} updated successfully".format(repo_name))
    else:
        logging.error(
            "Repo {} update failed, return code: {} return message {}".format(
                repo_name, resp.status_code, resp.text
            )
        )


def create_repo(source_repo, repo_name):
    logging.info("Create new repo {}".format(repo_name))
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
    if resp.status_code in (200, 201):
        logging.info("Repo {} created successfully".format(repo_name))
    else:
        logging.error(
            "Repo {} create failed, return code: {} return message {}".format(
                repo_name, resp.status_code, resp.text
            )
        )


def process_repo(repo_info, all_repo_list):
    """Create/update repo metadata then mirror."""
    try:
        target_repo_name = get_repo_name(repo_info["target_repo"])
        logging.info("Processing %s", target_repo_name)

        if target_repo_name in all_repo_list:
            update_repo_info(repo_info["source_repo"], target_repo_name)
        else:
            create_repo(repo_info["source_repo"], target_repo_name)

        sync_repo(
            repo_info["source_repo"],
            repo_info["target_repo"],
            repo_info.get("repo_dir"),
        )
        logging.info("Done %s", target_repo_name)
        return True
    except Exception:
        logging.exception("Failed %s", repo_info.get("target_repo", "<unknown>"))
        return False


def main():
    repo_info_list = read_csv(repo_info_csv)
    all_repo_list = get_all_repo()
    logging.info("Total repos to process: %d", len(repo_info_list))

    # Run up to 5 tasks concurrently
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(process_repo, repo_info, all_repo_list)
            for repo_info in repo_info_list
        ]
        # Collect results as they complete
        for _ in as_completed(futures):
            pass  # minimal reporting; each task logs its own progress


if __name__ == "__main__":
    main()

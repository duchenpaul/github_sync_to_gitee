import json
import requests
import os
import urllib.parse
try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus


USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']
GITEE_PAT = os.environ['GITEE_PAT']

repo_name = ''
source_repo = ''

url = "https://gitee.com/api/v5/repos/{}/{}".format(USERNAME, repo_name)

json_data = {
    "access_token": GITEE_PAT,
    "name": repo_name,
    "description": "Mirror of " + source_repo,
    "has_issues": "true",
    "has_wiki": "true",
    "can_comment": "true"
}

url = "https://gitee.com/api/v5/user/repos?access_token={GITEE_PAT}&sort=full_name&per_page=2000".format(
    GITEE_PAT=GITEE_PAT)
# resp = requests.get(url)
# response_text = resp.text

# json.dump(all_repo_dict, open('all_repo.json', 'w'), indent=4)

with open('all_repo.json') as f:
    response_text = f.read()

all_repo_dict = json.loads(response_text)

# print(all_repo_dict)

repo_html_url_list = [x["html_url"] for x in all_repo_dict]

# print(repo_html_url_list)


# proxies = { "http": "http://127.0.0.1:8888", }

url = 'http://example.com/'


class Gitee():
    """docstring for Example"""

    def __init__(self):
        self.sess = requests.Session()
        self.first_header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Cookie': 'user_locale=zh-CN; oschina_new_user=false; tz=Asia%2FShanghai; Hm_lvt_24f17767262929947cc3631f99bfd274=1657882494; sajssdk_2015_cross_new_user=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22182017f44af43-0e4964c8ddefd88-1c525635-2007040-182017f44b0c7a%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22%24device_id%22%3A%22182017f44af43-0e4964c8ddefd88-1c525635-2007040-182017f44b0c7a%22%7D; sensorsdata2015jssdkchannel=%7B%22prop%22%3A%7B%22_sa_channel_landing_url%22%3A%22%22%7D%7D; Hm_lpvt_24f17767262929947cc3631f99bfd274=1657882506; gitee_user=true; gitee-session-n=Si9uVGg3RTVUN1NtZDJVb2NjVW1sT1R4c2E3ZU81Zk1OQU5YeG10RmJVV2FON0tMazRPaFRhTzVBYnJtN1FyTk1jU2VjWm1KaTdjSWJzQ1VlVFkxZ2FveWJiT0JwNWQwa2pEOFFHMGJZd3grWFVBZC8wc1c3djlaV2JoWUJ2VFRlT1ZZR1Y5Vzc2aDJHQkx1czdRaVNiUnFzdGNPNThNNXZvMm16YlF5ZGtHSC9jeWJqUmlZM2UzRUhPd3Z6YlFEQ1g4SW4wbmNUS2ZtekkvQ3VqU1RqbjRBTGhZT1pLclNka1pNZm15VndXNkdMRU1TalY3S3o1N3ZZcHlOS2dsT1BNZzdUZmxMTCtPL1IxSi9EcTRwakhQWTVJdCthSU1TUVp6L2dOSUdZY2M9LS1TNExSQkRLcWxlcllhRlkwRVduc2pRPT0%3D--dac59e215016b08dbbb3dacfda1fea36b955b53a',
            'Host': 'gitee.com',
            'Referer': 'https://gitee.com/login',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }

    def webpage_get(self, url, headers=None, allow_redirects=True):
        if headers is None:
            headers = dict()
        # print("Get: " + url)
        proxies = None
        self.resp = self.sess.get(
            url, headers=headers, allow_redirects=allow_redirects, verify=False, proxies=proxies, timeout=10)
        # print(self.resp.content.decode('utf-8').replace('\r\n', '\n'))
        return self.resp

    def webpage_post(self, url, data=None, json=None, headers=None):
        if headers is None:
            headers = dict()
        proxies = None
        self.resp = self.sess.post(
            url, data=data, json=json, headers=headers, verify=False, proxies=proxies, timeout=10)
        # self.req = requests.Request('POST', url, data=data, headers=headers)
        # self.prepped = self.sess.prepare_request(self.req)
        # self.resp = self.sess.send(self.prepped)
        return self.resp

    def save_page(self, page, filename):
        with open('./temp/{}.html'.format(filename), 'w', encoding='utf-8') as f:
            f.write(page)
        print("Page has been saved as " + './test.html')


if __name__ == '__main__':
    gitee = Gitee()
    # print(gitee.webpage_get('https://gitee.com', headers=gitee.first_header).text)
    for x in repo_html_url_list:
        repo = os.path.basename(x)
        print(repo)
        gitee.webpage_get(x, headers=gitee.first_header)
        gitee.save_page(gitee.resp.text, repo)

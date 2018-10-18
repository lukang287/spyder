import json
import os
import re
from _md5 import md5
from json import JSONDecodeError
from multiprocessing.pool import Pool
from urllib.parse import urlencode

import pymongo
import requests
from bs4 import BeautifulSoup
from requests import RequestException
from toutiao_config import *

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


def get_page_index(offset, keyword):
    data = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': 20,
        'cur_tab': 3,
        'from': 'gallery'
    }
    url = 'https://www.toutiao.com/search_content/?' + urlencode(data)
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return res.text
        return None
    except RequestException as e:
        print('获取index失败', e)
        return None


def parse_index_data(html):
    try:
        data = json.loads(html)
        if data and 'data' in data.keys():
            for item in data.get('data'):
                # yield item.get('article_url').replace('group/', 'a')
                id = item.get('id')
                if id:
                    yield 'https://www.toutiao.com/a' + id
    except JSONDecodeError:
        pass


def get_page_detail(url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Host': 'www.toutiao.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
    }
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.text
        return None
    except RequestException as e:
        print('获取detail失败', e)
        return None


def parse_page_detail(html, url):
    soup = BeautifulSoup(html, 'lxml')
    title = soup.select('title')[0].get_text()
    pattern = re.compile('JSON.parse\("(.*?)"\)', re.S)
    res = re.search(pattern, html)
    if res:
        json_str = res.group(1).replace('\\', '')
        jdata = json.loads(json_str)
        if jdata and 'sub_images' in jdata.keys():
            sub_images = jdata.get('sub_images')
            images = [item.get('url') for item in sub_images]
            for image in images:
                print('下载图片：',image)
                download_image(image)
            return {
                'title': title,
                'url': url,
                'images': images
            }


def save_to_mongo(info):
    if db[MONGO_TABLE].insert(info):
        print('存储到mongo成功')
        return True
    return False


def download_image(url):
    try:
        res = requests.get(url)
        if res.status_code == 200:
            save_image(res.content)
        return None
    except RequestException as e:
        print('获取图片失败', e)
        return None


def save_image(content):
    file_path = '{0}/img/{1}.{2}'.format(os.getcwd(), md5(content).hexdigest(), 'jpg')
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)
            f.close()


def main(offset):
    html = get_page_index(offset, '街拍')
    for url in parse_index_data(html):
        if url:
            detail = get_page_detail(url)
            if detail:
                images_info = parse_page_detail(detail, url)
                if images_info:
                    save_to_mongo(images_info)


if __name__ == '__main__':
    groups = [x * 20 for x in range(GROUP_START, GROUP_END + 1)]
    pool = Pool()
    pool.map(main, groups)

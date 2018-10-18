import requests
import re
import json
from multiprocessing import Pool
from requests.exceptions import RequestException

def get_one_page(url):
    try:
        headers = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                   'Accept-Encoding':'gzip,deflate',
                   'Accept-Language':'zh-CN',
                   'Connection':'keep-alive',
                   'Host':'maoyan.com',
                   'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
        res = requests.get(url, params=None, headers=headers)
        if res.status_code == 200:
            return res.text
        return res.status_code
    except RequestException as e:
        return e.strerror

def parse_html(html):
    #pattern = re.compile('<dd>.*?board-index-1">(\d+)</i>.*?data-src="(.*?)".*?title="(.*?)".*?class="star">(.*?)</p>'
    #                     +'.*?class="integer">(.*?)</li>.*?class="fraction">(.*?)</li>.*?</dd>',re.S)
    # pattern = re.compile('<dd>.*?</dd>',re.S)
    pattern = re.compile('<dd>.*?board-index-\d+">(\d+)</i>.*?data-src="(.*?)".*?class="name"><a.*?>(.*?)</a>.*?class="star">(.*?)</p>.*?class="releasetime">(.*?)</p>.*?class="integer">(.*?)</i>.*?class="fraction">(\d+)</i>.*?</dd>',re.S)
    items = re.findall(pattern, html)
    # print(items)
    for item in items:
        yield {
            'index':item[0],
            'title':item[1],
            'image':item[2],
            'actor':item[3].strip()[3:],
            'time':item[4].strip()[5:],
            'point':item[5]+item[6]
        }

def write_to_file(content):
    with open('result.txt', 'a', encoding='utf-8') as f:
        f.write(json.dumps(content,ensure_ascii=False)+'\n')
        f.close()

def main(offset):
    url = 'http://maoyan.com/board/4?offset='+str(offset)
    html = get_one_page(url)
    #print(html)
    for item in parse_html(html):
        #print(item)
        write_to_file(item)


if __name__ == '__main__':
    pool = Pool()
    pool.map(main,[i for i in range(0,100,10)])
    # for i in range(10):
    #     main(i*10)
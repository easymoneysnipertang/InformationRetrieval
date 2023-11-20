'''
爬虫模块，从url_pool中获取url不断爬取
todo: 1.多线程
'''

import time
import random
import sys
import requests
from bs4 import BeautifulSoup
import mysql_config as db
from urllib.parse import urljoin,urlparse
from robotexclusionrulesparser import RobotExclusionRulesParser


class crawler():
    def __init__(self,root_url,stop_url):
        # url池
        self.url_pool = [root_url]
        self.root_url = root_url
        self.stop_url = stop_url
        # user-agent
        self.request_header = {
            "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 "
                "Safari/537.36 Edg/114.0.1823.58",
            "Connection":
                "keep-alive",
            "Referer":
                'www.baidu.com'
        }
        # mysql数据库
        db.get_database()
        db.get_table()

    def get_robots(self):
        # 获取robots.txt
        resp = requests.get(self.root_url+ 'robots.txt')
        if resp.status_code == 200:
            robots_txt = resp.text
            rp = RobotExclusionRulesParser()
            rp.parse(robots_txt)
            self.rp = rp
        else:
            print("获取robots.txt失败")
    
    def add_url(self,url):
        parsed_url = urlparse(url)
        if self.rp.is_allowed('*', parsed_url.path) and url not in self.stop_url:
            # 添加url到url池
            if url not in self.url_pool and db.check_url(url) is False:
                # 在数据库代表已经爬取过，在url池代表已经加入过
                self.url_pool.append(url)
    
    def scrap_page(self):
        # 从url池中获取url，爬取页面
        if len(self.url_pool) == 0:
            print("url池爬取完毕")
            return
        
        url = self.url_pool.pop(0)
        try:
            resp = requests.get(url,headers=self.request_header)
        except:
            print(f"URL: {url} get失败")
            return
        status_code = resp.status_code
        if status_code == 200:
                print(f"URL: {url} 开始解析")
                html_text = resp.text
                # 解析html
                soup = BeautifulSoup(html_text,"html.parser")
                try:
                    # 获取title
                    title = soup.title.string
                    text = soup.get_text()
                    # 分割文本并去除空行
                    lines = [line for line in text.split('\n') if line.strip() != '']
                    text = '\n'.join(lines)
                    # 获取外链
                    a_tags = soup.find_all('a')
                    links = [
                            urljoin(url, tag.get('href')) 
                            for tag in a_tags 
                            if tag.get('href') is not None  # 防止空链接 
                            and not tag.get('href').startswith(('javascript:', 'mailto:','#'))  # 不爬js
                            and '?' not in tag.get('href')  # 不爬get请求
                            and tag.get('href') != '/'  # 防止重复爬取
                    ]
                    link_str = ''
                    if len(links)>50:
                        links = random.sample(links,50)
                    for link in links:
                        if 'cnblogs' in link:  # 免得爬的太离谱
                            self.add_url(link)  # 添加链接到url池
                            link_str += link + '\n'  # 外链
                    # 当前页面插入数据库
                    db.insert_page(title,text,url,link_str)
                except:
                    # 打印错误信息
                    print(f"URL: {url} 解析失败")
                    print(sys.exc_info()[1])
                    return
        else: 
            print(f"URL: {url} 爬取失败")
            return
        
    def pipline(self):
        # 获取robots.txt
        self.get_robots()
        # 开始爬虫
        while self.url_pool != []:
            self.scrap_page()
            #time.sleep(1)
           

if __name__ == "__main__":
    spider = crawler("https://www.cnblogs.com/",['https://cnblogs.vip/',
                                                 'https://ing.cnblogs.com/',
                                                 'https://edu.cnblogs.com/',
                                                 'https://hh.hanghang.com/AIjingpinke',
                                                 'https://account.cnblogs.com/signup',
                                                 'https://q.cnblogs.com/',
                                                 'https://news.cnblogs.com/',
                                                 ])
    spider.pipline()




'''
1. 解决部分网页乱码问题
2. 处理同title不同url的问题
3. 处理links过多的问题
'''

import random
import mysql_config as db
import chardet
import requests
from bs4 import BeautifulSoup

# 处理网页乱码
def deal_with_garbled(ids,decoding):
    for id in ids:
        # 从数据库中获取id的记录的URL
        db.cursor.execute("SELECT url FROM page WHERE id = %s", (id,))
        url = db.cursor.fetchone()[0]
        # 获取URL的HTML内容
        response = requests.get(url)
        # 解码响应内容
        text = response.content.decode(decoding, errors='ignore')
        # 解析HTML内容并提取标题
        soup = BeautifulSoup(text, 'html.parser')
        title = soup.title.string
        print(f"id: {id}, title: {title}")

        content = soup.get_text()
        # 分割文本并去除空行
        lines = [line for line in content.split('\n') if line.strip() != '']
        content = '\n'.join(lines)
        # 更新数据库中的记录
        db.cursor.execute("UPDATE page SET title = %s, content = %s WHERE id = %s", (title, content, id))
    
    db.cnx.commit()


# 处理同title不同url的问题
def deal_with_same_title():
    pass


# 随机删除一半的links
def delete_links():
    db.cursor.execute("SELECT id FROM page")
    ids = [record[0] for record in db.cursor.fetchall()]
    
    for id in ids:
        if id ==1:
            continue
        db.cursor.execute("SELECT links FROM page WHERE id=%s", (id,))
        links = db.cursor.fetchone()[0].split('\n')
        half_len = len(links) // 2
        links_to_keep = random.sample(links, half_len)
        new_links = '\n'.join(links_to_keep)
        db.cursor.execute("UPDATE page SET links=%s WHERE id=%s", (new_links, id))
        print(f"ID: {id} links删除完毕")
    
    db.cnx.commit()


def count_links():
    db.cursor.execute("SELECT id FROM page")
    ids = [record[0] for record in db.cursor.fetchall()]
    max_len = 0
    for id in ids:
        db.cursor.execute("SELECT links FROM page WHERE id=%s", (id,))
        links = db.cursor.fetchone()[0].split('\n')
        print(f"ID: {id} links数量: {len(links)}")
        if len(links) > max_len:
            max_len = len(links)
    print(f"最大links数量: {max_len}")


def delete_links_above_threshold(threshold):
    db.cursor.execute("SELECT id FROM page")
    ids = [record[0] for record in db.cursor.fetchall()]
    
    for id in ids:
        db.cursor.execute("SELECT links FROM page WHERE id=%s", (id,))
        links = db.cursor.fetchone()[0].split('\n')
        if len(links) > threshold:
            print(f"ID: {id} links数量: {len(links)}")
            half_len = len(links) // 2
            links_to_keep = random.sample(links, half_len)
            new_links = '\n'.join(links_to_keep)
            db.cursor.execute("UPDATE page SET links=%s WHERE id=%s", (new_links, id))
    
    db.cnx.commit()


def delete_links_below_threshold(threshold):
    db.cursor.execute("SELECT id FROM page")
    ids = [record[0] for record in db.cursor.fetchall()]
    
    for id in ids:
        db.cursor.execute("SELECT links FROM page WHERE id=%s", (id,))
        links = db.cursor.fetchone()[0].split('\n')
        if len(links) < threshold:
           db.cursor.execute("DELETE FROM page WHERE id =%s", (id,))

def delete_duplicate_urls():
    # 找出重复的url和它们的id
    db.cursor.execute("SELECT url, GROUP_CONCAT(id) FROM page GROUP BY url HAVING COUNT(url) > 1")
    duplicate_urls = db.cursor.fetchall()

    for url, ids in duplicate_urls:
        # 将id字符串分割成列表，然后转换为整数
        id_list = list(map(int, ids.split(',')))
        # 保留每组重复记录中的第一个，删除其余的
        id_list.pop(0)
        db.cursor.execute("DELETE FROM page WHERE id IN (%s)" % ', '.join(map(str, id_list)))

    db.cnx.commit()


def test_encoding():
    # test
    db.cursor.execute("SELECT title FROM page WHERE id = 1")
    correct_title = db.cursor.fetchone()
    correct_encoding = chardet.detect(correct_title[0].encode())['encoding']
    db.cursor.execute("SELECT title FROM page WHERE id = 4914")
    wrong_title = db.cursor.fetchone()
    wrong_encoding = chardet.detect(wrong_title[0].encode())['encoding']
    print(correct_encoding, wrong_encoding)
    # 尝试使用不同的编码来解码
    encodings = ['utf8','gbk', 'gb2312', 'gb18030', 'hz', 'big5']
    for encoding in encodings:
        try:
            fixed_title = wrong_title[0].encode('utf8').decode(encoding)
            print(f"使用'{encoding}'编码解码的标题: {fixed_title}")
        except UnicodeDecodeError:
            print(f"无法使用'{encoding}'编码来修复这个标题1")
        except UnicodeEncodeError:
            print(f"无法使用'{encoding}'编码来修复这个标题2")

if __name__ == "__main__":
    db.get_database()
    db.get_table()
    # delete_links()
    # print("删除links成功")
    #test_encoding()
    # gb2312编码的网页
    # ids = [4914, 4920, 4921, 4924, 4929, 4941, 4948, 4960, 4961, 4965, 4967, 
    #        4984, 4985, 4986] + list(range(5861, 5883))
    # decoding = 'gb2312'
    # deal_with_garbled(ids, decoding)
    # UTF-8编码的网页
    #ids = list(range(4599, 4694))
    # decoding = 'UTF-8'
    # deal_with_garbled(ids, decoding)
    # count_links()
    # delete_links_above_threshold(400)
    delete_duplicate_urls()
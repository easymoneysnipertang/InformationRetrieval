'''
mysql数据库模块
'''

import pymysql

# 创建连接
cnx = pymysql.connect(host='localhost', user='root', password='123qwe12')
cursor = cnx.cursor()

def get_database():
    # 创建数据库
    cursor.execute("CREATE DATABASE IF NOT EXISTS IR_db")
    # 使用数据库
    cnx.select_db('IR_db')

def get_table():
    # 创建表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS page (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255),
            content TEXT,
            url VARCHAR(255),
            links TEXT
        )
    """)
    # 提交
    cnx.commit()

def check_url(url):
    # 查询url是否存在
    cursor.execute("SELECT * FROM page WHERE url=%s", (url,))
    if cursor.fetchone() is None:
        return False
    else:
        return True
    

def insert_page(title, content, url, links):
    # 冗余查询一遍url是否存在
    if check_url(url):
        print(f"URL: {url} 已存在")
        return
    # 插入数据
    cursor.execute("INSERT INTO page (title, content, url, links) VALUES (%s, %s, %s, %s)", (title, content, url, links))
    # 提交
    cnx.commit()
    print(f"URL: {url} 插入成功")

def remove_duplicate():
    # 删除具有相同URL的重复行
    cursor.execute("""
        DELETE FROM page
        WHERE id NOT IN (
            SELECT min(id)
            FROM page
            GROUP BY url
        )
    """)
    cnx.commit()

def clear_table():
    # 清空表
    cursor.execute("TRUNCATE TABLE page")
    cnx.commit()


# 删除记录
def delete_pages(id_list):
    for id in id_list:
        cursor.execute("DELETE FROM page WHERE id=%s", (id,))
    cnx.commit()


def get_one_page(id):
    cursor.execute("SELECT * FROM page WHERE id=%s", (id,))
    return cursor.fetchone()

    

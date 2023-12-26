import pymysql

cnx = pymysql.connect(host='localhost', user='root', password='123qwe12')
cursor = cnx.cursor()
cnx.select_db('IR_db')

# userid,password,interest,clicked_url

def create_user_table():
    # 创建新表的 SQL 语句
    create_table_sql = """
    CREATE TABLE users (
        userid VARCHAR(255) NOT NULL,
        passport VARCHAR(255) NOT NULL,
        interest VARCHAR(255),
        clicked_url TEXT
    )
    """
    # 执行 SQL 语句
    cursor.execute(create_table_sql)
    # 提交事务
    cnx.commit() 


def save_user(userid,password,interest):
    # 保存用户信息
    # 首先判断用户是否存在
    sql = 'select * from users where userid = %s'
    cursor.execute(sql,userid)
    result = cursor.fetchall()
    if len(result) == 0:
        # 不存在
        sql = 'insert into users values(%s,%s,%s,"")'
        cursor.execute(sql,(userid,password,interest))
        cnx.commit()
        return True
    else:
        # 存在
        return False
    

def update_user(userid, clicked_url):
    # 更新用户信息
    sql = 'SELECT clicked_url FROM users WHERE userid = %s'
    cursor.execute(sql, (userid,))
    result = cursor.fetchone()
    # 将 clicked_url 字符串分割成 URL 列表
    new_urls = clicked_url.split('\n')

    if result is None:
        # 用户不存在
        return False
    else:
        # 用户存在
        # 获取数据库中的 URL 列表
        existing_urls = result[0].split('\n') if result[0] else []
        # 将新的 URL 添加到 URL 列表中（如果它们还不在列表中）
        for url in new_urls:
            if url not in existing_urls:
                existing_urls.append(url)
        # 将 URL 列表转换回字符串
        updated_clicked_url = '\n'.join(existing_urls)
        # 更新数据库
        sql = 'UPDATE users SET clicked_url = %s WHERE userid = %s'
        cursor.execute(sql, (updated_clicked_url, userid))
        cnx.commit()
        return True
    

def get_user(userid):
    # 获取用户信息
    sql = 'SELECT clicked_url FROM users WHERE userid = %s'
    cursor.execute(sql, (userid,))
    result = cursor.fetchone()

    if result is None:
        # 用户不存在
        return None
    else:
        # 用户存在
        # 获取数据库中的 URL 列表
        clicked_urls = result[0].split('\n') if result[0] else []
        return clicked_urls
    

if __name__ == '__main__':
    create_user_table()
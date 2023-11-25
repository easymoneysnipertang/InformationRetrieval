## crawler
使用beautifulsoup4和requests库实现的爬虫，爬取了睡前消息、豆瓣电影、豆瓣图书、菜鸟教程、博客园等网站的数据，保存到mysql数据库中

- crawl_news：爬取睡前消息的每日新闻。保存了新闻的标题、内容、时间、链接，约4000条
- crawl_douban：爬取豆瓣电影和图书Top250以及相关的影评。保存了网页标题、内容、链接、外链，约5000条
- crwal_web：和mysql_config.py配合使用，实现的爬虫pipline，输入网址，自动爬取网页标题、内容、链接、外链到数据库中。爬了菜鸟教程、博客园等约6000条
- clean_data：由于crrwal_web不对网页进行结构分析的爬取，所以需要进行数据清洗
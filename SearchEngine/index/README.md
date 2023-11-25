## index

Copilot Is All You Need！👨‍💻

使用ElasticSearch建立索引，索引的数据来源于爬虫保存的MySQL数据库，索引的结构与MySQL数据库的表结构基本一致  

> Relational DB ‐> Databases ‐> Tables ‐> Rows ‐> Columns  
> Elasticsearch ‐> Indices ‐> Types ‐> Documents ‐> Fields 

- test_es.ipynb: 测试ElasticSearch的基本功能
- index_news.ipynb: 为睡前消息的每日新闻建立索引
- index_web.ipynb: 为爬取的网页建立索引，后续还需要往里面添加page_rank等信息
from elasticsearch import Elasticsearch
from datetime import datetime
import os
import pymysql

# type: douban,page,html
# label: douban,page,news

class Query:
    def __init__(self,label):
        self.label = label 
        self.es = Elasticsearch(hosts="http://localhost:9200")
        self.cnx = pymysql.connect(host='localhost', user='root', password='123qwe12')
        self.cursor = self.cnx.cursor()
        self.cnx.select_db('IR_db')
        # 创建表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_queries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                query_content TEXT,
                query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                count INT
            )
        """)
        # 提交
        self.cnx.commit()

    def set_label(self, label):
        '''
        设置搜索的内容标签
        '''
        self.label = label

    def get_pop_query(self):
        '''
        获取热门查询
        '''
        # 查询语句
        query = ("SELECT query_content FROM user_queries ORDER BY count DESC LIMIT 20")
        # 执行查询
        self.cursor.execute(query)
        # 获取查询结果
        results = self.cursor.fetchall()
        # 将查询结果转换为列表
        pop_query = [result[0] for result in results]
        return pop_query

    def save_query_log(self, type, query):
        '''
        保存用户查询记录
        '''
        # 查询时间
        query_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 获取log文件的路径
        current_path = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(current_path, "..", "logs", "query.log")
        # 打开log文件
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("[" + query_time + "]" + "\t" + type + "\t" + query + "\n")
        # 检查query_content是否存在
        check_query = ("SELECT count(*) FROM user_queries WHERE query_content = %s")
        self.cursor.execute(check_query, (query,))
        result = self.cursor.fetchone()
        if result[0] > 0:  # query_content存在，更新行
            update_query = ("UPDATE user_queries SET count = count + 1, query_time = %s WHERE query_content = %s")
            query_data = (query_time, query)
        else:  # query_content不存在，插入新行
            update_query = ("INSERT INTO user_queries (query_content, query_time, count) VALUES (%s, %s, 1)")
            query_data = (query, query_time)
        self.cursor.execute(update_query, query_data)
        self.cnx.commit()
        
    def response_to_result(self, response):
        '''
        将搜索结果转换为前端需要的格式
        '''
        # 获取搜索结果
        hits = response["hits"]["hits"]
        # 格式化搜索结果
        results = [
            {
                "id": hit["_id"],
                "title": hit["_source"]["title"],
                "content": hit["_source"]["content"],
                "url": hit["_source"]["url"],
                "type": hit["_source"]["type"],
                "score": hit["_score"]
            }
            for hit in hits
        ]
        return results
    
    def search(self,query):
        '''
        最基本的查询方式
        使用bool查询，查询title和content字段
        在title和pageRank值会影响排序结果
        '''
        self.save_query_log('<basic_search>', query)
        # 执行搜索
        response = self.es.search(
            index="web",
            body={
                "size": 100,
                "query": {
                    "function_score": {
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "multi_match": {
                                            "query": query,
                                            "fields": ["title^1.5", "content"],
                                            "type": "most_fields",
                                            "analyzer": "ik_max_word"
                                        }
                                    }
                                ]
                            }
                        },
                        "functions": [
                        {
                            "script_score": {
                                "script": {
                                    "source": "doc['pageRank'].value == 0 ? 1 : Math.log1p(doc['pageRank'].value * params.factor)",
                                    "params": {
                                        "factor": 100000
                                    }
                                }
                            }
                        },
                        {
                            "filter": {
                                "term": {
                                    "type": self.label
                                }
                            },
                            "script_score": {
                                "script": {
                                    "source": "_score * 1.1"
                                }
                            }
                        }],
                        "boost_mode": "sum"
                    }
                }
            }
        )
        return self.response_to_result(response)
    
    def phase_search(self,query):
        '''
        短语查询
        '''
        self.save_query_log('<phase_search>', query)
        # 执行搜索
        response = self.es.search(
            index="web",
            body={
                "size": 100,
                "query": {
                    "function_score": {
                        "query": {
                            "multi_match": {
                                "query": query,
                                "fields": ["title", "content"],
                                "type": "phrase"
                            }
                        },
                        "functions": [
                        {
                            "script_score": {
                                "script": {
                                    "source": "doc['pageRank'].value == 0 ? 1 : Math.log1p(doc['pageRank'].value * params.factor)",
                                    "params": {
                                        "factor": 100000
                                    }
                                }
                            }
                        },
                        {
                            "filter": {
                                "term": {
                                    "type": self.label
                                }
                            },
                            "script_score": {
                                "script": {
                                    "source": "_score * 1.1"
                                }
                            }
                        }],
                        "boost_mode": "sum"
                    }
                }
            }
        )
        return self.response_to_result(response)
    
    def bool_search(self, must, mustnot, should , position = ["title", "content"]):
        '''
        布尔查询
        提供must，mustnot，should三个选项
        position参数用于指定搜索的位置
        '''
        save_query = "[must]:" + str(must) + "\t[mustnot]:" + str(mustnot) + "\t[should]:" + str(should) + "\t[position]:" + str(position)
        self.save_query_log('<bool_search>', save_query)
        # 执行搜索
        # 创建空的查询数组
        must_queries = []
        mustnot_queries = []
        should_queries = []
        # 为每个字符串创建一个multi_match查询，并添加到相应的查询数组中
        for m in must:
            must_queries.append({"multi_match": {"query": m, "fields": position}})
        for mn in mustnot:
            mustnot_queries.append({"multi_match": {"query": mn, "fields": position}})
        for s in should:
            should_queries.append({"multi_match": {"query": s, "fields": position}})
        # 执行搜索
        response = self.es.search(
            index="web",
            body={
                "size" : 100,
                "query": {
                    "function_score": {
                        "query": {
                            "bool": {
                                "must": must_queries,
                                "must_not": mustnot_queries,
                                "should": should_queries
                            }
                        },
                        "script_score": {
                            "script": {
                                "source": "doc['pageRank'].value == 0 ? 1 : Math.log1p(doc['pageRank'].value * params.factor)",
                                "params": {
                                    "factor": 100000
                                }
                            }
                        },
                        "boost_mode": "sum"
                    }
                }
            }
        )
        return self.response_to_result(response)

    def site_search(self, url, query):
        '''
        站内搜索
        网页链接中必须包含url
        实现的很不优雅, es不配合
        '''
        save_query = "[url]:" + url + "\t[query]:" + query
        self.save_query_log('<site_search>', save_query)
        results = self.search(query)
        # 过滤掉不包含url的结果
        results = [result for result in results if url in result['url']]
        return results
        
    def fuzz_search(self, query):
        '''
        模糊查询
        '''
        self.save_query_log('<fuzz_search>', query)
        # 执行搜索
        response = self.es.search(
            index="web",
            body={
                "size" : 100,
                "query": {
                    "function_score": {
                        "query": {
                            "multi_match": {
                                "query": query,
                                "fields": ["title", "content"],
                                "fuzziness": "AUTO"
                            }
                        },
                        "functions": [
                        {
                            "script_score": {
                                "script": {
                                    "source": "doc['pageRank'].value == 0 ? 1 : Math.log1p(doc['pageRank'].value * params.factor)",
                                    "params": {
                                        "factor": 100000
                                    }
                                }
                            }
                        },
                        {
                            "filter": {
                                "term": {
                                    "type": self.label
                                }
                            },
                            "script_score": {
                                "script": {
                                    "source": "_score * 1.1"
                                }
                            }
                        }],
                        "boost_mode": "sum"
                    }
                }
            }
        )
        return self.response_to_result(response)

    def wildcard_search(self, query):
        '''
        通配符查询
        暂时不可用
        '''
        self.save_query_log('<wildcard_search>', query)
        # 执行搜索
        response = self.es.search(
            index="web",
            body={
                "query": {
                    "bool": {
                        "should": [
                            {
                                "wildcard": {
                                    "title": {
                                        "value": query,
                                        "boost": 1.0,
                                        "rewrite": "constant_score"
                                    }
                                }
                            },
                            {
                                "wildcard": {
                                    "content": {
                                        "value": query,
                                        "boost": 1.0,
                                        "rewrite": "constant_score"
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        )
        return self.response_to_result(response)
    
    def regexp_search(self, query):
        '''
        正则表达式查询
        可行性待验证
        '''
        self.save_query_log('<regexp_search>', query)
        # 执行搜索
        response = self.es.search(
            index="web",
            body={
                "size" : 100,
                "query": {
                    "bool": {
                        "should": [
                            {
                                "regexp": {
                                    "title": {
                                        "value": query,
                                        "flags": "ALL",
                                        "case_insensitive": True,
                                        "max_determinized_states": 10000,
                                        "rewrite": "constant_score"
                                    }
                                }
                            },
                            {
                                "regexp": {
                                    "content": {
                                        "value": query,
                                        "flags": "ALL",
                                        "case_insensitive": True,
                                        "max_determinized_states": 10000,
                                        "rewrite": "constant_score"
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        )
        return self.response_to_result(response)

    
if __name__ == "__main__":
    query = Query('news')
    print(query.get_pop_query())
    # results = query.phase_search("越南两位副总理")
    # for result in results[0:10]:
    #     print(result['title'], result['url'], result['type'])
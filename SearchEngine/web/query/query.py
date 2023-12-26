from elasticsearch import Elasticsearch
from datetime import datetime
import os
import pymysql
import re


bool_pattern = r"(\+|\-|\|)\((.*?)\)"  # 布尔查询的正则表达式

# type: douban,page,html
# label: douban,page,news

class Query:
    def __init__(self,label):
        self.clicked_urls = []  # 全局点击过的URL
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

    def set_urls(self,urls):
        self.clicked_urls = urls

    def get_pop_query(self,n):
        '''
        获取热门查询
        '''
        # 查询语句
        query = ("SELECT query_content FROM user_queries ORDER BY count DESC LIMIT %s")
        # 执行查询
        self.cursor.execute(query, (n,))
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
        
        # 只保存特定查询到数据库
        if type in ['<basic_search>', '<phase_search>', '<fuzz_search>']:
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
    
    def basic_search(self,query):
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
                "size": 300,
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
                                    "source": "_score * 0.1"
                                }
                            }
                        },
                        {
                            "filter": {
                                "terms": {
                                    "url": self.clicked_urls
                                }
                            },
                            "script_score": {
                                "script": {
                                    "source": "_score * 0.05"
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
                "size": 300,
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
                                    "source": "_score * 0.1"
                                }
                            }
                        },
                        {
                            "filter": {
                                "terms": {
                                    "url": self.clicked_urls
                                }
                            },
                            "script_score": {
                                "script": {
                                    "source": "_score * 0.05"
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
                "size" : 300,
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
        results = self.basic_search(query)
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
                "size" : 300,
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
                                    "source": "_score * 0.1"
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
                "size" : 300,
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

    def get_bool_querys(self,query):
        # 使用正则表达式检查must(+),must_not(-),should(|)三个关键词
        must = []
        must_not = []
        should = []
        matches = re.findall(bool_pattern,query)
        for match in matches:
            if match[0] == '+':
                must.extend(match[1].split(' '))
            elif match[0] == '-':
                must_not.extend(match[1].split(' '))
            elif match[0] == '|':
                should.extend(match[1].split(' '))
        # 去除空字符串
        must = [m for m in must if m != '']
        must_not = [m for m in must_not if m != '']
        should = [m for m in should if m != '']
        # 去除重复
        must = list(set(must))
        must_not = list(set(must_not))
        should = list(set(should))
        return must,must_not,should

    def search(self,query):
        '''
        分情况处理查询
        普通查询: query
        短语查询: "query"
        站内查询: #site:url query
        布尔查询: (must) +(query query); (must_not) -(query query); (should) |(query query)
        位置查询: #title: (query); #content: (query); 默认content和title都有
        正则表达式查询 #regex:query
        通配符查询: #wildcard:query
        '''
        # 分情况处理查询
        if query[0] == '"':
            # 短语查询
            results = self.phase_search(query[1:-1])
            query = query[1:-1]
        elif query[0] == '#':
            # 高级查询
            if query[1:6] == 'regex':
                # 正则表达式查询
                results = self.regexp_search(query[7:])
                query = query[7:]
            elif query[1:9] == 'wildcard':
                # 通配符查询
                results = self.wildcard_search(query[10:])
                query = query[10:]
            elif query[1:5] == 'site':
                # 站内查询
                query = query[6:]
                site = query.split(' ')[0]
                query = query[len(site)+1:]
                results = self.site_search(site,query)
            else:
                # 特定位置的布尔查询
                if query[1:6] == 'title':
                    field = 'title'
                    query = query[7:]
                elif query[1:8] == 'content':
                    field = 'content'
                    query = query[9:]
                else:
                    print('error in field')
                    raise Exception
                # 获取查询
                must,must_not,should = self.get_bool_querys(query)
                results = self.bool_search(must,must_not,should,field)
                if len(must) != 0:
                    query = must[0]
                elif len(should) != 0:
                    query = should[0]
                else:
                    print('error in bool search')
                    raise Exception
        elif query[0] == '+' or query[0] == '-' or query[0] == '|':
            # 全位置布尔查询
            must,must_not,should = self.get_bool_querys(query)
            results = self.bool_search(must,must_not,should)
            if len(must) != 0:
                query = must[0]
            elif len(should) != 0:
                query = should[0]
            else:
                print('error in bool search')
                raise Exception
        else:
            # 普通查询
            results = self.basic_search(query)
        
        # 如果结果不足10个，使用模糊查询补充
        if(len(results)<10):
            fuzz_results = self.fuzz_search(query)
            for result in fuzz_results:
                if result not in results:
                    results.append(result)

        return query,results
    

if __name__ == "__main__":
    # 测试正则表达式查询
    # bool_pattern = r"(\+|\-|\|)\((.*?)\)"  # 布尔查询的正则表达式
    # query = "+(apple watermelon) -(banana) |(cherry orange)"
    # matches = re.findall(bool_pattern,query)
    # for match in matches:
    #     if match[0] == '+':
    #         print(match[1].split(' '))
    #     elif match[0] == '-':
    #         print(match[1].split(' '))
    #     elif match[0] == '|':
    #         print(match[1].split(' '))
    query = Query('news')
    results = query.basic_search("越南两位副总理")
    for result in results[0:10]:
        print(result['title'], result['url'], result['type'])
from elasticsearch import Elasticsearch
import jieba
from datetime import datetime
import os

class Query:
    def __init__(self):
        self.es = Elasticsearch(hosts="http://localhost:9200")

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
    
    def wildcard_search(self, query):
        '''
        通配符查询
        '''
        self.save_query_log('<wildcard_search>', query)
        # 执行搜索
        response = self.es.search(
            index="web",
            body={
                "query": {
                    "wildcard": {
                        "title": {
                            "value": query,
                            "boost": 1.0,
                            "rewrite": "constant_score"
                        }
                    }
                }
            }
        )
        return self.response_to_result(response)
    
    def regexp_search(self, query):
        self.save_query_log('<regexp_search>', query)
        # 执行搜索
        response = self.es.search(
            index="web",
            body={
                "query": {
                    "regexp": {
                        "title": {
                            "value": query,
                            "flags": "ALL",
                            "case_insensitive": True,
                            "max_determinized_states": 10000,
                            "rewrite": "constant_score"
                        }
                    }
                }
            }
        )
        return self.response_to_result(response)
    # must mustnot should
            

if __name__ == "__main__":
    query = Query()
    results = query.regexp_search("Open(.)*") 
    for result in results[0:10]:
        print(result['title'], result['url'], result['type'])
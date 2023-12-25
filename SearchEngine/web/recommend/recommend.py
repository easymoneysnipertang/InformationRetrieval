import joblib
import jieba
import pymysql
from sklearn.metrics.pairwise import cosine_similarity
import jieba.analyse
import os
import numpy as np
import random

uselessClusters = [0,14]

class Recommend:
    def __init__(self):
        # 获取当前Python脚本的目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 更改当前工作目录
        os.chdir(current_dir)
        # 加载模型
        self.kmeans = joblib.load('kmeans_model.pkl')
        self.vectorizer = joblib.load('tfidf_model.pkl')
        # 连接数据库
        self.cnx = pymysql.connect(host='localhost', user='root', password='123qwe12')
        self.cursor = self.cnx.cursor()
        self.cnx.select_db('IR_db')
        # 初始化jieba分词
        jieba.initialize()
    
    def get_cluster(self,query):
        # 使用jieba进行分词
        query_cut = ' '.join(jieba.cut(query))
        # 使用TF-IDF模型将文本转换为数值向量
        query_vec = self.vectorizer.transform([query_cut])
        # 使用KMeans进行预测
        query_label = self.kmeans.predict(query_vec)
        print(f"The query is in cluster {query_label[0]}")
        return query_label[0]
    
    def get_cluster_docs(self,query_label,isSample=False):
        # 查询数据库
        self.cursor.execute("""
            SELECT web_id, title, type
            FROM cluster
            WHERE label = %s
        """, (query_label,))
        # 获取查询结果
        results = self.cursor.fetchall()
        # 如果isSample为真，随机采样
        if isSample and len(results) > 2000:
            results = random.sample(results, 2000)
        return results
    
    def cal_recommend(self,query,list,num,threshold):
        # 使用jieba进行分词
        list_cut = [' '.join(jieba.cut(l)) for l in list]
        # 使用TF-IDF模型将文本转换为数值向量
        list_vec = self.vectorizer.transform(list_cut)
        query_vec = self.vectorizer.transform([query])
        # 计算查询与簇中文档的余弦相似度
        similarities = cosine_similarity(query_vec, list_vec).flatten()
        # 获取相似度大于threshold的文档的索引
        indices = np.where(similarities >= threshold)[0]
        # 获取相似度大于threshold的文档的相似度
        similarities = similarities[indices]
        # 获取相似度排序的索引
        sorted_indices = similarities.argsort()[-num:]  # 取相似度最高的前n个
        # 获取推荐文档
        recommend_querys = [list[i] for i in indices[sorted_indices]]
        return recommend_querys


    def get_recommend(self,query,pop_query):
        # 获取查询所在的簇
        query_label = self.get_cluster(query)
        if query_label not in uselessClusters:
            recommend_querys = self.cal_recommend(query,pop_query,3,0.1)
            # 获取簇中的文档
            docs = self.get_cluster_docs(query_label)
            titles = [doc[1] for doc in docs]
            # 计算推荐文档索引
            recommend_cluster_querys = self.cal_recommend(query,titles,7,0.25)
        else:
            recommend_querys = self.cal_recommend(query,pop_query,5,0)
            # 获取簇中的文档
            docs = self.get_cluster_docs(query_label,True)
            titles = [doc[1] for doc in docs]
            # 计算推荐文档索引
            recommend_cluster_querys = self.cal_recommend(query,titles,5,0.1)
        # 合并
        recommend_querys.extend(recommend_cluster_querys)

        return recommend_querys
    

if __name__ == '__main__':
    recommend = Recommend()
    results = recommend.get_recommend('python', ['霸王别姬','肖申克','我爱python','java'])
    print(results)



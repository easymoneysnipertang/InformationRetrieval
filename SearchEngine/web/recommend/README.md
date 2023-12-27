## recommend

1. 保存查询记录，推荐top query
   - 选出top query来计算cosine_similarity
   
2. 对网页进行kmeans聚类，预测查询属于的类别，从类别里选取网页
   - 先使用jieba分词，去除停用词
   - 使用tfidf提取特征
   - 使用PCA降维
   - 使用kmeans聚类
   - 对查询进行predict，在类别里计算cosine_similarity

- clustering.ipynb：使用kmeans聚类
- recommend.py：计算推荐查询
- cn_stopwords.txt：中文停用词表
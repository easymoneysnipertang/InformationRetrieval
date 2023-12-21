# Information Retrieval
信息检索作业仓库  

- hw1：实现斯坦福大学CS 276 / LING 286: Information Retrieval and Web Search课程的代码框架

- hw2：论文阅读：RCENR

- hw5：搜索引擎
    - crawler：beautifulsoup4 + requests爬取了约15000条数据
    - index：elastic search建索引
    - search：elastic search查询，包含高级查询
    - page_rank：networkx计算pageRank，更新es索引
    - recommend：kmeans聚类用于后续推荐系统
    - web：flask搭建网页  

- hw6：倒排索引压缩与求交算法并行化
    - 压缩：d-gap + OptPFD
    - 求交：SVS
    - 并行化：SIMD + OpenMP
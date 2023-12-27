## pageRank

1. 从mysql数据库中读取数据，构建有向图  
2. 使用networkx包计算pageRank  
3. 将结果通过update语句更新到es索引中  
4. 查询时通过script_score来影响排序，但由于数据量太小，效果并不太好，使用函数不断平滑

- page_rank.ipynb


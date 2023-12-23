from flask import Flask, render_template, request
from query.query import Query
from recommend.recommend import Recommend

app = Flask(__name__)

global_label = 'douban'  # 用户选定的感兴趣内容标签
global_query = Query(global_label)  # 全局查询对象
global_recommend = Recommend()  # 全局推荐对象


def deal_query(query):
    results = global_query.search(query)
    results = results[:10]
    return results


def deal_recommend(query,pop_query):
    recommend_query = global_recommend.get_recommend(query,pop_query)
    print(recommend_query)
    # 推荐内容拆分
    if len(recommend_query) == 0:
        has_recommend = 0
    else:
        has_recommend = 1
    # 拆成两个列表
    recommend_query1 = recommend_query[:5]
    recommend_query2 = recommend_query[5:]
    return has_recommend,recommend_query1,recommend_query2


@app.route('/')
@app.route('/index')
def index():  # put application's code here
    # 获取当前热门查询
    pop_query = global_query.get_pop_query()
    return render_template('index.html',pop_query = pop_query)


@app.route('/results',methods=['POST','GET'])
def result():
    # 全局变量
    global global_label
    
    # 处理请求
    if request.method == 'POST':
        query = request.form['query']
    else:
        query = request.args.get('q')
        label = request.args.get('label')
        if label is not None:
            global_label = label
            global_query.set_label(global_label)
    print(query)

    # 处理查询
    results = deal_query(query)

    # 当前热门查询
    pop_query = global_query.get_pop_query()

    # 获取推荐内容
    has_recommend,recommend_query1,recommend_query2 = deal_recommend(query,pop_query)

    return render_template('result.html',pop_query = pop_query,query = query,
                           number=len(results),costTime=1,last_page=1,
                           results=results,
                           has_recommend=has_recommend,recommend_query1=recommend_query1,recommend_query2=recommend_query2)


if __name__ == '__main__':
    app.run()

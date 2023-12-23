from flask import Flask, render_template, request
from query.query import Query
from recommend.recommend import Recommend
import time
import jieba
import re

app = Flask(__name__)

stop_words = ["的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "他", "这", "中", "大", "以", "到", "说", "等", "能", "也", "上", "或", "之", "但", "个", "都", "而", "啊", "把", "那", "你", "一", "为", "所", "年", "没", "着", "要", "与"]
global_label = 'douban'  # 用户选定的感兴趣内容标签
global_query = Query(global_label)  # 全局查询对象
global_recommend = Recommend()  # 全局推荐对象
bool_pattern = r"(\+|\-|\|)\((.*?)\)"  # 布尔查询的正则表达式


def get_bool_querys(query):
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


def deal_query(query):
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
        results = global_query.phase_search(query[1:-1])
        query = query[1:-1]
    elif query[0] == '#':
        # 高级查询
        if query[1:6] == 'regex':
            # 正则表达式查询
            results = global_query.regexp_search(query[7:])
            query = query[7:]
        elif query[1:10] == 'wildcard':
            # 通配符查询
            results = global_query.wildcard_search(query[11:])
            query = query[11:]
        elif query[1:5] == 'site':
            # 站内查询
            query = query[6:]
            site = query.split(' ')[0]
            query = query[len(site)+1:]
            results = global_query.site_search(site,query)
        else:
            # 特定位置的布尔查询
            if query[1:6] == 'title':
                field = 'title'
                query = query[7:]
            elif query[1:8] == 'content':
                field = 'content'
                query = query[9:]
            else:
                print('error')
                raise Exception
            # 获取查询
            must,must_not,should = get_bool_querys(query)
            results = global_query.bool_search(must,must_not,should,field)
            if len(must) != 0:
                query = must[0]
            elif len(should) != 0:
                query = should[0]
            else:
                print('error')
                raise Exception
    elif query[0] == '+' or query[0] == '-' or query[0] == '|':
        # 全位置布尔查询
        must,must_not,should = get_bool_querys(query)
        results = global_query.bool_search(must,must_not,should)
        if len(must) != 0:
            query = must[0]
        elif len(should) != 0:
            query = should[0]
        else:
            print('error')
            raise Exception
    else:
        # 普通查询
        results = global_query.search(query)
    
    # 如果结果不足10个，使用模糊查询补充
    if(len(results)<10):
        fuzz_results = global_query.fuzz_search(query)
        for result in fuzz_results:
            if result not in results:
                results.append(result)
    # 暂时只返回前10个结果
    results = results[:10]
    return query,results


def deal_recommend(query,pop_query):
    # 获取推荐内容
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


def deal_highlight(query):
    # 得到高亮词汇
    query_cut = [word for word in jieba.cut(query) if word not in stop_words]
    highlight = ' '.join(query_cut)
    return highlight


@app.route('/')
@app.route('/index')
def index():  # put application's code here
    # 获取当前热门查询
    pop_query = global_query.get_pop_query(5)
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

    # 记录开始时间
    start_time = time.time()

    # 处理查询
    try:
        query,results = deal_query(query)
    except:
        return render_template('error.html',query=query)
    
    # 当前热门查询
    pop_query = global_query.get_pop_query(20)

    # 处理相关搜索
    has_recommend,recommend_query1,recommend_query2 = deal_recommend(query,pop_query)

    # 记录结束时间
    end_time = time.time()
    cost_time = round(end_time - start_time, 3)

    # 处理高亮
    highlight = deal_highlight(query)

    return render_template('result.html',pop_query = pop_query[:8],query = query,
                           number=len(results),cost_time=cost_time,last_page=1,
                           results=results,
                           has_recommend=has_recommend,recommend_query1=recommend_query1,recommend_query2=recommend_query2,
                           highlight=highlight)


if __name__ == '__main__':
    app.run()

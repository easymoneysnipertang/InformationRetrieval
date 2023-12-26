from flask import Flask, render_template, request
from query.query import Query
from recommend.recommend import Recommend
import time
import jieba
import save_user

app = Flask(__name__)

page_number = 1  # 全局页码
total_page = 1  # 全局总页数
global_results = []  # 全局结果
last_query = ''  # 上一次查询

global_login = False  # 全局登录状态
global_userid = ''  # 全局用户ID
global_label = 'douban'  # 用户选定的感兴趣内容标签
clicked_urls = []  # 全局点击过的URL

global_query = Query(global_label)  # 全局查询对象
global_recommend = Recommend()  # 全局推荐对象

stop_words = ["的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "他", "这", "中", "大", "以", "到", "说", "等", "能", "也", "上", "或", "之", "但", "个", "都", "而", "啊", "把", "那", "你", "一", "为", "所", "年", "没", "着", "要", "与"]


def deal_query(query):
    # 全局变量
    global global_results,page_number,total_page
    # 处理查询
    query,global_results = global_query.search(query)
    total_page = len(global_results) // 10 + 1
    page_number = 1
    results = global_results[:10]
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
@app.route('/login', methods=['POST'])
@app.route('/index/login', methods=['POST'])
def index():  # put application's code here
    global global_login,global_userid,global_label,clicked_urls,global_query
    # 获取用户输入的数据
    userid = request.form.get('userid')
    password = request.form.get('password')
    interest = request.form.get('interest')
    if userid is not None:
        # 处理登录
        global_login = True
        global_userid = userid
        global_label = interest
        global_query.set_label(global_label)
        print('用户登录成功: ' + userid)
        # 保存用户信息
        if save_user.save_user(userid,password,interest) == False:
            # 用户已存在，提取url记录
            clicked_urls = save_user.get_user(userid)
            global_query.set_urls(clicked_urls)

    # 获取当前热门查询
    pop_query = global_query.get_pop_query(5)
    return render_template('index.html',pop_query = pop_query ,is_login=global_login,user_id=global_userid)


@app.route('/results',methods=['POST','GET'])
def result():
    # 全局变量
    global global_label,last_query,page_number,total_page,global_results
    
    # 处理请求
    if request.method == 'POST':
        query = request.form['query']
        get_page = None
    else:
        query = request.args.get('q')
        label = request.args.get('label')
        get_page = request.args.get('page')
        if label is not None:
            global_label = label
            global_query.set_label(global_label)

    # 记录开始时间
    start_time = time.time()

    # 处理查询
    if get_page is not None:
        page_number = int(get_page)
        results = global_results[(page_number-1)*10:page_number*10]
        query = last_query
    else:
        try:
            query,results = deal_query(query)
            last_query = query
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
                           number=len(global_results),cost_time=cost_time,
                           last_page=total_page,page=page_number,
                           results=results,
                           has_recommend=has_recommend,recommend_query1=recommend_query1,recommend_query2=recommend_query2,
                           highlight=highlight)


@app.route('/results/handle_click', methods=['POST'])
def handle_click():
    global clicked_urls,global_userid,global_query
    url = request.form.get('url')
    if url is None:
        return 'none'
    print('用户点击了URL: ' + url)
    # 处理点击
    clicked_urls.append(url)
    print(clicked_urls)
    global_query.set_urls(clicked_urls)
    # 更新用户信息
    save_user.update_user(global_userid, url)
    return 'success'


if __name__ == '__main__':
    app.run()

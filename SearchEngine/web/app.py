from flask import Flask, render_template, request

app = Flask(__name__)

pop_query = ['test1','test2']

@app.route('/')
def index():  # put application's code here
    return render_template('index.html',pop_query = pop_query)


@app.route('/results',methods=['POST','GET'])
def result():
    if request.method == 'POST':
        query = request.form['query']
    else:
        query = request.args.get('q')
    print(query)
    return render_template('result.html',pop_query = pop_query,query = query,number=0,costTime=1,last_page=1)


if __name__ == '__main__':
    app.run()

# encoding: utf-8
from flask import Flask, request, session, render_template
from app import Wechat, wechat_required,command_handler
from wechatpy.replies import TextReply




app = Flask(__name__)

wechat = Wechat(app)


@app.route('/')
def index():
    host = request.url_root
    return render_template("index.html", host=host)

@app.route('/test')
def test():
    return 


@app.route('/clear')
def clear():
    if 'wechat_user_id' in session:
        session.pop('wechat_user_id')
    return "ok"


@app.route('/vanilla', methods=['GET', 'POST'])
@wechat_required
def wechat_vanilla():
    msg = request.wechat_msg
    #handler = handlerr.Handler()
    #text = handler.command()
    print(msg)
    reply = TextReply(content='hello', message=msg)
    return reply
    

@app.route('/chocolate', methods=['GET', 'POST'])
@wechat_required
def wechat_chocolate():
    msg = request.wechat_msg
    print(msg)
    handler = command_handler.Handler(app)
    try:
        text = str(handler.command())
    except Exception as e:
        text = str(e)
    reply = TextReply(content=text, message=msg)
    return reply



@app.route('/access_token')
def access_token():
    return "access token: {}".format(wechat.access_token)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    
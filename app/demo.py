# -*- coding: utf-8 -*-
import os
from flask import Flask, request, abort, render_template
try:
    from wechatpy.enterprise import parse_message, create_reply
except ImportError:
    from wechatpy.work import parse_message, create_reply
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.enterprise.exceptions import InvalidCorpIdException



TOKEN = os.getenv("WECHAT_TOKEN", "Or8MFOL3JoFXrP6uHUIKMahhrJpss")
EncodingAESKey = os.getenv("WECHAT_ENCODING_AES_KEY", "SF2UTLoDQsUMn24Afy4j4U7wX27E6e3O9GfaATKu8d0")
CorpId = os.getenv("WECHAT_CORP_ID", "wwc5f877b25a062a89")

app = Flask(__name__)


@app.route("/")
def index():
    host = request.url_root
    return render_template("index.html", host=host)


@app.route("/wechat", methods=["GET", "POST"])
def wechat():
    signature = request.args.get("msg_signature", "")
    timestamp = request.args.get("timestamp", "")
    nonce = request.args.get("nonce", "")

    crypto = WeChatCrypto(TOKEN, EncodingAESKey, CorpId)
    if request.method == "GET":
        echo_str = request.args.get("echostr", "")
        try:
            echo_str = crypto.check_signature(signature, timestamp, nonce, echo_str)
        except InvalidSignatureException:
            abort(403)
        return echo_str
    else:
        try:
            msg = crypto.decrypt_message(request.data, signature, timestamp, nonce)
        except (InvalidSignatureException, InvalidCorpIdException):
            abort(403)
        msg = parse_message(msg)
        if msg.type == "text":
            reply = create_reply(msg.content, msg).render()
        else:
            reply = create_reply("Can not handle this for now", msg).render()
        res = crypto.encrypt_message(reply, nonce, timestamp)
        return res
def _check_user():
    from flask import session
    return session.get('wechat_user_id')


def _set_user(user_info):
    from flask import session
    session['wechat_user_id'] = user_info['openid']


def oauth(check_func=_check_user, set_user=_set_user, scope='snsapi_base', state=None):
    def decorater(method):
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            from wechatpy.oauth import WeChatOAuth
            if callable(state):
                _state = state()
            else:
                _state = state or ''
            redirect_uri = current_app.config.get('WECHAT_OAUTH_URI')
            if not redirect_uri:
                redirect_uri = request.url

            user_agent = request.headers.get('User-Agent').lower()
            if 'micromessenger' in user_agent:
                app_id = current_app.config['WECHAT_APPID']
                secret = current_app.config['WECHAT_SECRET']
                url_method = 'authorize_url'
            else:
                app_id = current_app.config['WECHAT_OPEN_APP_ID']
                secret = current_app.config['WECHAT_OPEN_APP_SECRET']
                url_method = 'qrconnect_url'

            wechat_oauth = WeChatOAuth(app_id, secret, redirect_uri, scope, _state)

            user = check_func()
            if request.args.get('code') and not user:
                try:
                    res = wechat_oauth.fetch_access_token(request.args['code'])
                except WeChatOAuthException:
                    return abort(403)
                else:
                    if scope == 'snsapi_base':
                        set_user(res)
                    else:
                        user_info = wechat_oauth.get_user_info()
                        set_user(user_info)
            elif not user:
                return redirect(getattr(wechat_oauth, url_method))
            return method(*args, **kwargs)
        return wrapper
    return decorater


class WechatPay(object):

    def __init__(self, app=None):

        self._wechat_client = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        config = app.config
        config.setdefault('WECHAT_APPID', None)
        config.setdefault('WECHAT_PAY_API_KEY', None)
        config.setdefault('WECHAT_PAY_MCH_CERT', None)
        config.setdefault('WECHAT_PAY_MCH_KEY', None)
        config.setdefault('WECHAT_PAY_MCH_ID', None)
        config.setdefault('WECHAT_PAY_SUB_MCH_ID', None)

        assert config['WECHAT_APPID'] is not None
        assert config['WECHAT_PAY_API_KEY'] is not None
        assert config['WECHAT_PAY_MCH_CERT'] is not None
        assert config['WECHAT_PAY_MCH_KEY'] is not None
        assert config['WECHAT_PAY_MCH_ID'] is not None

        self._wechat_pay = ori_WeChatPay(
            appid=config['WECHAT_APPID'],
            api_key=config['WECHAT_PAY_API_KEY'],
            mch_id=config['WECHAT_PAY_MCH_ID'],
            sub_mch_id=config.get('WECHAT_PAY_SUB_MCH_ID', None),
            mch_cert=config['WECHAT_PAY_MCH_CERT'],
            mch_key=config['WECHAT_PAY_MCH_KEY'],
        )
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['wechat_pay'] = self

    def __getattr__(self, name):
        return getattr(self._wechat_pay, name)


if __name__ == "__main__":
    app.run("127.0.0.1", 5001, debug=True)
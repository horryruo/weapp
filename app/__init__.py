#!/usr/bin/env python
# encoding: utf-8

from requests.sessions import session
from app.demo import oauth
import functools, configparser
from flask import request, current_app, abort, redirect
from wechatpy.replies import BaseReply
from wechatpy.pay import WeChatPay as ori_WeChatPay
from wechatpy.utils import check_signature
from wechatpy.exceptions import (
    InvalidSignatureException,
    InvalidAppIdException,
    WeChatOAuthException,
)
class AppConfig(object):
    def __init__(self,app):
        config = configparser.ConfigParser()
        config.read("config.ini", encoding='utf-8')
        app.config['WECHAT_TYPE'] = config['default']['type']
        app.config['WECHAT_SECRET'] = config['push']['corp_secret']
        app.config['WECHAT_APPID'] = config['wechat_corp']['corp_id']
        app.config['WECHAT_TOKEN'] = config['wechat_corp']['corp_token']
        app.config['WECHAT_AES_KEY'] = config['wechat_corp']['corp_aeskey']
        app.config['WECHAT_AGENTID'] = config['push']['corp_agentid']
        if config['ql']['ql_api'] == 'true':
            app.config['QL_HOST'] = config['ql']['ql_host']
            Client_ID = config['ql']['ql_client_id']
            Client_Secret = config['ql']['ql_client_secret']
            app.config['QL_TOKEN'] = self.ql_token(config['ql']['ql_token'],Client_ID,Client_Secret,config['ql']['ql_host'],config)
        secret_key = config['default']['secret_key']
        if secret_key == '':
            import os
            secret_key = os.urandom(24)
            config.set("default", "secret_key", str(secret_key))
            with open("config.ini", "w+") as f:
                config.write(f)
        app.secret_key = secret_key
    def ql_token(self,token,id,secret,host,config):
        import json,requests
        headers = {
            'Authorization': 'Bearer %s'%token,
            'Content-Type': 'application/json;charset=UTF-8',
            }
        token_url = 'http://{}/open/auth/token?client_id={}&client_secret={}'.format(host,id,secret)
        oauth_url = 'http://%s/open/envs'%host
        res = requests.get(oauth_url,headers=headers)
        stats = str(json.loads(res.text).get('code'))
        if stats=='200':
            return token
        else:
            res = requests.get(token_url)
            token = json.loads(res.text).get('data').get('token')
            config.set("ql", "ql_token", str(token))
            with open("config.ini", "w+") as f:
                config.write(f)
            print(token)
            return token

class Wechat(object):

    def __init__(self, app=None):

        self._wechat_client = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        appconfig = AppConfig(app)
        config = app.config
        config.setdefault('WECHAT_APPID', None)
        config.setdefault('WECHAT_SECRET', None)
        config.setdefault('WECHAT_TYPE', 1)
        config.setdefault('WECHAT_SESSION_TYPE', None)
        config.setdefault('WECHAT_SESSION_PREFIX', 'wechatapp')
        config.setdefault('WECHAT_AUTO_RETRY', True)
        config.setdefault('WECHAT_TIMEOUT', None)

        assert config['WECHAT_APPID'] is not None
        assert config['WECHAT_SECRET'] is not None

        if config['WECHAT_TYPE'] == 0:
            from wechatpy import WeChatClient
        else:
            from wechatpy.enterprise import WeChatClient

        if config['WECHAT_SESSION_TYPE'] == 'redis':
            from wechatpy.session.redisstorage import RedisStorage
            from redis import Redis
            if config.get('WECHAT_SESSION_REDIS_URL'):
                redis = Redis.from_url(config['WECHAT_SESSION_REDIS_URL'])
            else:
                redis = Redis(
                    host=config.get('WECHAT_SESSION_REDIS_HOST', 'localhost'),
                    port=config.get('WECHAT_SESSION_REDIS_PORT', 6379),
                    db=config.get('WECHAT_SESSION_REDIS_DB', 0),
                    password=config.get('WECHAT_SESSION_REDIS_PASS', None)
                )
            session_interface = RedisStorage(redis, prefix=config['WECHAT_SESSION_PREFIX'])
        elif config['WECHAT_SESSION_TYPE'] == 'memcached':
            from wechatpy.session.memcachedstorage import MemcachedStorage
            mc = self._get_mc_client(config['WECHAT_SESSION_MEMCACHED'])
            session_interface = MemcachedStorage(mc, prefix=config['WECHAT_SESSION_PREFIX'])
        elif config['WECHAT_SESSION_TYPE'] == 'shove':
            pass
        else:
            session_interface = None

        self._wechat_client = WeChatClient(
            config['WECHAT_APPID'],
            config['WECHAT_SECRET'],
            session=session_interface,
            timeout=config['WECHAT_TIMEOUT'],
            auto_retry=config['WECHAT_AUTO_RETRY'],
        )

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['wechatpy'] = self

    def __getattr__(self, name):
        return getattr(self._wechat_client, name)

    def _get_mc_client(self, servers):
        try:
            import pylibmc
        except ImportError:
            pass
        else:
            return pylibmc.Client(servers)

        try:
            import memcache
        except ImportError:
            pass
        else:
            return memcache.Client(servers)


def wechat_required(method):

    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        if current_app.config['WECHAT_TYPE'] == 0:
            res = _wechat_required(method, *args, **kwargs)
        else:
            res = _enterprise_wechat_required(method, *args, **kwargs)

        return res

    return wrapper


def _wechat_required(method, *args, **kwargs):
    from wechatpy.crypto import WeChatCrypto
    from wechatpy import parse_message

    signature = request.args.get('signature')

    timestamp = request.args.get('timestamp')
    nonce = request.args.get('nonce')

    if not current_app.config.get('WECHAT_TOKEN'):
        return abort(500, "Token is None")

    token = current_app.config['WECHAT_TOKEN']
    try:
        check_signature(token, signature, timestamp, nonce)
    except InvalidSignatureException:
        current_app.logger.warning('check signature failed.')
        return abort(403)

    if request.method == 'GET':
        return request.args.get('echostr', '')

    raw_msg = request.data
    current_app.logger.debug(raw_msg)
    if current_app.config.get('WECHAT_AES_KEY'):
        crypto = WeChatCrypto(
            current_app.config['WECHAT_TOKEN'],
            current_app.config['WECHAT_AES_KEY'],
            current_app.config['WECHAT_APPID']
        )
        try:
            msg_signature = request.args.get('msg_signature', '')
            raw_msg = crypto.decrypt_message(
                raw_msg,
                msg_signature,
                timestamp,
                nonce
            )
        except (InvalidAppIdException, InvalidSignatureException):
            current_app.logger.warning('decode message failed.')
            return abort(403)

    request.wechat_msg = parse_message(raw_msg)

    res = method(*args, **kwargs)
    xml = ''

    if isinstance(res, BaseReply):
        xml = res.render()

    if current_app.config.get('WECHAT_AES_KEY'):
        crypto = WeChatCrypto(
            current_app.config['WECHAT_TOKEN'],
            current_app.config['WECHAT_AES_KEY'],
            current_app.config['WECHAT_APPID']
        )
        xml = crypto.encrypt_message(xml, nonce, timestamp)

    return xml


def _enterprise_wechat_required(method, *args, **kwargs):
    from wechatpy.enterprise import parse_message
    from wechatpy.enterprise.crypto import WeChatCrypto
    from wechatpy.exceptions import InvalidSignatureException
    from wechatpy.enterprise.exceptions import InvalidCorpIdException
    signature = request.args.get("msg_signature", "")
    timestamp = request.args.get("timestamp", "")
    nonce = request.args.get("nonce", "")

    if not current_app.config.get('WECHAT_TOKEN'):
        return abort(500, "Token is None")

    crypto = WeChatCrypto(
        current_app.config['WECHAT_TOKEN'],
        current_app.config['WECHAT_AES_KEY'],
        current_app.config['WECHAT_APPID']
    )
    
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
        request.wechat_msg = msg
    res = method(*args, **kwargs)
    xml = ''
    if isinstance(res, BaseReply):
        xml = res.render()
    xml = crypto.encrypt_message(xml, nonce, timestamp)
    return xml



class Wecom(object):
    def __init__(self):
        self.wecom_cid = current_app.config['WECHAT_APPID']
        self.wecom_aid = current_app.config['WECHAT_AGENTID']
        self.wecom_secret = current_app.config['WECHAT_SECRET']
        
    def send(self,text,wecom_touid='@all'):
        import json,requests
        get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.wecom_cid}&corpsecret={self.wecom_secret}"
        response = requests.get(get_token_url).content
        access_token = json.loads(response).get('access_token')
        if access_token and len(access_token) > 0:
            send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
            data = {
                "touser":wecom_touid,
                "agentid":self.wecom_aid,
                "msgtype":"text",
                "text":{
                    "content":text
                },
                "duplicate_check_interval":600
            }
            response = requests.post(send_msg_url,data=json.dumps(data)).content
            return response
        else:
            return False






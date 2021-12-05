import requests,time,json
from flask import current_app
import prettytable as pt


class QLAPI(object):
    def __init__(self, app=None):
        self.token = self.api_token(current_app.config['QL_TOKEN'],app)
        self.host = 'http://{}/open/'.format(current_app.config['QL_HOST'])
        headers = {
            'Authorization': 'Bearer %s'%self.token,
            'Content-Type': 'application/json;charset=UTF-8',
            }
        self.session = requests.session()
        self.session.headers.update(headers)
        self.time = round(time.time() * 1000)
    
    def api_token(self,token, app=None):
        headers = {
            'Authorization': 'Bearer %s'%token,
            'Content-Type': 'application/json;charset=UTF-8',
            }
        token_url = 'http://{}/open/auth/token?client_id={}&client_secret={}'.format(current_app.config['QL_HOST'],current_app.config['Client_ID'],current_app.config['Client_Secret'])
        oauth_url = 'http://%s/open/envs'%current_app.config['QL_HOST']
        res = requests.get(oauth_url,headers=headers)
        stats = str(json.loads(res.text).get('code'))
        if stats=='200':
            return token
        else:
            res = requests.get(token_url)
            token = json.loads(res.text).get('data').get('token')
            app.config['QL_TOKEN'] = token
            print(token)
            return token

    def new_envs(self,name,value,remarks=None):
        if name == 'jd':
            name = 'JD_COOKIE'
        if remarks ==None:
            data = [{"value": value, "name": name}]
        else:
            data = [{"value": value, "name": name,"remarks":remarks}]
        url = self.host + 'envs'
        res = self.session.post(url, json=data,params={"t":self.time})
        res.encoding = 'utf-8'
        res_json = json.loads(res.text)
        stats = str(res_json['code'])
        if stats=='200':
            data = res_json['data']
            if name =='JD_COOKIE':
                text = '成功添加{},cookies={},id为{},稍后推送状态'.format(name,value,data[0]['_id'])
                id = ['3OP1NFLv3OCt1Gdd']
                run = self.run_crons(id)
                return text
            else:
                text = '成功添加不是京东ck:{},cookies={},id={},'.format(name,value,data[0]['_id'])
                return text
        else:
            error = res_json.get('message')
            return error

    def get_envs(self):
        url = self.host + 'envs'
        res = self.session.get(url,params={"t":self.time,"searchValue":""})
        res_json = json.loads(res.text)
        data = res_json['data']
        res.encoding = 'utf-8'
        tb = pt.PrettyTable()
        tb.left_padding_width = 0
        tb.right_padding_width = 0
        #tb.set_style(pt.MSWORD_FRIENDLY)
        tb.field_names = ["名字", "状态","别名"]
        for id in data:
            tb.add_row([id['name'],id['status'],id.get('remarks')])
        tbb = tb.get_string()
        return tbb
        

    def run_crons(self,idlist):
        url = self.host + 'crons/run'
        res = self.session.put(url, json=idlist,params={"t":self.time})
        res.encoding = 'utf-8'
        res_json = json.loads(res.text)
        stats = str(res_json['code'])
        print(res.text)
        if stats =='200':
            return stats
        else:
            return stats
    def get_crons(self,value):
        url = self.host + 'crons'
        res = self.session.get(url,params={"t":self.time,"searchValue":value})
        res.encoding = 'utf-8'
        res_json = json.loads(res.text)
        stats = str(res_json['code'])
        #print(res.text)
        return res.text



if __name__ == '__main__':
#access_token()
#new_corns()
    new_envs()

import requests,time,json
from flask import current_app
import prettytable as pt


class QLAPI(object):
    def __init__(self):
        self.host = 'http://{}/open/'.format(current_app.config['QL_HOST'])
        headers = {
            'Authorization': 'Bearer %s'%current_app.config['QL_TOKEN'],
            'Content-Type': 'application/json;charset=UTF-8',
            }
        self.session = requests.session()
        self.session.headers.update(headers)
        self.time = round(time.time() * 1000)

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
                run = self.run_corns('GVZlQ05o9h2zBknd')
                return text
            else:
                text = '成功添加不是京东ck:{},cookies={},id={},'.format(name,value,data[0]['_id'])
                return text
        else:
            error = res_json['message']
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
        tb.field_names = ["名字", "创建时间", "状态","别名"]
        for id in data:
            tb.add_row([id['name'],id['timestamp'],id['status'],id['remarks']])
        tbb = tb.get_string()
        return tbb
        

    def run_corns(self,idlist):
        data = []
        data.append(idlist)
        url = self.host + 'corns/run'
        res = self.session.put(url, json=data,params={"t":self.time})
        res.encoding = 'utf-8'
        res_json = json.loads(res.text)
        stats = str(res_json['code'])
        print(res.text)
        if stats =='200':
            return stats
        else:
            return stats





if __name__ == '__main__':
#access_token()
#new_corns()
    new_envs()

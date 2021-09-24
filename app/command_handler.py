from six import remove_move
from app import ql
from flask import request


class Handler(object):
    def __init__(self):
        self.msg = request.wechat_msg.content
        self.qlapi = ql.QLAPI()
    def command(self):
        content = self.msg.split(' ')
        command = content[0]
        args = content[1:]
        if command == '添加':
            return self.new_envs(args)
        if command == '查看':
            return self.get_envs()
        if command =='运行':
            return self.run_corns(args)
        else:
            error = '指令错误'
            return error
        
    def new_envs(self,args):
        try:
            
            if args[2:]==[]:
                return self.qlapi.new_envs(args[0],args[1])
            else:
                remarks = args[2]
                return self.qlapi.new_envs(args[0],args[1],remarks)
        except Exception as e:
            print(str(e))
            return  str(e)
    def get_envs(self):
        return self.qlapi.get_envs()
    def run_corns(self,args):
        if args[0] == "ck":
            return self.qlapi.run_corns('GVZlQ05o9h2zBknd')
        else:
            return self.qlapi.run_corns(args)










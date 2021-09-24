
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
        if command == 'addck':
            return self.new_envs(args)
        elif command == 'getck':
            return self.get_envs()
        elif command =='runcron':
            return self.run_crons(args)
        elif command == 'getcron':
            return self.get_crons(args)
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
    def run_crons(self,args):
        if args[0] == "ck":
            id = ['3OP1NFLv3OCt1Gdd']
            return self.qlapi.run_crons(id)
        else:
            return self.qlapi.run_crons(args)

    def get_crons(self,value=None):
        return self.qlapi.get_crons(value)








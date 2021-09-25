
from app import ql, get_update
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
        elif command == 'update':
            return self.get_updates(args)
        elif command == 'restart':
            return self.restart()
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

    def get_updates(self,args):
        repo = get_update.Version('https://github.com/horryruo/weapp.git')
        if args[:] == []:
            updatetime = repo.get_time()
            text = '最新版本更新日期：{} (UTC+8)'.format(updatetime)
            return text
        elif args[0]=='ok':
            try:
                pull = repo.pull()
            except Exception as e:
                pull = str(e)
            print(pull)
            import re
            matchline = re.search( r'file changed|Already|merge', pull, re.M|re.I).group()
            #print(matchline)
            if matchline == 'Already':
                text = '版本已是最新，无需更新'
            elif matchline == 'file changed':
                text = '更新完成，请输入restart 重启程序完成更新'
            elif matchline == 'merge':
                text = '你可能修改过项目文件，无法自动更新，请手动解决或重新下载程序'
            else:
                text = str(pull)
            return text
            
        else:
            error = '指令错误'
            return error

    def restart(self):
        return get_update.restart()


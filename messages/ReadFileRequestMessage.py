# last generated 2016-12-30 20:11:43.962000
from messages import BaseMessage
from msg_codes import READ_FILE_REQUEST as READ_FILE_REQUEST
__author__ = 'Mike'


class ReadFileRequestMessage(BaseMessage):
    def __init__(self, sid=None, cloud_uname=None, cname=None, fpath=None):
        super(ReadFileRequestMessage, self).__init__()
        self.type = READ_FILE_REQUEST
        self.sid = sid
        self.cloud_uname = cloud_uname
        self.cname = cname
        self.fpath = fpath

    @staticmethod
    def deserialize(json_dict):
        msg = ReadFileRequestMessage()
        msg.sid = json_dict['sid']
        msg.cloud_uname = json_dict['cloud_uname']
        msg.cname = json_dict['cname']
        msg.fpath = json_dict['fpath']
        return msg


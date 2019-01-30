#!/usr/bin/python
# -*- coding: UTF-8 -*-
# 导入阿里云SDK
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
# 导入阿里云错误模块
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
# 导入需要模块
import json,sys,re,os,string

def cprint(str, color, display=1):
    """ 
        -------------------------------------------
        color:
        -------------------------------------------
        字体色     |       背景色     |      颜色描述
        -------------------------------------------
        30        |        40       |       黑色
        31        |        41       |       红色
        32        |        42       |       绿色
        33        |        43       |       黃色
        34        |        44       |       蓝色
        35        |        45       |       紫红色
        36        |        46       |       青蓝色
        37        |        47       |       白色
        -------------------------------------------
        display:
        -------------------------------
        显示方式     |      效果
        -------------------------------
        0           |     终端默认设置
        1           |     高亮显示
        4           |     使用下划线
        5           |     闪烁
        7           |     反白显示
        8           |     不可见
        -------------------------------
    """
    return '\033[{2};{1}m{0}\033[0m'.format(str,color,display)


class DDNS:
    '''针对指定域名的主机记录为A的动态域名解析'''
    my_ip=None
    def __init__(self,access_key_id,access_key_secret,domain,rr="@"):
        '''针对指定域名的DDNS初始化'''
        self.domain=domain
        self.rr=rr
        self.type=type
        # AcsClient连接
        self.__client = AcsClient(access_key_id, access_key_secret, 'cn-hangzhou')
        # 使用CommonRequest进行调用
        self.__request = CommonRequest()
        # CommonRequest请求公共参数
        self.__public_request()
        # 初次请求
        response = self.__Initial_request(domain, rr)
        #保存返回解析记录
        self.save_record(response)


    def __public_request(self):
        # 设置CommonRequest返回格式
        self.__request.set_accept_format('json')
        # 设置CommonRequest服务地址
        self.__request.set_domain('alidns.aliyuncs.com')
        # 设置CommonRequest提交方式
        self.__request.set_method('POST')
        # 设置CommonRequest通讯协议
        self.__request.set_protocol_type('https') # https | http
        # 设置CommonRequest版本信息
        self.__request.set_version('2015-01-09')


    def __Initial_request(self, domain_name, rr_word, type_word='A'):
        # 请求操作接口名：DescribeDomainRecords
        self.__request.set_action_name('DescribeDomainRecords')
        # 请求指定域名
        self.__request.add_query_param('DomainName', domain_name)
        # 请求指定主机记录
        self.__request.add_query_param('RRKeyWord', rr_word)
        # 请求指定解析类型
        self.__request.add_query_param('TypeKeyWord', type_word)
        # 发送请求,并获取返回参数或错误
        response = self.__client.do_action_with_exception(self.__request)
        return response

    def save_record(self, response):
        '''保存需要的解析记录'''
        if sys.version_info > (3,0):
            response = response.decode('utf-8')
        # json转换
        response = json.JSONDecoder().decode(response)
        if 'DomainRecords' in response :
            # 获取解析记录
            response = response['DomainRecords']
            if 'Record' in response:
                response = response['Record']
                if len(response) == 0:
                    print(cprint('No ','31')+cprint(self.rr+"."+self.domain,'36')+cprint(" parsing record!",'31'))
                    self.__status=False
                    return
                elif len(response) == 1:
                    response = response[0]

        # 获取解析记录IP
        self.__parser_ip = response['Value']
        # 获取解析记录RecordId
        self.__record_id = response['RecordId']
        # 获取解析记录RR
        self.__rr = response['RR']
        # 获取解析记录Type
        self.__type = response['Type']
        # 获取解析记录ttl
        self.__ttl = response['TTL']
        # DDNS状态
        self.__status = True


    @staticmethod
    def native_ip(url="http://txt.go.sohu.com/ip/soip"):
        '''获取本机当前公网ip'''
        # 判断当前python版本
        if sys.version_info < (3,0):
            # python2.*导入的模块
            import urllib2
            url = urllib2.urlopen(url)
            text = url.read()
            ip = re.findall(r'\d+.\d+.\d+.\d+',text)
            DDNS.my_ip = "{0}".join(ip)
            return "{0}".join(ip)
        else:
            # python3.*导入的模块
            import urllib
            url = urllib.request.urlopen(url)
            text = url.read().decode('utf-8')
            ip = re.findall(r'\d+.\d+.\d+.\d+',text)
            DDNS.my_ip = "{0}".join(ip)
            return "{0}".join(ip)


    def parser_ip(self):
        '''获取解析记录IP'''
        # 判断DDNS初始化是否成功
        if not self.__status :
            return
        # 请求操作接口名：DescribeDomainRecordInfo
        self.__request.set_action_name('DescribeDomainRecordInfo')
        # 请求指定解析记录的ID
        self.__request.add_query_param('RecordId', self.__record_id)
        # 发送请求,并获取返回参数或错误
        response = self.__client.do_action_with_exception(self.__request)
        # 保存新的解析记录
        self.save_record(response)
        return self.__parser_ip



    def update_ip(self, dns_value, dns_ttl='600'):
        '''更新解析ip'''
        # 判断DDNS初始化是否成功
        if not self.__status :
            return
        # 请求操作接口名：UpdateDomainRecord
        self.__request.set_action_name('UpdateDomainRecord')
        # 请求解析记录的ID：RecordId
        self.__request.add_query_param('RecordId', self.__record_id)
        # 请求设置解析记录的主机记录：RR
        self.__request.add_query_param('RR', self.__rr)
        # 请求设置解析记录类型：Type
        self.__request.add_query_param('Type', self.__type)
        # 请求设置解析记录的记录值：IP
        self.__request.add_query_param('Value', dns_value)
        # 请求设置生存时间：TTL
        self.__request.add_query_param('TTL', dns_ttl)
        # 发送请求,并获取返回参数或错误
        response = self.__client.do_action_with_exception(self.__request)
        return response

    
def main(cmd):
    '''程序执行'''
    if cmd == 2:
        # 判断返回本机当前公网IP
        if sys.argv[1]=="my_ip":
            DDNS.native_ip()
            print(DDNS.my_ip)
            return True
        # 判断是否JSON配置文件
        elif re.search('.json$',sys.argv[1]) :
            with open(sys.argv[1]) as file:
                jsonStr = json.loads(file.read())
            # 判断JSON配置是否正确
            if 'AccessKeyId' in jsonStr:
                key_id = jsonStr.get('AccessKeyId')
            else:
                print(cprint("Your JSON configuration is incorrect and lacks the key of AccessKeyId!",'31'))
            if 'AccessKeySecret' in jsonStr:
                key_secret = jsonStr.get('AccessKeySecret')
            else:
                print(cprint("Your JSON configuration is incorrect and lacks the key of AccessKeySecret!",'31'))
            if 'domain_name' in jsonStr:
                domain_name = jsonStr.get('domain_name')
            else:
                print(cprint("Your JSON configuration is incorrect and lacks the key of domain_name!",'31'))
            if 'type_key_word' in jsonStr:
                type_key_word = jsonStr.get('type_key_word')
            else:
                print(cprint("Your JSON configuration is incorrect and lacks the key of type_key_word!",'31'))
            if not key_id or not key_secret or not domain_name or not type_key_word:
                return False
            # 执行DDNS初始化
            myddns = DDNS(key_id,key_secret,domain_name,type_key_word)
    elif cmd == 4:
        key_id = sys.argv[1]
        key_secret = sys.argv[2]
        domain_name = sys.argv[3]
        # 默认@主机记录的DDNS初始化
        myddns = DDNS(key_id,key_secret,domain_name)
    elif cmd == 5:
        key_id = sys.argv[1]
        key_secret = sys.argv[2]
        domain_name = sys.argv[3]
        type_key_word = sys.argv[4]
        # 自定主机记录的DDNS初始化
        myddns = DDNS(key_id,key_secret,domain_name,type_key_word)
    else:
        print(cprint("The parameters are not enough to initialize the program",'31'))
        return False
    # 获取解析记录IP
    ip = myddns.parser_ip()
    # 获取本机当前公网IP
    my_ip = DDNS.native_ip()
    # 判断两个IP都成功获取后
    if ip and my_ip:
        print("%s IP: %s My IP: %s"%(domain_name,cprint(ip,"36","4"),cprint(my_ip,"36","4")))
        if ip == my_ip:
            print(cprint("Dynamic parsing results: Local IP and domain name parsing IP are the same!","32"))
        else:
            myddns.update_ip(my_ip)
            return True
    return False

if __name__ == '__main__' :
    cmd = len(sys.argv)
    try:
        if main(cmd):
            print(cprint("Successful change of parsing content!","32"))
        else:
            print(cprint("Failed to change parsing content!","31"))
    except (ServerException,ClientException) as reason:
        print(cprint("Failed to change parsing content! ",'31'))
        print(cprint("ERROR:",'33')+cprint(reason.get_error_msg(),"35"))
    except Exception as err:
        print(cprint("ERROR:",'33')+cprint(err,"35"))
    
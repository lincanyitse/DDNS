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
        # json转换
        response = json.JSONDecoder().decode(response)
        if 'DomainRecords' in response :
            # 获取解析记录
            response = response['DomainRecords']
            if 'Record' in response:
                response = response['Record']
                if len(response) == 0:
                    print('No '+self.rr+"."+self.domain+" parsing record")
                    self.__status=False
                    return
                elif len(response) == 1:
                    response = response[0]
            else:
                print(response)
                self.__status=False
                return
        elif 'Code' in response :
            self.__status=False
            print("Code:"+response['Code'])
            return
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
        import urllib2
        url = urllib2.urlopen(url)
        text = url.read()
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
    if(cmd == 2):
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
                print("Your JSON configuration is incorrect and lacks the key of AccessKeyId!")
            if 'AccessKeySecret' in jsonStr:
                key_secret = jsonStr.get('AccessKeySecret')
            else:
                print("Your JSON configuration is incorrect and lacks the key of AccessKeySecret!")
            if 'domain_name' in jsonStr:
                domain_name = jsonStr.get('domain_name')
            else:
                print("Your JSON configuration is incorrect and lacks the key of domain_name!")
            if 'type_key_word' in jsonStr:
                type_key_word = jsonStr.get('type_key_word')
            else:
                print("Your JSON configuration is incorrect and lacks the key of type_key_word!")
            if not key_id or not key_secret or not domain_name or not type_key_word:
                return False
            # 执行DDNS初始化
            myddns = DDNS(key_id,key_secret,domain_name,type_key_word)
    elif(cmd > 3):
        key_id = sys.argv[1]
        key_secret = sys.argv[2]
        domain_name = sys.argv[3]
        # 是否有主机记录
        if cmd > 4:
            type_key_word = sys.argv[4]
            # 自定主机记录的DDNS初始化
            myddns = DDNS(key_id,key_secret,domain_name,type_key_word)
        else:
            # 默认@主机记录的DDNS初始化
            myddns = DDNS(key_id,key_secret,domain_name)
    else:
        print("The parameters are not enough to initialize the program！")
        return False
    # 获取解析记录IP，并返回
    ip = myddns.parser_ip()
    my_ip = DDNS.native_ip()
    if ip and my_ip:
        print("%s IP:%s  My IP:%s"%(domain_name,ip,my_ip))
        if ip == my_ip:
            print("Dynamic parsing results: Local IP and domain name parsing IP are the same!")
        else:
            myddns.update_ip(my_ip)
            return True
    return False

if __name__ == '__main__' :
    cmd = len(sys.argv)
    try:
        if main(cmd):
            print("Successful change of parsing content!")
        else:
            print("Failed to change parsing content!")
    except (ServerException,ClientException) as reason:
        print("Failed to change parsing content! The reason is:"+reason.get_error_msg())
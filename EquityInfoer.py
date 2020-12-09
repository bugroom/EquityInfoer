#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author: xq17

import requests, pysnooper, re, time, json, sys
from lxml import etree
from urllib.parse import quote, unquote
from argparse import ArgumentParser, RawTextHelpFormatter

#### 采用类的写法方便后期导入调用

config = {
    "timeout": 5
}

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36",
    "Orgin": "https://dis.tianyancha.com",
    "Referer": "https://www.tianyancha.com/login?from=https%3A%2F%2Fwww.tianyancha.com%2Fsearch%3Fkey%3Dbaidu"
}

# 创建一个工具类
class Utils:
    def percent_to_int(self, string):
        try:
            if "%" in string:
                newint = float(string.strip("%"))
                return newint
        except:
            pass
        return 0.0

    def parse_cid(self, cid):
        if type(cid) == int:
            return cid
        if cid.startswith("http"):
            return int(re.search("company/(\d+)", cid).group(1))

#创建个公司类,默认都是public可以直接调用,orz,快忘了
class Company:
    def __init__(self, cid):
        # 公司名字
        self.name = ""
        # 公司手机
        self.tel = ""
        # 公司域名
        self.website = ""
        # 公司邮箱
        self.email = ""
        # 公司标识
        self.cid = self.parse_cid(cid)
        # 公司股权结构
        self.equity = ""

    def __str__(self):
        return f"{self.name}, {self.tel}, {self.website}, {self.email}, {self.cid}, {self.equity}"


    def toArray(self):
        return [self.name, self.tel, self.website, self.email, self.cid, self.equity]

    def toDict(self):
        return {
            "cid": self.cid,
            "name": self.name,
            "tel": self.tel,
            "website": self.website,
            "email": self.email,
            "equity": self.equity
        }

    def get_equity(self):
        return self.equity

    def set_equity(self, data):
        self.equity = data

    def parse_cid(self, cid):
        if type(cid) == int:
            return cid
        if cid.startswith("http"):
            return int(re.search("company/(\d+)", cid).group(1))


# 创建一个核心Hacker操作类
class Hacker:
    def __init__(self, query="", pages="", offset=0, cookies=""):
        self.query = quote(unquote(query))
        self.offset = offset
        self.pages = pages
        self.cookies = self.parse_cookie(cookies)
        self.preHTML = self.prepare()
        self.total = self.get_total()
        self.utils = Utils()

    def __str__(self):
        return f"{self.query}, {self.offset}, {self.pages}, {self.cookie}, {self.self.total}"

    def toDict(self):
        hacker_dict = {
            "query": self.query,
            "pages": self.pages,
            "cookie":self.cookie,
            "preHTML": self.preHTML,
            "total": self.total
        }
        return hacker_dict

    def prepare(self):
        if self.query:
            url = f"https://www.tianyancha.com/search/p1?key={self.query}"
            try:
                r = requests.get(url, headers=headers, cookies=self.cookies, timeout=config["timeout"], allow_redirects=False)
                # print(r.text)
                html = etree.HTML(r.text)
                return html
            except Exception as e:
                print("[-] Hacker>prepare Failed!")
        return ""

    def parse_cookie(self, cookies):
        if type(cookies) == str and cookies != "":
            cookies = { item.split('=')[0]:item.split('=')[1] for item in cookies.split("; ")}
            return cookies
        else:
            return {}

    def get_total(self):
        if self.query:
            page = self.preHTML.xpath('//*[@id="customize"]/div/@onclick')
            if page:
                try:
                    total = re.search(", (\d+?)\)", str(page[0])).group(1)
                    # print(total)
                    return int(total)
                except Exception as e:
                    print("[-] get_total Exception!")
            else:
                print("[-] get_total Failed!")
        return 0


    def search(self):
        if self.pages == None:
            if self.cookies:
                self.pages = self.total
            else:
                if self.total < 5:
                    self.pages = self.total
                else:
                    self.pages = 5
        if self.offset > self.pages:
            print("[-] search Failed! offset > page Error")
            exit(0)

        print(f"[+] total page:{self.total}")
        print(f"[+] Now searching {unquote(self.query)} keyword from {self.offset} to {self.pages}")
        company_ids = []
        for page in range(self.offset, self.pages+1):
            company_ids += self.get_id(page)

        print(f"[+] Success explored {len(company_ids)} relevant companies!")
        company_infos = [self.get_info(cid) for cid in company_ids]
        # 打印基础信息
        for obj in company_infos:
            # print(obj.name)
            print(obj.toArray())
            print(f"now retrying {obj.name}'s equity...")
            obj.set_equity(self.get_equity(obj.cid))
        return company_infos

    def get_id(self,page):
        url = f"https://www.tianyancha.com/search/p{page}?key={self.query}"
        try:
            res = requests.get(url, headers=headers, cookies=self.cookies, timeout=config["timeout"], allow_redirects=False)
            html = etree.HTML(res.text)
            hrefs = html.xpath('//div[@class="search-result-single  "]//a[contains(@class,"name")]/@href')
            # href_id = [re.search("company/(\d+)", url).group(1) for url in href]
            return list(set(hrefs))
        except Exception as e:
            print("[-] get_id Failed!")
            # exit(0)
        return []

    # @pysnooper.snoop()
    def get_info(self, cid):
        cid = self.utils.parse_cid(cid)
        url = f"https://www.tianyancha.com/company/{cid}"
        company = Company(cid)
        try:
            res =  requests.get(url, headers=headers, cookies=self.cookies, timeout=config["timeout"])
            # print(res.text)
            html = etree.HTML(res.text)
            name = html.xpath('//div[@class="content"]//h1[@class="name"]/text()')
            tel = html.xpath('//div[@class="detail "]//div[@class="f0"]/div[1]/span[2]/text()')
            email = html.xpath('//div[@class="detail "]//div[@class="f0"]/div[2]/span[2]/text()')
            website = html.xpath('//*[@id="company_web_top"]/div[2]/div[3]/div[3]/div[2]/div[1]/a/@href')
            company.website = "" if len(website) == 0 else website[0]
            company.email = "" if len(email) == 0 else email[0]
            company.tel = "" if len(tel) == 0 else tel[0]
            company.name = "" if len(name) == 0 else  name[0]
            # print(company.name)
        except Exception as e:
            print(f"[-] get_info Fail! \n{e}")
        return company


    # @pysnooper.snoop()
    def get_equity(self, cid="", ratio=0):
        # 获取cloud_token
        url = f"https://capi.tianyancha.com/cloud-equity-provider/v4/qq/name.json?id={cid}?random={int(time.time())}"
        self.cookies["CT_TYCID"] = str(cid)
        cloud_token = ""
        try:
            res = requests.get(url, headers=headers, cookies=self.cookies, timeout=config["timeout"], allow_redirects=False)
            # print(res.status_code)
            res_data = json.loads(res.text)
            # print(res_data)
            chars = res_data['data']['v']
            fnStr = "".join([chr(int(x)) for x in chars.split(',')])
            cloud_token = re.search("cloud_token=([a-z0-9A-Z]+)?;", fnStr).group(1)
        except Exception as e:
            print(f"[-] get_equity Failed! \n{e}")

        _url = f"https://capi.tianyancha.com/cloud-equity-provider/v4/equity/indexnode.json?id={cid}"
        self.cookies["cloud_token"] = cloud_token
        try:
            res_data = requests.get(_url, headers=headers, cookies=self.cookies, timeout=config["timeout"]).text
            json_data = json.loads(res_data)["data"]["investorList"]
            # print(type(json_data))
            json_res = []
            for k in json_data:
                # print(k["percent"])
                if self.utils.percent_to_int(k["percent"]) >= ratio:
                    print("name:" + k["name"] + "-equity:" + str(k["percent"]) + "-id:" + str(k["id"]))
                    json_res.append(k)
            # 分隔目标
            print("\n")
            return json_res
        except Exception as e:
            print(f"[-] get_equity Failed! \n{e}")


def check_args(args):
    if not args.cookies:
        print("[-] Missing your cookies, the frequent search may be detected!")

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("-key", type=str, help="search query")
    parser.add_argument("-t", dest="target" , type=int, help="company's identity,like 22822(baidu.com)")
    parser.add_argument("--percent",dest="percent", type=int, default=0, help='specify percent equity,degfault 0')
    parser.add_argument("--json", dest='json', type=str, help='output reult to json type')
    parser.add_argument("-m", "--mode", dest="mode", type=int, default=1, help='1: info 2.equity 3.all')
    parser.add_argument("-o", "--offset", dest='offset', type=int, default=0, help='page offset to start from')
    parser.add_argument("-p", "--pages", dest='pages', type=int, help='specify multiple pages')
    parser.add_argument("-c", "--cookies", dest='cookies', type=str, default={}, help='specify your cookies')
    if len(sys.argv) == 1:
        sys.argv.append("-h")
    args = parser.parse_args()
    check_args(args)
    return args

def start_work(args):
    print(args)
    ratio = args.percent
    cookies = args.cookies
    offset = args.offset
    pages = args.pages
    keyword = args.key
    json_file = args.json

    if not args.target and args.key:
        # 简单搜索查询
        hacker = Hacker(keyword, offset=offset, pages=pages, cookies=cookies)
        # 这个是返回的数据,如果想保存成其他格式可以在这里开始修改
        data = [ obj.toDict() for obj in hacker.search()]
        if json_file:
            json_data = json.dumps(data)
            with open(json_file, "w") as f:
                f.write(json_data)

    elif args.target:
        cid = args.target
        # 针对特定目标查询
        if args.mode == 1:
            # 只查询基本信息
            print(Hacker(cookies=cookies).get_info(cid=cid))
        elif args.mode == 2:
            Hacker(cookies=cookies).get_equity(cid=cid, ratio=ratio)
        elif args.mode == 3:
            print(Hacker(cookies=cookies).get_info(cid=cid))
            Hacker(cookies=cookies).get_equity(cid=cid, ratio=ratio)

def main():
    args = parse_args()
    start_work(args)
    # hacker = Hacker("百度", offset=0, pages=0, cookies=cookies)
    # hacker.search()
    # print(Hacker(cookies=cookies).get_equity(cid=22822, ratio=50))
    # print(Hacker(cookies=cookies).get_info(cid=22822))

if __name__ == '__main__':
    main()
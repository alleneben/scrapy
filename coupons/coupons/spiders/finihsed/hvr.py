        # coding=utf8
import scrapy
import re
import urllib.parse
from scrapy.spiders.crawl import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.link import Link
from bs4 import BeautifulSoup
from coupons.items import CouponsItem, allowed_shipping_list
import json
from coupons.filters import cleanString, filterBrands, getBrands
from datetime import datetime
import requests

def my_selenium_request_processor(request, response):
    request.meta['selenium'] = True
    return request

def process_item_href(value):
    m = re.search(r"(?=home_page\.aspx).*,\d{5,8}", value)
    if m:
        return 'https://www.hvr.co.il/' + m.group(0)

def process_item_id(value):
    m = re.search(r"\d{5,8}", value)
    if m:
        return 'https://www.hvr.co.il/home_page.aspx?page=mcc_item_new,'+ m.group(0)

def process_cat(value):
    m = re.search(r'(?=home_page\.aspx).*page=(.+)"}',value)
    if m:
        return 'https://www.hvr.co.il/' + m.group(0)[:-2]

def process_lst(value):
    n = re.search(r'(?=show_list).*\d{5,7}"}', value)
    o = re.search(r'(?=Search\.aspx).*"}',value)
    if n:
        return 'https://www.hvr.co.il/' + n.group(0)[:-2]
    if o:
        return 'https://www.hvr.co.il/' + o.group(0)[:-2]

class HvrSpider(CrawlSpider):
    name = 'hvr'
    undetectable = True
    elementId = 'wrap'
    wait = True
    allowed_domains = ['hvr.co.il']
    start_urls = []
    signin_url = 'https://hvr.co.il/signin.aspx'
    usrEId,username = 'tz','052046133'
    pwdEId,password = 'password','5167722'
    brands = getBrands()
    headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'}
    rules = [
        Rule(LinkExtractor(allow=(),tags=('div','a','area','button'),attrs=('data-item_id',),process_value=process_item_id),callback="parse_item",follow=False),
        Rule(LinkExtractor(allow=(),tags=('div','a','area','button'),attrs=('href',),process_value=process_item_href),callback="parse_item",follow=False),
        Rule(LinkExtractor(allow=(),tags=('div','a','area','button'),attrs=('href',),process_value=process_lst),callback="parse_lst",follow=True),
        Rule(LinkExtractor(allow=(),tags=('div','a','area','button'),attrs=('href',),process_value=process_cat),follow=True)
    ]
    

    def start_requests(self):
        yield scrapy.Request(self.signin_url, callback=self.after_login,meta={"selenium":True,"login":True,"elementId":"tz"})

    def after_login(self,response):
        result = [re.search(r"(.+?)\.json",i).group(0) for i in response.css("div::attr(title)").extract() if re.search(r"(.+?)\.json",i)]
        result2 = [re.search(r"(.+?)\.json",i).group(0) for i in response.css("div::attr(data-json)").extract() if re.search(r"(.+?)\.json",i)]
        for uri in result+result2:
            uri = re.search(r"(?<=\\).*",uri).group(0) if re.search(r"(?<=\\).*",uri) else uri
            r = requests.get('https://www.hvr.co.il/ajax/'+uri,headers=self.headers)
            m = re.findall(r"(page|url)':\s?'(.+?)'",str(r.json())) if r.status_code == 200 else None
            if m:
                for t,s in m:
                    n = re.search(r"(?=home_page\.aspx).*", s)
                    if t == 'page':
                        url = 'https://www.hvr.co.il/home_page.aspx?page=' + s
                    elif t == 'url' and n:
                        url = 'https://www.hvr.co.il/'+n.group(0)
                    self.start_urls.append(url)
        self.start_urls.append(response.url)
        return super(HvrSpider, self).start_requests()


    def parse_lst(self, response):
        template_links = re.findall(r'template_link:\s?"(.+)\d{5,8}"',str(response.body))
        for uri in template_links:
            yield scrapy.Request(urllib.parse.urljoin('https://www.hvr.co.il/',uri), callback=self.parse_item)

    def parse_item(self, response):
        print(response.url)

    
    parse_start_url = parse_item
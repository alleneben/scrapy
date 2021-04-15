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

def my_selenium_request_processor(request, response):
    request.meta['selenium'] = True
    return request

def categoryHandler(value):
    m = re.search(r'search\.aspx\?searchword=(.+)', value)
    if m:
        return "https://www.tov.org.il/site/search/?w"+ re.search(r"=(.+)",m.group(0)).group(0)
    n = re.search(r"\/pg\/(.+)",value)
    if n:
        return "https://www.tov.org.il/site" + n.group(0)
    o = re.search(r"\/search\/\?w=(.+)",value)
    if o:
        return "https://www.tov.org.il/site"+o.group(0)


def itemHandler(value):
    m = re.search(r"javascript:(.+?)\(\s?'(.+?),\d{1,10}(.+?)(\d{1,10}?)'", value)
    if m:
        if 'page:' in m.group(0):
            return m.group(0).replace("page:","https://www.tov.org.il/site/pg/")
        return "https://www.tov.org.il/site/pg/" + re.search(r"'(.+?),\d{1,10}(.+?)(\d{1,10}?)'", m.group(0)).group(0)[1:-1]
    n = re.search(r'page:(.+?),\d{1,10}', value)
    if n:
        return n.group(0).replace("page:","https://www.tov.org.il/site/pg/")
    o = re.search(r"\/pg/(.+?),\d{1,10}", value)
    if o:
        return "https://www.tov.org.il/site"+o.group(0)
    

class TovSpider(CrawlSpider):
    name = 'tov'
    undetectable = True
    wait = False
    allowed_domains = ['tov.org.il']
    start_urls = []
    signin_url = 'https://www.tov.org.il/signin.aspx'
    usrEId,username = 'tz','025190273'
    pwdEId,password = 'password','2535271'
    brands = getBrands()
    rules = [
        Rule(LinkExtractor(allow=(),tags=('div','a','area','button'),attrs=('data-href','href','onclick'),process_value=itemHandler),callback='parse_item',process_request=my_selenium_request_processor,follow=False),
        Rule(LinkExtractor(allow=(),tags=('div','a','area','button'),attrs=('data-href','href','onclick'),process_value=categoryHandler),process_request=my_selenium_request_processor,follow=True)
    ]

    def start_requests(self):
        yield scrapy.Request(self.signin_url, callback=self.after_login,meta={"selenium":True,"login":True})

    def after_login(self,response):
        self.start_urls.append(response.url)
        return super(TovSpider, self).start_requests()
    
    def parse_item(self,response):
        with open('log.txt', 'a') as f:
            f.write(response.url+'\n')
        
    parse_start_url = parse_item
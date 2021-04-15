    # coding=utf8
import scrapy
import re
import urllib.parse
from scrapy.spiders.crawl import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from bs4 import BeautifulSoup
from coupons.items import CouponsItem, allowed_shipping_list
import json
from coupons.filters import cleanString, filterBrands, getBrands
from datetime import datetime

def my_selenium_request_processor(request, response):
    request.meta['selenium'] = True
    return request

def process_catOrderOnclick(value):
    m = re.search(
        r"\w+\.aspx\?CatOrder\s?=\s?\d{1,10}(.+?)';",
        value)
    if m:
        return urllib.parse.urljoin(
            'https://www.behatsdaa.org.il/',m.group(0))[:-2]


def process_catNumberOnclick(value):
    m = re.search(
        r"Business\.aspx\?catnumber=\d{1,10}',\d\)",
        value)
    if m:
        return urllib.parse.urljoin(
            'https://www.behatsdaa.org.il/',
            re.search(r'Business\.aspx\?catnumber=\d{1,10}', value).group(0))

def process_dealsClick(value):
    m = re.search(
        r"deals\.php\?act=click&id=\d{1,10}",
        value)
    n = re.search(
        r"deals\.php\?filter=\d{1,10}",
        value)
    if m:
        return urllib.parse.urljoin(
            'https://www.hotels.wisegroup.co.il/carform/',m.group(0))
    elif n:
        return urllib.parse.urljoin(
            'https://www.hotels.wisegroup.co.il/carform/',n.group(0))

class BehatsdaSpider(CrawlSpider):
    name = 'behatsda'
    undetectable = True
    wait = True
    elementId = 'aspnetForm'
    allowed_domains = ['behatsdaa.org.il']
    login_url = 'https://behatsdaa.org.il/'
    start_urls = ['https://www.behatsdaa.org.il/HomePage.aspx']
    usrEId,username = 'TextBoxPersonalNumber','0000'
    pwdEId,password = 'TextBoxCardNumber','0000'
    brands = getBrands()

    rules = [
        Rule(LinkExtractor(allow=(),tags=('a','area','button','div',),attrs=('onclick','href', ),process_value=process_dealsClick),
             follow=False,callback='parse_item'),
        Rule(LinkExtractor(allow=(),tags=('a','area','button','div',),attrs=('onclick','href', ),process_value=process_catNumberOnclick),
             follow=False,callback='parse_item'),
        Rule(
            LinkExtractor(allow=(),tags=('a','area','button','div',),
                          attrs=('onclick','href', ),
                          process_value=process_catOrderOnclick),
            process_request=my_selenium_request_processor,follow=True),
        Rule(LinkExtractor(allow=("deals\.php\?filter")),process_request=my_selenium_request_processor,follow=True),
    ]

    def __init__(self, *args, **kwargs):
        super(BehatsdaSpider, self).__init__(*args, **kwargs)
        self.cycleid = kwargs.get('cycleid', '')

    def start_requests(self):
        yield scrapy.Request(self.login_url, callback=self.after_login,meta={"selenium":True,"login":True,"elementId":"TextBoxPersonalNumber"})

    def after_login(self, response):
        return super(BehatsdaSpider, self).start_requests()

    def parse_item(self, response):
        isValid = response.css('#ctl00_ContentPlaceHolder2_LabelCategoryDescription').extract_first() is not None
        if isValid:
            title=response.css('#ctl00_ContentPlaceHolder2_LabelCategoryName::text').get()
            description = response.css('#ctl00_ContentPlaceHolder2_LabelCategoryDescription::text').get() + cleanString(response.css('#ctl00_ContentPlaceHolder2_LabelCategoryText').extract())
            yield CouponsItem(Title=title,
                          supplier='998',
                          brand=filterBrands(cleanString(response.css('#ctl00_ContentPlaceHolder2_LabelCategoryName::text').get()),self.brands),
                          JoinUrl=response.url,
                          Description=description,
                          ScrapeDate = datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                          DoorToDoorShipping= any(ext in (description+title) for ext in allowed_shipping_list),
                          cyclerun=self.cycleid )
    
    parse_start_url = parse_item
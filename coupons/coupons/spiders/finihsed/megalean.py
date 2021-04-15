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

def process_item(value):
    m = re.search(r"javascript:gotoListItem\('page:(.+?)',", value)
    if m:
        return 'https://www.megalean.co.il/site/pg/'+ (re.search(r"page:(.+?)'", value).group(0)).replace('page:', '')[:-1]

def process_divLinks(value):
    m = re.search(r"url:search.aspx\?searchWord=(.+?)&", value)
    if m:
        return 'https://www.megalean.co.il/site/search/?w'+ (re.search(r'=(.+?)&', value).group(0))[:-1]

class MegaleanSpider(CrawlSpider):
    name = 'megalean'
    undetectable = False
    wait = False
    allowed_domains = ['megalean.co.il']
    start_urls = ['https://www.megalean.co.il/site/pg/home']
    brands = getBrands()
    rules = [
        Rule(
            LinkExtractor(allow=(),
                          attrs=('onclick', ),
                          process_value=process_item),
            callback='parse',follow=True),
        Rule(
            LinkExtractor(allow=(),
                          tags=('div', ),
                          attrs=('data-href', ),
                          process_value=process_divLinks),process_request=my_selenium_request_processor,follow=True),

        Rule(LinkExtractor(allow=('/search/', '/cat_')),process_request=my_selenium_request_processor,
             follow=True),
    ]

    def __init__(self, *args, **kwargs):
        super(MegaleanSpider, self).__init__(*args, **kwargs)
        self.cycleid = kwargs.get('cycleid', '')

    def parse(self, response):
        description =cleanString(response.css('ul.product-info li:nth-child(6)').extract())
        title=cleanString(response.css("#ptitle::text").get())
        yield CouponsItem(Title=title,
                          supplier='994', 
                          brand=filterBrands(cleanString(response.css("#ptitle::text").get()),self.brands),
                          JoinUrl=response.url,
                          Description=description,
                          ScrapeDate = datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                          DoorToDoorShipping= any(ext in (description+title) for ext in allowed_shipping_list),
                          cyclerun=self.cycleid )
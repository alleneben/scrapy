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
from difflib import SequenceMatcher

def my_selenium_request_processor(request, response):
    request.meta['selenium'] = True
    return request

def itemHandler(value):
    m = re.search(r"product\.php\?pid=(.+)", value)
    if m:
        result = 'https://www.diners-store.co.il/'+ m.group(0)
        return result

def categoryHandler(value):
    m = re.search(r"productlist\.php\?cid=(.+)", value)
    if m:
        result = 'https://www.diners-store.co.il/'+ m.group(0)
        return result

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

class DinersSpider(CrawlSpider):
    name = 'diners'
    undetectable = True
    wait = True
    elementId = 'cal-shop-brand'
    allowed_domains = ['diners-store.co.il']
    start_urls = ['https://www.diners-store.co.il/']
    brands = getBrands()
    integrator = '-כותרת משנה' 
    rules = [
        Rule(LinkExtractor(allow=(),process_value=itemHandler),callback='parse',process_request=my_selenium_request_processor,follow=False),
        Rule(LinkExtractor(allow=(),process_value=categoryHandler),process_request=my_selenium_request_processor,follow=True)
    ]

    def __init__(self, *args, **kwargs):
        super(DinersSpider, self).__init__(*args, **kwargs)
        self.cycleid = kwargs.get('cycleid', '')

    def parse(self, response):
        description=cleanString(response.css("div#full-description-text").extract())
        if not description:
            description = cleanString(response.css("div.banner-club-big-text-box").extract())
        greenbox = cleanString(response.css("h1.productTitle").extract()) + cleanString(response.css("div.productSubTitle").extract()) 
        big_redbox = cleanString(response.css("td.product-list-checkboxes").extract())
        if similar(greenbox, big_redbox) > 0.9:
            title = greenbox
        else:
            low_price = re.search(r"'PriceDiscount':\s'\d{1,}'",str(response.body)).group(0) if  re.search(r"'PriceDiscount':\s'\d{1,}'",str(response.body)) else ''
            title = greenbox + self.integrator + big_redbox + low_price.replace("'PriceDiscount':",'')
        yield CouponsItem(Title = title,
                            supplier='16', 
                            brand=filterBrands(cleanString(response.css("h1.productTitle").extract()),self.brands),
                            JoinUrl=response.url,
                            Description=description,
                            ScrapeDate = datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                            DoorToDoorShipping= any(ext in (description+title) for ext in allowed_shipping_list),
                            cyclerun=self.cycleid )
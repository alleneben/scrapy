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
    request.meta['selenium'] = False
    return request

def categoryHandler(value):
    m = re.search(r"partialPagesHandler\.carouselCategoryItemClickHandler((.+?),'\/link\/(.+?)\.aspx')", value)
    if m:
        return urllib.parse.urljoin('https://benefits.isracard.co.il/', re.search(r"\/link\/(.+?)\.aspx", value).group(0))

def mainHandler(value):
    m = re.search(r"partialPagesHandler\.mainBenefitClick\('(.+?)','(.+?)'\)",value)
    if m:
        print(m)
        path = re.search(r",'(.+?)'",value).group(0)[2 : : ][:-1]
        print(path)
        if re.search(r"^\/",path):
            uri =  urllib.parse.urljoin('https://benefits.isracard.co.il/', re.search(r"\/link\/(.+?)\.aspx", value).group(0))
        else:
            uri = path
        print(uri)
        return uri

def itemHandler(value):
    m = re.search(r"benefitPageHandler\.saveBenefitInfo\('\/link\/(.+?)\.aspx'",value)
    if m:
        return urllib.parse.urljoin("https://benefits.isracard.co.il/", re.search(r"\/link\/(.+?)\.aspx",value).group(0))



class IsracardSpider(CrawlSpider):
    name = 'isracard'
    undetectable = False
    wait = False
    allowed_domains = ['benefits.isracard.co.il']
    start_urls = ['https://benefits.isracard.co.il/']
    brands = getBrands()
    rules = [
        Rule(LinkExtractor(allow=(),tags=('div','a','area','button',),
                          attrs=('onclick', ),process_value=itemHandler),
             callback='parse',process_request=my_selenium_request_processor,follow=False),
        Rule(LinkExtractor(allow=(),tags=('div','a','area','button',),
                          attrs=('onclick', ),process_value=categoryHandler),process_request=my_selenium_request_processor,follow=True),
        Rule(LinkExtractor(allow=(),tags=('div','a','area','button',),
                          attrs=('onclick', ),process_value=mainHandler),callback='parse',process_request=my_selenium_request_processor,follow=True)
    ]

    def __init__(self, *args, **kwargs):
        super(IsracardSpider, self).__init__(*args, **kwargs)
        self.cycleid = kwargs.get('cycleid', '')   

    def parse(self, response):
        isValid = response.css('.benefit-details-txt').extract_first() is not None
        if isValid:
            description=cleanString(response.css("div.benefit-details-txt").extract())
            title=cleanString(response.css("div.benefit-info h1::text").extract_first())
            yield CouponsItem(Title=title,
                            supplier='996', 
                            brand=filterBrands(cleanString(response.css("div.benefit-info h1::text").extract_first()),self.brands),
                            JoinUrl=response.url,
                            Description=description,
                            ScrapeDate = datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                            DoorToDoorShipping= any(ext in (description+title) for ext in allowed_shipping_list), 
                            cyclerun=self.cycleid )


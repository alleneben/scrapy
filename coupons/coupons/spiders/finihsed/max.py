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
    
    
class MaxSpider(CrawlSpider):
    name = 'max'
    undetectable = False
    wait = False
    allowed_domains = ['max.co.il']
    start_urls = ['https://www.max.co.il/he-il/Benefits/Pages/SummerBenefits.aspx']
    home = 'https://www.max.co.il/he-il/Benefits/Pages/SummerBenefits.aspx'
    brands = getBrands()
    starter = True
    rules = [
        Rule(LinkExtractor(allow=('/anonymous/benefits')),
             callback='parse',process_request=my_selenium_request_processor,follow=True),
        Rule(LinkExtractor(allow=('/he-il/Benefits/(.+?)/Pages/(.+?)\.aspx')),callback='parse',process_request=my_selenium_request_processor,follow=True)
    ]

    def __init__(self, *args, **kwargs):
        super(MaxSpider, self).__init__(*args, **kwargs)
        self.cycleid = kwargs.get('cycleid', '')

    def parse(self, response):
        if self.starter:
            yield scrapy.Request(self.home,meta={'selenium':False}, callback=self.anonymous_scrape)
        self.starter = False

        isValid = response.css('.benefitInfo_content').extract_first() is not None
        if isValid:
            if 'online.max.co.il' in response.url:
                description=cleanString(response.css("div.richHtml p").extract())
            else:
                description=cleanString(response.css("#ctl00_PlaceHolderMain_ctl00_divInitializeWrapperClass p").extract())
            title=cleanString(response.css("div.benefitInfo_content h2::text").extract_first())
            yield CouponsItem(Title=title,
                          supplier= '100' if (re.search(r'/Biz/Pages/',response.url)) else '995' if (re.search(r'/BeyahadBishvilha/Pages/',response.url)) else '995', 
                          brand=filterBrands(cleanString(response.css("div.benefitInfo_content h1::text").extract_first()),self.brands),
                          JoinUrl=response.url,
                          Description=description,
                          ScrapeDate = datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                          DoorToDoorShipping= any(ext in (description+title) for ext in allowed_shipping_list),
                          cyclerun=self.cycleid )
    
    def anonymous_scrape(self, response):
        match = re.findall(r"https://online\.max\.co\.il/anonymous/benefits/(.+?)&Catnumber=(\d{1,10})", response.body.decode("utf-8"))
        for i in match:
            yield scrapy.Request('https://online.max.co.il/anonymous/benefits/{}&Catnumber={}'.format(*i),callback=self.parse)

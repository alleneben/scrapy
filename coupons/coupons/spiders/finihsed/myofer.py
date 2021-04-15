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


class MyoferSpider(scrapy.Spider):
    name = 'myofer'
    undetectable = False
    wait = False
    allowed_domains = ['myofer.co.il']
    start_urls = ['http://myofer.co.il/']
    token = ''
    brands = getBrands()
    BASE_URL = 'https://api-mobile.myofer.co.il/v2/sales'

    def __init__(self, *args, **kwargs):
        super(MyoferSpider, self).__init__(*args, **kwargs)
        self.cycleid = kwargs.get('cycleid', '')

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse_malls,meta={'selenium':True,'myoferToken':True})
    
    def parse_malls(self, response):
        self.token = next(item for item in response.meta["cookieJar"] if item["name"] == "token").get('value')
        result = [re.search(r"/(.+)/category/all-benefits",i).group(0) for i in response.css("a.mall-name-expanded::attr(href)").extract() if re.search(r"/(.+)/category/all-benefits",i)]
        for uri in result:
            yield scrapy.Request(f'https://myofer.co.il{uri}',callback=self.parse_mallId)

    def parse_mallId(self, response):
        headers = {'Accept': 'Accept: application/json','Authorization':f'Bearer {self.token}'}
        idString = re.search(r"mallId=\d+&",str(response.body)).group(0) if re.search(r"mallId=\d+&",str(response.body)) else None
        if idString:
            d = re.search(r"\d+",idString).group(0) if re.search(r"\d+",idString) else None
            if d:
                mallname = re.search(r"/(.+)/",re.search(r"\.il/(.+)/c",str(response.url)).group(0)).group(0) if re.search(r"\.il/(.+)/c",str(response.url)) else None
                if mallname:
                    params = {
                            'mallId': d,
                            'limit': 100000
                        }
                    url = f'{self.BASE_URL}?{urllib.parse.urlencode(params)}'
                    yield scrapy.Request(url, callback=self.parse, headers=headers, meta={'mallName':mallname})
        
    def parse(self, response):
        result = json.loads(response.body)
        n = result.get('meta').get('totalitems')
        if n > 0:
            data = result.get('data')
            for r in data:
                for sale in r.get('attributes').get('sales'):
                    description = cleanString(sale['description'])
                    brandName = filterBrands(cleanString(sale['brand']['title']),self.brands)
                    title=cleanString(sale['title'])
                    title=f'{brandName} {title}'
                    yield CouponsItem(Title=title,
                                    supplier='2',
                                    brand= brandName,
                                    JoinUrl= f"https://myofer.co.il{response.meta['mallName']}brands/{sale['brand']['seoname']}/{sale['id']}",
                                    Description=description,
                                    ScrapeDate = datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                                    DoorToDoorShipping= any(ext in (description+title) for ext in allowed_shipping_list),
                                    cyclerun=self.cycleid )

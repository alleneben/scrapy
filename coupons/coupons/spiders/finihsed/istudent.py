
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

class IstudentSpider(scrapy.Spider):
    name = 'istudent'
    undetectable = False
    wait = False
    allowed_domains = ['istudent.co.il']
    start_urls = ['http://istudent.co.il/']
    brands = getBrands()

    def __init__(self, *args, **kwargs):
        super(IstudentSpider, self).__init__(*args, **kwargs)
        self.cycleid = kwargs.get('cycleid', '')

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse_brands,meta={'selenium':True})
    
    def parse_brands(self,response):
        result = [re.search(r"hotSaleByBrand\.php\?brandId=(.+)&name=(.+)",i).group(0) for i in response.css("a.to-sales::attr(href)").extract()]
        for uri in result:
            yield scrapy.Request(urllib.parse.urljoin('https://istudent.co.il/',uri), callback=self.parse_products,meta={'selenium':True})

    def parse_products(self, response):
        brandname = re.search(r"&name=(.+)",response.url).group(0)[6:]
        result = [re.search(r"saleInner\.php\?saleId=(.+)",i).group(0) for i in response.css("a.to-sale::attr(href)").extract() if re.search(r"saleInner\.php\?saleId=(.+)",i)]
        for uri in result:
            yield scrapy.Request(urllib.parse.urljoin('https://istudent.co.il/',uri), callback=self.parse_item,meta={'selenium':True,'brandname':brandname})

    def parse_item(self, response):
        description=cleanString(response.css("div.desc").extract())
        title=cleanString(response.css("div.info-box h1.title").extract_first())
        yield CouponsItem(Title=title,
                            supplier='1', 
                            brand= filterBrands(urllib.parse.unquote(response.meta["brandname"]),self.brands),
                            JoinUrl=response.url,
                            Description=description,
                            ScrapeDate = datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                            DoorToDoorShipping= any(ext in (description+title) for ext in allowed_shipping_list),
                            cyclerun=self.cycleid )
    # coding=utf8
import scrapy
import re
import urllib.parse
from scrapy.spiders.crawl import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from bs4 import BeautifulSoup
from coupons.items import CouponsItem, allowed_shipping_list
import json
from coupons.filters import cleanString,filterBrands,getBrands
from datetime import datetime
import requests
from scrapy.http import HtmlResponse

class OgenSpider(CrawlSpider):
    name = 'ogen'
    undetectable = False
    wait = False
    allowed_domains = ['ogen.org.il']
    start_urls = ['https://ogen.org.il/']
    brands = getBrands()
    # ajax_url = 'https://ogen.org.il/wp-admin/admin-ajax.php'
    # payload = "------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name=\"action\"\r\n\r\nmatat_filter\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name=\"data\"\r\n\r\nminPrice=0&maxPrice=1000\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name=\"security\"\r\n\r\ncb03a93ccd\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--"
    # headers = {
    # 'content-type': "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
    # 'cache-control': "no-cache",
    # 'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'
    # }
    rules = [
        Rule(LinkExtractor(allow=('/product-category/')),follow=True,),

        Rule(LinkExtractor(allow=('/product/')),
             callback='parse')
    ]

    # def start_requests(self):
    #     yield scrapy.Request(self.start_urls[0], callback=self.ajax_parse) 

    # def ajax_parse(self, response):
    #     result = requests.request("POST", self.ajax_url, data=self.payload, headers=self.headers)
    #     response = HtmlResponse(self.ajax_url, body=result.text, encoding='utf-8')
    #     products = [i for i in response.css("a::attr(href)").extract() if re.search(r"/product/",i)]
    #     for links in products:
    #         yield scrapy.Request(links, callback=self.parse)
    #     return super(OgenSpider, self).start_requests()

    def __init__(self, *args, **kwargs):
        super(OgenSpider, self).__init__(*args, **kwargs)
        self.cycleid = kwargs.get('cycleid', '')

    def parse(self, response):
        description =cleanString(response.css("div.short-info p::text").getall())
        title=cleanString(response.css("h2.product-name::text").get()) + cleanString(response.css("div.price").extract())
        yield CouponsItem(Title=title,
                          supplier='992', 
                          brand=filterBrands(cleanString(response.css("h2.product-name::text").get()),self.brands),
                          JoinUrl=response.url,
                          Description=description,
                          ScrapeDate = datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                          DoorToDoorShipping= any(ext in (description+title) for ext in allowed_shipping_list),
                          cyclerun=self.cycleid )
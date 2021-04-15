    # coding=utf8
import scrapy
from coupons.items import CouponsItem, allowed_shipping_list
from bs4 import BeautifulSoup
import json
from coupons.filters import cleanString,filterBrands,getBrands
from datetime import datetime

class UniqclubSpider(scrapy.Spider):
    name = 'uniqClub'
    undetectable = False
    wait = False
    allowed_domains = ['uniq-club.co.il']
    start_urls = ['http://uniq-club.co.il/']
    apiBase = 'https://www.uniq-club.co.il/discounts/ajax/{}'
    linkBase = 'https://www.uniq-club.co.il/discounts#{}'
    brands = getBrands()
    
    def __init__(self, *args, **kwargs):
        super(UniqclubSpider, self).__init__(*args, **kwargs)
        self.cycleid = kwargs.get('cycleid', '')

    def parse(self, response):
        for d in range(0, 1000):
            uri = self.apiBase.format(d)
            yield scrapy.Request(uri,
                                 callback=self.parse_coupon,
                                 method='POST', meta={'d_number':d})

    def parse_coupon(self, response):
        isValid = response.css('i.cafe_logo').extract_first() is not None
        if isValid:
            description = cleanString(response.css('span.small_text').extract())
            title=cleanString(response.css('div.richtext_div').extract_first())
            yield CouponsItem(Title=title,
                            supplier='990',
                            brand=filterBrands(cleanString(response.css('div.d_section > h1::text').get())[:-3],self.brands),
                            JoinUrl=self.linkBase.format(response.meta['d_number']),
                            Description=description,
                            ScrapeDate = datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                            DoorToDoorShipping= any(ext in (description+title) for ext in allowed_shipping_list),
                            cyclerun=self.cycleid )
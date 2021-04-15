    # coding=utf8
import scrapy
from coupons.items import CouponsItem, allowed_shipping_list
from bs4 import BeautifulSoup
import json
from coupons.filters import cleanString,filterBrands,getBrands
from datetime import datetime
import re
import random
import math


def convertToNumber(s):
    return int.from_bytes(s.encode(), 'little')

def convertFromNumber(n):
    return n.to_bytes(math.ceil(n.bit_length() / 8), 'little').decode()

class DreamcardSpider(scrapy.Spider):
    name = 'dreamcard'
    undetectable = False
    wait = False
    allowed_domains = ['dreamcard.co.il']
    start_urls = ['https://www.dreamcard.co.il/special-offers']
    brands = getBrands()

    
    def __init__(self, *args, **kwargs):
        super(DreamcardSpider, self).__init__(*args, **kwargs)
        self.cycleid = kwargs.get('cycleid', '')

    def parse(self, response):
        lst = response.css("nav.content ul.center li a").extract()
        for a in lst:
            soup = BeautifulSoup(a, 'lxml')
            input_tag = soup.find("a")
            href = input_tag.get('href')
            title = input_tag.get('title')
            img_tag = soup.find("img")
            desc = img_tag.get('src')
            m = re.search(r'https:\/\/www\.dreamcard\.co\.il\/special-offers\/',href)
            if m:
                yield CouponsItem(Title=cleanString(title),
                                supplier='101',
                                brand=filterBrands(title,self.brands),
                                JoinUrl=href+"&&"+str(convertToNumber(title)),
                                Description=desc,
                                ScrapeDate = datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                                DoorToDoorShipping= any(ext in (title) for ext in allowed_shipping_list),
                                cyclerun=self.cycleid )
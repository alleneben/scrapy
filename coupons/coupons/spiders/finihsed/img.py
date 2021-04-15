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


def process_nextPageOnclick(value):
    m = re.search(r"(.+?)\.aspx\?(.+?)", value)
    if m:
        return urllib.parse.urljoin("https://www.igm.org.il/", m.group(0))


def process_couponOnclick(value):
    m = re.search(r"home_page\.aspx\?page=(.+?),\d{1,10}", value)
    if m:
        return urllib.parse.urljoin("https://www.igm.org.il/", m.group(0))

def process_couponFollow(value):
    m = re.search(r"home_page\.aspx\?page=(.+?)", value)
    if m:
        return urllib.parse.urljoin("https://www.igm.org.il/", m.group(0))

def process_item(value):
    m = re.search(r"javascript:gt1\(\s?'(.+?),\d{1,10}',", value)
    if m:
        return 'https://www.igm.org.il/home_page.aspx?page='+ (re.search(r"'(.+?),\d{1,10}'", value).group(0)).replace("'","")[:-1]

def process_searchOnclick(value):
    m = re.search(r'search\.aspx\?searchWord=(.+?)"',value)
    if m:
        return urllib.parse.urljoin("https://www.igm.org.il/", m.group(0)[:-1])


class ImgSpider(CrawlSpider):
    name = 'teachersUnion'
    undetectable = False
    wait = False
    allowed_domains = ['igm.org.il']
    encoding = 'utf-8'
    start_urls = ['https://www.igm.org.il/home_page.aspx?page=megalean_home/']
    base_url = "https://www.igm.org.il/"
    brands = getBrands()
    rules = [           
        Rule(LinkExtractor(allow=(),
                           attrs=(
                               'onclick',
                               'href',
                           ),
                           process_value=process_item),callback="parse_item"),
        Rule(LinkExtractor(allow=(),
                           attrs=(
                               'onclick',
                               'href',
                           ),
                           process_value=process_couponOnclick),callback="parse_item"),
        Rule(LinkExtractor(allow=("search"),
                           attrs=(
                               'onclick',
                               'href',
                           ),tags=("div","a","area", ),
                           process_value=process_searchOnclick),
             follow=True),
        Rule(LinkExtractor(allow=(),
                           attrs=(
                               'onclick',
                               'href',
                           ),
                           process_value=process_couponFollow),
             follow=True),
        Rule(LinkExtractor(allow=(),
                           attrs=(
                               'onclick',
                               'href',
                           ),
                           process_value=process_nextPageOnclick),
             follow=True)
    ]

    def __init__(self, *args, **kwargs):
        super(ImgSpider, self).__init__(*args, **kwargs)
        self.cycleid = kwargs.get('cycleid', '')

    def start_requests(self):
        yield scrapy.Request('https://www.igm.org.il/home_page.aspx?page=igm_PNBS', callback=self.get_json,meta={'selenium':True})
    
    def get_json(self,response):
        result = [re.search(r"(.+?)\.json",i).group(0) for i in response.css("div.sidebarObject::attr(title)").extract()]
        for uri in result:
            yield scrapy.Request('https://www.igm.org.il/ajax/'+uri, callback=self.parse_json)

    def parse_json(self, response):
        jsonStr = str(response.body, self.encoding)
        m = re.findall(r'"url":"(.+?)\.aspx\?(.+?)"', jsonStr)
        for uri in m:
            self.start_urls.append(
                urllib.parse.urljoin(self.base_url, '.aspx?'.join(uri)))
        return super(ImgSpider, self).start_requests()

    def parse_item(self, response):
        isValid = response.css('div.text_more_info_white.benefits').extract_first() is not None
        validCoupon = cleanString(response.css("h2.page-title::text").extract_first())
        if isValid and validCoupon and (validCoupon != ""):
            description=cleanString(response.css("div#main").extract())
            title=cleanString(response.css("h2.page-title::text").extract_first())
            yield CouponsItem(Title=title,
                            supplier='997', 
                            brand=filterBrands(cleanString(response.css("h2.page-title::text").extract_first()),self.brands),
                            JoinUrl=response.url,
                            Description=description,
                            ScrapeDate = datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                            DoorToDoorShipping= any(ext in (description+title) for ext in allowed_shipping_list),
                            cyclerun=self.cycleid )

    parse_start_url = parse_item
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
import requests


def my_selenium_request_processor(request, response):
    request.meta['selenium'] = True
    return request


class YoursSpider(CrawlSpider):
    name = 'yours'
    undetectable = True
    wait = True
    elementId = 'accesability_container'
    allowed_domains = ['yours.co.il']
    apiBase = 'https://data.dolcemaster.co.il'
    start_urls = ['http://www.yours.co.il/']
    siteUuid = '3D6E6054-ACF9-44E7-8ED7-0ADF86732BFF'
    linkBase = 'http://yours.co.il/benefits/'
    getBenefitDetails = urllib.parse.urljoin(
        apiBase, f'api/v5_1/public/benefits_details')
    headers = {'Accept': 'Accept: application/json'}
    brands = getBrands()
    
    rules = [
        Rule(LinkExtractor(allow=('/category/')),process_request=my_selenium_request_processor,follow=True),
        Rule(LinkExtractor(allow=('/benefits/')),callback='parse',process_request=my_selenium_request_processor,follow=False)
    ]

    def __init__(self, *args, **kwargs):
        super(YoursSpider, self).__init__(*args, **kwargs)
        self.cycleid = kwargs.get('cycleid', '')

    def start_requests(self):
        yield scrapy.Request(self.start_urls[0], callback=self.start_crawl_requests) 
    
    def start_crawl_requests(self,response):
        return super(YoursSpider, self).start_requests()


    def parse(self, response):
        m = re.search(r'https://www\.yours\.co\.il/benefits/(.+)/',response.url)
        if m:
            benefit_id = m.group(1)
            formdata={'club_id': f'{self.siteUuid}','benefits_id': f'{benefit_id}'}
            r = requests.post(self.getBenefitDetails, json=formdata)
            if r.status_code == 200:
                data = r.json().get('benefits')[0]
                description = cleanString(data['benefits_description'])
                title=cleanString(data['benefits_name'])
                yield CouponsItem(Title=title,
                                    supplier='993',
                                    brand=filterBrands(description,self.brands),
                                    JoinUrl=self.linkBase + data['benefits_id'],
                                    Description=description,
                                    ScrapeDate = datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                                    DoorToDoorShipping= any(ext in (description+title) for ext in allowed_shipping_list),
                                    cyclerun=self.cycleid )
            else:
                self.logger.error("something went wrong:::"+r.status_code)

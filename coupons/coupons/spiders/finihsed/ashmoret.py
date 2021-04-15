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

class AshmoretSpider(CrawlSpider):
    name = 'ashmoret'
    undetectable = True
    elementId = 'btnChat'
    wait = True
    allowed_domains = ['ashmoret-itu.co.il']
    start_urls = []
    signin_url = 'https://www.ashmoret-itu.co.il'
    usrEId,username = 'login_name','אורחאשמורת'
    pwdEId,password = 'login_password','אורחאשמורת'

    def start_requests(self):
        yield scrapy.Request(self.signin_url, callback=self.after_login,meta={"selenium":True,"login":True,"interactElement":"login_button_regular","elementId":"login_name"})

    def after_login(self,response):
        print(response.url)

    def parse(self, response):
        pass

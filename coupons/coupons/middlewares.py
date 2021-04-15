# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import sys
import logging
from scrapy import signals
from scrapy.mail import MailSender
from scrapy.utils.project import get_project_settings
# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from shutil import which
import undetected_chromedriver as uc
from datetime import datetime
from selenium.webdriver.common.keys import Keys
from pyvirtualdisplay import Display
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message

settings = get_project_settings()

class CouponsRetryMiddleware(RetryMiddleware):
    
    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        if (response.status == 200) and (request.meta.get('myoferToken')) and (not any(item for item in response.meta["cookieJar"] if item["name"] == "token")):
            reason = "Missing token cookie"
            spider.logger.info('Spider %s retrying' % reason)
            return self._retry(request,reason, spider) or response
        return response

class CouponsSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class CouponsDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    def __init__(self):
        mailfrom=settings.get("MAIL_ADDRESS")
        smtpport=settings.get("MAIL_PORT")
        smtpuser=settings.get("MAIL_USER")
        smtppass=settings.get("MAIL_PASSWORD")
        smtphost=settings.get("SMTP_HOST")

        self.mailer = MailSender(mailfrom=mailfrom,smtphost=smtphost,
                smtpport=smtpport,smtpuser=smtpuser,smtppass=smtppass)
        

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        s.cookie = ""
        if sys.platform == "linux" or sys.platform == "linux2":
            s.display = Display(visible=0, size=(800, 600))
            s.display.start()
            logging.info("Virtual Display Initiated")
        chrome_options = Options()
        if crawler.spider.undetectable:
            s.driver = uc.Chrome()
        else:
            driver_location = "/usr/bin/chromedriver"
            #driver_location = which('chromedriver')
            # binary_location = "/usr/bin/google-chrome"
            userAgent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.56 Safari/537.36"
            # chrome_options.binary_location = binary_location
            chrome_options.add_argument(f'user-agent={userAgent}')
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--ignore-ssl-errors")
            chrome_options.add_argument("--headless" )
            # chrome_options.addArguments("--no-sandbox");
            #chrome_options.addArguments("--disable-dev-shm-usage")
            s.driver = webdriver.Chrome(executable_path="/home/knust/allen/igroup/coupons/chromedriver",chrome_options=chrome_options)  # your chosen driver
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s
    
    def popElement(self,interactElement):
        self.driver.find_element_by_id(interactElement).click()

    def selenium_login(self,usrEId,pwdEId,username,password):
        self.driver.find_element_by_id(usrEId).send_keys(username)
        self.driver.find_element_by_id(pwdEId).send_keys(password,Keys.ENTER)
        self.cookie = self.driver.get_cookies()

    def process_request(self, request, spider):
        # only process tagged request or delete this if you want all
        if not (request.meta.get('selenium') or spider.undetectable):   
            return
        if (not request.meta.get('login')) and (spider.name == 'hvr'):
            for k in self.cookie:
                self.driver.add_cookie(k)
        self.driver.get(request.url)
        if spider.wait:
            try:
                elementId = spider.elementId
                if request.meta.get('elementId'):
                    elementId = request.meta.get('elementId')
                element_present = EC.presence_of_element_located((By.ID, elementId))
                WebDriverWait(self.driver, 10).until(element_present)
            except TimeoutException:
                spider.logger.error('Spider %s took too long to load' % spider.name)
                return
        if request.meta.get('interactElement'):
            self.popElement(request.meta.get('interactElement'))
        if request.meta.get('login'):
            self.selenium_login(spider.usrEId,spider.pwdEId,spider.username,spider.password)
        body = self.driver.page_source
        url = self.driver.current_url
        response = HtmlResponse(url, body=body, encoding='utf-8', request=request)
        response.meta['cookieJar'] = self.driver.get_cookies()
        return response

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
        return self.mailer.send(to=settings.get("EMAIL_LIST"), cc=settings.get("CC_LIST"), subject=f"IGROUP Coupon Scraping - Spider {spider.name} status",body=f"Spider {spider.name} started at {datetime.now().strftime('%m/%d/%Y, %H:%M:%S')}")

    def spider_closed(self, spider):
        spider.logger.info('Spider closed: %s' % spider.name)
        if self.driver:
            self.driver.close()
            self.driver = None
        if sys.platform == "linux" or sys.platform == "linux2":
            self.display.stop()
            spider.logger.info("Virtual Display killed")
        return self.mailer.send(to=settings.get("EMAIL_LIST"), cc=settings.get("CC_LIST"), subject=f"IGROUP Coupon Scraping - Spider {spider.name} status",body=f"Spider {spider.name} closed at {datetime.now().strftime('%m/%d/%Y, %H:%M:%S')}")



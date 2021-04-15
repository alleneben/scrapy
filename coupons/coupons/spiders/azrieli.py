import scrapy


class AzrieliSpider(scrapy.Spider):
    name = 'azrieli'
    undetectable = False
    allowed_domains = ['azrielimalls.co.il']
    start_urls = ['https://azrielimalls.co.il/']
    items = []

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_mall_links)

    
    def parse_mall_links(self, response):
        mall_links = response.css("a.my-malls-mall::attr(href)").extract()
        for mall_link in mall_links:
            yield scrapy.Request(f'https://azrielimalls.co.il{mall_link}',callback=self.parse_mall)

    def parse_mall(self,response):
        print(response.css("div.desktop-cats-menu-item-image a::attr(href)").extract())
    
    def parse(self,response):
        pass

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import pymongo
from itemadapter import ItemAdapter
import requests
from scrapy.utils.project import get_project_settings
from scrapy.exceptions import DropItem
import json
import logging
import scrapy
from scrapy.exporters import JsonItemExporter

class JsonPipeline:    
    def __init__(self, name, path):
        self.file = open(f"{path}{name}.json", 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            name = crawler.spider.name,
            path = crawler.settings.get('FEED_PATH')
        )


    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

class MongoDBPipeline:
    def __init__(self, collection_name, mongo_uri, mongo_db):
        self.collection_name = collection_name
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            collection_name = crawler.settings.get('MONGODB_COLLECTION'),
            mongo_uri=crawler.settings.get('MONGODB_URL'),
            mongo_db=crawler.settings.get('MONGODB_DB')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        try:
            self.collection = self.db[self.collection_name]
            self.collection.create_index('link', unique = True) 
            self.collection.insert_one(ItemAdapter(item).asdict())
            return item
        except pymongo.errors.DuplicateKeyError:
            raise DropItem(f"Duplicate url in {item}")

class ApiPipeline:
    def __init__(self, authenticationPayload,auth_endpoint,create_coupon_endpoint):
        self.authenticationPayload = authenticationPayload
        self.auth_endpoint = auth_endpoint
        self.create_coupon_endpoint = create_coupon_endpoint

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            authenticationPayload = dict(password=crawler.settings.get('AUTH_PASSWORD'), identifier=crawler.settings.get('AUTH_ID')),
            auth_endpoint = crawler.settings.get('AUTH_URL'),
            create_coupon_endpoint = crawler.settings.get('CREATE_COUPON_URL')
        )

    def open_spider(self, spider):
        self.r = requests.post(self.auth_endpoint, json=self.authenticationPayload)
        self.token = json.loads(self.r.text).get('jwt')
        self.headers = dict(Accept= 'Accept: application/json',Authorization=f'Bearer {self.token}') 

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        itemPayload = dict(Title= item['Title'],
            Description= item['Description'],
            brand= item['brand'],
            coupon_type = item['supplier'],
            JoinUrl= item['JoinUrl'],
            Source= "scraping",
            DoorToDoorShipping= item['DoorToDoorShipping'],
            CouponEndDate= item['ScrapeDate'])
        r = requests.post(self.create_coupon_endpoint, json=itemPayload,headers=self.headers)
        spider.log(str(r.status_code)+":::"+ r.text, logging.INFO)
        if (r.status_code == 200) and (json.loads(r.text).get('success') == True):
            return item
        spider.log(f"Spider {spider.name}:::{str(r.status_code)}:::{r.text}", logging.ERROR)
        raise DropItem()

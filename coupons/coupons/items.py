# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

# -*- coding: utf-8 -*-
from scrapy import Item, Field
from itemloaders.processors import TakeFirst

allowed_shipping_list = [
        'כולל משלוח', 'משלוחים חינם', 'המחירים כוללים משלוח',
        'המחיר כולל משלוח', 'כולל משלוח', 'משלוח עד הבית', 'משלוח חינם'
    ]

class CouponsItem(Item):
    Title = Field(output_processor=TakeFirst())
    supplier = Field(output_processor=TakeFirst())
    brand = Field(output_processor=TakeFirst())
    JoinUrl = Field(output_processor=TakeFirst())
    Description = Field(output_processor=TakeFirst())
    DoorToDoorShipping = Field(output_processor=TakeFirst())
    cyclerun = Field(output_processor=TakeFirst())
    ScrapeDate = Field()
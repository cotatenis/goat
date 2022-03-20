from scrapy import Field
from itemloaders.processors import MapCompose, TakeFirst
from scrapy.item import Item


class GoatItem(Item):
    url = Field()
    breadcrumbs = Field()
    model = Field()
    price_new = Field()
    price_used = Field()
    description = Field()
    brand = Field()
    release = Field()
    sku = Field()
    material = Field()
    main_color = Field()
    colorway = Field()
    designer = Field()
    collection = Field()
    technology = Field()
    nickname = Field()
    category = Field()
    image_urls = Field()
    image_uris = Field()
    spider = Field()
    spider_version = Field()
    timestamp = Field()

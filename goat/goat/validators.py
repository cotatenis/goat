from schematics.models import Model
from schematics.types import URLType, StringType, ListType, DateType,  DateTimeType

class GoatItem(Model):
    url = URLType()
    breadcrumbs = ListType(StringType)
    model = StringType()
    price_new = StringType()
    price_used = StringType()
    description = StringType()
    brand = StringType()
    release = DateType()
    sku = StringType()
    material = StringType()
    main_color = StringType()
    colorway = ListType(StringType)
    designer = StringType()
    collection = StringType()
    technology = StringType()
    nickname = StringType()
    category = StringType()
    image_urls = ListType(URLType)
    image_uris = ListType(StringType)
    spider = StringType()
    spider_version = StringType()
    timestamp = DateTimeType(required=True)



from goat.spiders.adidas import AdidasSpider
from datetime import datetime

class AdidasYeezy(AdidasSpider):
    name = "goat-adidas-yeezy"
    def __init__(self, years=None, *args, **kwargs):
        super(AdidasSpider, self).__init__(*args, **kwargs)
        if not years:
            years = [datetime.now().year]
        self.urls = []
        for year in years:
            self.urls.append(f"https://www.goat.com/timeline/{year}?brand_name=Yeezy")
import scrapy
import re
from ..utils.config_loader import config_loader

class MeliUySpider(scrapy.Spider):
    name = "meli-uy-identify"
    allowed_domains = ["www.mercadolibre.com.uy"]
    custom_settings = {
        'ITEM_PIPELINES': {
            'meli_crawler.pipelines.ValidationPipeline': 100,
            'meli_crawler.pipelines.PriceNormalizationPipeline': 200,
            'meli_crawler.pipelines.DiscountCalculationPipeline': 300,
            'meli_crawler.pipelines.ReviewsNormalizationPipeline': 400,
            'meli_crawler.pipelines.SellerNormalizationPipeline': 500,
            'meli_crawler.pipelines.CreateSellerIdProductidBrandPipeline': 600,
            'meli_crawler.pipelines.DynamoDBPipeline': 800,
            'meli_crawler.pipelines.SQSPipeline': 900,
        }
    }

    def __init__(self, *args, **kwargs):
        super(MeliUySpider, self).__init__(*args, **kwargs)
        self.load_configurations()

    def load_configurations(self):
        self.logger.info("Loading yaml configurations .....")
        self.selectors = config_loader.get_selectors_config()
        self.logger.info("Yaml configurations loaded successfully")

    def start_requests(self):
        yield scrapy.Request(url="https://www.mercadolibre.com.uy/ofertas", callback=self.parse)


    def parse(self, response):
        xpath_cards = self.selectors["card"]
        cards = response.xpath(xpath_cards)
        self.logger.info(f"Found {len(cards)} cards")
        for card in cards:
            item = {}
            for field, xpath in self.selectors["fields"].items():
                item[field] = card.xpath(xpath).get()
            self.logger.info(f"Item: {item}")
            self.logger.info(f"Item length: {len(item)}")
            yield item

            next_page = response.xpath(self.selectors["next_page"]).get()
            if next_page:
                self.logger.info(f"Next page: {next_page}")
                yield scrapy.Request(next_page, callback=self.parse)
            else:
                print("No next page found")

import scrapy
import re
from ..utils.config_loader import config_loader
import time
from datetime import datetime

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
            'meli_crawler.pipelines.CreateSellerIdUrlIdPipeline': 600,
            'meli_crawler.pipelines.DynamoDBPipeline': 800,
            'meli_crawler.pipelines.SQSPipeline': 900,
            's3pipeline.S3Pipeline': 950,
        },
        'S3PIPELINE_URL': f's3://meli-uy-offers/identify/year={datetime.now().year}/month={datetime.now().month}/day={datetime.now().day}/items.csv'
    }

    def __init__(self, *args, **kwargs):
        super(MeliUySpider, self).__init__(*args, **kwargs)
        self.load_configurations()
        # Add pagination limits to prevent infinite loops
        self.max_pages = kwargs.get('max_pages', 20)  # Default max 20 pages
        self.current_page = 0
        self.scraped_items = 0
        self.max_items = kwargs.get('max_items', 2000)  # Default max 2000 items

    def load_configurations(self):
        self.logger.info("Loading yaml configurations .....")
        self.selectors = config_loader.get_selectors_config()
        self.logger.info("Yaml configurations loaded successfully")

    def start_requests(self):
        self.logger.info(f"Starting spider with max_pages: {self.max_pages}, max_items: {self.max_items}")
        yield scrapy.Request(
            url="https://www.mercadolibre.com.uy/ofertas", 
            callback=self.parse,
            meta={'page': 1}
        )

    def parse(self, response):
        page = response.meta.get('page', 1)
        self.logger.info(f"Processing page {page}")
        
        xpath_cards = self.selectors["card"]
        cards = response.xpath(xpath_cards)
        self.logger.info(f"Found {len(cards)} cards on page {page}")
        
        # Process only the first card as configured
        self.logger.info(f"Processing {len(cards)} cards (limited to first card)")
        
        for i, card in enumerate(cards):
            # Check if we've reached the maximum items limit
            if self.scraped_items >= self.max_items:
                self.logger.info(f"Reached maximum items limit ({self.max_items}), stopping spider")
                return
            
            item = {}
            for field, xpath in self.selectors["fields"].items():
                value = card.xpath(xpath).get()
                item[field] = value
                self.logger.debug(f"Field '{field}': {value}")
            
            self.logger.info(f"Yielding item {self.scraped_items + 1} (card {i + 1}): {item.get('title', 'N/A')}")
            self.logger.info(f"Item fields: {list(item.keys())}")
            self.logger.info(f"Item values: {item}")
            self.scraped_items += 1
            
            # Add a unique identifier to track this item
            item['_spider_item_id'] = f"item_{self.scraped_items}_{int(time.time())}"
            self.logger.info(f"Added tracking ID: {item['_spider_item_id']}")
            
            yield item

        self.logger.info(f"Finished processing page {page}. Total items yielded: {self.scraped_items}")
        # Check if we should continue to next page
        if page < self.max_pages:
            next_page = response.xpath(self.selectors["next_page"]).get()
            if next_page:
                self.logger.info(f"Following next page: {next_page}")
                yield scrapy.Request(
                    next_page, 
                    callback=self.parse,
                    meta={'page': page + 1}
                )
        else:
            self.logger.info(f"Reached maximum pages limit ({self.max_pages}), stopping spider")

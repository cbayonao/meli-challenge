from collections.abc import Iterable
from typing import Any
import scrapy


class MeliUyCollectSpider(scrapy.Spider):
    name = "meli-uy-collect"
    allowed_domains = ["www.mercadolibre.com.uy"]

    def start_requests(self) -> Iterable[Any]:
        """
        Read messages from SQS queue and yield requests to collect data
        """
        

    def parse(self, response):
        pass

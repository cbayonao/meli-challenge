# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import base64
import re
import json
import boto3
from decimal import Decimal, InvalidOperation
from datetime import datetime
from decouple import config
from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter


class ValidationPipeline:
    """
    Pipeline 100: ValidationPipeline
    """
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        required_fields = [
            'title',
            'current_price',
            'pub_url',
            'original_price',
            'seller',
            'brand',
            'rating',
            'reviews'
        ]
        for field in required_fields:
            if not adapter.get(field):
                raise DropItem(f"Missing required field: {field}")
        spider.logger.debug(f"Item validated: {adapter.get('title', 'N/A')}")
        return item

class PriceNormalizationPipeline:
    """
    Pipeline 200: PriceNormalizationPipeline
    """
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Normalize current price
        if adapter.get('current_price'):
            adapter['current_price_normalized'] = self.normalize_price(
                adapter['current_price']
            )
        
        # Normalize original price
        if adapter.get('original_price'):
            adapter['original_price_normalized'] = self.normalize_price(
                adapter['original_price']
            )
        else:
            # If there is no original price, use the current price
            adapter['original_price_normalized'] = adapter.get('current_price_normalized', 0)
        
        spider.logger.debug(f"Prices normalized - Original: {adapter.get('original_price_normalized')}, Current: {adapter.get('current_price_normalized')}")
        return item

    def normalize_price(self, price_str):
        """
        Normalize price to numeric format
        
        Args:
            price_str: String with price (e.g: "$1.234", "2.970")
            
        Returns:
            float: Normalized price
        """
        if not price_str:
            return 0.0
            
        try:
            # Remove currency symbols and spaces
            clean_price = re.sub(r'[^\d.,]', '', str(price_str))
            
            # Handle Uruguayan format (point as thousand separator, comma as decimal)
            # Example: "2.970" -> 2970, "2.970,50" -> 2970.50
            if ',' in clean_price:
                # If there is a comma, the comma is the decimal
                parts = clean_price.split(',')
                integer_part = parts[0].replace('.', '')  # Remove dots (thousand separators)
                decimal_part = parts[1]
                clean_price = f"{integer_part}.{decimal_part}"
            else:
                # Only point, assume it is a thousand separator
                clean_price = clean_price.replace('.', '')
            
            return float(clean_price)
            
        except (ValueError, AttributeError) as e:
            return 0.0
        
class DiscountCalculationPipeline:
    """
    Pipeline 300: DiscountCalculationPipeline
    """
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        original_price = adapter.get('original_price_normalized', 0)
        current_price = adapter.get('current_price_normalized', 0)
        if original_price > 0 and current_price > 0:
            # Calculate discount percentage
            discount_amount = original_price - current_price
            discount_percentage = (discount_amount / original_price) * 100
            
            adapter['discount_amount'] = round(discount_amount, 2)
            adapter['discount_percentage'] = round(discount_percentage, 2)
            adapter['has_discount'] = discount_percentage > 0
        else:
            adapter['discount_amount'] = 0
            adapter['discount_percentage'] = 0
            adapter['has_discount'] = False
        spider.logger.debug(f"Discount calculated - Amount: {adapter.get('discount_amount')}, Percentage: {adapter.get('discount_percentage')}, Has discount: {adapter.get('has_discount')}")
        return item
        
class ReviewsNormalizationPipeline:
    """
    Pipeline 400: ReviewsNormalizationPipeline
    """
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Normalize reviews: "(26)" -> 26
        reviews_str = adapter.get('reviews', '')
        if reviews_str:
            # Extract number from the parentheses
            match = re.search(r'\((\d+)\)', reviews_str)
            if match:
                adapter['reviews_count'] = int(match.group(1))
            else:
                # If there is no parentheses, try to extract the number directly
                numbers = re.findall(r'\d+', reviews_str)
                adapter['reviews_count'] = int(numbers[0]) if numbers else 0
        else:
            adapter['reviews_count'] = 0

        # Normalize rating: "4.5" -> 4.5
        rating_str = adapter.get('rating', '')
        if rating_str:
            try:
                adapter['rating_score'] = float(rating_str)
            except (ValueError, TypeError):
                adapter['rating_score'] = 0.0
        else:
            adapter['rating_score'] = 0.0
        
        spider.logger.debug(f"Reviews normalized: {adapter.get('reviews_count')} reviews, rating: {adapter.get('rating_score')}")
        return item
    
class SellerNormalizationPipeline:
    """
    Pipeline 500: SellerNormalizationPipeline
    """
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        # Normalize seller name 'Por Mercadolibre' -> 'Mercadolibre' Remove 'Por '
        seller_name = adapter.get('seller', '')
        if seller_name:
            adapter['seller_name'] = seller_name.replace('Por ', '')
        else:
            adapter['seller_name'] = ''
        
        # Normalize seller id 'Por Mercadolibre' -> 'Mercadolibre' Remove 'Por '
        
        spider.logger.debug(f"Seller normalized: {adapter.get('seller_name')}")
        return item
    
class CreateSellerIdProductidBrandPipeline:
    """
    Pipeline 600: CreateSellerIdPipeline
    Create seller_id field based on seller name and productid_brand field based on title and brand
    seller_id: base64(seller_name)
    productid_brand: str(base64(title) + "#" + brand_name)
    """
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        adapter['seller_id'] = base64.b64encode(adapter.get('seller_name').encode()).decode()
        adapter['productid_brand'] = base64.b64encode(adapter.get('title').encode()).decode() + "#" + adapter.get('brand')
        return item

class DynamoDBPipeline:
    """
    Pipeline 800: Save in DynamoDB
    """
    def __init__(self):
        # Configuración AWS
        self.aws_access_key = config('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = config('AWS_SECRET_ACCESS_KEY')
        self.region = config('DYNAMODB_REGION', default='us-east-1')
        self.table_name = config('DYNAMODB_TABLE_NAME')
        
        # Cliente DynamoDB
        self.dynamodb = None
        self.table = None
    
    def open_spider(self, spider):
        """Initialize connection when the spider starts"""
        try:
            self.dynamodb = boto3.resource(
                'dynamodb',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region
            )
            
            self.table = self.dynamodb.Table(self.table_name)
            spider.logger.info(f"DynamoDB connection established: {self.table_name}")
            
        except Exception as e:
            spider.logger.error(f"Error connecting to DynamoDB: {e}")
            raise
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        try:
            # Prepare item for DynamoDB (convert floats to Decimal)
            dynamo_item = self.prepare_item_for_dynamo(dict(adapter))
            
            # Insert into DynamoDB
            response = self.table.put_item(Item=dynamo_item)
            
            # Add DynamoDB information to the item
            adapter['dynamodb_inserted'] = True
            adapter['dynamodb_response_metadata'] = response.get('ResponseMetadata', {})
            
            spider.logger.info(f"Item saved in DynamoDB: {adapter.get('productid_brand')}")
            return item
            
        except Exception as e:
            spider.logger.error(f"Error saving in DynamoDB: {e}")
            adapter['dynamodb_inserted'] = False
            adapter['dynamodb_error'] = str(e)
            return item
    
    def prepare_item_for_dynamo(self, item):
        """
        Preparar item para DynamoDB convirtiendo tipos incompatibles
        """
        dynamo_item = {}
        
        for key, value in item.items():
            if value is None:
                continue
            elif isinstance(value, float):
                dynamo_item[key] = Decimal(str(value))
            elif isinstance(value, dict):
                dynamo_item[key] = self.prepare_item_for_dynamo(value)
            else:
                dynamo_item[key] = value
        
        return dynamo_item
    
    def close_spider(self, spider):
        """Cerrar conexión cuando el spider termina"""
        spider.logger.info("DynamoDB pipeline cerrado")

class SQSPipeline:
    """
    Pipeline 900: Send ID to SQS queue for later processing
    """
    
    def __init__(self):
        self.aws_access_key = config('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = config('AWS_SECRET_ACCESS_KEY')
        self.region = config('SQS_REGION', default='us-east-1')
        self.queue_url = config('SQS_QUEUE_URL')
        
        self.sqs = None
    
    def open_spider(self, spider):
        """Inicializar conexión SQS"""
        try:
            self.sqs = boto3.client(
                'sqs',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region
            )
            
            spider.logger.info(f"Conexión SQS establecida: {self.queue_url}")
            
        except Exception as e:
            spider.logger.error(f"Error conectando a SQS: {e}")
            raise
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Solo enviar a SQS si se guardó correctamente en DynamoDB
        if not adapter.get('dynamodb_inserted', False):
            spider.logger.warning(f"Item no enviado a SQS: no se guardó en DynamoDB")
            return item
        
        try:
            # Preparar mensaje para SQS
            message_body = {
                'seller_id': adapter.get('seller_id'),
                'productid_brand': adapter.get('productid_brand'),
                'scraped_at': adapter.get('scraped_at'),
                'spider_name': adapter.get('spider_name'),
                'processing_status': 'pending'
            }
            
            # Enviar mensaje a SQS
            # Check if this is a FIFO queue (ends with .fifo)
            is_fifo_queue = self.queue_url.endswith('.fifo')
            
            # Prepare message parameters
            message_params = {
                'QueueUrl': self.queue_url,
                'MessageBody': json.dumps(message_body),
                'MessageAttributes': {
                    'product_id': {
                        'StringValue': adapter.get('product_id', 'unknown'),
                        'DataType': 'String'
                    },
                    'price_category': {
                        'StringValue': adapter.get('price_category', 'unknown'),
                        'DataType': 'String'
                    },
                    'has_discount': {
                        'StringValue': str(adapter.get('has_discount', False)),
                        'DataType': 'String'
                    }
                }
            }
            
            # Add FIFO-specific parameters if needed
            if is_fifo_queue:
                message_params['MessageGroupId'] = adapter.get('product_id', 'default_group')
                message_params['MessageDeduplicationId'] = f"{adapter.get('product_id', 'unknown')}_{adapter.get('scraped_at', 'unknown')}"
            
            response = self.sqs.send_message(**message_params)
            
            # Agregar información de SQS al item
            adapter['sqs_sent'] = True
            adapter['sqs_message_id'] = response.get('MessageId')
            
            spider.logger.info(f"Mensaje enviado a SQS: {response.get('MessageId')}")
            return item
            
        except Exception as e:
            spider.logger.error(f"Error enviando a SQS: {e}")
            adapter['sqs_sent'] = False
            adapter['sqs_error'] = str(e)
            return item
    
    def close_spider(self, spider):
        """Cerrar conexión SQS"""
        spider.logger.info("SQS pipeline cerrado")
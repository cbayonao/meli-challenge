# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import base64
import re
import json
import boto3
import hashlib
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
            'pub_url',
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
    Normalize seller name: "Por Meli" -> "Meli"
    Default to "no seller found" if no seller is listed
    """
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        seller = adapter.get('seller')
        
        if seller and seller.strip():  # Check if seller exists and is not just whitespace
            # Remove "Por " prefix if present
            normalized_seller = seller.replace('Por ', '').strip()
            adapter['seller'] = normalized_seller
            spider.logger.debug(f"Seller normalized: '{seller}' -> '{normalized_seller}'")
        else:
            # Default to "no seller found" if no seller is listed
            adapter['seller'] = 'no seller found'
            spider.logger.debug(f"No seller found, defaulting to: 'no seller found'")
        
        # Ensure seller field is always present and not empty
        if not adapter.get('seller') or not adapter.get('seller').strip():
            adapter['seller'] = 'no seller found'
            spider.logger.warning(f"Seller field was empty after normalization, defaulting to: 'no seller found'")
        
        spider.logger.info(f"✅ Seller field processed: '{adapter.get('seller')}'")
        return item

class CreateSellerIdUrlIdPipeline:
    """
    Pipeline 600: CreateSellerIdUrlIdPipeline
    Create seller_id field based on seller name and url_id field based on pub_url
    seller_id: base64(seller_name)
    url_id: base64(pub_url)
    """
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        spider.logger.info(f"🔧 CreateSellerIdUrlIdPipeline processing item: {adapter.get('_spider_item_id', 'unknown')}")
        
        seller = adapter.get('seller')
        pub_url = adapter.get('pub_url')
        
        if seller and pub_url:
            adapter['seller_id'] = base64.b64encode(seller.encode()).decode()
            adapter['url_id'] = hashlib.sha256(pub_url.encode('utf-8')).hexdigest()
            
            spider.logger.info(f"✅ Created seller_id: {adapter['seller_id'][:10]}... and url_id: {adapter['url_id'][:10]}...")
            spider.logger.debug(f"Seller: '{seller}' -> seller_id: {adapter['seller_id']}")
            
            # Log special case for "no seller found"
            if seller == 'no seller found':
                spider.logger.info(f"ℹ️ Processing item with default seller: 'no seller found'")
        else:
            spider.logger.error(f"❌ Missing seller or pub_url: seller={seller}, pub_url={pub_url}")
        
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
            adapter['dynamodb_response_metadata_request_id'] = response.get('ResponseMetadata', {}).get('RequestId')
            adapter['dynamodb_response_metadata_http_status_code'] = response.get('ResponseMetadata', {}).get('HTTPStatusCode')
            adapter['dynamodb_inserted_at'] = datetime.now().isoformat()
            spider.logger.info(f"Item saved in DynamoDB: {adapter.get('url_id')}")
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
        self.processed_items = set()  # Track processed items to prevent duplicates
    
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
        spider.logger.info(f"📤 SQSPipeline processing item: {adapter.get('_spider_item_id', 'unknown')}")
        
        # Solo enviar a SQS si se guardó correctamente en DynamoDB
        if not adapter.get('dynamodb_inserted', False):
            spider.logger.warning(f"⚠️ Item no enviado a SQS: no se guardó en DynamoDB")
            return item
        
        # Create a unique identifier for this item to prevent duplicates
        item_key = f"{adapter.get('seller_id')}_{adapter.get('url_id')}"
        
        # Check if we've already processed this item
        if item_key in self.processed_items:
            spider.logger.warning(f"🔄 Item ya procesado, saltando SQS: {item_key}")
            return item
        
        try:
            # Preparar mensaje para SQS con la estructura que espera el collector
            message_body = {
                'seller_id': adapter.get('seller_id'),
                'url_id': adapter.get('url_id'),
                'inserted_at': adapter.get('dynamodb_inserted_at'),
                'processing_status': 'pending'
            }
            
            # Verificar que tenemos los campos requeridos
            if not message_body['seller_id'] or not message_body['url_id']:
                spider.logger.warning(f"⚠️ Item no enviado a SQS: campos requeridos faltantes - seller_id: {message_body['seller_id']}, url_id: {message_body['url_id']}")
                return item

            # Enviar mensaje a SQS
            response = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body)
            )
            
            # Mark this item as processed
            self.processed_items.add(item_key)
            
            # Agregar información de SQS al item
            adapter['sqs_sent'] = True
            adapter['sqs_message_id'] = response.get('MessageId')
            spider.logger.info(f"✅ Mensaje enviado a SQS: {response.get('MessageId')} para seller_id: {message_body['seller_id']} (Item key: {item_key})")
            return item
            
        except Exception as e:
            spider.logger.error(f"❌ Error enviando a SQS: {e}")
            adapter['sqs_sent'] = False
            adapter['sqs_error'] = str(e)
            return item
    
    def close_spider(self, spider):
        """Cerrar conexión SQS"""
        spider.logger.info(f"SQS pipeline cerrado. Total items procesados: {len(self.processed_items)}")
        spider.logger.info(f"Items procesados: {list(self.processed_items)}")


class CollectSpiderUpdatePipeline:
    """
    Pipeline 950: Update specific columns in DynamoDB for meli-uy-collect spider
    Updates: currency, availability, features, mainImage, images, description
    Uses seller_id as partition key and url_id as sort key
    """
    
    def __init__(self):
        self.aws_access_key = config('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = config('AWS_SECRET_ACCESS_KEY')
        self.region = config('DYNAMODB_REGION', default='us-east-1')
        self.table_name = config('DYNAMODB_TABLE_NAME')
        
        self.dynamodb = None
        self.table = None
    
    def open_spider(self, spider):
        """Initialize connection when the spider starts"""
        try:
            self.dynamodb = boto3.client(
                'dynamodb',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region
            )
            
            spider.logger.info(f"CollectSpiderUpdatePipeline: DynamoDB connection established: {self.table_name}")
            
        except Exception as e:
            spider.logger.error(f"Error connecting to DynamoDB: {e}")
            raise
    
    def process_item(self, item, spider):
        # Only process items from meli-uy-collect spider
        if spider.name != 'meli-uy-collect':
            return item
        
        try:
            # Extract the required fields from the Zyte API product response
            product_data = item.get('product', {})
            
            if not product_data:
                spider.logger.warning("No product data found in item")
                return item
            
            # Extract the specific fields we want to update
            update_fields = {}
            
            # Currency
            if 'currency' in product_data:
                update_fields['currency'] = product_data['currency']
            
            # Availability
            if 'availability' in product_data:
                update_fields['availability'] = product_data['availability']
            
            # Features
            if 'features' in product_data:
                update_fields['features'] = product_data['features']
            
            # Main Image
            if 'mainImage' in product_data:
                update_fields['mainImage'] = product_data['mainImage']
            
            # Images
            if 'images' in product_data:
                update_fields['images'] = product_data['images']
            
            # Description
            if 'description' in product_data:
                update_fields['description'] = product_data['description']
            
            if not update_fields:
                spider.logger.warning("No fields to update found in product data")
                return item
            
            # Get seller_id and url_id from the message body
            message_body = item.get('message_body', {})
            seller_id = message_body.get('seller_id')
            url_id = message_body.get('url_id')
            
            if not seller_id or not url_id:
                spider.logger.error("Missing seller_id or url_id in message_body")
                return item
            
            # Prepare the update expression
            update_expression = "SET "
            expression_attribute_values = {}
            expression_attribute_names = {}
            
            for field_name, field_value in update_fields.items():
                # Create attribute name placeholder
                attr_name = f"#{field_name}"
                attr_value = f":{field_name}"
                
                update_expression += f"{attr_name} = {attr_value}, "
                expression_attribute_names[attr_name] = field_name
                
                # Convert field value to proper DynamoDB format
                dynamo_value = self.convert_to_dynamodb_format(field_value)
                expression_attribute_values[attr_value] = dynamo_value
                
                # Log the conversion for debugging
                spider.logger.debug(f"Field '{field_name}': {type(field_value).__name__} -> {dynamo_value}")
            
            # Remove trailing comma and space
            update_expression = update_expression.rstrip(", ")
            
            spider.logger.info(f"Update expression: {update_expression}")
            spider.logger.info(f"Expression attribute names: {expression_attribute_names}")
            spider.logger.info(f"Expression attribute values: {expression_attribute_values}")
            
            # Log a sample of the converted data for verification
            spider.logger.info("Sample converted data:")
            for field_name, field_value in update_fields.items():
                attr_value = f":{field_name}"
                if attr_value in expression_attribute_values:
                    spider.logger.info(f"  {field_name}: {expression_attribute_values[attr_value]}")
            
            # Update the item in DynamoDB
            response = self.dynamodb.update_item(
                TableName=self.table_name,
                Key={
                    'seller_id': {'S': seller_id},
                    'url_id': {'S': url_id}
                },
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="UPDATED_NEW"
            )
            
            spider.logger.info(f"✅ Updated DynamoDB item: seller_id={seller_id}, url_id={url_id}")
            spider.logger.info(f"Updated fields: {list(update_fields.keys())}")
            
            # Add update information to the item
            item['dynamodb_updated'] = True
            item['dynamodb_update_response'] = response.get('Attributes', {})
            item['updated_fields'] = list(update_fields.keys())
            
            return item
            
        except Exception as e:
            spider.logger.error(f"❌ Error updating DynamoDB item: {e}")
            item['dynamodb_updated'] = False
            item['dynamodb_update_error'] = str(e)
            return item
    
    def close_spider(self, spider):
        """Close connection when the spider ends"""
        spider.logger.info("CollectSpiderUpdatePipeline: DynamoDB pipeline closed")

    def convert_to_dynamodb_format(self, value):
        """
        Convert Python values to proper DynamoDB format
        """
        if value is None:
            return {'NULL': True}
        elif isinstance(value, str):
            return {'S': value}
        elif isinstance(value, (int, float)):
            return {'N': str(value)}
        elif isinstance(value, bool):
            return {'BOOL': value}
        elif isinstance(value, list):
            # Convert list items to DynamoDB format
            dynamo_list = []
            for item in value:
                if isinstance(item, dict):
                    # Handle nested objects (like images with url)
                    dynamo_item = {}
                    for k, v in item.items():
                        dynamo_item[k] = self.convert_to_dynamodb_format(v)
                    dynamo_list.append({'M': dynamo_item})
                else:
                    # Handle simple list items
                    dynamo_list.append(self.convert_to_dynamodb_format(item))
            return {'L': dynamo_list}
        elif isinstance(value, dict):
            # Convert dict to DynamoDB map format
            dynamo_map = {}
            for k, v in value.items():
                dynamo_map[k] = self.convert_to_dynamodb_format(v)
            return {'M': dynamo_map}
        else:
            # Fallback: convert to string
            return {'S': str(value)}
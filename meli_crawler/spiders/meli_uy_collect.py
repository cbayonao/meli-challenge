import boto3
import scrapy
import json
from decouple import config
from typing import Any, Dict, Optional
from collections.abc import Iterable
from botocore.exceptions import NoCredentialsError, ClientError
from datetime import datetime


class MeliUyCollectSpider(scrapy.Spider):
    name = "meli-uy-collect"
    custom_settings = {
        "ADDONS": {
            "scrapy_zyte_api.Addon": 500,
        },
        "ROBOTSTXT_OBEY": False,
        # Zyte API specific settings to avoid User-Agent warnings
        # "ZYTE_API_TRANSPARENT_MODE": False,
        # "ZYTE_API_BROWSER_HEADERS": True,  # Enable browser headers mapping
        # Disable default User-Agent to let Zyte API handle it
        "USER_AGENT": None,
        # Disable default headers that conflict with Zyte API
        "DEFAULT_REQUEST_HEADERS": {},
        # Custom pipelines for this spider only
        "ITEM_PIPELINES": {
            "meli_crawler.pipelines.CollectSpiderUpdatePipeline": 300,
            's3pipeline.S3Pipeline': 400,
        },
        'S3PIPELINE_URL': f's3://meli-uy-offers/collect/year={datetime.now().year}/month={datetime.now().month}/day={datetime.now().day}/details.csv'
    }

    def __init__(self, *args, **kwargs):
        super(MeliUyCollectSpider, self).__init__(*args, **kwargs)
        self.aws_access_key_id = config("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = config("AWS_SECRET_ACCESS_KEY")
        self.aws_region = config("AWS_DEFAULT_REGION")
        self.sqs_queue_url = config("SQS_QUEUE_URL")
        self.dynamo_table_name = config("DYNAMODB_TABLE_NAME")
        self.max_messages_per_batch = 5  # Limit messages per batch
        self.batch_count = 0  # Track processed batches
        self.max_batches = kwargs.get('max_batches', 2)  # Limit total batches to prevent infinite loops
        
        # Retry configuration for "Mercado Libre" title
        self.max_retries = kwargs.get('max_retries', 5)  # Maximum retry attempts
        
        try:
            self.sqs_client = boto3.client(
                'sqs',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            self.dynamo_client = boto3.client(
                'dynamodb',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            self.logger.info("AWS clients initialized successfully")
        except NoCredentialsError:
            self.logger.error("No credentials found for AWS")
            raise
        except Exception as e:
            self.logger.error(f"Error initializing AWS clients: {e}")
            raise

    def start_requests(self) -> Iterable[Any]:
        """
        Read messages from SQS queue and yield requests to collect data
        """
        self.logger.info("Reading messages from SQS queue")
        if not self.sqs_queue_url:
            self.logger.error("No sqs_queue_url provided")
            return
        
        # Process messages in batches to avoid infinite loops
        while self.batch_count < self.max_batches:
            try:
                response = self.sqs_client.receive_message(
                    QueueUrl=self.sqs_queue_url,
                    MaxNumberOfMessages=self.max_messages_per_batch,
                    VisibilityTimeout=30,
                    WaitTimeSeconds=5,  # Reduced wait time
                    MessageAttributeNames=['All']
                )
                messages = response.get('Messages', [])
                
                if not messages:
                    self.logger.info("No messages found in SQS queue, stopping spider")
                    break
                
                self.logger.info(f"Processing batch {self.batch_count + 1} with {len(messages)} messages")
                
                for message in messages:
                    message_body = json.loads(message['Body'])
                    receipt_handle = message['ReceiptHandle']

                    self.logger.info(f"Message body: {message_body}")                    
                    seller_id = message_body.get('seller_id')
                    url_id = message_body.get('url_id')
                    if seller_id and url_id:
                        # Get the url from the dynamo db based on seller_id as partition key and url_id as sort key
                        response = self.dynamo_client.get_item(
                            TableName=self.dynamo_table_name,
                            Key={
                                'seller_id': {'S': seller_id},
                                'url_id': {'S': url_id}
                            }
                        )
                        pub_url = response.get('Item', {}).get('pub_url', {}).get('S')
                    else:
                        self.logger.warning(f"No seller_id or url_id found in message: {message_body}")
                        continue

                    if pub_url:
                        self.logger.info(f"Processing URL: {pub_url}")
                        yield scrapy.Request(
                            url=pub_url,
                            callback=self.parse,
                            meta={
                                "zyte_api_automap": {
                                    "browserHtml": True,  
                                    "product": True,
                                    "productOptions": {"extractFrom":"browserHtml","ai":True},
                                    "geolocation": "UY"
                                },
                                'message_body': message_body,
                                'receipt_handle': receipt_handle,
                                'pub_url': pub_url
                            }
                        )
                    else:
                        self.logger.warning(f"No pub_url found in dynamo db: {message_body}")
                        # Delete message without pub_url to avoid infinite loops
                        self.delete_sqs_message(receipt_handle)
                        continue
                
                self.batch_count += 1
                self.logger.info(f"Completed batch {self.batch_count}")
                
                # If we processed fewer messages than the batch size, we're likely done
                if len(messages) < self.max_messages_per_batch:
                    self.logger.info("Received fewer messages than batch size, likely done")
                    break
                    
            except ClientError as e:
                self.logger.error(f"Error related to AWS client: {e}")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                break
        
        self.logger.info(f"Spider completed after processing {self.batch_count} batches")

    def parse(self, response):
        """
        Process the response of the scraped URL
        """
        message_body = response.meta['message_body']
        receipt_handle = response.meta['receipt_handle']
        pub_url = response.meta['pub_url']
        response_body = response.text

        self.logger.info(f"Processing URL: {pub_url}")
        self.logger.info(f"Status code: {response.status}")
        
        try:
            # Extract data from the response
            title = response.css('title::text').get()
            
            # Check if we got a generic "Mercado Libre" page instead of product content
            if title == "Mercado Libre":
                self.logger.warning(f"Got generic 'Mercado Libre' page for URL: {pub_url}")
                
                # Get retry attempt number from meta
                retry_attempt = response.meta.get('retry_attempt', 0)
                
                # Check if we should retry
                if retry_attempt < self.max_retries:
                    retry_attempt += 1
                    self.logger.info(f"Retrying request (attempt {retry_attempt}/{self.max_retries}) for URL: {pub_url}")
                    
                    # Retry with enhanced Zyte API parameters
                    yield scrapy.Request(
                        url=pub_url,
                        callback=self.parse,
                        meta={
                            'message_body': message_body,
                            'receipt_handle': receipt_handle,
                            'pub_url': pub_url,
                            'retry_attempt': retry_attempt,
                            "zyte_api_automap": {
                                "browserHtml": True,  
                                "product": True,
                                "productOptions": {"extractFrom":"browserHtml","ai":True},
                                "geolocation": "UY"
                            },
                        },
                        dont_filter=True,  # Allow duplicate requests for retries
                        errback=self.handle_retry_error
                    )
                    return
                else:
                    self.logger.error(f"Max retries reached ({self.max_retries}) for URL: {pub_url}. Title still 'Mercado Libre'")
                    # Continue processing but log the issue
            
            # Create item with scraped data
            retry_attempt = response.meta.get('retry_attempt', 0)
            product = response.raw_api_response["product"]
            
            # Create item structure for the pipeline
            item = {
                'product': product,  # Zyte API product data
                'message_body': message_body,  # For pipeline to extract seller_id and url_id
                'retry_attempts': retry_attempt,
                'url': pub_url,
                'title': title,
                'status_code': response.status,
                'scraped_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Item processed successfully: {title} (after {retry_attempt} retries)")
            
            # Delete the SQS message after successful processing
            self.delete_sqs_message(receipt_handle)
            
            yield item
            
            
        except Exception as e:
            self.logger.error(f"Error processing product: {e}")
            # Even if processing fails, delete the message to avoid infinite loops
            self.delete_sqs_message(receipt_handle)

    def delete_sqs_message(self, receipt_handle: str):
        """
        Delete the message from the SQS queue after processing it
        """
        try:
            self.sqs_client.delete_message(
                QueueUrl=self.sqs_queue_url,
                ReceiptHandle=receipt_handle
            )
            self.logger.info("Message deleted from SQS")
        except ClientError as e:
            self.logger.error(f"Error deleting message from SQS: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error deleting SQS message: {e}")

    def handle_retry_error(self, failure):
        """
        Handle errors during retry attempts
        """
        request = failure.request
        pub_url = request.meta.get('pub_url', 'unknown')
        receipt_handle = request.meta.get('receipt_handle')
        retry_attempt = request.meta.get('retry_attempt', 0)
        
        self.logger.error(f"Retry attempt {retry_attempt} failed for URL: {pub_url}")
        self.logger.error(f"Error: {failure.value}")
        
        # Delete the SQS message to prevent infinite loops
        if receipt_handle:
            self.delete_sqs_message(receipt_handle)
            self.logger.info(f"Deleted SQS message after retry failure for URL: {pub_url}")
        else:
            self.logger.warning(f"No receipt_handle found for failed retry: {pub_url}")

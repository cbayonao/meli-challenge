# MercadoLibre Uruguay Spiders - Usage Guide

## Overview

This project contains two Scrapy spiders that work together to scrape MercadoLibre Uruguay offers:

1. **MeliUySpider** (`meli-uy-identify`): Scrapes offer pages and sends data to DynamoDB + SQS
2. **MeliUyCollectSpider** (`meli-uy-collect`): Reads SQS messages and scrapes individual product pages

## Fixed Issues

### 1. Infinite Loop Prevention
- **MeliUySpider**: Added `max_pages` and `max_items` limits to prevent infinite pagination
- **MeliUyCollectSpider**: Added `max_batches` limit and proper SQS message deletion to prevent infinite message processing

### 2. SQS Message Structure
- Fixed message format to include `seller_id`, `url_id`, and other required fields as expected by the collector
- Proper message deletion after processing to prevent message accumulation

### 3. Seller Normalization
- **SellerNormalizationPipeline**: Automatically normalizes seller names and handles missing sellers
- **Default Value**: Items without sellers now default to "no seller found" instead of failing
- **Prefix Removal**: Automatically removes "Por " prefix from seller names (e.g., "Por Meli" → "Meli")

### 4. Error Handling
- Better error handling and logging
- Messages are deleted even if processing fails to prevent infinite loops

## Usage

### Option 1: Using the Helper Script (Recommended)

```bash
# Run the identify spider (scrapes offers)
python run_spiders.py identify --max-pages 3 --max-items 50

# Run the collect spider (processes SQS messages)
python run_spiders.py collect --max-batches 20
```

### Option 2: Direct Scrapy Commands

```bash
# Run identify spider with limits
scrapy crawl meli-uy-identify -a max_pages=3 -a max_items=50

# Run collect spider with batch limits
scrapy crawl meli-uy-collect -a max_batches=20
```

## Parameters

### MeliUySpider (identify)
- `max_pages`: Maximum number of pages to scrape (default: 20)
- `max_items`: Maximum number of items to scrape (default: 2000)

### MeliUyCollectSpider (collect)
- `max_batches`: Maximum number of SQS batches to process (default: 100)

## Pipeline Processing Order

The spiders use the following pipeline order:

1. **ValidationPipeline** (100): Validates required fields (`title`, `pub_url`)
2. **PriceNormalizationPipeline** (200): Normalizes price formats
3. **DiscountCalculationPipeline** (300): Calculates discounts
4. **ReviewsNormalizationPipeline** (400): Normalizes review counts and ratings
5. **SellerNormalizationPipeline** (500): **Normalizes seller names and handles missing sellers**
6. **CreateSellerIdUrlIdPipeline** (600): Creates unique IDs for seller and URL
7. **DynamoDBPipeline** (800): Saves data to DynamoDB
8. **SQSPipeline** (900): Sends messages to SQS for further processing

## Seller Handling

### Automatic Normalization
- **Prefix Removal**: "Por Meli" → "Meli"
- **Whitespace Handling**: Trims leading/trailing spaces
- **Missing Seller**: Defaults to "no seller found" when no seller is listed

### Examples
```yaml
# Input → Output
"Por Meli" → "Meli"
"  Seller Name  " → "Seller Name"
"" → "no seller found"
null → "no seller found"
"   " → "no seller found"
```

## Workflow

1. **Run MeliUySpider first** to scrape offers and populate DynamoDB + SQS
2. **Run MeliUyCollectSpider** to process SQS messages and scrape individual product pages
3. Both spiders will automatically stop when they reach their limits

## Monitoring

- Check AWS SQS console to monitor message processing
- Check AWS DynamoDB console to verify data storage
- Monitor spider logs for processing status and seller normalization

## Best Practices

1. **Start with small limits** (e.g., `max_pages=2`, `max_items=20`) to test
2. **Monitor SQS queue** to ensure messages are being processed and deleted
3. **Use appropriate batch sizes** for the collect spider based on your queue volume
4. **Check logs** for any errors or warnings, especially seller normalization
5. **Verify seller data** in DynamoDB to ensure normalization is working correctly

## Testing

### Test Seller Normalization
```bash
python test_seller_normalization.py
```

This script will:
- Run the spider with minimal configuration
- Check that seller normalization is working
- Verify that missing sellers default to "no seller found"
- Show pipeline processing logs

## Troubleshooting

### SQS Messages Not Being Deleted
- Ensure the collector spider has proper AWS credentials
- Check that the SQS queue URL is correct
- Verify message structure matches expectations

### Infinite Loops
- Always set appropriate limits when running spiders
- Monitor the AWS console for message accumulation
- Check spider logs for processing status

### DynamoDB Issues
- Verify AWS credentials and region settings
- Check that the table name is correct
- Ensure proper table structure with required fields

### Seller Normalization Issues
- Check that `SellerNormalizationPipeline` is in the pipeline order (500)
- Verify logs show "Seller field processed" messages
- Check that items without sellers show "no seller found" in DynamoDB

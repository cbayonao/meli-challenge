#!/usr/bin/env python3
"""
Script to run the MercadoLibre Uruguay spiders with proper parameters
to avoid infinite loops and control the scraping process.
"""

import subprocess
import sys
import argparse
from pathlib import Path

def run_spider(spider_name, **kwargs):
    """Run a Scrapy spider with the given parameters"""
    
    # Build the command
    cmd = ["scrapy", "crawl", spider_name]
    
    # Add parameters
    for key, value in kwargs.items():
        if value is not None:
            cmd.extend(["-a", f"{key}={value}"])
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Spider completed successfully!")
        print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Spider failed with error code {e.returncode}")
        print("Error output:", e.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Run MercadoLibre Uruguay spiders")
    parser.add_argument("spider", choices=["identify", "collect"], 
                       help="Which spider to run: identify (scrapes offers) or collect (processes SQS messages)")
    
    # Parameters for identify spider
    parser.add_argument("--max-pages", type=int, default=5,
                       help="Maximum number of pages to scrape (default: 5)")
    parser.add_argument("--max-items", type=int, default=100,
                       help="Maximum number of items to scrape (default: 100)")
    
    # Parameters for collect spider
    parser.add_argument("--max-batches", type=int, default=50,
                       help="Maximum number of SQS batches to process (default: 50)")
    
    args = parser.parse_args()
    
    if args.spider == "identify":
        print("Running MeliUySpider (identify) to scrape offers...")
        success = run_spider(
            "meli-uy-identify",
            max_pages=args.max_pages,
            max_items=args.max_items
        )
    else:  # collect
        print("Running MeliUyCollectSpider to process SQS messages...")
        success = run_spider(
            "meli-uy-collect",
            max_batches=args.max_batches
        )
    
    if success:
        print(f"\n✅ {args.spider} spider completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ {args.spider} spider failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

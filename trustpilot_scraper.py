import requests
from bs4 import BeautifulSoup
import json
import time
import re
import csv
import argparse
import os
import logging
import urllib.robotparser
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# LEGAL COMPLIANCE WARNING
LEGAL_WARNING = """
⚠️  LEGAL COMPLIANCE WARNING ⚠️

This scraper may NOT be compliant with Trustpilot's Terms of Service and robots.txt.

RISKS:
- Trustpilot's robots.txt prohibits general automated access (User-agent: * Disallow: /)
- Terms of Service explicitly prohibit web scraping and data mining
- Potential legal action, account termination, or technical blocking

RECOMMENDATIONS:
1. Use Trustpilot's official Business API instead
2. Seek explicit written permission from Trustpilot
3. Consider alternative, compliant data sources

By continuing, you acknowledge these risks and take full legal responsibility.
Consult with legal counsel before proceeding.

Continue at your own risk.
"""

# Configuration parameters
CONFIG = {
    # Compliance settings
    'respect_robots_txt': True,
    'min_crawl_delay': 30,  # Minimum 30 seconds between requests
    'user_agent': 'TrustpilotParser/1.0 (Research Purpose; +https://github.com/yourproject)',
    'max_concurrent_requests': 1,  # Single-threaded for politeness
    
    # Browser settings
    'chrome_options': [
        '--headless',
        '--disable-gpu',
        '--window-size=1920,1080',
        '--disable-extensions',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled',
        '--user-agent=TrustpilotParser/1.0 (Research Purpose)'
    ],
    
    # Request settings
    'max_retries': 2,  # Reduced for politeness
    'page_load_timeout': 30,  # Increased timeout
    'retry_delay': 60,  # Increased delay between retries
    'page_delay': 30,  # Increased delay between pages
    
    # Debugging
    'save_debug_html': False,
    'debug_html_path': 'debug_page.html',
    'verbose': False,
    
    # Parsing settings
    'reviews_per_page': 20,
    
    # Pagination handling
    'empty_pages_before_stop': 2,  # Reduced for politeness
    'force_continue_to_estimated_pages': False,  # More conservative
    'min_reviews_last_page': 10,
    
    # Legal compliance
    'require_robots_check': True,
    'require_legal_acknowledgment': True,
    'log_all_requests': True,
}

# Robots.txt checker
class RobotsChecker:
    def __init__(self, user_agent=None):
        self.user_agent = user_agent or CONFIG['user_agent']
        self.robots_parsers = {}
    
    def can_fetch(self, url):
        """Check if the URL can be fetched according to robots.txt"""
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            if base_url not in self.robots_parsers:
                robots_url = urljoin(base_url, '/robots.txt')
                rp = urllib.robotparser.RobotFileParser()
                rp.set_url(robots_url)
                rp.read()
                self.robots_parsers[base_url] = rp
                logger.info(f"Loaded robots.txt from {robots_url}")
            
            can_fetch = self.robots_parsers[base_url].can_fetch(self.user_agent, url)
            logger.info(f"Robots.txt check for {url}: {'ALLOWED' if can_fetch else 'DISALLOWED'}")
            return can_fetch
            
        except Exception as e:
            logger.error(f"Error checking robots.txt for {url}: {e}")
            # Conservative approach: if we can't check, assume disallowed
            return False

def show_legal_warning():
    """Display legal warning and require acknowledgment"""
    print(LEGAL_WARNING)
    
    if CONFIG['require_legal_acknowledgment']:
        while True:
            response = input("Do you acknowledge these risks and wish to continue? (yes/no): ").lower().strip()
            if response == 'yes':
                logger.warning("User acknowledged legal risks and chose to continue")
                print("⚠️  Legal risks acknowledged. Proceeding with extreme caution.")
                break
            elif response == 'no':
                logger.info("User declined to proceed due to legal risks")
                print("Smart choice. Exiting.")
                exit(0)
            else:
                print("Please enter 'yes' or 'no'")

def check_compliance(url):
    """Check basic compliance requirements"""
    issues = []
    
    # Check robots.txt
    if CONFIG['respect_robots_txt']:
        robots_checker = RobotsChecker()
        if not robots_checker.can_fetch(url):
            issues.append("❌ ROBOTS.TXT VIOLATION: URL is disallowed by robots.txt")
    
    # Check if it's Trustpilot
    if 'trustpilot.com' in url.lower():
        issues.append("❌ TRUSTPILOT ToS VIOLATION: Terms of Service prohibit automated access")
        issues.append("❌ LEGAL RISK: High risk of legal action or technical blocking")
    
    # Check crawl delay
    if CONFIG['page_delay'] < 30:
        issues.append("⚠️  INSUFFICIENT DELAY: Recommend minimum 30 seconds between requests")
    
    return issues

# Function to update config from command line arguments
def update_config_from_args(args):
    """Update the CONFIG dictionary based on command line arguments"""
    if args.debug:
        CONFIG['verbose'] = True
        CONFIG['save_debug_html'] = True
    
    if args.debug_html_path:
        CONFIG['debug_html_path'] = args.debug_html_path
    
    if args.page_load_timeout:
        CONFIG['page_load_timeout'] = args.page_load_timeout
    
    if args.retry_delay:
        CONFIG['retry_delay'] = max(args.retry_delay, 60)  # Minimum 60 seconds
    
    if args.page_delay:
        CONFIG['page_delay'] = max(args.page_delay, 30)  # Minimum 30 seconds
    
    if args.max_retries:
        CONFIG['max_retries'] = min(args.max_retries, 3)  # Maximum 3 retries

    # Force compliance overrides
    if args.skip_robots_check:
        CONFIG['respect_robots_txt'] = False
        logger.warning("⚠️  Robots.txt checking disabled by user")
    
    if args.skip_legal_warning:
        CONFIG['require_legal_acknowledgment'] = False
        logger.warning("⚠️  Legal warning disabled by user")

def log_request(url, response_code=None, error=None):
    """Log all requests for audit purposes"""
    if CONFIG['log_all_requests']:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'url': url,
            'response_code': response_code,
            'error': str(error) if error else None,
            'user_agent': CONFIG['user_agent']
        }
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Write to audit log
        with open('logs/request_audit.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')

def get_reviews_with_selenium(url, star_filter=None, max_pages=None):
    """Extract reviews from Trustpilot using Selenium with compliance features"""
    
    # Legal and compliance checks
    show_legal_warning()
    
    compliance_issues = check_compliance(url)
    if compliance_issues:
        print("\n🚨 COMPLIANCE ISSUES DETECTED:")
        for issue in compliance_issues:
            print(f"   {issue}")
        print()
        
        if CONFIG['require_robots_check'] and any('ROBOTS.TXT VIOLATION' in issue for issue in compliance_issues):
            print("❌ Cannot proceed: robots.txt violations detected")
            print("Use --skip-robots-check to override (NOT RECOMMENDED)")
            return []
    
    all_reviews = []
    page_num = 1
    max_retries = CONFIG['max_retries']
    last_page_reached = False
    robots_checker = RobotsChecker() if CONFIG['respect_robots_txt'] else None
    
    # Set up Chrome options with compliance-focused user agent
    chrome_options = Options()
    for option in CONFIG['chrome_options']:
        chrome_options.add_argument(option)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Initial compliance check
        if robots_checker and not robots_checker.can_fetch(url):
            logger.error("❌ Robots.txt check failed. Aborting.")
            return []
        
        # Load first page
        main_url = url.split('?')[0] if '?' in url else url
        base_url = url
        
        logger.info(f"🚀 Starting compliant crawl of {main_url}")
        log_request(main_url)
        
        driver.get(main_url)
        
        # Respectful delay after initial load
        logger.info(f"⏳ Respectful delay: {CONFIG['page_delay']} seconds")
        time.sleep(CONFIG['page_delay'])
        
        try:
            WebDriverWait(driver, CONFIG['page_load_timeout']).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            # Try to get total review count (for estimation only)
            total_reviews = 0
            try:
                total_reviews_element = driver.find_elements(By.CSS_SELECTOR, ".typography_body-l, .typography_heading-s, span[data-reviews-count-typography]")
                
                for element in total_reviews_element:
                    try:
                        text = element.text.strip()
                        if "review" in text.lower():
                            matches = re.search(r'(\d[\d,]+)', text)
                            if matches:
                                total_reviews = int(matches.group(1).replace(',', ''))
                                logger.info(f"📊 Estimated total reviews: {total_reviews}")
                                break
                    except Exception as e:
                        logger.debug(f"Error parsing review count: {e}")
                        
            except Exception as e:
                logger.warning(f"Could not determine total review count: {e}")
        
        except Exception as e:
            logger.error(f"Error loading initial page: {e}")
            return []
        
        # Main scraping loop with compliance features
        while not last_page_reached and (not max_pages or page_num <= max_pages):
            
            # Construct page URL
            if '?' in base_url:
                if 'page=' in base_url:
                    page_url = re.sub(r'page=\d+', f'page={page_num}', base_url)
                else:
                    page_url = f"{base_url}&page={page_num}"
            else:
                page_url = f"{base_url}?page={page_num}"
            
            # Check robots.txt for this specific page
            if robots_checker and not robots_checker.can_fetch(page_url):
                logger.error(f"❌ Page {page_num} disallowed by robots.txt: {page_url}")
                break
            
            logger.info(f"📄 Processing page {page_num}: {page_url}")
            log_request(page_url)
            
            # Implement respectful retry logic
            retry_count = 0
            page_loaded = False
            
            while retry_count < max_retries and not page_loaded:
                try:
                    driver.get(page_url)
                    log_request(page_url, response_code=200)
                    
                    # Check for 404 or error pages
                    if "404" in driver.title or "Whoops" in driver.title:
                        logger.info(f"📄 Reached end of available pages at page {page_num}")
                        last_page_reached = True
                        break
                    
                    # Wait for content
                    WebDriverWait(driver, CONFIG['page_load_timeout']).until(
                        EC.presence_of_element_located((By.TAG_NAME, "article"))
                    )
                    page_loaded = True
                    
                except TimeoutException:
                    logger.warning(f"⏰ Timeout loading page {page_num}, attempt {retry_count + 1}")
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.info(f"⏳ Waiting {CONFIG['retry_delay']} seconds before retry")
                        time.sleep(CONFIG['retry_delay'])
                    
                except Exception as e:
                    logger.error(f"❌ Error loading page {page_num}: {e}")
                    log_request(page_url, error=e)
                    retry_count += 1
                    if retry_count < max_retries:
                        time.sleep(CONFIG['retry_delay'])
            
            if last_page_reached or not page_loaded:
                break
            
            # Save debug HTML for first page only
            if page_num == 1 and CONFIG['save_debug_html']:
                with open(CONFIG['debug_html_path'], "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                logger.info(f"💾 Debug HTML saved to {CONFIG['debug_html_path']}")
            
            # Extract reviews from current page
            try:
                review_elements = driver.find_elements(By.TAG_NAME, "article")
                
                if not review_elements:
                    logger.warning(f"📭 No reviews found on page {page_num}")
                    last_page_reached = True
                    break
                
                logger.info(f"🔍 Found {len(review_elements)} review elements on page {page_num}")
                
                page_reviews = []
                for review_element in review_elements:
                    try:
                        review = extract_review_data(review_element, page_num, page_url)
                        
                        # Apply star filter if specified
                        if star_filter and review.get('stars') not in star_filter:
                            continue
                            
                        if review and (review.get('text') or review.get('stars')):
                            page_reviews.append(review)
                            
                    except Exception as e:
                        logger.warning(f"⚠️  Error extracting review: {e}")
                
                all_reviews.extend(page_reviews)
                logger.info(f"✅ Extracted {len(page_reviews)} reviews from page {page_num}")
                
                # Check if we've reached the end
                if len(review_elements) < CONFIG['reviews_per_page']:
                    logger.info(f"📄 Reached last page (fewer reviews than expected)")
                    last_page_reached = True
                
            except Exception as e:
                logger.error(f"❌ Error processing page {page_num}: {e}")
                break
            
            # Move to next page with respectful delay
            page_num += 1
            
            if not last_page_reached:
                logger.info(f"⏳ Respectful delay: {CONFIG['page_delay']} seconds before next page")
                time.sleep(CONFIG['page_delay'])
    
    finally:
        driver.quit()
        logger.info("🔄 Browser session closed")
    
    # Final summary with compliance notes
    logger.info(f"\n📊 SCRAPING SUMMARY")
    logger.info(f"   Pages processed: {page_num - 1}")
    logger.info(f"   Reviews extracted: {len(all_reviews)}")
    logger.info(f"   Total delay time: {(page_num - 1) * CONFIG['page_delay']} seconds")
    logger.info(f"   Average delay: {CONFIG['page_delay']} seconds per page")
    
    if total_reviews and len(all_reviews) < total_reviews * 0.1:
        logger.warning("⚠️  Low extraction rate may indicate blocking or rate limiting")
    
    return all_reviews

def extract_review_data(review_element, page_num, page_url):
    """Extract data from a single review element"""
    review = {
        'stars': None,
        'title': '',
        'text': '',
        'company_response': '',
        'reviewer': {
            'name': '',
            'location': '',
            'reviews_count': None,
        },
        'date': {
            'published': '',
            'experience': ''
        },
        'metadata': {
            'verified': False,
            'useful_votes': 0,
            'page_number': page_num,
            'source_url': page_url,
            'extracted_timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'extraction_method': 'selenium'
        }
    }
    
    # Extract star rating
    try:
        rating_element = review_element.find_element(By.CSS_SELECTOR, "[data-service-review-rating]")
        rating_text = rating_element.get_attribute("data-service-review-rating")
        star_rating = int(re.search(r'\d+', rating_text).group()) if rating_text else None
        review['stars'] = star_rating
    except:
        try:
            stars_element = review_element.find_element(By.CSS_SELECTOR, "div.star-rating")
            rating_text = stars_element.get_attribute("aria-label")
            star_rating = int(re.search(r'\d+', rating_text).group()) if rating_text else None
            review['stars'] = star_rating
        except:
            pass
    
    # Extract review title
    try:
        title_element = review_element.find_element(By.CSS_SELECTOR, "h2[data-service-review-title-typography], .review-content__title, .typography_heading-s")
        review['title'] = title_element.text.strip()
    except:
        pass
    
    # Extract review text
    try:
        review_content = review_element.find_element(By.CSS_SELECTOR, "p[data-service-review-text-typography], p.review-content__text, .typography_body-l")
        review['text'] = review_content.text.strip()
    except:
        pass
    
    # Extract reviewer name
    try:
        reviewer_element = review_element.find_element(By.CSS_SELECTOR, "span.typography_heading-xxs, .consumer-information__name")
        review['reviewer']['name'] = reviewer_element.text.strip()
    except:
        review['reviewer']['name'] = "Anonymous"
    
    # Extract review date
    try:
        date_element = review_element.find_element(By.CSS_SELECTOR, "time")
        review['date']['published'] = date_element.get_attribute("datetime")
    except:
        pass
    
    return review

def get_reviews(url, star_filter=None, max_pages=None):
    """Legacy function that uses requests+BeautifulSoup. Now we use Selenium."""
    # print("Using Selenium...")
    return get_reviews_with_selenium(url, star_filter, max_pages)

def save_reviews_json(reviews, filename):
    """Save reviews to a JSON file with indentation for readability"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'total_reviews': len(reviews),
                'extracted_date': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'version': '2.0'
            },
            'reviews': reviews
        }, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(reviews)} reviews to {filename}")

def save_reviews_csv(reviews, filename):
    """Save reviews to a CSV file with flattened structure"""
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        # Define the CSV fields - flatten the nested structure
        fieldnames = [
            'stars', 'title', 'text', 'company_response', 
            'reviewer_name', 'reviewer_location', 'reviewer_reviews_count',
            'date_published', 'date_experience', 
            'verified', 'useful_votes', 'page_number'
        ]
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        # Write the header
        writer.writeheader()
        
        # Write the data - flatten the nested structure
        for review in reviews:
            flat_review = {
                'stars': review.get('stars'),
                'title': review.get('title', ''),
                'text': review.get('text', ''),
                'company_response': review.get('company_response', ''),
                'reviewer_name': review.get('reviewer', {}).get('name', ''),
                'reviewer_location': review.get('reviewer', {}).get('location', ''),
                'reviewer_reviews_count': review.get('reviewer', {}).get('reviews_count'),
                'date_published': review.get('date', {}).get('published', ''),
                'date_experience': review.get('date', {}).get('experience', ''),
                'verified': review.get('metadata', {}).get('verified', False),
                'useful_votes': review.get('metadata', {}).get('useful_votes', 0),
                'page_number': review.get('metadata', {}).get('page_number')
            }
            writer.writerow(flat_review)
    
    print(f"Saved {len(reviews)} reviews to {filename}")

def parse_arguments():
    """Parse command line arguments with compliance options"""
    parser = argparse.ArgumentParser(
        description='Scrape reviews from Trustpilot (⚠️  LEGAL RISKS INVOLVED)',
        epilog='⚠️  WARNING: This tool may violate Trustpilot\'s Terms of Service. Use at your own risk.'
    )
    
    # Required arguments
    parser.add_argument('url', help='URL of the Trustpilot reviews page')
    
    # Optional arguments
    parser.add_argument('-o', '--output', default='trustpilot_reviews.json', 
                        help='Output file path (default: trustpilot_reviews.json)')
    parser.add_argument('-f', '--format', choices=['json', 'csv'], default='json',
                        help='Output format: json or csv (default: json)')
    parser.add_argument('-s', '--stars', type=int, nargs='+', choices=[1, 2, 3, 4, 5],
                        help='Filter by star ratings (e.g., -s 1 4 5 for 1, 4, and 5 star reviews)')
    parser.add_argument('-p', '--max-pages', type=int,
                        help='Maximum number of pages to scrape (default: all available pages)')
    
    # Compliance options
    compliance_group = parser.add_argument_group('Compliance Options (⚠️  USE WITH CAUTION)')
    compliance_group.add_argument('--skip-robots-check', action='store_true',
                                help='Skip robots.txt compliance check (NOT RECOMMENDED)')
    compliance_group.add_argument('--skip-legal-warning', action='store_true',
                                help='Skip legal warning prompt (NOT RECOMMENDED)')
    
    # Debug configuration arguments
    debug_group = parser.add_argument_group('Debug Options')
    debug_group.add_argument('--debug', action='store_true',
                            help='Enable debug mode (verbose output and HTML saving)')
    debug_group.add_argument('--debug-html-path', type=str,
                            help='Path to save debug HTML (default: debug_page.html)')
    
    # Performance tuning arguments
    perf_group = parser.add_argument_group('Performance Options')
    perf_group.add_argument('--page-load-timeout', type=int,
                           help='Timeout for page loading in seconds (default: 30)')
    perf_group.add_argument('--retry-delay', type=int,
                           help='Delay between retries in seconds (minimum: 60)')
    perf_group.add_argument('--page-delay', type=int,
                           help='Delay between pages in seconds (minimum: 30)')
    perf_group.add_argument('--max-retries', type=int,
                           help='Maximum number of retries per page (maximum: 3)')
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()
    
    # Update CONFIG with command line arguments
    update_config_from_args(args)
    
    # Get the URL
    url = args.url
    
    # Check if stars are already in the URL
    if not ('stars=' in url) and args.stars:
        # Add star filter to URL if not already present
        stars_param = '&'.join([f'stars={star}' for star in args.stars])
        if '?' in url:
            url += f'&{stars_param}'
        else:
            url += f'?{stars_param}'
    
    # Get the reviews
    reviews = get_reviews(url, args.stars, args.max_pages)
    
    # Save the reviews in the specified format
    output_file = args.output
    
    # Ensure output file has the correct extension
    if args.format == 'json' and not output_file.endswith('.json'):
        output_file = os.path.splitext(output_file)[0] + '.json'
    elif args.format == 'csv' and not output_file.endswith('.csv'):
        output_file = os.path.splitext(output_file)[0] + '.csv'
    
    # Save in the appropriate format
    if args.format == 'json':
        save_reviews_json(reviews, output_file)
    else:  # csv
        save_reviews_csv(reviews, output_file)
    
    print(f"Extracted {len(reviews)} reviews in total")

if __name__ == "__main__":
    main() 
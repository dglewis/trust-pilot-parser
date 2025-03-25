import requests
from bs4 import BeautifulSoup
import json
import time
import re
import csv
import argparse
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configuration parameters
CONFIG = {
    # Browser settings
    'chrome_options': [
        '--headless',
        '--disable-gpu',
        '--window-size=1920,1080',
        '--disable-extensions',
        '--no-sandbox',
        '--disable-dev-shm-usage'
    ],
    
    # Request settings
    'max_retries': 3,
    'page_load_timeout': 15,
    'retry_delay': 2,
    'page_delay': 2,
    
    # Debugging
    'save_debug_html': False,  # Default to false
    'debug_html_path': 'debug_page.html',
    'verbose': False,  # Default to false
    
    # Parsing settings
    'reviews_per_page': 20,
    
    # Pagination handling
    'empty_pages_before_stop': 3,  # Number of consecutive empty pages before stopping
    'force_continue_to_estimated_pages': True,  # Continue until we reach estimated page count
    'min_reviews_last_page': 10  # If we find fewer than this number of reviews, assume we're on the last page
}

# Function to update config from command line arguments
def update_config_from_args(args):
    """Update the CONFIG dictionary based on command line arguments"""
    # Set debug mode if specified
    if args.debug:
        CONFIG['verbose'] = True
        CONFIG['save_debug_html'] = True
    
    if args.debug_html_path:
        CONFIG['debug_html_path'] = args.debug_html_path
    
    if args.page_load_timeout:
        CONFIG['page_load_timeout'] = args.page_load_timeout
    
    if args.retry_delay:
        CONFIG['retry_delay'] = args.retry_delay
    
    if args.page_delay:
        CONFIG['page_delay'] = args.page_delay
    
    if args.max_retries:
        CONFIG['max_retries'] = args.max_retries

def get_reviews_with_selenium(url, star_filter=None, max_pages=None):
    """Extract reviews from Trustpilot using Selenium (for JavaScript rendered content)"""
    
    all_reviews = []
    page_num = 1
    max_retries = CONFIG['max_retries']
    last_page_reached = False
    highest_page_seen = 1
    reviews_by_page = {}  # Track reviews found on each page for debugging
    consecutive_empty_pages = 0  # Track consecutive pages with no reviews
    estimated_total_pages = 0  # Will be calculated from total_reviews
    
    # Set up Chrome options
    chrome_options = Options()
    for option in CONFIG['chrome_options']:
        chrome_options.add_argument(option)
    
    # Initialize the driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # First, load the main page to get total review count and calculate total pages
        main_url = url.split('?')[0] if '?' in url else url
        base_url = url
        
        driver.get(main_url)
        try:
            # Wait for page to load
            WebDriverWait(driver, CONFIG['page_load_timeout']).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            # Try to find the total review count
            total_reviews_element = driver.find_elements(By.CSS_SELECTOR, ".typography_body-l, .typography_heading-s, span[data-reviews-count-typography]")
            total_reviews = 0
            
            # First try to find the review count from the main page
            for element in total_reviews_element:
                try:
                    text = element.text.strip()
                    if "review" in text.lower():
                        # Try to extract the number from formats like "371 reviews" or "371 total reviews"
                        matches = re.search(r'(\d[\d,]+)', text)
                        if matches:
                            # Remove commas and convert to int
                            total_reviews = int(matches.group(1).replace(',', ''))
                            print(f"Found total reviews from main page: {total_reviews}")
                            break
                except Exception as e:
                    if CONFIG['verbose']:
                        print(f"Error parsing review count text: {e}")
            
            # If not found in text, look for specific attribute
            if total_reviews == 0:
                try:
                    count_elements = driver.find_elements(By.CSS_SELECTOR, "[data-service-review-count], [data-reviews-count-typography]")
                    for elem in count_elements:
                        data_count = elem.get_attribute("data-service-review-count")
                        if data_count and data_count.isdigit():
                            total_reviews = int(data_count)
                            print(f"Found total reviews from data attribute: {total_reviews}")
                            break
                except Exception as e:
                    if CONFIG['verbose']:
                        print(f"Error extracting review count from data attribute: {e}")
                        
            if total_reviews:
                # Calculate estimated pages based on reviews per page
                estimated_total_pages = (total_reviews + CONFIG['reviews_per_page'] - 1) // CONFIG['reviews_per_page']
                print(f"Found approximately {total_reviews} total reviews across ~{estimated_total_pages} pages")
            else:
                print("Couldn't determine total review count, will iterate until no more pages are found")
                
            # Try to find the maximum page number from pagination
            try:
                pagination_elements = driver.find_elements(By.CSS_SELECTOR, "nav[aria-label='Pagination'] button, nav[aria-label='Pagination'] a, button[data-pagination-button-page], a[data-pagination-button-page]")
                max_page = 1
                for element in pagination_elements:
                    text = element.text.strip()
                    if text.isdigit():
                        page_num_int = int(text)
                        if page_num_int > max_page:
                            max_page = page_num_int
                
                if max_page > 1:
                    print(f"Detected {max_page} pages in pagination")
                    highest_page_seen = max_page
                    
                    # If we found pagination but couldn't determine total reviews, estimate based on highest page seen
                    if total_reviews == 0:
                        estimated_total_pages = max_page
                        total_reviews = estimated_total_pages * CONFIG['reviews_per_page']
                        print(f"Estimating {total_reviews} total reviews from highest visible page number ({max_page})")
            except Exception as e:
                print(f"Error detecting max pages from pagination: {e}")
                
        except Exception as e:
            print(f"Error determining total pages: {e}")
        
        # Now iterate through all pages with direct URL access
        while not last_page_reached:
            if max_pages and page_num > max_pages:
                print(f"Reached maximum requested page limit ({max_pages})")
                break
            
            # Check if the page is a 404 by looking at the URL
            if page_num > 1 and "page=" + str(page_num - 1) in driver.current_url and "404" in driver.title:
                print(f"Detected 404 page after page {page_num-1}. Stopping scraping.")
                break
            
            # Construct page URL - ensure we're using the right format
            if '?' in base_url:
                if 'page=' in base_url:
                    # Replace existing page parameter
                    page_url = re.sub(r'page=\d+', f'page={page_num}', base_url)
                else:
                    # Add page parameter
                    page_url = f"{base_url}&page={page_num}"
            else:
                page_url = f"{base_url}?page={page_num}"
                
            print(f"Scraping page {page_num}: {page_url}")
            
            # Load the page with retry logic
            retry_count = 0
            page_loaded = False
            
            while retry_count < max_retries and not page_loaded:
                try:
                    driver.get(page_url)
                    
                    # Check for 404 page
                    if "404" in driver.title or "Whoops" in driver.title:
                        print(f"Reached a 404 error page. Stopping at page {page_num-1}.")
                        last_page_reached = True
                        break
                    
                    # Wait for content to load - try multiple selectors
                    try:
                        WebDriverWait(driver, CONFIG['page_load_timeout']).until(
                            EC.presence_of_element_located((By.TAG_NAME, "article"))
                        )
                        page_loaded = True
                    except TimeoutException:
                        try:
                            WebDriverWait(driver, CONFIG['page_load_timeout'] - 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "div.styles_reviewCard__hcAvl"))
                            )
                            page_loaded = True
                        except TimeoutException:
                            # Check for 404 page again after timeout
                            if "404" in driver.title or "Whoops" in driver.title:
                                print(f"Reached a 404 error page after timeout. Stopping at page {page_num-1}.")
                                last_page_reached = True
                                break
                                
                            print(f"Timeout waiting for page {page_num} to load, retrying...")
                            retry_count += 1
                            time.sleep(CONFIG['retry_delay'])  # Wait before retry
                
                except Exception as e:
                    print(f"Error loading page {page_num}: {e}")
                    retry_count += 1
                    time.sleep(CONFIG['retry_delay'])  # Wait before retry
            
            # If we've hit a 404 page, stop
            if last_page_reached:
                break
                
            if not page_loaded:
                print(f"Failed to load page {page_num} after {max_retries} attempts")
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= CONFIG['empty_pages_before_stop']:
                    print(f"Stopping after {consecutive_empty_pages} consecutive failed page loads")
                    break
                page_num += 1
                continue
                
            # Save HTML for debugging (first page only)
            if page_num == 1 and CONFIG['save_debug_html']:
                with open(CONFIG['debug_html_path'], "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"Saved first page HTML to {CONFIG['debug_html_path']} for inspection")
            
            # Check for "no reviews found" message that indicates we've gone too far
            try:
                no_results = driver.find_elements(By.CSS_SELECTOR, 
                                              "p.typography_body-l:contains('No reviews matching'), div.noResultsContainer, div:contains('No reviews found')")
                if no_results:
                    print(f"Found 'No reviews' message on page {page_num}")
                    last_page_reached = True
                    break
            except Exception as e:
                if CONFIG['verbose']:
                    print(f"Error checking for no results: {e}")
            
            # Detect if we've been redirected to another page (indicating we've gone beyond the last page)
            current_url = driver.current_url
            url_page_match = re.search(r'page=(\d+)', current_url)
            if url_page_match:
                actual_page = int(url_page_match.group(1))
                if actual_page != page_num:
                    print(f"Requested page {page_num} but got redirected to page {actual_page} - we've likely gone beyond the last page")
                    last_page_reached = True
                    break
                
            # Find all reviews
            try:
                # Try different possible selectors
                review_elements = driver.find_elements(By.TAG_NAME, "article")
                
                if not review_elements:
                    print("No reviews found with article tag. Trying alternative selectors...")
                    review_elements = driver.find_elements(By.CSS_SELECTOR, "div.styles_reviewCard__hcAvl")
                
                if not review_elements:
                    review_elements = driver.find_elements(By.CSS_SELECTOR, "div.review-card")
                
                if not review_elements:
                    print("No reviews found on this page. This may be the last page.")
                    last_page_reached = True
                    break
                
                # If we're on a page that has fewer reviews than expected, we're likely on the last page
                if len(review_elements) < CONFIG['reviews_per_page'] and page_num > 1:
                    print(f"Found only {len(review_elements)} reviews on page {page_num} (fewer than standard {CONFIG['reviews_per_page']})")
                    print(f"This indicates we're on the last page of reviews")
                    last_page_reached = True
                
                print(f"Found {len(review_elements)} review elements on page {page_num}")
                
                # Initialize page stats
                reviews_by_page[page_num] = {
                    'raw_elements': len(review_elements),
                    'extracted': 0,
                    'filtered': 0,
                    'errors': 0
                }
                
                # Process each review element
                for review_element in review_elements:
                    try:
                        # Create a comprehensive review object
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
                                'source_url': current_url
                            }
                        }
                        
                        # Extract star rating
                        try:
                            # Try finding the rating from data attributes
                            rating_element = review_element.find_element(By.CSS_SELECTOR, "[data-service-review-rating]")
                            rating_text = rating_element.get_attribute("data-service-review-rating")
                            star_rating = int(re.search(r'\d+', rating_text).group()) if rating_text else None
                            review['stars'] = star_rating
                        except:
                            # Try finding from star images
                            try:
                                stars_element = review_element.find_element(By.CSS_SELECTOR, "div.star-rating")
                                rating_text = stars_element.get_attribute("aria-label")
                                star_rating = int(re.search(r'\d+', rating_text).group()) if rating_text else None
                                review['stars'] = star_rating
                            except:
                                # Try one more way to find stars (look for the star images)
                                try:
                                    star_images = review_element.find_elements(By.CSS_SELECTOR, "img.star-rating__star")
                                    if star_images:
                                        filled_stars = [img for img in star_images if "filled" in img.get_attribute("alt").lower()]
                                        review['stars'] = len(filled_stars)
                                except:
                                    pass
                        
                        # Skip if not in the requested star filter
                        if star_filter and review['stars'] not in star_filter:
                            reviews_by_page[page_num]['filtered'] += 1
                            continue
                            
                        # Extract review title
                        try:
                            title_element = review_element.find_element(By.CSS_SELECTOR, "h2[data-service-review-title-typography], .review-content__title, .typography_heading-s")
                            review['title'] = title_element.text.strip()
                        except Exception as e:
                            if CONFIG['verbose']:
                                print(f"Error extracting title: {e}")
                            
                        # Extract review text
                        try:
                            review_content = review_element.find_element(By.CSS_SELECTOR, "p[data-service-review-text-typography], p.review-content__text, .typography_body-l")
                            review['text'] = review_content.text.strip()
                        except Exception as e:
                            if CONFIG['verbose']:
                                print(f"Error extracting review text: {e}")
                        
                        # Extract company response
                        try:
                            response_element = review_element.find_element(By.CSS_SELECTOR, "div.review-business-reply, div[data-service-review-business-response]")
                            response_text = response_element.text.strip()
                            # Clean up the response
                            if "Reply from" in response_text:
                                parts = response_text.split("Reply from", 1)
                                reply_from = parts[1].split("\n", 1)[0].strip() if len(parts) > 1 else ""
                                actual_response = parts[1].split("\n", 1)[1].strip() if len(parts) > 1 and "\n" in parts[1] else parts[1].strip()
                                review['company_response'] = actual_response
                                review['metadata']['company_reply_name'] = reply_from
                            else:
                                review['company_response'] = response_text
                        except Exception as e:
                            if CONFIG['verbose']:
                                print(f"Error extracting company response: {e}")
                        
                        # Extract reviewer name and location
                        try:
                            reviewer_element = review_element.find_element(By.CSS_SELECTOR, "span.typography_heading-xxs, .consumer-information__name")
                            review['reviewer']['name'] = reviewer_element.text.strip()
                            
                            try:
                                location_element = review_element.find_element(By.CSS_SELECTOR, ".consumer-information__location")
                                review['reviewer']['location'] = location_element.text.strip()
                            except Exception as e:
                                if CONFIG['verbose']:
                                    print(f"Error extracting reviewer location: {e}")
                                
                            # Extract review count if available
                            try:
                                reviews_count_element = review_element.find_element(By.CSS_SELECTOR, ".consumer-information__review-count")
                                count_text = reviews_count_element.text.strip()
                                count_match = re.search(r'(\d+)', count_text)
                                if count_match:
                                    review['reviewer']['reviews_count'] = int(count_match.group(1))
                            except Exception as e:
                                if CONFIG['verbose']:
                                    print(f"Error extracting reviewer count: {e}")
                                
                        except Exception as e:
                            if CONFIG['verbose']:
                                print(f"Error extracting reviewer info: {e}")
                            review['reviewer']['name'] = "Anonymous"
                            
                        # Extract review date (published)
                        try:
                            date_element = review_element.find_element(By.CSS_SELECTOR, "time")
                            review['date']['published'] = date_element.get_attribute("datetime")
                        except Exception as e:
                            # Try an alternative way to get the date
                            try:
                                # Look for date text in a more general way
                                date_elements = review_element.find_elements(By.CSS_SELECTOR, "[data-service-review-date-time-ago]")
                                if date_elements:
                                    date_attr = date_elements[0].get_attribute("data-service-review-date-time-ago")
                                    if date_attr:
                                        # Date might be in a different format, but we'll store it as is
                                        review['date']['published'] = date_attr
                            except:
                                pass
                                
                            if CONFIG['verbose']:
                                print(f"Error extracting review date: {e}")
                            
                        # Extract experience date if available
                        try:
                            exp_date_elements = review_element.find_elements(By.CSS_SELECTOR, ".review-content-header__dates")
                            for elem in exp_date_elements:
                                if "Date of experience" in elem.text:
                                    exp_date_text = elem.text.replace("Date of experience:", "").strip()
                                    review['date']['experience'] = exp_date_text
                                    break
                        except Exception as e:
                            if CONFIG['verbose']:
                                print(f"Error extracting experience date: {e}")
                        
                        # Extract verification status
                        try:
                            verified_elements = review_element.find_elements(By.CSS_SELECTOR, ".review-content-header__verification")
                            review['metadata']['verified'] = len(verified_elements) > 0 and "verified" in verified_elements[0].text.lower()
                        except Exception as e:
                            if CONFIG['verbose']:
                                print(f"Error extracting verification status: {e}")
                            
                        # Extract useful/helpful votes
                        try:
                            votes_elements = review_element.find_elements(By.CSS_SELECTOR, ".useful-count")
                            if votes_elements:
                                votes_text = votes_elements[0].text.strip()
                                votes_match = re.search(r'(\d+)', votes_text)
                                if votes_match:
                                    review['metadata']['useful_votes'] = int(votes_match.group(1))
                        except Exception as e:
                            if CONFIG['verbose']:
                                print(f"Error extracting useful votes: {e}")
                            
                        # Extract any tags/categories
                        try:
                            tags_elements = review_element.find_elements(By.CSS_SELECTOR, ".review-tag")
                            if tags_elements:
                                review['metadata']['tags'] = [tag.text.strip() for tag in tags_elements]
                        except Exception as e:
                            if CONFIG['verbose']:
                                print(f"Error extracting tags: {e}")
                        
                        # Only add reviews with text or a star rating
                        if review['text'] or review['stars']:
                            all_reviews.append(review)
                            reviews_by_page[page_num]['extracted'] += 1
                            if CONFIG['verbose']:
                                print(f"Extracted review: {review['stars']} stars, {len(review['text'])} chars")
                        else:
                            reviews_by_page[page_num]['filtered'] += 1
                            if CONFIG['verbose']:
                                print(f"Skipping review - no text or star rating")
                    
                    except Exception as e:
                        print(f"Error extracting review data: {e}")
                        reviews_by_page[page_num]['errors'] += 1
                
                # Report page stats
                print(f"Page {page_num} summary: found {reviews_by_page[page_num]['raw_elements']} elements, "
                      f"extracted {reviews_by_page[page_num]['extracted']} reviews, "
                      f"filtered {reviews_by_page[page_num]['filtered']}, "
                      f"errors {reviews_by_page[page_num]['errors']}")
                
                # If we got no reviews on this page (but found review elements), something's wrong
                if reviews_by_page[page_num]['extracted'] == 0 and reviews_by_page[page_num]['raw_elements'] > 0:
                    print("WARNING: Found review elements but couldn't extract any valid reviews.")
                    if page_num == 1:
                        print("This is the first page, so there might be a problem with the page structure.")
                        print("Check the HTML content in debug_page.html")
                
                # If this is the last page, break out
                if last_page_reached:
                    break
                
            except Exception as e:
                print(f"Error finding reviews: {e}")
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= CONFIG['empty_pages_before_stop']:
                    print(f"Stopping after {consecutive_empty_pages} consecutive error pages")
                    break
                page_num += 1
                continue
            
            # Move to the next page
            page_num += 1
            # print(f"Moving to page {page_num}")
            time.sleep(CONFIG['page_delay'])  # Delay between pages to be polite
    
    finally:
        # Clean up
        driver.quit()
    
    # Final summary
    print(f"\n--- SCRAPING SUMMARY ---")
    print(f"Total pages processed: {len(reviews_by_page)}")
    print(f"Total reviews extracted: {len(all_reviews)}")
    
    # Calculate what percentage of the claimed total we extracted
    if total_reviews > 0:
        percentage = (len(all_reviews) / total_reviews) * 100
        print(f"Extracted {percentage:.1f}% of the claimed {total_reviews} total reviews")
        if percentage < 90:
            print("NOTE: The claimed total may include reviews that are not publicly accessible")
            print("      Trustpilot may archive older reviews or filter some based on their criteria")
    
    # Calculate per-page statistics
    for page, stats in reviews_by_page.items():
        if stats['raw_elements'] > 0:
            success_rate = (stats['extracted'] / stats['raw_elements']) * 100
            print(f"Page {page}: {success_rate:.1f}% extraction rate ({stats['extracted']}/{stats['raw_elements']})")
    
    if estimated_total_pages > 0:
        expected_reviews = estimated_total_pages * CONFIG['reviews_per_page']
        coverage_percentage = (len(all_reviews) / expected_reviews) * 100
        print(f"Coverage: {coverage_percentage:.1f}% of expected reviews (estimated {expected_reviews} reviews)")
    
    raw_elements_total = sum(page['raw_elements'] for page in reviews_by_page.values())
    filtered_total = sum(page['filtered'] for page in reviews_by_page.values())
    errors_total = sum(page['errors'] for page in reviews_by_page.values())
    
    print(f"Total review elements found: {raw_elements_total}")
    print(f"Total reviews filtered out: {filtered_total}")
    print(f"Total extraction errors: {errors_total}")
    
    if len(all_reviews) < raw_elements_total - filtered_total:
        print(f"WARNING: Expected {raw_elements_total - filtered_total} reviews but only extracted {len(all_reviews)}")
        print("Some reviews may have failed to extract without raising errors.")
    
    return all_reviews

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
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Scrape reviews from Trustpilot')
    
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
    parser.add_argument('--pretty', action='store_true',
                        help='Output pretty-printed JSON (default for JSON output)')
    
    # Debug configuration arguments
    debug_group = parser.add_argument_group('Debug Options')
    debug_group.add_argument('--debug', action='store_true',
                            help='Enable debug mode (verbose output and HTML saving)')
    debug_group.add_argument('--debug-html-path', type=str,
                            help='Path to save debug HTML (default: debug_page.html)')
    
    # Performance tuning arguments
    perf_group = parser.add_argument_group('Performance Options')
    perf_group.add_argument('--page-load-timeout', type=int,
                           help='Timeout for page loading in seconds (default: 15)')
    perf_group.add_argument('--retry-delay', type=int,
                           help='Delay between retries in seconds (default: 2)')
    perf_group.add_argument('--page-delay', type=int,
                           help='Delay between pages in seconds (default: 2)')
    perf_group.add_argument('--max-retries', type=int,
                           help='Maximum number of retries per page (default: 3)')
    
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
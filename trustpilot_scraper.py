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
    'save_debug_html': True,
    'debug_html_path': 'debug_page.html',
    
    # Parsing settings
    'reviews_per_page': 20
}

def get_reviews_with_selenium(url, star_filter=None, max_pages=None):
    """Extract reviews from Trustpilot using Selenium (for JavaScript rendered content)"""
    
    all_reviews = []
    page_num = 1
    max_retries = CONFIG['max_retries']
    last_page_reached = False
    highest_page_seen = 1
    
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
            total_reviews_element = driver.find_elements(By.CSS_SELECTOR, ".typography_body-l, .typography_heading-s")
            total_reviews = 0
            for element in total_reviews_element:
                if "total" in element.text:
                    try:
                        total_reviews = int(re.search(r'(\d+)', element.text).group())
                        break
                    except:
                        pass
                        
            if total_reviews:
                # Calculate estimated pages based on reviews per page
                estimated_total_pages = (total_reviews + CONFIG['reviews_per_page'] - 1) // CONFIG['reviews_per_page']
                print(f"Found approximately {total_reviews} total reviews across ~{estimated_total_pages} pages")
            else:
                print("Couldn't determine total review count, will iterate until no more pages are found")
                
            # Try to find the maximum page number from pagination
            try:
                pagination_elements = driver.find_elements(By.CSS_SELECTOR, "nav[aria-label='Pagination'] button, nav[aria-label='Pagination'] a")
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
            except Exception as e:
                print(f"Error detecting max pages from pagination: {e}")
                
        except Exception as e:
            print(f"Error determining total pages: {e}")
        
        # Now iterate through all pages with direct URL access
        while not last_page_reached:
            if max_pages and page_num > max_pages:
                print(f"Reached maximum requested page limit ({max_pages})")
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
                            print(f"Timeout waiting for page {page_num} to load, retrying...")
                            retry_count += 1
                            time.sleep(CONFIG['retry_delay'])  # Wait before retry
                
                except Exception as e:
                    print(f"Error loading page {page_num}: {e}")
                    retry_count += 1
                    time.sleep(CONFIG['retry_delay'])  # Wait before retry
            
            if not page_loaded:
                print(f"Failed to load page {page_num} after {max_retries} attempts")
                break
                
            # Save HTML for debugging (first page only)
            if page_num == 1 and CONFIG['save_debug_html']:
                with open(CONFIG['debug_html_path'], "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"Saved first page HTML to {CONFIG['debug_html_path']} for inspection")
            
            # Detect if we've been redirected to another page (indicating we've gone beyond the last page)
            current_url = driver.current_url
            url_page_match = re.search(r'page=(\d+)', current_url)
            if url_page_match:
                actual_page = int(url_page_match.group(1))
                if actual_page != page_num:
                    print(f"Requested page {page_num} but got redirected to page {actual_page} - we've likely gone beyond the last page")
                    last_page_reached = True
                    break
                    
            # Look for pagination elements to find the highest page number
            try:
                pagination_elements = driver.find_elements(By.CSS_SELECTOR, "nav[aria-label='Pagination'] button, nav[aria-label='Pagination'] a")
                max_page = 1
                
                # Find the current active page in pagination
                current_page_in_pagination = None
                
                for element in pagination_elements:
                    text = element.text.strip()
                    if text.isdigit():
                        page_num_int = int(text)
                        if page_num_int > max_page:
                            max_page = page_num_int
                            
                        # Check if this is the currently active page
                        try:
                            is_current = element.get_attribute("aria-current") == "true" or "active" in element.get_attribute("class") or "current" in element.get_attribute("class")
                            if is_current:
                                current_page_in_pagination = page_num_int
                        except:
                            pass
                
                if max_page > highest_page_seen:
                    highest_page_seen = max_page
                    print(f"Updated highest page number to {highest_page_seen}")
                    
                # If we can see the current page in pagination and it doesn't match our expected page,
                # we've likely gone past the last page
                if current_page_in_pagination and current_page_in_pagination != page_num:
                    print(f"Pagination shows we're on page {current_page_in_pagination} but we requested page {page_num}")
                    last_page_reached = True
                    break
                
                # Check for "Next" button - if missing, we're on the last page
                next_buttons = [el for el in pagination_elements if "next" in el.text.lower()]
                if not next_buttons and page_num >= highest_page_seen:
                    print(f"No 'Next' button found and we're at page {page_num} (highest page seen: {highest_page_seen}), likely the last page")
                    last_page_reached = True
                    break
                    
            except Exception as e:
                print(f"Error analyzing pagination: {e}")
            
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
                
                print(f"Found {len(review_elements)} reviews on page {page_num}")
                
                # If we found no new reviews on this page, we've reached the end
                if len(review_elements) == 0:
                    print("No reviews found on this page. Reached the last page.")
                    last_page_reached = True
                    break
                
                # If we're already at or past the highest page number we've seen in pagination,
                # and we have reviews, check if we should continue
                if page_num >= highest_page_seen:
                    print(f"Warning: We're at page {page_num}, which is at or beyond the highest page number seen in pagination ({highest_page_seen})")
                
                reviews_found_on_page = 0
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
                                pass
                        
                        # Skip if not in the requested star filter
                        if star_filter and review['stars'] not in star_filter:
                            continue
                            
                        # Extract review title
                        try:
                            title_element = review_element.find_element(By.CSS_SELECTOR, "h2[data-service-review-title-typography], .review-content__title")
                            review['title'] = title_element.text.strip()
                        except:
                            pass
                            
                        # Extract review text
                        try:
                            review_content = review_element.find_element(By.CSS_SELECTOR, "p[data-service-review-text-typography], p.review-content__text")
                            review['text'] = review_content.text.strip()
                        except:
                            pass
                        
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
                        except:
                            pass
                        
                        # Extract reviewer name and location
                        try:
                            reviewer_element = review_element.find_element(By.CSS_SELECTOR, "span.typography_heading-xxs, .consumer-information__name")
                            review['reviewer']['name'] = reviewer_element.text.strip()
                            
                            try:
                                location_element = review_element.find_element(By.CSS_SELECTOR, ".consumer-information__location")
                                review['reviewer']['location'] = location_element.text.strip()
                            except:
                                pass
                                
                            # Extract review count if available
                            try:
                                reviews_count_element = review_element.find_element(By.CSS_SELECTOR, ".consumer-information__review-count")
                                count_text = reviews_count_element.text.strip()
                                count_match = re.search(r'(\d+)', count_text)
                                if count_match:
                                    review['reviewer']['reviews_count'] = int(count_match.group(1))
                            except:
                                pass
                                
                        except:
                            review['reviewer']['name'] = "Anonymous"
                            
                        # Extract review date (published)
                        try:
                            date_element = review_element.find_element(By.CSS_SELECTOR, "time")
                            review['date']['published'] = date_element.get_attribute("datetime")
                        except:
                            pass
                            
                        # Extract experience date if available
                        try:
                            exp_date_elements = review_element.find_elements(By.CSS_SELECTOR, ".review-content-header__dates")
                            for elem in exp_date_elements:
                                if "Date of experience" in elem.text:
                                    exp_date_text = elem.text.replace("Date of experience:", "").strip()
                                    review['date']['experience'] = exp_date_text
                                    break
                        except:
                            pass
                        
                        # Extract verification status
                        try:
                            verified_elements = review_element.find_elements(By.CSS_SELECTOR, ".review-content-header__verification")
                            review['metadata']['verified'] = len(verified_elements) > 0 and "verified" in verified_elements[0].text.lower()
                        except:
                            pass
                            
                        # Extract useful/helpful votes
                        try:
                            votes_elements = review_element.find_elements(By.CSS_SELECTOR, ".useful-count")
                            if votes_elements:
                                votes_text = votes_elements[0].text.strip()
                                votes_match = re.search(r'(\d+)', votes_text)
                                if votes_match:
                                    review['metadata']['useful_votes'] = int(votes_match.group(1))
                        except:
                            pass
                            
                        # Extract any tags/categories
                        try:
                            tags_elements = review_element.find_elements(By.CSS_SELECTOR, ".review-tag")
                            if tags_elements:
                                review['metadata']['tags'] = [tag.text.strip() for tag in tags_elements]
                        except:
                            pass
                        
                        # Only add reviews with text or a star rating
                        if review['text'] or review['stars']:
                            all_reviews.append(review)
                            reviews_found_on_page += 1
                            print(f"Extracted review: {review['stars']} stars, {len(review['text'])} chars")
                    
                    except Exception as e:
                        print(f"Error extracting review data: {e}")
                
                # If we got no reviews on this page (but found review elements), something's wrong
                if reviews_found_on_page == 0 and len(review_elements) > 0:
                    print("Warning: Found review elements but couldn't extract any valid reviews.")
                
            except Exception as e:
                print(f"Error finding reviews: {e}")
                break
            
            # If we didn't get any reviews and this is the first page, there might be a problem
            if not all_reviews and page_num == 1:
                print("No reviews extracted from first page. Check the HTML structure.")
                break
                
            # Check if we've reached the last page by looking for a "No results found" message
            try:
                no_results_elements = driver.find_elements(By.CSS_SELECTOR, "div.noResultsContainer")
                if no_results_elements:
                    print("Found 'No results' message. Reached the last page.")
                    last_page_reached = True
                    break
            except:
                pass
                
            # Check if we're already at the highest detected page number
            if page_num >= highest_page_seen:
                try:
                    # One final check - look for a Next button
                    next_buttons = driver.find_elements(By.CSS_SELECTOR, 
                                                     "a[data-pagination-button-next='true'], a.pagination-link_next, a.next-page, button.next-page")
                    
                    if not next_buttons:
                        print(f"No next button found and we're at page {page_num} which is the highest page we've seen")
                        last_page_reached = True
                        break
                    else:
                        # If there is a next button on the highest page we've seen,
                        # let's assume there's at least one more page
                        print(f"Found next button on page {page_num} which is the highest page we've seen")
                except Exception as e:
                    print(f"Error checking for next button: {e}")
            
            # Move to the next page
            page_num += 1
            print(f"Moving to page {page_num}")
            time.sleep(CONFIG['page_delay'])  # Delay between pages to be polite
    
    finally:
        # Clean up
        driver.quit()
    
    return all_reviews

def get_reviews(url, star_filter=None, max_pages=None):
    """Legacy function that uses requests+BeautifulSoup. Now we use Selenium."""
    print("Using Selenium for better handling of dynamic content...")
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
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()
    
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
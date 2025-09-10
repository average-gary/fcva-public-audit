#!/usr/bin/env python3
"""
Enhanced FCVA Video Scraper

Uses multiple strategies to find video IDs from the FCVA website
"""

import requests
import re
import json
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def scrape_with_enhanced_selenium():
    """Use Selenium with enhanced strategies"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("Loading FCVA page with Selenium...")
        driver.get("https://www.fcva.us/departments/board-of-supervisors/meeting-agendas-minutes-video")
        
        # Wait for initial page load
        time.sleep(5)
        
        # Try to find and click any "load more" or pagination buttons
        try:
            load_more_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Load') or contains(text(), 'More') or contains(text(), 'Show')]")
            for button in load_more_buttons:
                try:
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(2)
                    print(f"Clicked button: {button.text}")
                except:
                    pass
        except:
            pass
        
        # Look for pagination links and click through them
        try:
            page_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'page') or contains(text(), 'Next') or contains(text(), '»')]")
            current_page = 1
            max_pages = 10  # Limit to prevent infinite loops
            
            while current_page <= max_pages and page_links:
                print(f"Scanning page {current_page}")
                time.sleep(3)  # Wait for content to load
                
                # Try to click next page
                next_found = False
                for link in page_links:
                    if 'next' in link.text.lower() or '»' in link.text or 'more' in link.text.lower():
                        try:
                            driver.execute_script("arguments[0].click();", link)
                            time.sleep(3)
                            current_page += 1
                            next_found = True
                            break
                        except:
                            pass
                
                if not next_found:
                    break
                    
                # Update page_links for next iteration
                page_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'page') or contains(text(), 'Next') or contains(text(), '»')]")
                
        except Exception as e:
            print(f"Pagination handling error: {e}")
        
        # Scroll to load any lazy-loaded content
        print("Scrolling to load content...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # Get final page source
        page_source = driver.page_source
        
        # Also check network requests for any API calls
        logs = driver.get_log('performance')
        api_calls = []
        for log in logs:
            message = json.loads(log['message'])
            if message['message']['method'] == 'Network.responseReceived':
                url = message['message']['params']['response']['url']
                if 'api' in url.lower() or 'granicus' in url.lower() or 'video' in url.lower():
                    api_calls.append(url)
        
        print(f"Found {len(api_calls)} potential API calls: {api_calls[:3]}{'...' if len(api_calls) > 3 else ''}")
        
        driver.quit()
        return page_source, api_calls
        
    except Exception as e:
        print(f"Enhanced Selenium failed: {e}")
        return None, []

def extract_video_ids_from_content(content, api_calls):
    """Extract video IDs using multiple patterns and sources"""
    video_ids = set()
    
    if content:
        soup = BeautifulSoup(content, 'html.parser')
        
        # Strategy 1: Look for direct Granicus links
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href')
            if href and 'granicus' in href:
                print(f"Found Granicus link: {href}")
                # Extract ID from various Granicus URL patterns
                patterns = [
                    r'/clip/(\d+)',
                    r'view_id=(\d+)',
                    r'player/clip/(\d+)',
                    r'ViewPublisher\.php\?view_id=(\d+)'
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, href)
                    video_ids.update(matches)
        
        # Strategy 2: Look for embedded video players or iframes
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            src = iframe.get('src', '')
            if 'granicus' in src or 'video' in src:
                print(f"Found video iframe: {src}")
                matches = re.findall(r'/(\d+)', src)
                video_ids.update(matches)
        
        # Strategy 3: Search for video IDs in JavaScript or data attributes
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for video IDs in JSON data or JavaScript variables
                json_matches = re.findall(r'"(?:clip|video|id)"\s*:\s*"?(\d+)"?', script.string)
                video_ids.update(json_matches)
                
                # Look for Granicus URLs in JavaScript
                granicus_matches = re.findall(r'granicus[^"\']*?(\d+)', script.string)
                video_ids.update(granicus_matches)
        
        # Strategy 4: Look for data attributes
        elements_with_data = soup.find_all(attrs={"data-video-id": True}) + \
                           soup.find_all(attrs={"data-clip-id": True}) + \
                           soup.find_all(attrs={"data-granicus-id": True})
        
        for elem in elements_with_data:
            for attr in ['data-video-id', 'data-clip-id', 'data-granicus-id']:
                if elem.get(attr):
                    video_ids.add(elem.get(attr))
        
        # Strategy 5: Look in the raw HTML for any number patterns near video-related keywords
        video_keywords = ['granicus', 'video', 'clip', 'meeting', 'recording']
        for keyword in video_keywords:
            pattern = f'{keyword}[^\\d]*(\\d{{2,5}})'
            matches = re.findall(pattern, content, re.IGNORECASE)
            video_ids.update(matches)
    
    # Strategy 6: Extract from API calls
    for api_url in api_calls:
        matches = re.findall(r'(\d{2,5})', api_url)
        video_ids.update(matches)
    
    # Filter out obviously wrong IDs (too short/long, common false positives)
    filtered_ids = set()
    for vid_id in video_ids:
        if vid_id.isdigit() and 2 <= len(vid_id) <= 6:  # Reasonable length for video IDs
            # Skip common false positives
            if vid_id not in ['2024', '2023', '2022', '2021', '2020', '100', '200', '300', '404', '500']:
                filtered_ids.add(vid_id)
    
    return sorted(list(filtered_ids), key=int)

def test_video_urls(video_ids):
    """Test if video URLs are accessible"""
    working_ids = []
    
    print(f"Testing {len(video_ids)} video IDs...")
    for vid_id in video_ids[:10]:  # Test first 10 to avoid overwhelming the server
        test_url = f"https://fcva.granicus.com/player/clip/{vid_id}"
        try:
            response = requests.head(test_url, timeout=5)
            if response.status_code == 200:
                print(f"✓ Video {vid_id} is accessible")
                working_ids.append(vid_id)
            else:
                print(f"✗ Video {vid_id} returned {response.status_code}")
        except Exception as e:
            print(f"✗ Video {vid_id} failed: {e}")
    
    return working_ids

def main():
    print("Enhanced FCVA Video Scraper Starting...")
    print("=" * 60)
    
    # Try enhanced Selenium approach
    content, api_calls = scrape_with_enhanced_selenium()
    
    if not content:
        print("Failed to get page content")
        return []
    
    # Extract video IDs using multiple strategies
    video_ids = extract_video_ids_from_content(content, api_calls)
    
    print(f"\nFound {len(video_ids)} potential video IDs: {video_ids}")
    
    if video_ids:
        # Test a few URLs to verify they work
        working_ids = test_video_urls(video_ids)
        
        if working_ids:
            print(f"\nConfirmed {len(working_ids)} working video IDs")
            video_ids = working_ids
        
        # Save results
        with open('video_ids.json', 'w') as f:
            json.dump(video_ids, f, indent=2)
        
        print(f"\nSaved {len(video_ids)} video IDs to video_ids.json")
        return video_ids
    else:
        print("\nNo video IDs found. The website structure may have changed.")
        print("Manual inspection may be required.")
        return []

if __name__ == "__main__":
    video_ids = main()
    
    if video_ids:
        print(f"\n{'='*60}")
        print("SUCCESS! Ready to download and transcribe:")
        print(f"python granicus_transcribe.py {' '.join(video_ids[:5])}{'...' if len(video_ids) > 5 else ''}")
    else:
        print(f"\n{'='*60}")
        print("No video IDs found. Try manual inspection or check if website structure changed.")
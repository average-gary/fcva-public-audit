#!/usr/bin/env python3
"""
FCVA Video Scraper

Scrapes all Granicus video IDs from the FCVA meeting page
"""

import requests
import re
from bs4 import BeautifulSoup
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_with_selenium():
    """Use Selenium to scrape JavaScript-rendered content"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.fcva.us/departments/board-of-supervisors/meeting-agendas-minutes-video")
        
        # Wait for page to load
        time.sleep(5)
        
        # Get page source after JavaScript execution
        page_source = driver.page_source
        driver.quit()
        
        return page_source
        
    except Exception as e:
        print(f"Selenium failed: {e}")
        return None

def scrape_fcva_videos():
    """Scrape all Granicus video IDs from FCVA meeting page"""
    url = "https://www.fcva.us/departments/board-of-supervisors/meeting-agendas-minutes-video"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Try multiple methods
    page_content = None
    
    # Method 1: Direct requests
    try:
        print("Trying direct request...")
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            page_content = response.content
            print("✓ Direct request successful")
        else:
            print(f"Direct request failed: {response.status_code}")
    except Exception as e:
        print(f"Direct request error: {e}")
    
    # Method 2: Try Selenium if direct fails
    if not page_content:
        print("Trying Selenium...")
        page_content = scrape_with_selenium()
        if page_content:
            print("✓ Selenium successful")
    
    if not page_content:
        # Method 3: Manual input fallback
        print("\nAutomatic scraping failed. You can manually provide video IDs.")
        print("Visit: https://www.fcva.us/departments/board-of-supervisors/meeting-agendas-minutes-video")
        print("Look for Granicus video links and extract the numbers from URLs like '/clip/123'")
        
        manual_ids = input("Enter video IDs separated by spaces (or press Enter to skip): ").strip()
        if manual_ids:
            video_ids = manual_ids.split()
            with open('video_ids.json', 'w') as f:
                json.dump(video_ids, f, indent=2)
            return video_ids
        return []
    
    soup = BeautifulSoup(page_content, 'html.parser')
    
    # Look for Granicus video links
    granicus_links = []
    
    # Find all links containing granicus
    all_links = soup.find_all('a', href=True)
    
    for link in all_links:
        href = link.get('href')
        if href and ('granicus.com' in href or 'fcva.granicus.com' in href) and 'clip' in href:
            granicus_links.append(href)
    
    # Also search in the page text for any granicus URLs
    page_text = soup.get_text()
    granicus_urls = re.findall(r'https?://[^\s]*granicus[^\s]*clip[^\s]*', page_text)
    granicus_links.extend(granicus_urls)
    
    # Extract video IDs using regex
    video_ids = []
    clip_pattern = r'/clip/(\d+)'
    
    for link in granicus_links:
        match = re.search(clip_pattern, link)
        if match:
            video_ids.append(match.group(1))
    
    # Remove duplicates and sort
    video_ids = sorted(list(set(video_ids)), key=int)
    
    print(f"Found {len(video_ids)} unique videos:")
    for vid_id in video_ids:
        print(f"  - Video ID: {vid_id}")
    
    # Save to file
    with open('video_ids.json', 'w') as f:
        json.dump(video_ids, f, indent=2)
    
    print(f"\nVideo IDs saved to video_ids.json")
    return video_ids

if __name__ == "__main__":
    video_ids = scrape_fcva_videos()
    
    if video_ids:
        print(f"\nTo download and transcribe all videos, run:")
        print(f"python granicus_transcribe.py {' '.join(video_ids)}")
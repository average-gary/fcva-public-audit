#!/usr/bin/env python3
"""
Simple FCVA Video Scraper - No Selenium required
"""

import requests
import re
import json

def scrape_fcva_videos():
    url = "https://www.fcva.us/departments/board-of-supervisors/meeting-agendas-minutes-video"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    try:
        print("Fetching FCVA meeting page...")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 403:
            print("Site is blocking automated access. Manual extraction needed.")
            print("\nPlease visit: https://www.fcva.us/departments/board-of-supervisors/meeting-agendas-minutes-video")
            print("Look for Granicus video links and extract the clip numbers.")
            print("Example: if you see 'https://fcva.granicus.com/player/clip/123', the ID is '123'")
            
            manual_ids = input("\nEnter video IDs separated by spaces: ").strip()
            if manual_ids:
                video_ids = manual_ids.split()
                # Sort numerically
                try:
                    video_ids = sorted([int(x) for x in video_ids])
                    video_ids = [str(x) for x in video_ids]
                except ValueError:
                    pass  # Keep as strings if not all numeric
                
                with open('video_ids.json', 'w') as f:
                    json.dump(video_ids, f, indent=2)
                
                print(f"\nSaved {len(video_ids)} video IDs to video_ids.json")
                return video_ids
            return []
        
        # If successful, parse the content
        content = response.text
        
        # Look for Granicus clip URLs in various formats
        patterns = [
            r'fcva\.granicus\.com/player/clip/(\d+)',
            r'granicus\.com/player/clip/(\d+)',
            r'/clip/(\d+)',
        ]
        
        video_ids = set()
        for pattern in patterns:
            matches = re.findall(pattern, content)
            video_ids.update(matches)
        
        video_ids = sorted([int(x) for x in video_ids])
        video_ids = [str(x) for x in video_ids]
        
        print(f"Found {len(video_ids)} video IDs: {video_ids}")
        
        with open('video_ids.json', 'w') as f:
            json.dump(video_ids, f, indent=2)
        
        return video_ids
        
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    video_ids = scrape_fcva_videos()
    
    if video_ids:
        print(f"\nTo download all videos:")
        print(f"python granicus_transcribe.py {' '.join(video_ids)}")
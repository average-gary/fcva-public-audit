#!/usr/bin/env python3
"""
FCVA Incremental Video ID Scanner

Starting from a known video ID, scan incrementally to find all available videos
"""

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def check_video_exists(video_id):
    """Check if a video ID exists by testing the Granicus URL"""
    url = f"https://fcva.granicus.com/player/clip/{video_id}"
    
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        # Granicus typically returns 200 for valid videos, 404 for invalid
        if response.status_code == 200:
            return video_id, True, response.url
        else:
            return video_id, False, None
    except Exception as e:
        return video_id, False, str(e)

def scan_range(start_id, end_id, max_workers=10):
    """Scan a range of video IDs concurrently"""
    print(f"Scanning video IDs {start_id} to {end_id}...")
    
    valid_ids = []
    total_checked = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_id = {executor.submit(check_video_exists, vid_id): vid_id 
                       for vid_id in range(start_id, end_id + 1)}
        
        # Process results as they complete
        for future in as_completed(future_to_id):
            video_id, is_valid, info = future.result()
            total_checked += 1
            
            if is_valid:
                print(f"✓ Found video {video_id}")
                valid_ids.append(video_id)
            elif total_checked % 50 == 0:  # Progress update every 50 checks
                print(f"  Checked {total_checked}/{end_id - start_id + 1} IDs, found {len(valid_ids)} videos")
            
            # Small delay to be respectful to the server
            time.sleep(0.1)
    
    return sorted(valid_ids)

def smart_scan(start_id=28, initial_range=100):
    """Smart scanning that adjusts range based on findings"""
    print(f"Starting smart scan from video ID {start_id}")
    print("=" * 60)
    
    all_valid_ids = []
    current_start = start_id
    
    # First, scan backwards from the starting point to find earlier videos
    print(f"\n📹 Scanning backwards from {start_id}...")
    backwards_end = max(1, start_id - 200)  # Don't go below 1
    backwards_ids = scan_range(backwards_end, start_id - 1, max_workers=5)
    all_valid_ids.extend(backwards_ids)
    print(f"Found {len(backwards_ids)} videos going backwards")
    
    # Scan the initial range forward
    print(f"\n📹 Scanning forward from {start_id}...")
    end_id = start_id + initial_range
    valid_ids = scan_range(start_id, end_id)
    all_valid_ids.extend(valid_ids)
    
    print(f"Found {len(valid_ids)} videos in range {start_id}-{end_id}")
    
    # If we found videos in the last portion, extend the search
    recent_videos = [vid for vid in valid_ids if vid > end_id - 20]
    
    while recent_videos and end_id < start_id + 1000:  # Limit to prevent runaway
        print(f"\n📹 Extending search (found recent videos)...")
        new_start = end_id + 1
        end_id = new_start + initial_range
        
        new_valid_ids = scan_range(new_start, end_id)
        all_valid_ids.extend(new_valid_ids)
        
        print(f"Found {len(new_valid_ids)} videos in range {new_start}-{end_id}")
        
        # Check if we found videos in the recent portion of this range
        recent_videos = [vid for vid in new_valid_ids if vid > end_id - 20]
        
        # Adaptive range sizing
        if len(new_valid_ids) == 0:
            break  # No more videos found
        elif len(new_valid_ids) > 10:
            initial_range = min(200, initial_range + 50)  # Increase range if finding many
        else:
            initial_range = max(50, initial_range - 20)   # Decrease range if finding few
    
    return sorted(set(all_valid_ids))

def main():
    print("FCVA Incremental Video Scanner")
    print("=" * 60)
    
    # Start scanning
    valid_ids = smart_scan(start_id=28)
    
    print(f"\n{'='*60}")
    print("SCAN COMPLETE")
    print(f"{'='*60}")
    print(f"Found {len(valid_ids)} total videos")
    
    if valid_ids:
        print(f"Video ID range: {min(valid_ids)} to {max(valid_ids)}")
        print(f"Sample IDs: {valid_ids[:10]}{'...' if len(valid_ids) > 10 else ''}")
        
        # Save results
        with open('video_ids.json', 'w') as f:
            json.dump([str(vid) for vid in valid_ids], f, indent=2)
        
        print(f"\n✅ Saved {len(valid_ids)} video IDs to video_ids.json")
        
        # Show command to start transcription
        print(f"\n🎬 Ready to download and transcribe:")
        if len(valid_ids) <= 5:
            print(f"python granicus_transcribe.py {' '.join(str(vid) for vid in valid_ids)}")
        else:
            print(f"python granicus_transcribe.py --from-file video_ids.json")
            print(f"# Or start with first few: python granicus_transcribe.py {' '.join(str(vid) for vid in valid_ids[:3])}")
        
        return valid_ids
    else:
        print("❌ No videos found")
        return []

if __name__ == "__main__":
    main()
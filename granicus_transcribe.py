#!/usr/bin/env python3
"""
Granicus Video Download and Transcription Tool

Usage:
    python granicus_transcribe.py 291
    python granicus_transcribe.py 291 292 293  # Multiple videos
    python granicus_transcribe.py --from-file video_ids.json  # From JSON file
    python granicus_transcribe.py --resume  # Resume failed downloads
"""

import sys
import subprocess
import os
import json
import time
from pathlib import Path
from datetime import datetime

def download_video(clip_id):
    """Download video from Granicus using yt-dlp"""
    url = f"https://fcva.granicus.com/player/clip/{clip_id}"
    output_file = f"video_{clip_id}.%(ext)s"
    
    print(f"Downloading video {clip_id}...")
    cmd = ["yt-dlp", url, "-o", output_file]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✓ Downloaded video {clip_id}")
        
        # Find the actual downloaded file
        downloaded_files = list(Path(".").glob(f"video_{clip_id}.*"))
        if downloaded_files:
            return str(downloaded_files[0])
        else:
            print(f"Warning: Could not find downloaded file for video {clip_id}")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to download video {clip_id}: {e}")
        return None

def transcribe_video(video_file, clip_id):
    """Transcribe video using whisper with timestamps"""
    if not os.path.exists(video_file):
        print(f"Video file {video_file} not found")
        return None
        
    # Generate multiple output formats with timestamps
    output_vtt = f"transcript_{clip_id}.vtt"   # VTT with timestamps
    output_srt = f"transcript_{clip_id}.srt"   # SRT with timestamps  
    output_txt = f"transcript_{clip_id}.txt"   # Plain text backup
    
    # Skip if transcript already exists
    if os.path.exists(output_vtt):
        print(f"✓ Transcript already exists: {output_vtt}")
        return output_vtt
    
    print(f"Transcribing {video_file} with timestamps...")
    start_time = time.time()
    
    # Use OpenAI Whisper with multiple formats including timestamps
    whisper_commands = [
        # Generate VTT (with timestamps), SRT (with timestamps), and TXT
        ["whisper", video_file, "--model", "tiny", "--output_format", "vtt", "--output_format", "srt", "--output_format", "txt", "--output_dir", ".", "--verbose", "False"],
        # Fallback to just VTT if multiple formats fail
        ["whisper", video_file, "--model", "tiny", "--output_format", "vtt", "--output_dir", ".", "--verbose", "False"],
        # Python module version
        [sys.executable, "-m", "whisper", video_file, "--model", "tiny", "--output_format", "vtt", "--output_dir", "."],
    ]
    
    for i, cmd in enumerate(whisper_commands):
        try:
            print(f"  Trying method {i+1}/{len(whisper_commands)}: {cmd[0]}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # OpenAI Whisper creates files with original name + extension
            base_name = Path(video_file).stem
            
            # Rename generated files to our naming convention
            generated_files = {
                f"{base_name}.vtt": output_vtt,
                f"{base_name}.srt": output_srt, 
                f"{base_name}.txt": output_txt
            }
            
            files_created = []
            for generated, target in generated_files.items():
                if os.path.exists(generated):
                    os.rename(generated, target)
                    files_created.append(target)
            
            elapsed = time.time() - start_time
            print(f"✓ Transcribed in {elapsed:.1f}s")
            for file in files_created:
                print(f"  Created: {file}")
            
            # Return the VTT file (with timestamps) as primary output
            return output_vtt if os.path.exists(output_vtt) else files_created[0]
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"  Method {i+1} failed: {e}")
            continue
    
    print(f"✗ Failed to transcribe {video_file} - no working whisper installation found")
    return None

def load_video_ids_from_file(filename):
    """Load video IDs from JSON file"""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(x) for x in data]
        else:
            print(f"Invalid format in {filename}")
            return []
    except FileNotFoundError:
        print(f"File {filename} not found")
        return []
    except json.JSONDecodeError:
        print(f"Invalid JSON in {filename}")
        return []

def save_progress(completed_ids, failed_ids):
    """Save progress to resume later"""
    progress = {
        "completed": completed_ids,
        "failed": failed_ids,
        "timestamp": datetime.now().isoformat()
    }
    with open('transcription_progress.json', 'w') as f:
        json.dump(progress, f, indent=2)

def load_progress():
    """Load previous progress"""
    try:
        with open('transcription_progress.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"completed": [], "failed": []}

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python granicus_transcribe.py <clip_id> [clip_id2] ...")
        print("  python granicus_transcribe.py --from-file video_ids.json")
        print("  python granicus_transcribe.py --resume")
        sys.exit(1)
    
    # Parse arguments
    if sys.argv[1] == '--from-file':
        if len(sys.argv) < 3:
            print("Usage: python granicus_transcribe.py --from-file <filename>")
            sys.exit(1)
        clip_ids = load_video_ids_from_file(sys.argv[2])
    elif sys.argv[1] == '--resume':
        progress = load_progress()
        all_ids = load_video_ids_from_file('video_ids.json')
        completed = set(progress.get('completed', []))
        clip_ids = [x for x in all_ids if x not in completed]
        print(f"Resuming: {len(clip_ids)} remaining out of {len(all_ids)} total")
    else:
        clip_ids = sys.argv[1:]
    
    if not clip_ids:
        print("No video IDs to process")
        sys.exit(0)
    
    print(f"Processing {len(clip_ids)} videos: {clip_ids[:5]}{'...' if len(clip_ids) > 5 else ''}")
    
    completed_ids = []
    failed_ids = []
    
    for i, clip_id in enumerate(clip_ids, 1):
        print(f"\n{'='*60}")
        print(f"Processing video {clip_id} ({i}/{len(clip_ids)})")
        print(f"{'='*60}")
        
        try:
            # Download video
            video_file = download_video(clip_id)
            if not video_file:
                failed_ids.append(clip_id)
                continue
                
            # Transcribe video
            transcript_file = transcribe_video(video_file, clip_id)
            if transcript_file:
                print(f"✓ Process complete for video {clip_id}")
                print(f"  Video: {video_file}")
                print(f"  Transcript: {transcript_file}")
                completed_ids.append(clip_id)
            else:
                print(f"✗ Transcription failed for video {clip_id}")
                failed_ids.append(clip_id)
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted by user")
            save_progress(completed_ids, failed_ids)
            print(f"Progress saved. Resume with: python granicus_transcribe.py --resume")
            sys.exit(1)
        except Exception as e:
            print(f"✗ Unexpected error for video {clip_id}: {e}")
            failed_ids.append(clip_id)
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"✓ Completed: {len(completed_ids)}")
    print(f"✗ Failed: {len(failed_ids)}")
    
    if failed_ids:
        print(f"\nFailed videos: {failed_ids}")
        print(f"Retry with: python granicus_transcribe.py {' '.join(failed_ids)}")
    
    save_progress(completed_ids, failed_ids)

if __name__ == "__main__":
    main()
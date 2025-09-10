#!/usr/bin/env python3
"""
Organized FCVA Video Download and Transcription Tool

Downloads and transcribes videos with proper folder organization
"""

import sys
import subprocess
import os
import json
import time
from pathlib import Path
from datetime import datetime

def setup_directories():
    """Create organized directory structure"""
    base_dir = Path("fcva_videos")
    directories = {
        'videos': base_dir / "videos",
        'transcripts': base_dir / "transcripts",
        'logs': base_dir / "logs",
        'metadata': base_dir / "metadata"
    }
    
    for name, path in directories.items():
        path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {path}")
    
    return directories

def download_video(clip_id, dirs):
    """Download video from Granicus using yt-dlp"""
    url = f"https://fcva.granicus.com/player/clip/{clip_id}"
    video_dir = dirs['videos']
    output_pattern = str(video_dir / f"video_{clip_id}.%(ext)s")
    
    print(f"📥 Downloading video {clip_id}...")
    cmd = ["yt-dlp", url, "-o", output_pattern, "--write-info-json"]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✓ Downloaded video {clip_id}")
        
        # Find the actual downloaded files
        video_files = list(video_dir.glob(f"video_{clip_id}.*"))
        video_file = None
        info_file = None
        
        for file in video_files:
            if file.suffix == '.json':
                info_file = file
            elif file.suffix in ['.mp4', '.mkv', '.webm', '.avi']:
                video_file = file
        
        # Save download metadata
        if info_file and dirs['metadata']:
            metadata_file = dirs['metadata'] / f"video_{clip_id}_info.json"
            if info_file.exists() and not metadata_file.exists():
                info_file.rename(metadata_file)
        
        return str(video_file) if video_file else None
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to download video {clip_id}: {e}"
        print(f"✗ {error_msg}")
        
        # Log the error
        error_log = dirs['logs'] / "download_errors.log"
        with open(error_log, 'a') as f:
            f.write(f"{datetime.now().isoformat()}: {error_msg}\n")
        
        return None

def transcribe_video(video_file, clip_id, dirs):
    """Transcribe video using whisper with timestamps"""
    if not os.path.exists(video_file):
        print(f"Video file {video_file} not found")
        return None
    
    transcript_dir = dirs['transcripts']
    
    # Generate multiple output formats with timestamps
    outputs = {
        'vtt': transcript_dir / f"video_{clip_id}.vtt",   # VTT with timestamps
        'srt': transcript_dir / f"video_{clip_id}.srt",   # SRT with timestamps  
        'txt': transcript_dir / f"video_{clip_id}.txt"    # Plain text
    }
    
    # Skip if transcript already exists
    if outputs['vtt'].exists():
        print(f"✓ Transcript already exists: {outputs['vtt']}")
        return str(outputs['vtt'])
    
    print(f"🎯 Transcribing video {clip_id}...")
    start_time = time.time()
    
    # Use OpenAI Whisper with multiple formats including timestamps
    whisper_commands = [
        # Try with multiple output formats
        ["whisper", video_file, "--model", "base", "--output_format", "vtt", "--output_format", "srt", "--output_format", "txt", "--output_dir", str(transcript_dir), "--verbose", "False"],
        # Fallback to just VTT
        ["whisper", video_file, "--model", "base", "--output_format", "vtt", "--output_dir", str(transcript_dir), "--verbose", "False"],
        # Python module fallback
        [sys.executable, "-m", "whisper", video_file, "--model", "base", "--output_format", "vtt", "--output_dir", str(transcript_dir)]
    ]
    
    for i, cmd in enumerate(whisper_commands):
        try:
            print(f"  🔄 Trying transcription method {i+1}/{len(whisper_commands)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Whisper creates files with original filename base
            video_base = Path(video_file).stem
            
            # Map generated files to our organized naming
            generated_files = {
                transcript_dir / f"{video_base}.vtt": outputs['vtt'],
                transcript_dir / f"{video_base}.srt": outputs['srt'],
                transcript_dir / f"{video_base}.txt": outputs['txt']
            }
            
            files_created = []
            for generated, target in generated_files.items():
                if generated.exists() and not target.exists():
                    generated.rename(target)
                    files_created.append(target)
            
            elapsed = time.time() - start_time
            print(f"✓ Transcribed video {clip_id} in {elapsed:.1f}s")
            for file in files_created:
                print(f"  📄 Created: {file.name}")
            
            # Log successful transcription
            success_log = dirs['logs'] / "transcription_success.log"
            with open(success_log, 'a') as f:
                f.write(f"{datetime.now().isoformat()}: Video {clip_id} transcribed successfully\n")
            
            return str(outputs['vtt']) if outputs['vtt'].exists() else str(files_created[0])
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"  ✗ Method {i+1} failed: {e}")
            continue
    
    error_msg = f"Failed to transcribe video {clip_id} - no working whisper installation found"
    print(f"✗ {error_msg}")
    
    # Log transcription error
    error_log = dirs['logs'] / "transcription_errors.log"
    with open(error_log, 'a') as f:
        f.write(f"{datetime.now().isoformat()}: {error_msg}\n")
    
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

def save_progress(completed_ids, failed_ids, dirs):
    """Save progress to resume later"""
    progress = {
        "completed": completed_ids,
        "failed": failed_ids,
        "timestamp": datetime.now().isoformat(),
        "total_videos": len(completed_ids) + len(failed_ids)
    }
    
    progress_file = dirs['logs'] / 'transcription_progress.json'
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)

def load_progress(dirs):
    """Load previous progress"""
    progress_file = dirs['logs'] / 'transcription_progress.json'
    try:
        with open(progress_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"completed": [], "failed": []}

def create_summary_report(dirs, completed_ids, failed_ids):
    """Create a summary report of the transcription process"""
    report_file = dirs['logs'] / 'transcription_summary.md'
    
    with open(report_file, 'w') as f:
        f.write("# FCVA Video Transcription Summary\n\n")
        f.write(f"**Generated**: {datetime.now().isoformat()}\n\n")
        f.write(f"## Results\n")
        f.write(f"- **Total Videos Processed**: {len(completed_ids) + len(failed_ids)}\n")
        f.write(f"- **Successfully Transcribed**: {len(completed_ids)}\n")
        f.write(f"- **Failed**: {len(failed_ids)}\n")
        f.write(f"- **Success Rate**: {len(completed_ids)/(len(completed_ids) + len(failed_ids))*100:.1f}%\n\n")
        
        if completed_ids:
            f.write(f"## Completed Videos\n")
            for vid_id in sorted(completed_ids, key=int):
                f.write(f"- Video {vid_id}\n")
            f.write("\n")
        
        if failed_ids:
            f.write(f"## Failed Videos\n")
            for vid_id in sorted(failed_ids, key=int):
                f.write(f"- Video {vid_id}\n")
            f.write("\n")
        
        f.write(f"## File Organization\n")
        f.write(f"```\n")
        f.write(f"fcva_videos/\n")
        f.write(f"├── videos/          # Temporary video downloads (deleted after transcription)\n")
        f.write(f"├── transcripts/     # VTT, SRT, and TXT transcripts (kept)\n")
        f.write(f"├── metadata/        # Video metadata from yt-dlp (kept)\n")
        f.write(f"└── logs/           # Process logs and reports (kept)\n")
        f.write(f"```\n")
        f.write(f"\n**Note**: Video files are automatically deleted after successful transcription to save disk space and keep the repository lightweight for Git.\n")

def main():
    print("🎬 FCVA Organized Video Transcription Pipeline")
    print("=" * 60)
    
    # Set up organized directory structure
    dirs = setup_directories()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python granicus_transcribe_organized.py <clip_id> [clip_id2] ...")
        print("  python granicus_transcribe_organized.py --from-file video_ids.json")
        print("  python granicus_transcribe_organized.py --resume")
        sys.exit(1)
    
    # Parse arguments
    if sys.argv[1] == '--from-file':
        if len(sys.argv) < 3:
            print("Usage: python granicus_transcribe_organized.py --from-file <filename>")
            sys.exit(1)
        clip_ids = load_video_ids_from_file(sys.argv[2])
    elif sys.argv[1] == '--resume':
        progress = load_progress(dirs)
        all_ids = load_video_ids_from_file('video_ids.json')
        completed = set(progress.get('completed', []))
        clip_ids = [x for x in all_ids if x not in completed]
        print(f"🔄 Resuming: {len(clip_ids)} remaining out of {len(all_ids)} total")
    else:
        clip_ids = sys.argv[1:]
    
    if not clip_ids:
        print("No video IDs to process")
        sys.exit(0)
    
    print(f"\n📋 Processing {len(clip_ids)} videos")
    print(f"🎯 First few: {clip_ids[:5]}{'...' if len(clip_ids) > 5 else ''}")
    
    completed_ids = []
    failed_ids = []
    
    for i, clip_id in enumerate(clip_ids, 1):
        print(f"\n{'='*60}")
        print(f"🎬 Processing video {clip_id} ({i}/{len(clip_ids)})")
        print(f"{'='*60}")
        
        try:
            # Download video
            video_file = download_video(clip_id, dirs)
            if not video_file:
                failed_ids.append(clip_id)
                continue
                
            # Transcribe video
            transcript_file = transcribe_video(video_file, clip_id, dirs)
            if transcript_file:
                print(f"✅ Process complete for video {clip_id}")
                print(f"  🎥 Video: {Path(video_file).name}")
                print(f"  📄 Transcript: {Path(transcript_file).name}")
                
                # Delete video file after successful transcription to save space
                try:
                    os.remove(video_file)
                    print(f"  🗑️  Deleted video file to save space")
                except Exception as e:
                    print(f"  ⚠️  Could not delete video file: {e}")
                
                completed_ids.append(clip_id)
            else:
                print(f"❌ Transcription failed for video {clip_id}")
                failed_ids.append(clip_id)
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted by user")
            save_progress(completed_ids, failed_ids, dirs)
            create_summary_report(dirs, completed_ids, failed_ids)
            print(f"📊 Progress saved. Resume with: python granicus_transcribe_organized.py --resume")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Unexpected error for video {clip_id}: {e}")
            failed_ids.append(clip_id)
        
        # Save progress every 10 videos
        if (i % 10) == 0:
            save_progress(completed_ids, failed_ids, dirs)
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"📊 FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Completed: {len(completed_ids)}")
    print(f"❌ Failed: {len(failed_ids)}")
    
    if failed_ids:
        print(f"\n🔄 Retry failed videos with:")
        print(f"python granicus_transcribe_organized.py {' '.join(failed_ids)}")
    
    save_progress(completed_ids, failed_ids, dirs)
    create_summary_report(dirs, completed_ids, failed_ids)
    
    print(f"\n📁 All files organized in: fcva_videos/")
    print(f"📊 Summary report: fcva_videos/logs/transcription_summary.md")

if __name__ == "__main__":
    main()
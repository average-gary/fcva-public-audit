#!/usr/bin/env python3
"""
Resumeable FCVA Video Download and Transcription Tool

Enhanced with better pause/resume, progress tracking, and timeout handling
"""

import sys
import subprocess
import os
import json
import time
import signal
from pathlib import Path
from datetime import datetime

class GracefulKiller:
    """Handle graceful shutdown on SIGTERM/SIGINT"""
    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
    
    def _handle_signal(self, signum, frame):
        print(f"\n🛑 Received signal {signum}, gracefully shutting down...")
        self.kill_now = True

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
    
    return directories

def load_progress_state(dirs):
    """Load comprehensive progress state"""
    progress_file = dirs['logs'] / 'comprehensive_progress.json'
    try:
        with open(progress_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "completed": [],
            "failed": [],
            "in_progress": None,
            "total_processed": 0,
            "last_updated": None,
            "session_start": datetime.now().isoformat()
        }

def save_progress_state(dirs, state):
    """Save comprehensive progress state"""
    state["last_updated"] = datetime.now().isoformat()
    progress_file = dirs['logs'] / 'comprehensive_progress.json'
    with open(progress_file, 'w') as f:
        json.dump(state, f, indent=2)

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

def download_video_with_timeout(clip_id, dirs, timeout_minutes=30):
    """Download video with configurable timeout"""
    url = f"https://fcva.granicus.com/player/clip/{clip_id}"
    video_dir = dirs['videos']
    output_pattern = str(video_dir / f"video_{clip_id}.%(ext)s")
    
    print(f"📥 Downloading video {clip_id} (timeout: {timeout_minutes}min)...")
    cmd = ["yt-dlp", url, "-o", output_pattern, "--write-info-json"]
    
    try:
        result = subprocess.run(
            cmd, 
            check=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout_minutes * 60
        )
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
        
    except subprocess.TimeoutExpired:
        error_msg = f"Download timeout ({timeout_minutes}min) for video {clip_id}"
        print(f"⏰ {error_msg}")
        
        # Log timeout
        timeout_log = dirs['logs'] / "timeout_errors.log"
        with open(timeout_log, 'a') as f:
            f.write(f"{datetime.now().isoformat()}: {error_msg}\n")
        
        return None
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to download video {clip_id}: {e}"
        print(f"✗ {error_msg}")
        
        # Log the error
        error_log = dirs['logs'] / "download_errors.log"
        with open(error_log, 'a') as f:
            f.write(f"{datetime.now().isoformat()}: {error_msg}\n")
        
        return None

def transcribe_video_with_timeout(video_file, clip_id, dirs, timeout_minutes=120):
    """Transcribe video with configurable timeout"""
    if not os.path.exists(video_file):
        print(f"Video file {video_file} not found")
        return None
    
    transcript_dir = dirs['transcripts']
    outputs = {
        'vtt': transcript_dir / f"video_{clip_id}.vtt",
        'srt': transcript_dir / f"video_{clip_id}.srt", 
        'txt': transcript_dir / f"video_{clip_id}.txt"
    }
    
    # Skip if transcript already exists
    if outputs['vtt'].exists():
        print(f"✓ Transcript already exists: {outputs['vtt']}")
        return str(outputs['vtt'])
    
    print(f"🎯 Transcribing video {clip_id} (timeout: {timeout_minutes}min)...")
    start_time = time.time()
    
    whisper_commands = [
        ["whisper", video_file, "--model", "base", "--output_format", "vtt", 
         "--output_format", "srt", "--output_format", "txt", 
         "--output_dir", str(transcript_dir), "--verbose", "False"],
        ["whisper", video_file, "--model", "base", "--output_format", "vtt", 
         "--output_dir", str(transcript_dir), "--verbose", "False"],
        [sys.executable, "-m", "whisper", video_file, "--model", "base", 
         "--output_format", "vtt", "--output_dir", str(transcript_dir)]
    ]
    
    for i, cmd in enumerate(whisper_commands):
        try:
            print(f"  🔄 Trying transcription method {i+1}/{len(whisper_commands)}")
            result = subprocess.run(
                cmd, 
                check=True, 
                capture_output=True, 
                text=True,
                timeout=timeout_minutes * 60
            )
            
            # Whisper creates files with original filename base
            video_base = Path(video_file).stem
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
            
            return str(outputs['vtt']) if outputs['vtt'].exists() else str(files_created[0])
            
        except subprocess.TimeoutExpired:
            error_msg = f"Transcription timeout ({timeout_minutes}min) for video {clip_id}"
            print(f"⏰ {error_msg}")
            
            # Log timeout
            timeout_log = dirs['logs'] / "timeout_errors.log"
            with open(timeout_log, 'a') as f:
                f.write(f"{datetime.now().isoformat()}: {error_msg}\n")
            
            continue
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"  ✗ Method {i+1} failed: {e}")
            continue
    
    error_msg = f"Failed to transcribe video {clip_id} - all methods exhausted"
    print(f"✗ {error_msg}")
    
    # Log transcription error
    error_log = dirs['logs'] / "transcription_errors.log"
    with open(error_log, 'a') as f:
        f.write(f"{datetime.now().isoformat()}: {error_msg}\n")
    
    return None

def cleanup_video_file(video_file):
    """Safely delete video file after successful transcription"""
    try:
        if os.path.exists(video_file):
            os.remove(video_file)
            print(f"  🗑️  Deleted video file: {Path(video_file).name}")
        return True
    except Exception as e:
        print(f"  ⚠️  Could not delete video file: {e}")
        return False

def print_status(dirs, current_video, total_videos, progress_state):
    """Print current processing status"""
    completed = len(progress_state['completed'])
    failed = len(progress_state['failed'])
    processed = completed + failed
    
    if total_videos > 0:
        completion_pct = (processed / total_videos) * 100
        success_rate = (completed / processed * 100) if processed > 0 else 0
        
        print(f"\n📊 STATUS UPDATE")
        print(f"Currently processing: Video {current_video}")
        print(f"Progress: {processed}/{total_videos} ({completion_pct:.1f}%)")
        print(f"✅ Completed: {completed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success rate: {success_rate:.1f}%")
        print(f"⏰ Last updated: {datetime.now().strftime('%H:%M:%S')}")

def create_resume_script(dirs):
    """Create a convenient resume script"""
    script_content = f"""#!/bin/bash
# Auto-generated resume script
cd "{os.getcwd()}"
source venv/bin/activate
python granicus_transcribe_resumeable.py --resume
"""
    
    script_path = dirs['logs'] / 'resume.sh'
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)
    print(f"📝 Created resume script: {script_path}")

def main():
    print("🎬 FCVA Resumeable Video Transcription Pipeline")
    print("=" * 60)
    
    # Set up graceful shutdown handler
    killer = GracefulKiller()
    
    # Set up directories
    dirs = setup_directories()
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python granicus_transcribe_resumeable.py <clip_id> [clip_id2] ...")
        print("  python granicus_transcribe_resumeable.py --from-file <filename>")
        print("  python granicus_transcribe_resumeable.py --resume")
        print("  python granicus_transcribe_resumeable.py --status")
        sys.exit(1)
    
    # Load progress state
    progress_state = load_progress_state(dirs)
    
    if sys.argv[1] == '--status':
        # Just show status and exit
        completed = len(progress_state['completed'])
        failed = len(progress_state['failed'])
        print(f"📊 Current Status:")
        print(f"✅ Completed: {completed}")
        print(f"❌ Failed: {failed}")
        print(f"📅 Last session: {progress_state.get('session_start', 'Unknown')}")
        if progress_state.get('in_progress'):
            print(f"🔄 Last processing: Video {progress_state['in_progress']}")
        sys.exit(0)
    
    # Determine which videos to process
    if sys.argv[1] == '--from-file':
        if len(sys.argv) < 3:
            print("Usage: python granicus_transcribe_resumeable.py --from-file <filename>")
            sys.exit(1)
        all_clip_ids = load_video_ids_from_file(sys.argv[2])
    elif sys.argv[1] == '--resume':
        all_clip_ids = load_video_ids_from_file('video_ids.json')
        if not all_clip_ids:
            all_clip_ids = load_video_ids_from_file('remaining_video_ids.json')
    else:
        all_clip_ids = sys.argv[1:]
    
    if not all_clip_ids:
        print("No video IDs to process")
        sys.exit(0)
    
    # Filter out already completed videos
    completed_set = set(progress_state['completed'])
    clip_ids = [vid for vid in all_clip_ids if vid not in completed_set]
    
    total_videos = len(all_clip_ids)
    remaining_videos = len(clip_ids)
    
    print(f"\n📋 Processing Plan:")
    print(f"Total videos: {total_videos}")
    print(f"Already completed: {len(completed_set)}")
    print(f"Remaining to process: {remaining_videos}")
    
    if remaining_videos == 0:
        print("🎉 All videos already completed!")
        sys.exit(0)
    
    create_resume_script(dirs)
    
    # Process videos
    for i, clip_id in enumerate(clip_ids, 1):
        if killer.kill_now:
            print("🛑 Graceful shutdown requested")
            break
        
        progress_state['in_progress'] = clip_id
        save_progress_state(dirs, progress_state)
        
        print(f"\n{'='*60}")
        print(f"🎬 Processing video {clip_id} ({i}/{remaining_videos})")
        print_status(dirs, clip_id, total_videos, progress_state)
        print(f"{'='*60}")
        
        try:
            # Download video (30 min timeout)
            video_file = download_video_with_timeout(clip_id, dirs, timeout_minutes=30)
            if not video_file:
                progress_state['failed'].append(clip_id)
                save_progress_state(dirs, progress_state)
                continue
            
            # Transcribe video (2 hour timeout)
            transcript_file = transcribe_video_with_timeout(video_file, clip_id, dirs, timeout_minutes=120)
            
            if transcript_file:
                print(f"✅ Process complete for video {clip_id}")
                print(f"  🎥 Video: {Path(video_file).name}")
                print(f"  📄 Transcript: {Path(transcript_file).name}")
                
                # Clean up video file
                cleanup_video_file(video_file)
                
                progress_state['completed'].append(clip_id)
            else:
                print(f"❌ Transcription failed for video {clip_id}")
                progress_state['failed'].append(clip_id)
                # Keep video file for manual retry if needed
            
            progress_state['in_progress'] = None
            save_progress_state(dirs, progress_state)
            
            # Save progress every video (more frequent than every 10)
            if i % 5 == 0:  # Status update every 5 videos
                print_status(dirs, "Next", total_videos, progress_state)
                
        except Exception as e:
            print(f"❌ Unexpected error for video {clip_id}: {e}")
            progress_state['failed'].append(clip_id)
            progress_state['in_progress'] = None
            save_progress_state(dirs, progress_state)
    
    # Final summary
    completed = len(progress_state['completed'])
    failed = len(progress_state['failed'])
    
    print(f"\n{'='*60}")
    print(f"📊 FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Total completed: {completed}")
    print(f"❌ Total failed: {failed}")
    
    if failed > 0:
        print(f"\n🔄 To retry failed videos:")
        print(f"python granicus_transcribe_resumeable.py {' '.join(progress_state['failed'][:10])}...")
    
    progress_state['in_progress'] = None
    save_progress_state(dirs, progress_state)
    
    print(f"\n📁 All files organized in: fcva_videos/")
    print(f"📊 Resume anytime with: ./fcva_videos/logs/resume.sh")

if __name__ == "__main__":
    main()
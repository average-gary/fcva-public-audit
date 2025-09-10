# Frederick County Virginia Board of Supervisors Meeting Transcription Project

## Project Overview

This project provides automated tools to discover, download, and transcribe public meeting videos from the Frederick County Virginia Board of Supervisors. The goal is to create a comprehensive, searchable archive of public meetings to improve government transparency and public access to local government proceedings.

## Key Features

- **Automated Video Discovery**: Intelligent scanning of the FCVA Granicus video platform
- **Bulk Video Processing**: Download and transcription of hundreds of meeting videos
- **Multiple Output Formats**: Generates VTT (timestamps), SRT (subtitles), and TXT (plain text) transcripts
- **Organized File Structure**: Systematic organization of videos, transcripts, metadata, and logs
- **Resume Capability**: Can resume interrupted transcription processes
- **Progress Tracking**: Comprehensive logging and progress monitoring

## Project Status

- **Videos Discovered**: 239 meeting videos (IDs 2-291 with gaps)
- **Successfully Transcribed**: 42 videos and growing
- **File Organization**: fcva_videos/ with structured subdirectories
- **Data Source**: https://fcva.granicus.com/player/clip/{VIDEO_ID}

## Core Scripts

### 1. Video Discovery Scripts

#### `fcva_scraper_enhanced.py`
Advanced web scraper using Selenium to discover video IDs from the FCVA website.
- **Purpose**: Extract video IDs from the official FCVA meeting pages
- **Method**: Multi-strategy extraction including Selenium automation, HTML parsing, and API detection
- **Output**: `video_ids.json` with discovered video IDs
- **Usage**: `python fcva_scraper_enhanced.py`

#### `fcva_incremental_scraper.py` 
Smart incremental scanner that discovers videos by testing ID ranges.
- **Purpose**: Systematically find all available videos by testing sequential video IDs
- **Method**: Concurrent HTTP requests to test video availability
- **Strategy**: Adaptive range scanning with backwards/forwards discovery
- **Usage**: `python fcva_incremental_scraper.py`

### 2. Transcription Pipeline

#### `granicus_transcribe_organized.py`
Complete transcription pipeline with organized output structure.
- **Purpose**: Download videos and generate transcripts with proper organization
- **Features**:
  - Downloads videos using yt-dlp
  - Transcribes using OpenAI Whisper
  - Generates multiple output formats (VTT, SRT, TXT)
  - Automatically deletes video files after transcription to save space
  - Resume interrupted sessions
  - Comprehensive progress tracking and error logging

**Usage Examples**:
```bash
# Process specific video IDs
python granicus_transcribe_organized.py 28 29 30

# Process all videos from file
python granicus_transcribe_organized.py --from-file video_ids.json

# Resume interrupted session
python granicus_transcribe_organized.py --resume
```

## File Organization

```
fcva-public-audit/
├── fcva_videos/                    # Main output directory
│   ├── transcripts/               # Final transcripts (42 files)
│   │   ├── video_2.txt           # Plain text transcript
│   │   ├── video_15.txt
│   │   └── ...
│   ├── metadata/                  # Video metadata from yt-dlp
│   │   ├── video_2_info.json
│   │   └── ...
│   ├── logs/                      # Process logs and reports
│   │   ├── transcription_summary.md
│   │   ├── transcription_progress.json
│   │   ├── download_errors.log
│   │   └── transcription_errors.log
│   └── videos/                    # Temporary downloads (auto-deleted)
├── video_ids.json                 # Master list of 239 video IDs
├── remaining_video_ids.json       # Videos still to process
├── video_discovery_log.md         # Documentation of discovery process
└── [script files]
```

## Data Sources

### FCVA Granicus Platform
- **Base URL**: https://fcva.granicus.com/player/clip/{VIDEO_ID}
- **Video Range**: IDs 2 to 291 (239 videos total, with gaps)
- **Content**: Frederick County Board of Supervisors meeting recordings
- **Format**: Various video formats (MP4, WebM, etc.)

### Meeting Coverage
The transcribed videos include:
- Regular Board of Supervisors meetings
- Public hearings
- Special meetings
- Work sessions
- Committee meetings

## Technical Requirements

### Dependencies
- **Python 3.7+**
- **yt-dlp**: For video downloading from Granicus platform
- **OpenAI Whisper**: For speech-to-text transcription
- **Selenium**: For web scraping and automation
- **BeautifulSoup**: For HTML parsing
- **requests**: For HTTP operations

### Installation
```bash
# Install Python dependencies
pip install yt-dlp openai-whisper selenium beautifulsoup4 requests

# Install system dependencies (macOS)
brew install whisper
```

## Usage Workflows

### Complete New Setup
```bash
# 1. Discover all available videos
python fcva_incremental_scraper.py

# 2. Start transcription process
python granicus_transcribe_organized.py --from-file video_ids.json
```

### Resume Interrupted Transcription
```bash
# Resume from where you left off
python granicus_transcribe_organized.py --resume
```

### Process Specific Videos
```bash
# Process just a few specific meetings
python granicus_transcribe_organized.py 28 29 30 31
```

## Output Formats

### Transcripts
- **TXT**: Plain text transcripts for easy reading and text analysis
- **VTT**: WebVTT format with timestamps for video synchronization  
- **SRT**: SubRip format for subtitle display

### Metadata
- **JSON**: Complete video metadata including title, duration, upload date, description
- **Logs**: Detailed processing logs with success/failure tracking

## Progress Tracking

The system maintains comprehensive logs:
- **Success Log**: Successfully processed videos
- **Error Logs**: Download and transcription failures with error details
- **Progress JSON**: Resume-capable progress tracking
- **Summary Report**: High-level statistics and completion status

## Performance Characteristics

- **Processing Speed**: ~3-5 videos per hour depending on video length
- **Storage**: ~100MB per hour of video content (transcripts + metadata only)
- **Success Rate**: Currently processing successfully, with error handling for edge cases
- **Resume**: Robust resume capability for long-running processes

## Use Cases

### Public Transparency
- Citizens can search meeting transcripts for specific topics
- Journalists can quickly find relevant discussion segments
- Researchers can analyze local government proceedings

### Government Accountability
- Track voting patterns and policy discussions
- Monitor budget discussions and decisions
- Analyze public comment periods and responses

### Civic Engagement
- Easier access to meeting content for busy citizens
- Historical archive of government proceedings
- Searchable database of policy decisions

## Legal and Ethical Considerations

- **Public Domain**: All content is from public government meetings
- **Transparency**: Enhances government transparency and public access
- **Accuracy**: Transcripts are automated and may contain errors; original videos remain authoritative
- **Attribution**: Content sourced from Frederick County Virginia official recordings

## Future Enhancements

### Planned Features
- **Search Interface**: Web-based search across all transcripts
- **Topic Classification**: Automatic categorization of meeting topics
- **Speaker Identification**: Distinguish between different speakers
- **Quality Metrics**: Accuracy assessment and improvement tracking

### Technical Improvements
- **Parallel Processing**: Speed up transcription with concurrent processing
- **Better Error Handling**: More robust failure recovery
- **Cloud Storage**: Integration with cloud storage for larger archives
- **API Access**: Programmatic access to transcript database

## Maintenance

### Regular Updates
```bash
# Check for new videos monthly
python fcva_incremental_scraper.py

# Process any new discoveries
python granicus_transcribe_organized.py --resume
```

### Storage Management
- Video files are automatically deleted after successful transcription
- Transcripts and metadata are retained permanently
- Logs can be archived periodically to manage disk usage

## Contact and Contributions

This project enhances public access to local government proceedings. For questions, improvements, or collaboration opportunities, see the project repository.

## Commands Summary

```bash
# Quick command reference for common operations

# Discovery
python fcva_incremental_scraper.py           # Find all videos
python fcva_scraper_enhanced.py             # Alternative web scraper

# Transcription  
python granicus_transcribe_organized.py --from-file video_ids.json    # Process all
python granicus_transcribe_organized.py --resume                      # Resume
python granicus_transcribe_organized.py 28 29 30                      # Specific IDs

# Status checking
ls fcva_videos/transcripts/ | wc -l          # Count completed transcripts
cat fcva_videos/logs/transcription_summary.md # View progress report
```
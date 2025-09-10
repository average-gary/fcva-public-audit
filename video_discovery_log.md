# FCVA Video Discovery Log

## Summary
- **Total Videos Found**: 239
- **ID Range**: 2 to 291
- **Discovery Method**: Incremental scanning starting from known video ID 28
- **Discovery Date**: August 26, 2025

## Video URL Pattern
Videos follow the pattern: `https://fcva.granicus.com/player/clip/{VIDEO_ID}`

## Complete List of Video IDs
```
2, 4, 15, 18, 28, 29, 30, 31, 32, 33, 35, 37, 39, 40, 42, 43, 44, 45, 46, 48, 50, 51, 52, 53, 54, 55, 57, 58, 59, 60, 61, 62, 65, 66, 67, 68, 69, 70, 71, 72, 74, 75, 76, 77, 78, 79, 80, 81, 82, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 142, 145, 146, 147, 148, 149, 150, 151, 153, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 212, 213, 214, 215, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 232, 233, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291
```

## Gap Analysis
The following video IDs were tested but do not exist:
- IDs 1, 3, 5-14, 16-17, 19-27 (early range gaps)
- IDs 34, 36, 38, 41, 47, 49, 56, 63-64, 73, 83-85 (mid-range gaps)
- IDs 104, 125, 138-141, 143-144, 152, 154 (scattered gaps)
- IDs 210-211, 216, 231, 234, 257 (later range gaps)

## Discovery Timeline
1. **Backwards scan** (IDs 1-27): Found 4 videos
2. **Initial forward scan** (IDs 28-128): Found 86 videos
3. **Extended scan 1** (IDs 129-229): Found 90 videos  
4. **Extended scan 2** (IDs 230-380): Found 59 videos
5. **Final optimization**: Stopped at ID 291 (last confirmed video)

## Next Steps
- Download all 239 videos using `python granicus_transcribe.py --from-file video_ids.json`
- Transcribe using OpenAI Whisper with timestamps
- Generate VTT, SRT, and TXT formats for each video
- Archive both videos and transcripts for public analysis

## Files Generated
- `video_ids.json` - Machine-readable list of all video IDs
- `fcva_incremental_scraper.py` - Reusable scraper for future updates
- `granicus_transcribe.py` - Complete transcription pipeline
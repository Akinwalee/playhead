import logging
import re
from typing import List, Dict, Optional
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import yt_dlp

logger = logging.getLogger(__name__)

class YouTubeScraper:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
        }

    def _get_video_id(self, url: str) -> Optional[str]:
        """Extracts video ID from a YouTube URL."""
        parsed = urlparse(url)
        if parsed.hostname in ('youtu.be', 'www.youtu.be'):
            return parsed.path[1:]
        if parsed.hostname in ('youtube.com', 'www.youtube.com'):
            if parsed.path == '/watch':
                return parse_qs(parsed.query).get('v', [None])[0]
            if parsed.path.startswith('/shorts/'):
                return parsed.path.split('/')[2]
        return None

    def _get_playlist_videos(self, url: str) -> List[str]:
        """Extracts all video IDs from a playlist or channel URL using yt-dlp."""
        video_ids = []
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry and 'id' in entry:
                            video_ids.append(entry['id'])
            except Exception as e:
                logger.error(f"Error fetching playlist info: {e}")
        return video_ids

    def get_video_ids(self, url: str) -> List[str]:
        """Determines if URL is single video or playlist/channel and returns list of video IDs."""
        video_id = self._get_video_id(url)
        if video_id:
            return [video_id]
        
        return self._get_playlist_videos(url)

    def get_transcript(self, video_id: str) -> Optional[str]:
        """Fetches transcript for a single video."""
        try:
            yt_api = YouTubeTranscriptApi()
            transcript_list = yt_api.fetch(video_id)

            full_text = " ".join([t.text for t in transcript_list])
            return full_text
        except Exception as e:
            logger.warning(f"No transcript found for {video_id}: {e}")
            return None

    def scrape(self, url: str) -> List[Dict]:
        """Main entry point: Scrapes transcripts for all videos found at URL."""
        video_ids = self.get_video_ids(url)
        logger.info(f"Found {len(video_ids)} videos to scrape.")
        
        results = []
        for vid in video_ids:
            text = self.get_transcript(vid)
            if text:
                results.append({
                    "video_id": vid,
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "text": text
                })

                logger.info("Scraped video text: ", text)
        
        return results

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = YouTubeScraper()
    # print(scraper.scrape("https://www.youtube.com/watch?v=jNQXAC9IVRw")) 

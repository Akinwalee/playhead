from typing import List, Dict

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.session_videos = {}
        return cls._instance

    def add_video(self, session_id: str, video_data: Dict):
        """Adds a video to the session's list if it's not already there."""
        if session_id not in self.session_videos:
            self.session_videos[session_id] = []
        
        if not any(v['video_id'] == video_data['video_id'] for v in self.session_videos[session_id]):
            self.session_videos[session_id].append(video_data)

    def get_videos(self, session_id: str) -> List[Dict]:
        """Returns the list of videos for a given session."""
        return self.session_videos.get(session_id, [])

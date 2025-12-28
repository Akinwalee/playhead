
from youtube_transcript_api import YouTubeTranscriptApi
video_id = "jNQXAC9IVRw"

try:
    print("Trying instantiation...")
    api = YouTubeTranscriptApi()
    print("Instantiation success")
    
    try:
        print("Trying instance list...")
        t_list = api.list(video_id)
        print("Instance list result:", t_list)
    except Exception as e:
        print("Instance list failed:", e)

    try:
        print("Trying instance fetch...")
        t_fetch = api.fetch(video_id)
        print("Instance fetch success")
        print("Fetch result type:", type(t_fetch))
        print("Fetch result sample (first item):", t_fetch[0] if t_fetch else "Empty")
        print("First item type:", type(t_fetch[0]) if t_fetch else "N/A")
    except Exception as e:
        print("Instance fetch failed:", e)

except Exception as e:
    print("Instantiation failed:", e)

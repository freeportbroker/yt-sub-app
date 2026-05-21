import re
import sys
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url_or_id):
    if re.fullmatch(r"[\w-]{11}", url_or_id):
        return url_or_id

    patterns = [
        r"v=([\w-]{11})",
        r"youtu\.be/([\w-]{11})",
        r"shorts/([\w-]{11})",
        r"embed/([\w-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    raise ValueError("Could not find a valid YouTube video ID.")


def get_english_subtitles(video_id):
    ytt_api = YouTubeTranscriptApi()

    try:
        fetched = ytt_api.fetch(video_id, languages=["en"])
        return "\n".join([item.text for item in fetched])
    except Exception:
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python yt_sub_app.py YOUTUBE_LINK")
        return

    url = sys.argv[1]

    try:
        video_id = extract_video_id(url)
        subtitles = get_english_subtitles(video_id)

        if subtitles:
            print(subtitles)
        else:
            print("No English subtitles found.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
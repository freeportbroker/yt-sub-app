import re
import sys
import json
import html
import urllib.request
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


def remove_duplicate_lines(lines):
    cleaned = []
    previous = None

    for line in lines:
        line = line.strip()
        if line and line != previous:
            cleaned.append(line)
            previous = line

    return cleaned


def fetched_to_text(fetched_transcript):
    return "\n".join([item.text for item in fetched_transcript])


def try_youtube_transcript_api(video_id):
    ytt_api = YouTubeTranscriptApi()
    transcript_list = ytt_api.list(video_id)

    english_codes = ["en", "en-US", "en-GB"]

    try:
        transcript = transcript_list.find_manually_created_transcript(english_codes)
        return fetched_to_text(transcript.fetch())
    except Exception:
        pass

    try:
        transcript = transcript_list.find_generated_transcript(english_codes)
        return fetched_to_text(transcript.fetch())
    except Exception:
        pass

    for transcript in transcript_list:
        try:
            if transcript.language_code.lower().startswith("en"):
                return fetched_to_text(transcript.fetch())
        except Exception:
            pass

    return None


def download_text(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def json3_to_text(content):
    data = json.loads(content)
    lines = []

    for event in data.get("events", []):
        pieces = event.get("segs", [])
        text = "".join(piece.get("utf8", "") for piece in pieces)
        text = html.unescape(text).strip()

        if text:
            lines.append(text)

    return "\n".join(remove_duplicate_lines(lines))


def vtt_to_text(content):
    lines = []

    for raw_line in content.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("WEBVTT"):
            continue

        if line.startswith("Kind:") or line.startswith("Language:"):
            continue

        if "-->" in line:
            continue

        if re.fullmatch(r"\d+", line):
            continue

        line = re.sub(r"<[^>]+>", "", line)
        line = html.unescape(line).strip()

        if line:
            lines.append(line)

    return "\n".join(remove_duplicate_lines(lines))


def track_to_text(track):
    content = download_text(track["url"])
    ext = track.get("ext", "").lower()

    if ext == "json3" or content.lstrip().startswith("{"):
        return json3_to_text(content)

    return vtt_to_text(content)


def choose_best_track(track_group):
    if not track_group:
        return None

    preferred_languages = ["en", "en-US", "en-GB", "en-orig"]

    for language in preferred_languages:
        if language in track_group:
            return choose_best_format(track_group[language])

    for language, tracks in track_group.items():
        if language.lower().startswith("en"):
            return choose_best_format(tracks)

    return None


def choose_best_format(tracks):
    preferred_formats = ["json3", "vtt", "srv3", "ttml"]

    for preferred_format in preferred_formats:
        for track in tracks:
            if track.get("ext") == preferred_format and track.get("url"):
                return track

    for track in tracks:
        if track.get("url"):
            return track

    return None


def try_ytdlp(video_id):
    try:
        from yt_dlp import YoutubeDL
    except ImportError:
        raise RuntimeError("yt-dlp is not installed. Run: python -m pip install yt-dlp")

    url = f"https://www.youtube.com/watch?v={video_id}"

    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)

    manual_track = choose_best_track(info.get("subtitles", {}))
    if manual_track:
        return track_to_text(manual_track)

    auto_track = choose_best_track(info.get("automatic_captions", {}))
    if auto_track:
        return track_to_text(auto_track)

    return None


def get_english_subtitles(video_id):
    try:
        subtitles = try_youtube_transcript_api(video_id)
        if subtitles:
            return subtitles
    except Exception:
        pass

    subtitles = try_ytdlp(video_id)
    if subtitles:
        return subtitles

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
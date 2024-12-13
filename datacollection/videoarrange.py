import yt_dlp
import os
import re
from typing import Dict, Any

def sanitize_filename(title: str) -> str:
    """Sanitizes a string to be safe for use as a filename.

    Args:
        title: The string to sanitize.

    Returns:
        A sanitized string.
    """
    return re.sub(r'[\\/*?:"<>|]', "", title)

def download_and_process_video(url: str) -> None:
    """Downloads video, audio, and transcript from a YouTube URL.

    Args:
        url: The YouTube video URL.

    Raises:
        ValueError: If the URL is invalid or not from YouTube.
        yt_dlp.utils.DownloadError: If there is an error during download.
        Exception: For other unexpected errors.
    """
    if not url.startswith("https://www.youtube.com/watch?v="):
        raise ValueError("Invalid YouTube URL provided.")

    try:
        ydl_opts: Dict[str, Any] = {
            'format': 'bestvideo+bestaudio/best',
            'writesubtitles': True,
            'skip_download': False,
            'outtmpl': '%(id)s/%(title)s.%(ext)s',
            'subtitleslangs': ['en'],  # You can modify the list for other languages
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_id: str = info_dict.get("id", None)
            video_title: str = info_dict.get('title', None)

            if not video_id or not video_title:
                raise ValueError("Could not extract video ID or title.")

            sanitized_title: str = sanitize_filename(video_title)
            folder_name: str = video_id

            if not os.path.exists(folder_name):
                os.makedirs(folder_name)

            print(f"Downloading video: {sanitized_title} (ID: {video_id})")

            # Download the video and audio
            ydl.download([url])

            # Handle potential subtitle download issues gracefully
            try:
                # If subtitles were not downloaded, try again with only subtitles
                subtitle_file = os.path.join(
                    folder_name, f"{sanitized_title}.en.vtt"
                )
                if not os.path.exists(subtitle_file):
                    print("Subtitles not found, attempting to download separately...")
                    ydl_opts_subs: Dict[str, Any] = {
                        'writesubtitles': True,
                        'skip_download': True,
                        'outtmpl': '%(id)s/%(title)s.%(ext)s',
                        'subtitleslangs': ['en'],
                        'writeautomaticsub': False, # Avoid automatic subs
                    }
                    with yt_dlp.YoutubeDL(ydl_opts_subs) as ydl_subs:
                        ydl_subs.download([url])
            except Exception as e:
                print(f"Warning: Could not download subtitles: {e}")

            print(
                f"Video, audio, and transcript saved to folder: {folder_name}"
            )

    except yt_dlp.utils.DownloadError as e:
        raise yt_dlp.utils.DownloadError(f"Download error: {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    url: str = "https://www.youtube.com/watch?v=W7ppd_RY-UE"
    try:
        download_and_process_video(url)
    except ValueError as e:
        print(f"Error: {e}")
    except yt_dlp.utils.DownloadError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

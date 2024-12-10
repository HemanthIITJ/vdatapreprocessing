import os
import subprocess
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs
import os
import subprocess
from typing import List, Optional

def extract_video_id(url: str) -> Optional[str]:
    """
    Extract the video ID from a YouTube URL.
    
    Args:
        url (str): The YouTube video URL.
    
    Returns:
        Optional[str]: The video ID if found, None otherwise.
    """
    parsed_url = urlparse(url)
    if parsed_url.netloc == 'youtu.be':
        return parsed_url.path[1:]
    if parsed_url.netloc in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            p = parse_qs(parsed_url.query)
            return p.get('v', [None])[0]
        if parsed_url.path[:7] == '/embed/':
            return parsed_url.path.split('/')[2]
        if parsed_url.path[:3] == '/v/':
            return parsed_url.path.split('/')[2]
    return None

def download_youtube_video(video_url: str, download_folder: str) -> Optional[str]:
    """
    Download a YouTube video to the specified folder.
    
    Args:
        video_url (str): The URL of the YouTube video.
        download_folder (str): The folder where the video will be downloaded.
    
    Returns:
        Optional[str]: The path of the downloaded video file, or None if download failed.
    """
    video_id = extract_video_id(video_url)
    if not video_id:
        print(f"Invalid YouTube URL: {video_url}")
        return None

    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    
    output_template = os.path.join(download_folder, f"{video_id}.%(ext)s")
    command = [
        'yt-dlp',
        '-f', 'bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best',
        '-o', output_template,
        video_url
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error downloading video {video_id}: {e.stderr}")
        return None
    
    downloaded_files = [f for f in os.listdir(download_folder) if f.startswith(video_id)]
    if not downloaded_files:
        print(f"No files were downloaded for video {video_id}.")
        return None
    
    video_path = os.path.join(download_folder, downloaded_files[0])
    print(f"Downloaded: {video_path}")
    return video_path

def download_videos(urls: List[str], download_folder: str) -> List[Optional[str]]:
    """
    Download multiple YouTube videos concurrently.
    
    Args:
        urls (List[str]): A list of YouTube video URLs.
        download_folder (str): The folder where videos will be downloaded.
    
    Returns:
        List[Optional[str]]: A list of paths to downloaded video files, or None for failed downloads.
    """
    with ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(download_youtube_video, url, download_folder): url for url in urls}
        results = []
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                print(f"{url} generated an exception: {exc}")
                results.append(None)
    return results



def download_youtube_video(video_url: str, download_folder: str) -> Optional[str]:
    """
    Downloads a YouTube video using yt-dlp and saves it in the specified folder.

    Args:
        video_url (str): The URL of the YouTube video to download.
        download_folder (str): The folder where the video will be saved.

    Returns:
        Optional[str]: The path to the downloaded video file, or None if download failed.
    """
    if not os.path.exists(download_folder):
        os.makedirs(download_folder, exist_ok=True)

    command = [
        'yt-dlp',
        '-o', os.path.join(download_folder, '%(id)s.%(ext)s'),
        video_url
    ]

    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=True
        )
        if result.stderr:
            print("Error downloading video:", result.stderr)
            return None
    except subprocess.CalledProcessError as e:
        print("Error occurred while downloading video:", e.stderr)
        return None

    downloaded_files = os.listdir(download_folder)
    if not downloaded_files:
        print("No files were downloaded.")
        return None

    video_path = os.path.join(download_folder, downloaded_files[0])
    print(f"Downloaded: {video_path}")
    return video_path


def download_videos(video_urls: List[str], download_folder: str) -> List[Optional[str]]:
    """
    Downloads multiple YouTube videos and returns their file paths.

    Args:
        video_urls (List[str]): A list of YouTube video URLs to download.
        download_folder (str): The folder where the videos will be saved.

    Returns:
        List[Optional[str]]: A list of paths to the downloaded video files.
    """
    downloaded_videos = []
    for video_url in video_urls:
        video_path = download_youtube_video(video_url, download_folder)
        downloaded_videos.append(video_path)
    return downloaded_videos


# Example usage
if __name__ == "__main__":
    urls = [
        "https://www.youtube.com/watch?v=W7ppd_RY-UE",
    ]
    download_folder = "./videos"
    download_videos(urls, download_folder)
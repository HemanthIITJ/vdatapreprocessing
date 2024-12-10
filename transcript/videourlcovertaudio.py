import yt_dlp


def extract_audio(video_url: str, output_file: str) -> bool:
    """
    Extracts audio from a YouTube video and saves it to the specified output file.

    Args:
        video_url (str): The URL of the YouTube video.
        output_file (str): The path where the extracted audio will be saved.

    Returns:
        bool: True if the audio extraction was successful, False otherwise.
    """
    try:
        # yt_dlp options for audio extraction
        ydl_opts = {
            'format': 'bestaudio/best',  # Download the best available audio quality
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',  # Use FFmpeg to extract audio
                    'preferredcodec': 'mp3',  # Save as MP3 format
                    'preferredquality': '192',  # Set audio quality to 192kbps
                }
            ],
            'outtmpl': output_file,  # Specify output file name and location
            'quiet': True,  # Suppress yt_dlp console output
        }

        # Use yt_dlp to download and process the audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        print(f"Audio successfully extracted and saved to: {output_file}")
        return True

    except yt_dlp.utils.DownloadError as e:
        print(f"Failed to download video data: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return False



# video_processor.py
import subprocess
import shlex
from typing import Dict, Union, Tuple
import os
from pathlib import Path
import re

def validate_video_path(video_path: str) -> None:
    """Validates if the path exists and if the file is a valid video format.

        Args:
            video_path: Path to the input video.

        Raises:
            FileNotFoundError: If the path does not exist.
            ValueError: If the file is not a video.
        """
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found at: {video_path}")

    # rudimentary check if the file is a video, you may need to refine this for different cases
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv','.webm']
    if not path.suffix.lower() in video_extensions:
         raise ValueError(f"The provided path doesn't point to a valid video file. Supported file extensions are: {', '.join(video_extensions)}")


def _is_ffmpeg_input_readable(input_path: str) -> Tuple[bool, str]:
    """Checks if ffmpeg can read the input file using ffprobe.

        Args:
           input_path: Path to the input video file.

        Returns:
           A tuple containing a boolean indicating success or failure and a message describing the outcome.
    """
    try:
        ffprobe_command = ["ffprobe", "-v", "error", "-show_entries", "format=format_name", "-of", "default=noprint_wrappers=1:nokey=1", shlex.quote(input_path)]
        result = subprocess.run(ffprobe_command, shell=True, check=False, capture_output=True, text=True)
        if result.returncode != 0:
                return False, f"ffprobe failed to read the input file. Error:\n{result.stderr}"
        return True, "Input file readable."
    except Exception as e:
        return False, f"An unexpected error occurred while running ffprobe: {e}"



def _build_ffmpeg_command(input_path: str, output_path: str, options: Dict[str, Union[str, int, float]]) -> str:
    """Builds the ffmpeg command based on user-provided options.

    Args:
        input_path: Path to the input video file.
        output_path: Path to the output video file.
        options: A dictionary of ffmpeg options and their values.

    Returns:
        The constructed ffmpeg command as a string.
    """

    command = ["ffmpeg", "-y", "-i", shlex.quote(input_path)] # -y will overwrite output file if exists
    for key, value in options.items():
        if value is not None:  # Skip options that are set to None
            command.append(f"-{key}")
            if not isinstance(value, bool): # if value is not boolean, then add the value to the command line
                command.append(str(value))

    command.append(shlex.quote(output_path))
    return " ".join(command)



def process_video(input_path: str, output_path: str, options: Dict[str, Union[str, int, float, bool]] = None) -> Tuple[bool, str]:
    """Processes a video file using ffmpeg.

    Args:
        input_path: Path to the input video file.
        output_path: Path to the output video file.
        options: A dictionary of ffmpeg options and their values.

    Returns:
        A tuple containing a boolean indicating success or failure and a message describing the outcome.
    """

    if options is None:
         options = {}
    try:
        validate_video_path(input_path)

        is_readable, read_message = _is_ffmpeg_input_readable(input_path)
        if not is_readable:
            return False, read_message


        ffmpeg_command = _build_ffmpeg_command(input_path, output_path, options)
        print(f"Executing command: {ffmpeg_command}") # For debugging, will remove on production version

        # Check if the output directory exists, create if it doesn't
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        result = subprocess.run(ffmpeg_command, shell=True, check=False, capture_output=True, text=True)

        if result.returncode != 0:
             error_message = result.stderr
            # specific error for input fail
             if re.search(r"Error opening input|Invalid argument", error_message):
                 return False, f"FFmpeg could not open the input file. It might be corrupted or use a codec that isn't supported by your ffmpeg: \n{error_message}"

             return False, f"FFmpeg command failed with error code {result.returncode}. Error:\n{error_message}"
        return True, "Video processing successful."

    except FileNotFoundError as e:
        return False, f"Error: {e}"
    except subprocess.CalledProcessError as e:
        return False, f"Error during ffmpeg execution: {e.stderr} "
    except ValueError as e:
        return False, f"Error: {e}"
    except Exception as e:
        return False, f"An unexpected error occurred: {e}"


if __name__ == '__main__':
     # Example Usage:
    input_video = "E:/LLMS/Fine-tuning/W7ppd_RY-UE/test.webm"
    output_video = "output.mp4" # Replace with your output video path

    # Create a dummy input.mp4 file for testing
    if not os.path.exists(input_video):
        open(input_video, 'w').close()
        print("Warning: Dummy input.mp4 created for testing, replace with a real file.")

    processing_options = {
        "b:v": "2000k",  # example bit rate
        "vf": "scale=1280:720",  # video filter example for scaling
        "af": "volume=2", # audio filter example for increasing volume
        "r": 30 # fps

    }
    success, message = process_video(input_video, output_video, processing_options)

    if success:
        print(f"Success: {message}")
    else:
        print(f"Failure: {message}")
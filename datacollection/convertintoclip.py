import os
import subprocess
import sys
from typing import Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_video_duration(video_path: str) -> float:
    """
    Gets the duration of a video using ffprobe.

    Args:
        video_path: Path to the video file.

    Returns:
        The duration of the video in seconds.

    Raises:
        FileNotFoundError: If the video file does not exist.
        RuntimeError: If ffprobe is not installed or if there's an error
                      during execution.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                video_path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Error getting video duration with ffprobe: {e}"
            f"Please ensure ffprobe is installed."
        ) from e
    except ValueError as e:
        raise RuntimeError(
            f"Error parsing ffprobe output for duration: {e}"
        ) from e


def split_video(
    video_path: str,
    output_dir: str,
    num_segments: int,
    start_time: float = 0.0,
    end_time: float = None,
) -> Tuple[str, int]:
    """
    Splits a video into equal segments without re-encoding, preserving quality.

    Args:
        video_path: Path to the input video file.
        output_dir: Directory to save the output segments.
        num_segments: Number of segments to split the video into.
        start_time: Optional start time of the part to split (in seconds).
                    Defaults to 0, the beginning of the video.
        end_time: Optional end time of the part to split (in seconds).
                  Defaults to None, indicating the end of the video.

    Returns:
        A tuple containing the output directory and the number of segments.

    Raises:
        FileNotFoundError: If the video file does not exist.
        ValueError: If the number of segments is invalid.
        RuntimeError: If ffmpeg is not installed, if there's an error during
                      execution, or if the output directory doesn't exist.
    """

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except OSError as e:
            raise RuntimeError(f"Failed to create output directory: {e}") from e

    if num_segments <= 0:
        raise ValueError(
            f"Number of segments must be greater than 0, got {num_segments}"
        )

    total_duration = end_time or get_video_duration(video_path)
    total_duration -= start_time
    segment_duration = total_duration / num_segments

    base_name, ext = os.path.splitext(os.path.basename(video_path))

    commands = []
    for i in range(num_segments):
        current_start = start_time + i * segment_duration
        output_path = os.path.join(
            output_dir, f"{base_name}_segment{i+1:03}{ext}"
        )
        command = [
            "ffmpeg",
            "-ss",
            str(current_start),
            "-i",
            video_path,
            "-t",
            str(segment_duration),
            "-c",
            "copy",  # Copy streams without re-encoding
            "-map",
            "0",  # Select all streams
            "-avoid_negative_ts",
            "make_zero",  # Fix timestamp issues if any
            "-loglevel",
            "error",  # Reduce verbosity
            output_path,
        ]
        commands.append(command)

    try:
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(subprocess.run, cmd, check=True)
                for cmd in commands
            ]

            for future in as_completed(futures):
                future.result()  # Check for exceptions in threads

    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Error splitting video with ffmpeg: {e}"
            f"Please check your ffmpeg installation and command"
        ) from e

    return output_dir, num_segments


def main():
    """
    Main function to handle user input and control the video splitting process.
    """
    if len(sys.argv) < 3:
        print(
            "Usage: python script.py <video_path> <num_segments> "
            "[start_time] [end_time]"
        )
        sys.exit(1)

    video_path = sys.argv[1]
    try:
        num_segments = int(sys.argv[2])
    except ValueError:
        print("Error: Number of segments must be an integer.")
        sys.exit(1)

    start_time = float(sys.argv[3]) if len(sys.argv) >= 4 else 0.0
    end_time = (
        float(sys.argv[4]) if len(sys.argv) >= 5 else None
    )  # Optional end time

    output_dir = os.path.join(
        os.path.dirname(video_path), "output_segments"
    )

    try:
        output_dir, num_splits = split_video(
            video_path, output_dir, num_segments, start_time, end_time
        )
        print(
            f"Successfully split video into {num_splits} segments. "
            f"Output saved in: {output_dir}"
        )
    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
        subprocess.CalledProcessError,
    ) as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
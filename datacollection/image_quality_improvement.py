import os
import cv2
import math
from typing import List, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import shutil

def improve_image_quality(image_path: str, output_path: str,
                          weight: float = 1.0) -> None:
    """
    Improves the quality of an image using a placeholder algorithm.

    Args:
        image_path: Path to the input image.
        output_path: Path to save the improved image.
        weight: A factor controlling the strength of the improvement.
                 (e.g., 0.5 for weaker, 2.0 for stronger improvement)
    
    Raises:
        FileNotFoundError: If the input image file does not exist.
        Exception: For any other errors during image processing.
    """
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        img = cv2.imread(image_path)
        if img is None:
            raise Exception(f"Failed to load image: {image_path}")

        # Placeholder for image quality improvement algorithm.
        # Replace this with a more sophisticated algorithm 
        # (e.g., using super-resolution techniques, denoising, etc.)
        improved_img = cv2.addWeighted(img, weight, img, 0, 0)  # Simple blending example

        cv2.imwrite(output_path, improved_img)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"An error occurred while improving image quality: {e}")
        raise

def extract_frames_optimized(
    video_path: str,
    output_folder: str,
    max_frame_length: int,
    select_interval: int,
    weight: float = 1.0,
) -> List[str]:
    """
    Extracts frames from a video at specified intervals, enhances them, and saves them to a folder.

    Args:
        video_path: Path to the input video file.
        output_folder: Path to the folder where extracted frames will be saved.
        max_frame_length: Maximum number of frames to extract.
        select_interval: Time interval (in seconds) between selected frames.
        weight: Weight factor for image quality improvement.

    Returns:
        A list of paths to the extracted and enhanced image files.

    Raises:
        FileNotFoundError: If the video file does not exist.
        ValueError: If the output folder cannot be created or if invalid parameters are provided.
        Exception: For any other errors during video processing or frame extraction.
    """
    try:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if not output_folder:
            raise ValueError("Output folder path cannot be empty.")
        
        os.makedirs(output_folder, exist_ok=True)
        
        if max_frame_length <= 0 or select_interval <= 0:
            raise ValueError("max_frame_length and select_interval must be greater than 0.")
        
        
        # Use ffprobe to get the video duration directly
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of",
                "default=noprint_wrappers=1:nokey=1", video_path
            ], capture_output=True, text=True, check=True)
            video_duration = float(result.stdout)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error getting video duration with ffprobe: {e}")
        

        total_frames_to_extract = min(
            max_frame_length, math.ceil(video_duration / select_interval)
        )
        frame_interval = video_duration / total_frames_to_extract

        temp_folder = os.path.join(output_folder, "temp")
        os.makedirs(temp_folder, exist_ok=True)
        
        frame_paths = []

        # Optimized frame extraction using FFmpeg
        ffmpeg_command = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"fps=1/{frame_interval}",  # Calculate fps based on interval
            "-q:v", "2",  # High-quality output
            os.path.join(temp_folder, "frame%06d.jpg")
        ]
        subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)

        extracted_frames = sorted(
            [
                os.path.join(temp_folder, f)
                for f in os.listdir(temp_folder)
                if os.path.isfile(os.path.join(temp_folder, f)) and f.endswith(".jpg")
            ]
        )

        # Parallelize Image Enhancement
        with ThreadPoolExecutor() as executor:
            futures = []
            for i, frame_path in enumerate(extracted_frames):
                output_path = os.path.join(
                    output_folder, f"frame{i:06d}.jpg"
                )
                futures.append(
                    executor.submit(
                        improve_image_quality, frame_path, output_path, weight
                    )
                )
                frame_paths.append(output_path)

            for future in as_completed(futures):
                try:
                    future.result()  # Wait for each enhancement to complete
                except Exception as e:
                    print(f"Error improving image quality: {e}")
                    # Handle error appropriately (e.g., remove corresponding frame_path)
                    

        # Cleanup temporary folder
        shutil.rmtree(temp_folder)

        return frame_paths

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return []
    except ValueError as e:
        print(f"Error: {e}")
        return []
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e}")
        print(f"FFmpeg stdout: {e.stdout}")
        print(f"FFmpeg stderr: {e.stderr}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []
    

if __name__ == "__main__":
    video_path = r"E:\LLMS\Fine-tuning\W7ppd_RY-UE\test.webm"  # Replace with your video path
    output_folder = r"E:\LLMS\Fine-tuning\W7ppd_RY-UE\output_frames"  # Replace with your desired output folder
    max_frame_length = 16  # Maximum number of frames to extract
    select_interval = 2  # Extract frame every 2 seconds
    weight = 1.2  # Image quality improvement weight

    try:
        extracted_frames = extract_frames_optimized(
            video_path, output_folder, max_frame_length, select_interval, weight
        )
        if extracted_frames:
            print(f"Extracted and enhanced {len(extracted_frames)} frames:")
            for frame_path in extracted_frames:
                print(frame_path)
        else:
            print("No frames were extracted.")

    except Exception as e:
        print(f"An error occurred during the process: {e}")
import cv2
import os
from typing import List, Tuple
import math


def convert_video_to_images(
    video_path: str, output_folder: str, max_length: int = 100
) -> None:
    """
    Converts a video into a sequence of images, saved in the specified output folder.

    Args:
        video_path: The path to the input video file.
        output_folder: The path to the folder where images will be saved.
        max_length: The maximum number of images to extract (evenly spaced).

    Raises:
        FileNotFoundError: If the video file or output folder does not exist.
        ValueError: If max_length is not a positive integer.
        RuntimeError: If an error occurs during video processing.
    """

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if not os.path.exists(output_folder):
        try:
            os.makedirs(output_folder)
        except OSError as e:
            raise RuntimeError(
                f"Failed to create output directory: {output_folder}. Error: {e}"
            ) from e

    if not isinstance(max_length, int) or max_length <= 0:
        raise ValueError("max_length must be a positive integer.")

    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps

        if total_frames == 0:
            raise RuntimeError("Video has no frames.")

        frame_interval = math.ceil(total_frames / max_length)
        frame_count = 0
        image_count = 0
        
        # Optimize for better encoding using 4:4:4 chroma subsampling 
        # and higher quality setting. Note: This might increase file size.
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95, 
                        int(cv2.IMWRITE_JPEG_CHROMA_QUALITY), 444]  

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                image_name = os.path.join(
                    output_folder, f"image_{image_count:04d}.jpg"
                )
                try:
                  #  cv2.imwrite(image_name, frame)
                    cv2.imwrite(image_name, frame, encode_param)
                except cv2.error as e:
                  raise RuntimeError(f"Error saving image: {image_name}. Error: {e}") from e


                image_count += 1

            frame_count += 1

        cap.release()

        print(f"Successfully extracted {image_count} images from {video_path} to {output_folder}")

    except cv2.error as e:
        raise RuntimeError(f"OpenCV error during video processing: {e}") from e
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}") from e


# Example usage:
if __name__ == "__main__":
    video_path = r"E:\LLMS\Fine-tuning\videos\W7ppd_RY-UE.webm"
    output_folder = "output"  # Replace with your desired output folder
    max_length = int(input("Enter the maximum number of images to extract: "))

    try:
        convert_video_to_images(video_path, output_folder, max_length)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"Error: {e}")
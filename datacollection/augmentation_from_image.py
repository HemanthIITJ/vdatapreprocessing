import os
import sys
from typing import List, Tuple, Optional

from PIL import Image
from torchvision import transforms
from torchvision.transforms import functional as F


def load_and_process_images(
    input_folder: str,
    output_folder: str,
    target_size: Tuple[int, int],
    augmentations: Optional[List[transforms.transforms.Compose]] = None,  # Corrected type hint
) -> None:
    """
    Loads images from a folder, resizes them, applies augmentations, and saves
    the results.

    Args:
        input_folder: Path to the folder containing the input images.
        output_folder: Path to the folder where augmented images will be saved.
        target_size: Tuple (width, height) representing the desired image size.
        augmentations: Optional list of torchvision transformations to apply.

    Raises:
        FileNotFoundError: If the input folder does not exist.
        RuntimeError: If there is an error during image processing or saving.
    """
    try:
        if not os.path.exists(input_folder):
            raise FileNotFoundError(f"Input folder not found: {input_folder}")

        os.makedirs(output_folder, exist_ok=True)

        for filename in os.listdir(input_folder):
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                try:
                    img_path = os.path.join(input_folder, filename)
                    img = Image.open(img_path).convert("RGB")

                    # Resize the image
                    img_resized = F.resize(img, target_size)

                    # Apply augmentations if provided
                    if augmentations:
                        composed_augmentations = transforms.Compose(augmentations)
                        img_resized = composed_augmentations(img_resized)

                    # Save the processed image
                    output_filename = f"aug_{filename}"
                    output_path = os.path.join(output_folder, output_filename)
                    img_resized.save(output_path)

                except Exception as e:
                    print(
                        f"Error processing image {filename}: {e}",
                        file=sys.stderr,
                    )

    except FileNotFoundError:
        raise
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")


def main():
    """
    Main function to demonstrate image processing.
    """
    input_folder = "E:\\LLMS\\Fine-tuning\\output"  # Replace with your input folder
    output_folder = "aug_output"
    target_size = (224, 224)  # Example target size

    # Define a list of augmentations using torchvision.transforms
    augmentations = [
        transforms.ColorJitter(
            brightness=0.7, 
            contrast=0.5, 
            saturation=0.4),
    ]

    try:
        load_and_process_images(
            input_folder, output_folder, target_size, augmentations
        )
        print(
            f"Images processed and saved to {output_folder}"
        )
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
from typing import Optional, Union
import plotly.graph_objects as go
from PIL import Image
import numpy as np


def display_image_with_plotly(
    image_path: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    add_axes: bool = True,
) -> None:
    """
    Displays an image using Plotly, handling potential errors gracefully.

    Args:
        image_path: The path to the image file.
        width: Optional width of the displayed image.
        height: Optional height of the displayed image.
        add_axes: Whether to display x and y axes. Defaults to True.

    Raises:
        FileNotFoundError: If the image file does not exist.
        IOError: If the image file cannot be opened or is not a valid image.
        Exception: For other unexpected errors.
    """
    try:
        # Open the image using Pillow (PIL)
        img = Image.open(image_path)

        # Resize if width or height is specified
        if width or height:
            if width and height:
                img = img.resize((width, height))
            elif width:
                current_width, current_height = img.size
                new_height = int(current_height * (width / current_width))
                img = img.resize((width, new_height))
            else:  # Only height is specified
                current_width, current_height = img.size
                new_width = int(current_width * (height / current_height))
                img = img.resize((new_width, height))

        # If image has an alpha channel (transparency),
        # convert to RGBA to handle correctly
        if img.mode not in ("RGB", "RGBA", "L"):
            raise ValueError(
                f"Unsupported image mode: {img.mode}. "
                "Only RGB, RGBA, and L (grayscale) modes are supported."
            )

        # If the image is 8-bit indexed, convert it to 'RGB' or 'RGBA'

        if img.mode == 'P':
           if 'transparency' in img.info:
               img = img.convert('RGBA')
           else:
               img = img.convert('RGB')


        # Convert the image to a NumPy array for compatibility with Plotly
        img_array = np.array(img)

        # Create a Plotly figure
        fig = go.Figure()

        # Add the image as a trace
        if img.mode == "RGBA":
            fig.add_trace(
                go.Image(z=img_array, colormodel="rgba", zmin=[0, 0, 0, 0])
            )
        else:
            fig.add_trace(go.Image(z=img_array, zmin=[0, 0, 0]))

        # Update layout for better image display
        layout_args = dict(
            xaxis_visible=add_axes,
            yaxis_visible=add_axes,
            margin=dict(l=0, r=0, b=0, t=0),
            plot_bgcolor="rgba(0,0,0,0)",  # Transparent background
            paper_bgcolor="rgba(0,0,0,0)",
        )

        if add_axes:
            layout_args.update(
                dict(
                    xaxis=dict(
                        showgrid=False,
                        zeroline=False,
                        showticklabels=True,
                        range=[0, img_array.shape[1]],
                    ),
                    yaxis=dict(
                        showgrid=False,
                        zeroline=False,
                        showticklabels=True,
                        range=[img_array.shape[0], 0],
                    ),
                )
            )
        else:
            layout_args.update(
                dict(
                    xaxis=dict(
                        showgrid=False,
                        zeroline=False,
                        showticklabels=False,
                        range=[0, img_array.shape[1]],
                    ),
                    yaxis=dict(
                        showgrid=False,
                        zeroline=False,
                        showticklabels=False,
                        range=[img_array.shape[0], 0],
                    ),
                )
            )

        fig.update_layout(**layout_args)
        fig.update_xaxes(showline=True, linewidth=1, linecolor="black", mirror=True)
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black", mirror=True)

        # Show the figure
        fig.show()

    except FileNotFoundError:
        raise FileNotFoundError(f"Image file not found at: {image_path}")
    except (IOError, ValueError) as e:
        raise IOError(f"Error processing image: {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    # Example usage:
    image_path = r"" 

    try:
        display_image_with_plotly(image_path, width=800, add_axes=False)
    except (FileNotFoundError, IOError, Exception) as e:
        print(f"Error: {e}")
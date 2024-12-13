import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from PIL import Image
import numpy as np
from typing import List, Tuple, Dict
import colorsys
from skimage import io, exposure, filters, color

def analyze_image(image_path: str) -> Dict:
    """
    Analyzes an image and extracts various metrics.

    Args:
        image_path: Path to the image file.

    Returns:
        A dictionary containing image analysis results, including:
        - dimensions: (width, height)
        - dominant_colors: List of dominant colors (hex)
        - average_color: Average color (hex)
        - brightness: Average brightness (0-255)
        - contrast: Standard deviation of pixel intensities
        - sharpness: Laplacian variance as a measure of sharpness

    Raises:
        FileNotFoundError: If the image file does not exist.
        Exception: For any other errors during image processing.
    """
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        img = io.imread(image_path)

        if img is None:
            raise Exception(f"Failed to load image: {image_path}")
        
        # 1. Dimensions
        height, width = img.shape[:2]

        # 2. Dominant Colors (using k-means clustering as an example)
        img_lab = color.rgb2lab(img)
        pixels = img_lab.reshape((-1, 3))

        
        # for simplicity using a simple method 
        from collections import Counter
        num_colors = 5
        
        
        def rgb_to_hex(rgb):
            return '#%02x%02x%02x' % rgb

        if len(img.shape) == 3 and img.shape[2] == 3:
          dominant_colors = [rgb_to_hex(tuple(color)) for color, count in Counter(tuple(rgb) for row in img for rgb in row).most_common(num_colors)]
        else :
          dominant_colors = []

        # 3. Average Color
        average_color_rgb = tuple(np.mean(img, axis=(0, 1)).astype(int))[:3]
        average_color = rgb_to_hex(average_color_rgb)  
          

        # 4. Brightness (using the L channel in LAB color space)
        brightness = np.mean(pixels[:, 0])

        # 5. Contrast (standard deviation of L channel)
        contrast = np.std(pixels[:, 0])

        # 6. Sharpness (using Laplacian variance)
        if len(img.shape) == 3 and img.shape[2] == 3:
          gray_img = color.rgb2gray(img)
          sharpness = filters.laplace(gray_img).var()
        else:
          sharpness=0

        return {
            "dimensions": (width, height),
            "dominant_colors": dominant_colors,
            "average_color": average_color,
            "brightness": brightness,
            "contrast": contrast,
            "sharpness": sharpness,
        }

    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"An error occurred while analyzing image: {e}")
        raise

def create_visualizations(image_folder: str) -> None:
    """
    Creates and displays interactive visualizations based on image analysis results.

    Args:
        image_folder: Path to the folder containing images.

    Raises:
        FileNotFoundError: If the image folder does not exist.
        Exception: For any errors during image analysis or visualization creation.
    """
    try:
        if not os.path.exists(image_folder):
            raise FileNotFoundError(f"Image folder not found: {image_folder}")

        image_files = [
            os.path.join(image_folder, f)
            for f in os.listdir(image_folder)
            if os.path.isfile(os.path.join(image_folder, f))
            and f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))
        ]
        
        if not image_files:
            raise ValueError("No image files found in the specified folder.")

        analysis_results = []
        for image_file in image_files:
            try:
                analysis_results.append(analyze_image(image_file))
            except Exception as e:
                print(f"Skipping image {image_file} due to error: {e}")

        if not analysis_results:
            raise ValueError("No image analysis results could be generated.")

        # --- Visualization 1: Scatter Plot of Brightness vs. Contrast ---
        fig1 = px.scatter(
            analysis_results,
            x="brightness",
            y="contrast",
            title="Brightness vs. Contrast of Images",
            hover_data=["dimensions", "average_color"],
            color="average_color",  # Color points by average color
        )
        fig1.update_layout(
            xaxis_title="Brightness (0-100)",
            yaxis_title="Contrast",
            template="plotly_dark",  # Optional: Use a dark template
        )
        fig1.show()

        # --- Visualization 2: Image Grid with Dominant Colors ---
        num_images = len(analysis_results)
        rows = int(np.ceil(np.sqrt(num_images)))
        cols = int(np.ceil(num_images / rows))
        
        fig2 = make_subplots(rows=rows, cols=cols,
                             subplot_titles=[f"Image {i+1}" for i in range(num_images)],
                             specs=[[{"type": "image"} for _ in range(cols)] for _ in range(rows)])
        
        
        for i, (result, image_file) in enumerate(zip(analysis_results, image_files)):
            row = i // cols + 1
            col = i % cols + 1

            img = Image.open(image_file)  # Use PIL for displaying images
            fig2.add_trace(go.Image(z=img), row=row, col=col)

            # Add dominant colors as annotations below the image
            y_offset = -0.2 
            for j, dom_color in enumerate(result["dominant_colors"]):
                fig2.add_annotation(
                    x=col - 0.5,
                    y=row + y_offset - (j * 0.07),
                    text="",
                    showarrow=False,
                    xref="x",
                    yref="y",
                    bgcolor=dom_color,
                    width=40,
                    height=20,
                )
                fig2.add_annotation(
                  x=col - 0.5,
                  y=row + y_offset - (j * 0.07)-0.06,
                  text=dom_color,
                  showarrow=False,
                  xref="x",
                  yref="y",
                  font=dict(size=10, color="black" if int(dom_color[1:], 16) > 0xffffff/2 else "white"),
                  xanchor="center",
                  yanchor="top"
                )
           

        fig2.update_xaxes(showticklabels=False)
        fig2.update_yaxes(showticklabels=False)
        fig2.update_layout(title_text="Image Grid with Dominant Colors", template="plotly_dark", height=800)
        fig2.show()
    

        # --- Visualization 3: Parallel Coordinates Plot for Multiple Metrics ---
        dimensions = [result["dimensions"] for result in analysis_results]
        dimensions_df = [f"{w}x{h}" for w, h in dimensions]

        fig3 = go.Figure(data=go.Parcoords(
            line=dict(
                color=[i for i in range(len(analysis_results))],
                colorscale=px.colors.sequential.Viridis,
                showscale=True,
                cmin=0,
                cmax=len(analysis_results) - 1
            ),
            dimensions=list([
                dict(range=[0, len(analysis_results) - 1],
                     tickvals=[],
                     label="Image Index", values=[i for i in range(len(analysis_results))]),
                dict(
                    range=[
                        min(d[0] for d in dimensions),
                        max(d[0] for d in dimensions)
                    ],
                    label="Width",
                    values=[d[0] for d in dimensions]
                ),
                dict(
                    range=[
                        min(d[1] for d in dimensions),
                        max(d[1] for d in dimensions)
                    ],
                    label="Height",
                    values=[d[1] for d in dimensions]
                ),
                dict(
                    range=[0, 100],
                    label="Brightness",
                    values=[result["brightness"] for result in analysis_results]
                ),
                dict(
                    range=[
                        min(result["contrast"] for result in analysis_results),
                        max(result["contrast"] for result in analysis_results)
                    ],
                    label="Contrast",
                    values=[result["contrast"] for result in analysis_results]
                ),
                dict(
                    range=[
                        min(result["sharpness"] for result in analysis_results),
                        max(result["sharpness"] for result in analysis_results)
                    ],
                    label="Sharpness",
                    values=[result["sharpness"] for result in analysis_results]
                ),
            ])
        ))
        fig3.update_layout(
          title="Parallel Coordinates Plot of Image Metrics",
          template="plotly_dark"
        )
        fig3.show()

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    image_folder = r"E:\LLMS\Fine-tuning\W7ppd_RY-UE\output_frames"  # Replace with your image folder
    try:
        create_visualizations(image_folder)
    except Exception as e:
        print(f"An error occurred during visualization: {e}")
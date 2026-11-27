import math

from PIL import Image
from pathlib import Path

from skimage.color import rgb2lab
import numpy as np


DOWNSAMPLED_SIZE = (300, 300)
NUM_COLORS = 8


def rgb_to_lab(rgb: list[int]) -> list[float]:
    rgb_normalized = np.array(rgb, dtype=float) / 255.0
    rgb_reshaped = rgb_normalized.reshape(1, 1, 3)
    lab = rgb2lab(rgb_reshaped)
    return lab[0][0].tolist()


def lab_distance(lab1: list[float], lab2: list[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))


def convert_to_rgb(image_path: Path) -> Image.Image:
    image = Image.open(image_path)
    image = image.convert(mode="RGB")
    return image


def resize_image(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    image_resized = image.resize(size)
    return image_resized


def convert_to_numpy_array(image: Image.Image) -> np.ndarray:
    np_array = np.asarray(image)
    np_array = np_array.reshape(-1, 3)
    return np_array


def extract_color_palette(image_array: np.ndarray, num_colors: int) -> list[dict]:
    from sklearn import cluster  # heavy; only needed when importing

    kmeans = cluster.KMeans(n_clusters=num_colors).fit(image_array)
    cluster_centers = kmeans.cluster_centers_
    pixel_counts_per_cluster = np.bincount(kmeans.labels_)
    total_pixels = sum(pixel_counts_per_cluster)

    cluster_percentages = {
        cluster_index: (pixel_count / total_pixels) * 100
        for cluster_index, pixel_count in enumerate(pixel_counts_per_cluster)
    }
    sorted_clusters_by_dominance = dict(
        sorted(cluster_percentages.items(), key=lambda item: item[1], reverse=True)
    )

    integer_colors = cluster_centers.astype(np.uint8)
    color_palette = integer_colors.reshape(num_colors, 3)

    color_palette_with_percentages = []
    for cluster_index, percentage in sorted_clusters_by_dominance.items():
        color_palette_with_percentages.append(
            {
                "rgb": color_palette[cluster_index].tolist(),
                "lab": rgb_to_lab(color_palette[cluster_index].tolist()),
                "percentage": float(percentage),
            }
        )

    return color_palette_with_percentages


def process_and_extract_color_palette(
    image_path: Path,
    num_colors: int,
    downsampled_size: tuple[int, int] = DOWNSAMPLED_SIZE,
) -> list[dict]:
    """
    Loads an image, downsizes it, and extracts the most dominant colors using K-means.

    Parameters:
    - image_path (Path): Path to the image file.
    - num_colors (int): The number of dominant colors to extract.
    - downsampled_size (tuple): Target dimensions for downsizing, e.g., (150, 150).
    """
    img_rgb = convert_to_rgb(image_path=image_path)
    img_resized = resize_image(img_rgb, downsampled_size)
    np_array = convert_to_numpy_array(img_resized)
    color_palette_with_percentages = extract_color_palette(np_array, num_colors)

    return color_palette_with_percentages

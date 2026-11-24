import open_clip
import torch
from pathlib import Path

from .colors import convert_to_rgb


model, _, preprocess = open_clip.create_model_and_transforms(
    "ViT-B-32", pretrained="laion2b_s34b_b79k"
)
model.eval()


def preprocess_image_embedding(image_path: Path):
    image_rgb = convert_to_rgb(image_path)
    processed_image = preprocess(image_rgb)

    return processed_image


def batch_generator(iterable: list, batch_size=1):
    length = len(iterable)
    for ndx in range(0, length, batch_size):
        yield iterable[ndx : min(ndx + batch_size, length)]


def generate_embeddings_batch(image_paths: list[Path], batch_size: int = 16) -> list:
    processed_images = []
    for image_path in image_paths:
        processed_image = preprocess_image_embedding(image_path)
        processed_images.append(processed_image)

    embeddings = []
    for batch in batch_generator(iterable=processed_images, batch_size=batch_size):
        with torch.no_grad():
            tensor = torch.stack(batch)
            embeddings.extend(model.encode_image(tensor).tolist())
    return embeddings

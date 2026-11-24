import open_clip
import torch
from pathlib import Path
import os
import pickle
import hashlib

from .colors import convert_to_rgb


# Global model instance for reuse
_model = None
_preprocess = None

def get_model():
    global _model, _preprocess
    if _model is None:
        _model, _, _preprocess = open_clip.create_model_and_transforms(
            "RN50", pretrained="laion2b_s34b_b79k"
        )
        _model.eval()
    return _model, _preprocess

def preprocess_image_embedding(image_path: Path):
    _, preprocess = get_model()
    image_rgb = convert_to_rgb(image_path)
    processed_image = preprocess(image_rgb)
    return processed_image


def batch_generator(iterable: list, batch_size=1):
    length = len(iterable)
    for ndx in range(0, length, batch_size):
        yield iterable[ndx : min(ndx + batch_size, length)]


def get_cache_path(image_path):
    """Generate cache path based on image hash"""
    with open(image_path, 'rb') as f:
        image_hash = hashlib.md5(f.read()).hexdigest()
    return f"cache/{image_hash}.pkl"

def generate_embeddings_batch(image_paths: list[Path], batch_size: int = 8) -> list:
    """Generate embeddings with caching to reduce processing time"""
    # Check cache first
    cached_embeddings = []
    uncached_paths = []
    
    for image_path in image_paths:
        cache_path = get_cache_path(image_path)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    cached_embeddings.append(pickle.load(f))
            except:
                uncached_paths.append(image_path)
        else:
            uncached_paths.append(image_path)
    
    # Process uncached images
    embeddings = []
    if uncached_paths:
        processed_images = []
        for image_path in uncached_paths:
            processed_image = preprocess_image_embedding(image_path)
            processed_images.append(processed_image)

        model, _ = get_model()
        for batch in batch_generator(iterable=processed_images, batch_size=batch_size):
            with torch.no_grad():
                tensor = torch.stack(batch)
                batch_embeddings = model.encode_image(tensor).tolist()
                
                # Cache results
                for i, embedding in enumerate(batch_embeddings):
                    cache_path = get_cache_path(uncached_paths[len(cached_embeddings) + i])
                    with open(cache_path, 'wb') as f:
                        pickle.dump(embedding, f)
                
                embeddings.extend(batch_embeddings)
    
    # Combine cached and new embeddings
    all_embeddings = cached_embeddings + embeddings
    return all_embeddings
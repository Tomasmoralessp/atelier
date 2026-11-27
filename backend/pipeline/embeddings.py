from pathlib import Path

import open_clip
import torch

import settings
from .colors import convert_to_rgb

MODEL_NAME = "RN50"
PRETRAINED = "openai"

_model = None
_preprocess = None


def get_model():
    """Load CLIP once. Uses bundled weights when ATELIER_MODEL_PATH is set,
    otherwise downloads them once into the data folder."""
    global _model, _preprocess
    if _model is None:
        if settings.MODEL_PATH:
            pretrained, cache_dir = settings.MODEL_PATH, None
        else:
            pretrained, cache_dir = PRETRAINED, str(settings.MODELS_DIR)
        _model, _, _preprocess = open_clip.create_model_and_transforms(
            MODEL_NAME, pretrained=pretrained, cache_dir=cache_dir
        )
        _model.eval()
    return _model, _preprocess


def batch_generator(iterable: list, batch_size=1):
    for ndx in range(0, len(iterable), batch_size):
        yield iterable[ndx : ndx + batch_size]


def generate_embeddings_batch(image_paths: list[Path], batch_size: int = 8) -> list:
    """Return one embedding per path, in the same order as image_paths."""
    model, preprocess = get_model()
    embeddings = []
    for batch_paths in batch_generator(image_paths, batch_size):
        tensor = torch.stack([preprocess(convert_to_rgb(p)) for p in batch_paths])
        with torch.no_grad():
            embeddings.extend(model.encode_image(tensor).tolist())
    return embeddings

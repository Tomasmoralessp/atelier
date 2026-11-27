import torch
import open_clip
from .embeddings import MODEL_NAME, get_model


# Global model instance for reuse
_model = None
_tokenizer = None

def get_global_model():
    global _model, _tokenizer
    if _model is None:
        _model, _ = get_model()
        _tokenizer = open_clip.get_tokenizer(MODEL_NAME)
    return _model, _tokenizer

# Cache: id(category_prompts) -> (categories, stacked text embeddings)
_category_embedding_cache: dict[int, tuple[list, torch.Tensor]] = {}


def get_averaged_text_embedding(prompts: list[str]) -> torch.Tensor:
    model, tokenizer = get_global_model()
    tokens = tokenizer(prompts)
    with torch.no_grad():
        embeddings = model.encode_text(tokens)
    embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)
    return embeddings.mean(dim=0)


def get_category_text_embeddings(category_prompts: dict) -> tuple[list, torch.Tensor]:
    cache_key = id(category_prompts)
    if cache_key in _category_embedding_cache:
        return _category_embedding_cache[cache_key]

    categories = list(category_prompts.keys())
    text_embeddings_list = [
        get_averaged_text_embedding(category_prompts[category])
        for category in categories
    ]
    text_embeddings = torch.stack(text_embeddings_list)

    _category_embedding_cache[cache_key] = (categories, text_embeddings)
    return categories, text_embeddings


def classify_zero_shot_batch(
    image_embeddings: list, category_prompts: dict
) -> list[dict]:
    model, _ = get_global_model()
    
    image_tensor = torch.tensor(image_embeddings)
    image_tensor = image_tensor / image_tensor.norm(dim=-1, keepdim=True)

    categories, text_embeddings = get_category_text_embeddings(category_prompts)

    similarity = image_tensor @ text_embeddings.T
    logit_scale = model.logit_scale.exp()
    similarity_scaled = similarity * logit_scale

    text_probabilities = similarity_scaled.softmax(dim=1)

    predicted_category_indices = text_probabilities.argmax(axis=1)

    results = []
    for i, predicted_index in enumerate(predicted_category_indices):
        predicted_category = categories[predicted_index]
        confidence = text_probabilities[i][predicted_index]
        results.append(
            {"category": predicted_category.name, "confidence": float(confidence)}
        )
    return results
"""Shared ML helpers used by both the FastAPI pipeline (pipeline.py) and the
CLI batch scripts (scripts/step*.py), so the two code paths can't drift out
of sync on model choice or thresholds.
"""
import difflib
import numpy as np
import torch
from rembg import new_session

CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"

# birefnet-general gives noticeably cleaner mattes than the rembg default
# (u2net), which left ghost artifacts from background objects in testing
# (see scratch/test_comparison/). bria-rmbg looked equally clean but carries
# a non-commercial license, so it's not used here.
REMBG_MODEL = "birefnet-general"

_clip_model = None
_clip_processor = None
_rembg_session = None


def get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_clip_model(device: str):
    """Load (and cache) the CLIP model/processor used for image embeddings."""
    global _clip_model, _clip_processor
    if _clip_model is None:
        from transformers import CLIPModel, CLIPProcessor
        _clip_model = CLIPModel.from_pretrained(CLIP_MODEL_NAME).to(device).eval()
        _clip_processor = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)
    return _clip_model, _clip_processor


def embed_image_clip(image, model, processor, device) -> np.ndarray:
    """L2-normalized CLIP image embedding for a single PIL image."""
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model.get_image_features(**inputs)
    # Newer transformers versions return a BaseModelOutputWithPooling instead
    # of a raw tensor; the projected embedding lives at .pooler_output there.
    features = output.pooler_output if hasattr(output, "pooler_output") else output
    vec = features.squeeze(0).cpu().numpy()
    return vec / np.linalg.norm(vec)


def get_rembg_session():
    """Load (and cache) the rembg background-removal session."""
    global _rembg_session
    if _rembg_session is None:
        _rembg_session = new_session(REMBG_MODEL)
    return _rembg_session


def compute_phash(image, hash_size=16):
    """Perceptual hash used to catch true near-duplicate shots (same frame,
    minor recompression/crop) - a more precise signal for "duplicate" than
    semantic embedding distance, which can call two similar-but-different
    images "close" too.
    """
    import imagehash
    return imagehash.phash(image, hash_size=hash_size)


def _names_similar(a, b, ratio_threshold=0.92, min_substring_len=10):
    """Same product name, allowing for OCR under-reads. OCR under-reads are
    truncations of the full label text (e.g. only "SWISSCHARD" instead of
    "ADVANTA_SWISSCHARD_FORDHOOK_GIANT"), not scrambled characters - so
    substring containment catches those reliably. A plain similarity ratio
    alone doesn't work here: genuinely different products that share a brand
    prefix (e.g. "ATESOILS_K25" vs "ATESOILS_UAN32") can score a *higher*
    ratio than a true partial-OCR match of the same product, so ratio is only
    used as a fallback for near-identical strings (e.g. single-character OCR
    noise), and the substring check requires a minimum length so short,
    generic tokens don't cause false merges.
    """
    a, b = a.upper(), b.upper()
    if a == b:
        return True
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if len(shorter) >= min_substring_len and shorter in longer:
        return True
    return difflib.SequenceMatcher(None, a, b).ratio() >= ratio_threshold


def group_by_ocr_name(file_names_areas):
    """Split a visually-clustered group of images by the product name OCR
    actually read off each one, so a cluster that merged several distinct
    products sharing the same bottle/pack (only distinguishable by label
    text) gets separated instead of silently kept together.

    file_names_areas: list of (filename, name, area) - the per-image result
    of clean_ocr_name(), where name may be "unidentified".

    Returns a list of (group_name, [filenames]). If every image agrees (or
    all are "unidentified"), this is a single entry - identical to the old
    behavior. Otherwise it's one entry per distinct product name, with
    "unidentified" images folded into the largest named group, since they're
    still visually part of that cluster and there's no text evidence to
    place them elsewhere.
    """
    named = [(f, n, a) for f, n, a in file_names_areas if n != "unidentified"]
    unnamed = [f for f, n, a in file_names_areas if n == "unidentified"]

    buckets = []  # [{"name": str, "best_area": int, "files": [str, ...]}]
    for f, n, a in named:
        target = next((b for b in buckets if _names_similar(b["name"], n)), None)
        if target is None:
            buckets.append({"name": n, "best_area": a, "files": [f]})
        else:
            target["files"].append(f)
            if a > target["best_area"]:
                target["name"] = n
                target["best_area"] = a

    if len(buckets) <= 1:
        all_files = [f for f, n, a in file_names_areas]
        name = buckets[0]["name"] if buckets else "unidentified"
        return [(name, all_files)]

    buckets.sort(key=lambda b: len(b["files"]), reverse=True)
    buckets[0]["files"].extend(unnamed)
    return [(b["name"], b["files"]) for b in buckets]


def clean_ocr_name(ocr_results, min_chars=3):
    """Pick the largest-area text region from EasyOCR results and turn it
    into a clean group/file name. Returns (name, max_area); name defaults
    to "unidentified" if nothing usable was found.
    """
    best_name = "unidentified"
    max_area = 0
    for (bbox, text, prob) in ocr_results:
        width = abs(bbox[1][0] - bbox[0][0])
        height = abs(bbox[2][1] - bbox[1][1])
        area = width * height
        if area > max_area and len(text) >= min_chars:
            clean = "".join(c for c in text if c.isalnum() or c in (" ", "_")).strip()
            clean = clean.replace(" ", "_")
            if clean:
                max_area = area
                best_name = clean
    return best_name, max_area

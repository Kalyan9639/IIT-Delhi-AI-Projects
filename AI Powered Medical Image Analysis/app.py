"""FastAPI deployment app for the chest X-ray model."""

from __future__ import annotations

import json
import hashlib
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional
import zipfile

import numpy as np
import tensorflow as tf
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image
from tensorflow.keras.applications.mobilenet_v3 import preprocess_input

from medical_ai.gradcam import (
    apply_heatmap_to_image,
    image_bytes_to_base64_png,
    load_image,
    make_gradcam_heatmap,
    preprocess_pil_image,
    render_gradcam_comparison,
)


DEFAULT_THRESHOLD = float(os.getenv("MODEL_THRESHOLD", "0.5"))
DEFAULT_CLASS_NAMES = ["NORMAL", "PNEUMONIA"]
DEFAULT_IMAGE_SIZE = (224, 224)
DEFAULT_PREFERRED_RUN_DIR = Path(
    "artifacts/runs/chestxray_mobilenetv3small_bal-oversample_normal"
)
DEFAULT_PREFERRED_MODEL_PATH = DEFAULT_PREFERRED_RUN_DIR / "chestxray_mobilenetv3small_bal-oversample_normal.keras"
DEFAULT_PREFERRED_METADATA_PATH = DEFAULT_PREFERRED_RUN_DIR / "model_metadata.json"
DEFAULT_MODEL_PATH = Path(
    os.getenv("MODEL_PATH", str(DEFAULT_PREFERRED_MODEL_PATH))
)
DEFAULT_METADATA_PATH = Path(
    os.getenv("MODEL_METADATA_PATH", str(DEFAULT_PREFERRED_METADATA_PATH))
)
LEGACY_CONFIG_KEYS_BY_CLASS = {
    "RandomContrast": {"value_range"},
    "BatchNormalization": {"renorm", "renorm_clipping", "renorm_momentum"},
    "Dense": {"quantization_config"},
}

logger = logging.getLogger(__name__)


class PredictionResponse(BaseModel):
    success: bool = True
    predicted_label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    probabilities: Dict[str, float]
    threshold: float
    model_name: str
    image_size: list[int]
    gradcam_overlay_base64: str
    gradcam_comparison_base64: str


class ModelBundle:
    def __init__(
        self,
        model: tf.keras.Model,
        class_names: list[str],
        threshold: float,
        image_size: tuple[int, int],
        model_name: str,
        metadata: dict[str, Any],
    ) -> None:
        self.model = model
        self.class_names = class_names
        self.threshold = threshold
        self.image_size = image_size
        self.model_name = model_name
        self.metadata = metadata


app = FastAPI(
    title="Medical Image AI API",
    description="FastAPI service for chest X-ray prediction and Grad-CAM explanations.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React dev server
        "http://localhost:8000",      # FastAPI docs
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "*" 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_BUNDLE: Optional[ModelBundle] = None
MODEL_LOAD_ERROR: Optional[str] = None


def load_metadata(metadata_path: Path) -> dict[str, Any]:
    if metadata_path.exists():
        try:
            return json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            return json.loads(metadata_path.read_text(encoding="utf-8"))
    return {}


def _strip_legacy_keras_config(node: Any) -> None:
    if isinstance(node, dict):
        class_name = node.get("class_name")
        config = node.get("config")
        if isinstance(config, dict):
            for key in LEGACY_CONFIG_KEYS_BY_CLASS.get(class_name, set()):
                config.pop(key, None)

        for value in node.values():
            _strip_legacy_keras_config(value)
    elif isinstance(node, list):
        for item in node:
            _strip_legacy_keras_config(item)


def _compat_cache_path(model_path: Path) -> Path:
    cache_dir = model_path.parent / ".compat_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    stat = model_path.stat()
    signature = f"{model_path.resolve()}|{stat.st_mtime_ns}|{stat.st_size}"
    digest = hashlib.sha1(signature.encode("utf-8")).hexdigest()[:16]
    return cache_dir / f"{model_path.stem}_{digest}.keras"


def _build_compat_archive(model_path: Path) -> Path:
    patched_path = _compat_cache_path(model_path)
    if patched_path.exists():
        return patched_path

    with zipfile.ZipFile(model_path, "r") as source, zipfile.ZipFile(
        patched_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as target:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename == "config.json":
                config = json.loads(data)
                _strip_legacy_keras_config(config)
                data = json.dumps(config).encode("utf-8")
            target.writestr(item, data)

    return patched_path


def _load_keras_model(model_path: Path) -> tuple[tf.keras.Model, Path, str]:
    try:
        model = tf.keras.models.load_model(model_path,compile=False,custom_objects={"preprocess_input": preprocess_input}
)
        return model, model_path, "direct"
    except Exception as direct_error:
        logger.warning(
            "Direct model loading failed for %s; trying compatibility patch.",
            model_path,
            exc_info=True,
        )

    compat_path = _build_compat_archive(model_path)
    model = tf.keras.models.load_model(
        compat_path,
        compile=False,
        safe_mode=False,
        custom_objects={
            "preprocess_input": tf.keras.applications.mobilenet_v3.preprocess_input
        },
    )
    return model, compat_path, "compatibility_patch"


def load_model_bundle() -> ModelBundle:
    model_path = DEFAULT_MODEL_PATH
    metadata_path = DEFAULT_METADATA_PATH

    if not model_path.exists():
        raise FileNotFoundError(
            "Trained model not found. "
            f"Tried {model_path} and {DEFAULT_PREFERRED_MODEL_PATH}. "
            "Train the model first or set MODEL_PATH."
        )

    metadata = load_metadata(metadata_path)
    class_names = list(metadata.get("class_names", DEFAULT_CLASS_NAMES))
    image_size_data = metadata.get("image_size", list(DEFAULT_IMAGE_SIZE))
    image_size = (int(image_size_data[0]), int(image_size_data[1]))
    threshold = float(metadata.get("threshold", DEFAULT_THRESHOLD))
    model_name = metadata.get("backbone", model_path.stem)

    model, loaded_model_path, load_mode = _load_keras_model(model_path)
    metadata["loaded_model_path"] = str(loaded_model_path)
    metadata["load_mode"] = load_mode
    return ModelBundle(
        model=model,
        class_names=class_names,
        threshold=threshold,
        image_size=image_size,
        model_name=model_name,
        metadata=metadata,
    )


@app.on_event("startup")
def startup_event() -> None:
    global MODEL_BUNDLE, MODEL_LOAD_ERROR
    try:
        MODEL_BUNDLE = load_model_bundle()
        MODEL_LOAD_ERROR = None
    except Exception as exc:
        MODEL_BUNDLE = None
        MODEL_LOAD_ERROR = f"{type(exc).__name__}: {exc}"
        logger.exception("Failed to load the model bundle.")


def get_model_bundle() -> ModelBundle:
    if MODEL_BUNDLE is None:
        detail = (
            "Model is not available. Train the model and place it at "
            f"{DEFAULT_PREFERRED_MODEL_PATH} or set MODEL_PATH."
        )
        if MODEL_LOAD_ERROR:
            detail += f" Load error: {MODEL_LOAD_ERROR}"
        raise HTTPException(
            status_code=503,
            detail=detail,
        )
    return MODEL_BUNDLE


def predict_and_explain(image: Image.Image, bundle: ModelBundle) -> PredictionResponse:
    image_array = preprocess_pil_image(image, target_size=bundle.image_size)
    batch = np.expand_dims(image_array, axis=0)

    raw_prediction = bundle.model.predict(batch, verbose=0)
    raw_prediction = np.asarray(raw_prediction)

    if raw_prediction.ndim == 2 and raw_prediction.shape[1] == 1:
        positive_probability = float(raw_prediction[0][0])
        probabilities = {
            bundle.class_names[0]: float(1.0 - positive_probability),
            bundle.class_names[1] if len(bundle.class_names) > 1 else "positive": positive_probability,
        }
        predicted_index = 1 if positive_probability >= bundle.threshold else 0
        confidence = positive_probability if predicted_index == 1 else 1.0 - positive_probability
    else:
        logits = raw_prediction[0]
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)
        probabilities = {
            bundle.class_names[idx] if idx < len(bundle.class_names) else f"class_{idx}": float(prob)
            for idx, prob in enumerate(probs)
        }
        predicted_index = int(np.argmax(probs))
        confidence = float(np.max(probs))

    predicted_label = bundle.class_names[predicted_index] if predicted_index < len(bundle.class_names) else f"class_{predicted_index}"

    heatmap = make_gradcam_heatmap(
        image_array,
        bundle.model,
    )
    overlay_image = apply_heatmap_to_image(image, heatmap)
    comparison_png = render_gradcam_comparison(
        original_image=image,
        overlay_image=overlay_image,
        prediction_label=predicted_label,
        confidence=confidence,
        figure_title=f"Grad-CAM Explanation of {predicted_label} Prediction",
    )
    # overlay_image = image
    # comparison_png = _image_to_png_bytes(image)


    return PredictionResponse(
        predicted_label=predicted_label,
        confidence=confidence,
        probabilities=probabilities,
        threshold=bundle.threshold,
        model_name=bundle.model_name,
        image_size=[bundle.image_size[0], bundle.image_size[1]],
        gradcam_overlay_base64=image_bytes_to_base64_png(
            _image_to_png_bytes(overlay_image)
        ),
        gradcam_comparison_base64=image_bytes_to_base64_png(comparison_png),
    )


def _image_to_png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@app.get("/health")
def health() -> dict[str, Any]:
    bundle = MODEL_BUNDLE
    return {
        "status": "ok" if bundle is not None else "model_not_loaded",
        "model_loaded": bundle is not None,
        "model_path": str(DEFAULT_MODEL_PATH),
        "loaded_model_path": bundle.metadata.get("loaded_model_path") if bundle else None,
        "load_mode": bundle.metadata.get("load_mode") if bundle else None,
    }


@app.get("/model-info")
def model_info() -> dict[str, Any]:
    bundle = get_model_bundle()
    return {
        "model_name": bundle.model_name,
        "class_names": bundle.class_names,
        "threshold": bundle.threshold,
        "image_size": list(bundle.image_size),
        "metadata": bundle.metadata,
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)) -> PredictionResponse:
    bundle = get_model_bundle()

    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        image = load_image(contents)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not decode image: {exc}") from exc

    return predict_and_explain(image, bundle)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Medical Image AI API is running.",
        "predict_endpoint": "/predict",
        "health_endpoint": "/health",
    }


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)

"""Grad-CAM utilities for medical image model explanations."""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Optional

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from PIL import Image


DEFAULT_IMAGE_SIZE = (224, 224)


def load_image(image_bytes: bytes) -> Image.Image:
    return Image.open(BytesIO(image_bytes)).convert("RGB")


def preprocess_pil_image(image: Image.Image, target_size: tuple[int, int] = DEFAULT_IMAGE_SIZE) -> np.ndarray:
    resized = image.convert("RGB").resize(target_size, Image.Resampling.BILINEAR)
    image_array = np.asarray(resized, dtype=np.float32)
    return image_array


def find_last_conv_layer_name(model: tf.keras.Model) -> str:
    for layer in reversed(model.layers):
        if layer.count_params() == 0:
            continue

        output_shape = getattr(layer, "output_shape", None)
        if isinstance(output_shape, tuple) and len(output_shape) == 4:
            return layer.name

        try:
            shape = layer.output.shape
        except Exception:
            continue

        if len(shape) == 4:
            return layer.name

    raise ValueError("Could not find a convolutional layer for Grad-CAM.")


# def make_gradcam_heatmap(
#     img_array: np.ndarray,
#     model: tf.keras.Model,
#     last_conv_layer_name: Optional[str] = None,
#     pred_index: Optional[int] = None,
# ) -> np.ndarray:
#     if img_array.ndim == 3:
#         img_array = np.expand_dims(img_array, axis=0)

#     if last_conv_layer_name is None:
#         last_conv_layer_name = find_last_conv_layer_name(model)

#     last_conv_layer = model.get_layer(last_conv_layer_name)
#     grad_model = tf.keras.Model(model.inputs, [last_conv_layer.output, model.output])

#     with tf.GradientTape() as tape:
#         conv_outputs, predictions = grad_model(img_array)
#         if predictions.shape[-1] == 1:
#             loss = predictions[:, 0]
#         else:
#             if pred_index is None:
#                 pred_index = int(tf.argmax(predictions[0]).numpy())
#             loss = predictions[:, pred_index]

#     grads = tape.gradient(loss, conv_outputs)
#     pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
#     conv_outputs = conv_outputs[0]
#     heatmap = tf.reduce_sum(conv_outputs * pooled_grads, axis=-1)
#     heatmap = tf.maximum(heatmap, 0)
#     max_value = tf.reduce_max(heatmap)
#     heatmap = tf.where(max_value > 0, heatmap / max_value, heatmap)
#     return heatmap.numpy()


def make_gradcam_heatmap(
    img_array: np.ndarray,
    model: tf.keras.Model,
    last_conv_layer_name: Optional[str] = None,
    pred_index: Optional[int] = None,
) -> np.ndarray:
    """Generate Grad-CAM heatmap for model predictions.
    
    Args:
        img_array: Input image array (H, W, 3) or (1, H, W, 3)
        model: Trained Keras model
        last_conv_layer_name: Name of last convolutional layer (auto-detected if None)
        pred_index: Class index for prediction (auto-detected if None)
    
    Returns:
        Heatmap array normalized to [0, 1]
    """
    # Ensure batch dimension
    if img_array.ndim == 3:
        img_array = np.expand_dims(img_array, axis=0)

    # Auto-detect last convolutional layer if not specified
    if last_conv_layer_name is None:
        last_conv_layer_name = find_last_conv_layer_name(model)

    last_conv_layer = model.get_layer(last_conv_layer_name)
    
    # Create grad model that outputs both conv layer and final prediction
    try:
        grad_model = tf.keras.Model(
            inputs=model.inputs,
            outputs=[last_conv_layer.output, model.output]
        )
    except ValueError as e:
        # Fallback for complex architectures
        grad_model = tf.keras.Model(
            inputs=model.input,
            outputs=[last_conv_layer.output, model.layers[-1].output]
        )
    
    # Compute gradients
    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_array, training=False)
        
        # Handle different output shapes (binary vs multi-class)
        if predictions.shape[-1] == 1:
            # Binary classification
            loss = predictions[:, 0]
        else:
            # Multi-class classification
            if pred_index is None:
                pred_index = int(tf.argmax(predictions[0]).numpy())
            loss = predictions[:, pred_index]

    # Calculate gradients
    grads = tape.gradient(loss, conv_outputs)
    
    # Handle None gradients (shouldn't happen, but safety check)
    if grads is None:
        raise ValueError("Gradients are None. Model may not be properly connected.")
    
    # Pool gradients over spatial dimensions
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    
    # Get first sample's conv output
    conv_outputs = conv_outputs[0]
    
    # Weight conv output by pooled gradients
    heatmap = tf.reduce_sum(conv_outputs * pooled_grads, axis=-1)
    
    # ReLU activation (keep positive gradients)
    heatmap = tf.maximum(heatmap, 0)
    
    # Normalize heatmap to [0, 1]
    max_value = tf.reduce_max(heatmap)
    if max_value > 0:
        heatmap = heatmap / max_value
    else:
        heatmap = tf.zeros_like(heatmap)
    
    return heatmap.numpy()

def apply_heatmap_to_image(
    image: Image.Image,
    heatmap: np.ndarray,
    alpha: float = 0.45,
    colormap: str = "jet",
) -> Image.Image:
    original = image.convert("RGB").resize(DEFAULT_IMAGE_SIZE, Image.Resampling.BILINEAR)
    original_array = np.asarray(original, dtype=np.float32) / 255.0

    heatmap = np.clip(heatmap, 0.0, 1.0)
    heatmap_rgb = cm.get_cmap(colormap)(heatmap)[..., :3]

    overlay = np.clip((1 - alpha) * original_array + alpha * heatmap_rgb, 0.0, 1.0)
    overlay_uint8 = (overlay * 255).astype(np.uint8)
    return Image.fromarray(overlay_uint8)


def render_gradcam_comparison(
    original_image: Image.Image,
    overlay_image: Image.Image,
    prediction_label: str,
    confidence: float,
    figure_title: str = "Grad-CAM Explanation of Medical Image Prediction",
) -> bytes:
    fig = plt.figure(figsize=(14, 8), facecolor="black")
    gs = fig.add_gridspec(2, 2, height_ratios=[18, 1], width_ratios=[1, 1])

    ax_original = fig.add_subplot(gs[0, 0])
    ax_overlay = fig.add_subplot(gs[0, 1])
    ax_bar = fig.add_subplot(gs[1, 1])
    ax_caption = fig.add_subplot(gs[1, 0])

    for ax in (ax_original, ax_overlay, ax_bar, ax_caption):
        ax.set_facecolor("black")

    ax_original.imshow(original_image.convert("RGB"))
    ax_original.set_title("Original X-Ray", color="white", fontsize=22, fontweight="bold", pad=18)
    ax_original.axis("off")

    ax_overlay.imshow(overlay_image)
    ax_overlay.set_title("Grad-CAM Visualization", color="white", fontsize=22, fontweight="bold", pad=18)
    ax_overlay.axis("off")

    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    ax_bar.imshow(gradient, aspect="auto", cmap="jet")
    ax_bar.set_axis_off()
    ax_bar.text(-0.02, 0.5, "Low", color="white", fontsize=16, fontweight="bold", ha="right", va="center", transform=ax_bar.transAxes)
    ax_bar.text(1.02, 0.5, "High", color="white", fontsize=16, fontweight="bold", ha="left", va="center", transform=ax_bar.transAxes)

    ax_caption.axis("off")
    ax_caption.text(
        0.5,
        0.5,
        f"{prediction_label} prediction | confidence: {confidence:.2%}",
        color="white",
        fontsize=18,
        fontweight="bold",
        ha="center",
        va="center",
        transform=ax_caption.transAxes,
    )

    fig.suptitle(figure_title, color="white", fontsize=24, fontweight="bold", y=0.97)
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=160, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()


def image_bytes_to_base64_png(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


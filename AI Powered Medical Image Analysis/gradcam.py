import numpy as np
import tensorflow as tf
import cv2
import os


def _find_base_model_and_last_conv(model):
    """
    Locate the nested base model (e.g. MobileNetV3Small) and its last Conv2D
    layer inside the outer wrapper model.

    Returns:
        (base_model, base_model_index, last_conv_layer)
    """
    base_model = None
    base_model_idx = -1
    for i, layer in enumerate(model.layers):
        if isinstance(layer, tf.keras.Model):
            base_model = layer
            base_model_idx = i
            break

    if base_model is None:
        raise ValueError("Could not find a nested tf.keras.Model (base model) inside the model.")

    last_conv = None
    for layer in reversed(base_model.layers):
        if isinstance(layer, tf.keras.layers.Conv2D):
            last_conv = layer
            break

    if last_conv is None:
        raise ValueError("Could not find any Conv2D layer inside the base model.")

    return base_model, base_model_idx, last_conv


def make_gradcam_heatmap(img_array: np.ndarray, model: tf.keras.Model) -> np.ndarray:
    """
    Generate a Grad-CAM heatmap for a given image and model.

    The model is expected to have the structure built in train.py:
        InputLayer → preprocess_input → MobileNetV3Small → GAP → Dense → Dropout → Dense(sigmoid)

    Because MobileNetV3Small is a *nested* sub-model, we cannot build a single
    tf.keras.Model that spans from the outer input to an inner conv layer
    (Keras raises "Output is not connected to inputs").

    Instead we split the forward pass into three stages:
      1. Apply MobileNetV3 preprocessing as a direct function call
      2. Run a base-model extractor that returns [last_conv_output, base_output]
      3. Replay the classifier head layers (GAP → Dense → Dropout → Dense)

    All three stages execute inside a GradientTape so gradients flow correctly
    from the final prediction back to the conv feature maps.
    """
    base_model, base_model_idx, last_conv_layer = _find_base_model_and_last_conv(model)

    # Build a two-output extractor from the base model's own graph.
    # This works because both outputs belong to the same (inner) graph.
    base_extractor = tf.keras.Model(
        inputs=base_model.input,
        outputs=[last_conv_layer.output, base_model.output],
    )

    # Collect the classifier-head layers that come AFTER the base model
    post_base_layers = model.layers[base_model_idx + 1:]

    img_tensor = tf.cast(img_array, tf.float32)

    with tf.GradientTape() as tape:
        # Stage 1 — Preprocessing
        # Apply the same preprocessing used during training.
        # We call the function directly instead of replaying the model's
        # TFOpLambda / Lambda layer, which avoids Keras 3 __call__ issues.
        x = tf.keras.applications.mobilenet_v3.preprocess_input(img_tensor)

        # Stage 2 — Base model forward pass (returns conv maps + pooled output)
        conv_outputs, base_output = base_extractor(x, training=False)
        tape.watch(conv_outputs)

        # Stage 3 — Classifier head
        x = base_output
        for layer in post_base_layers:
            x = layer(x, training=False) if 'training' in layer.call.__code__.co_varnames else layer(x)

        # For binary sigmoid the class score is the single output probability
        loss = x[:, 0]

    # Compute gradients of the class score w.r.t. the conv feature maps
    grads = tape.gradient(loss, conv_outputs)

    if grads is None:
        raise ValueError(
            "Gradients could not be computed. "
            "Ensure the model graph is connected from the prediction back to the conv layer."
        )

    # Global-average-pool the gradients → one importance weight per channel
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    # Weight each channel by its importance and sum across channels
    conv_outputs = conv_outputs[0]                          # (H, W, C)
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]  # (H, W, 1)
    heatmap = tf.squeeze(heatmap)                           # (H, W)

    # ReLU + normalize to [0, 1]
    heatmap = tf.maximum(heatmap, 0)
    heatmap = heatmap / (tf.math.reduce_max(heatmap) + 1e-10)

    return heatmap.numpy()


def save_and_display_gradcam(
    img_path: str,
    heatmap: np.ndarray,
    cam_path: str = "cam.jpg",
    alpha: float = 0.4,
) -> str:
    """
    Overlays the Grad-CAM heatmap on the original image and saves the result.
    """
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Could not read image at {img_path}")

    # Resize heatmap to match original image dimensions
    heatmap_resized = cv2.resize(heatmap, (img.shape[1], img.shape[0]))

    # Convert to 8-bit and apply colour map
    heatmap_uint8 = np.uint8(255 * heatmap_resized)
    heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

    # Blend with original image
    superimposed = cv2.addWeighted(heatmap_colored, alpha, img, 1 - alpha, 0)

    os.makedirs(os.path.dirname(cam_path) or ".", exist_ok=True)
    cv2.imwrite(cam_path, superimposed)
    return cam_path

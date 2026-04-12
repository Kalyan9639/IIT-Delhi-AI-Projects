"""
perception_bridge.py
====================
AI perception layer for the autonomous navigation system.

Responsibilities:
  1. Load YOLO26 (via Ultralytics) onto CUDA / CPU.
  2. Convert raw CARLA images to OpenCV/NumPy format.
  3. Run object detection and return structured detections.
  4. Estimate distance to each detection using:
        a) Lidar point-cloud projection (primary)
        b) Pinhole camera model with known object heights (fallback)
  5. Parse traffic light state (Red / Green / Unknown).

Compatible with: CARLA 0.9.16 | Ultralytics YOLO26 | Python 3.12
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

import config

# Lazy-import ultralytics so the module doesn't crash if YOLO weights aren't
# downloaded yet (the first run auto-downloads them from Ultralytics hub).
try:
    from ultralytics import YOLO
    _YOLO_AVAILABLE = True
except ImportError:
    _YOLO_AVAILABLE = False
    print("[PerceptionBridge] WARNING: ultralytics not installed. "
          "Run `uv pip install ultralytics` in the (ans) venv.")


# ---------------------------------------------------------------------------
# Data container for a single detection
# ---------------------------------------------------------------------------

@dataclass
class Detection:
    """Single object detection result."""
    label: str                    # human-readable class name
    class_id: int                 # COCO / model class index
    confidence: float             # detection score [0, 1]
    bbox_xyxy: list[int]          # [x1, y1, x2, y2] in pixel coords
    distance_m: float = -1.0      # metres to object centre; -1 = unknown
    tl_state: str = "unknown"     # "red" | "green" | "yellow" | "unknown"
    cam_x: float = 0.0
    cam_y: float = 0.0
    cam_z: float = 0.0

    @property
    def center_px(self) -> tuple[int, int]:
        """Pixel coords of bounding-box centre."""
        x1, y1, x2, y2 = self.bbox_xyxy
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    @property
    def is_traffic_light(self) -> bool:
        return self.label == "Traffic Light"

    def __repr__(self) -> str:
        dist_str = f"{self.distance_m:.1f}m" if self.distance_m >= 0 else "?"
        tl_str = f" [{self.tl_state.upper()}]" if self.is_traffic_light else ""
        return (f"Detection({self.label}{tl_str}, "
                f"conf={self.confidence:.2f}, dist={dist_str})")


# ---------------------------------------------------------------------------
# Lidar → Camera projection helpers
# ---------------------------------------------------------------------------

def _build_camera_intrinsics(width: int, height: int, fov_deg: float) -> np.ndarray:
    """Build the 3×3 camera intrinsic matrix K from FOV and resolution."""
    focal_length = width / (2.0 * math.tan(math.radians(fov_deg / 2.0)))
    cx, cy = width / 2.0, height / 2.0
    K = np.array([
        [focal_length, 0,           cx],
        [0,            focal_length, cy],
        [0,            0,           1],
    ], dtype=np.float32)
    return K


def _lidar_to_camera_frame(lidar_points: np.ndarray) -> np.ndarray:
    """
    Transform Lidar points from vehicle frame to camera frame.

    CARLA convention (right-hand, x=forward, y=right, z=up):
      Lidar → Camera requires:  x↔y axis swap + negate some axes
    This is a simplified extrinsic assuming Lidar & Camera share the same
    forward direction and the camera is on the centreline.

    Returns (N, 3) array in camera frame [x_c, y_c, z_c] (z_c = depth).
    """
    # Rotation: CARLA lidar (x-forward, y-left, z-up) → camera (x-right, y-down, z-fwd)
    # cam_x =  lidar_y
    # cam_y = -lidar_z + cam_height_offset (we ignore small vertical offset here)
    # cam_z =  lidar_x  (depth)
    pts = lidar_points[:, :3]   # drop intensity
    cam_pts = np.column_stack([
        pts[:, 1],   # cam_x  = lidar_y
        -pts[:, 2],  # cam_y  = -lidar_z
        pts[:, 0],   # cam_z  = lidar_x (forward depth)
    ])
    return cam_pts


def _project_lidar_onto_image(
    lidar_points: np.ndarray,
    K: np.ndarray,
    img_width: int,
    img_height: int,
) -> np.ndarray:
    """
    Project valid (depth > 0) Lidar points onto the image plane.

    Returns (N, 3) array of [u_px, v_px, depth_m] for points inside the frame.
    """
    if len(lidar_points) == 0:
        return np.zeros((0, 3), dtype=np.float32)

    cam_pts = _lidar_to_camera_frame(lidar_points)
    # Keep only points in front of the camera
    mask = cam_pts[:, 2] > 0.1
    cam_pts = cam_pts[mask]
    if len(cam_pts) == 0:
        return np.zeros((0, 3), dtype=np.float32)

    # Project: [u, v, 1] = K · [x/z, y/z, 1]^T
    u = (K[0, 0] * cam_pts[:, 0] / cam_pts[:, 2] + K[0, 2]).astype(np.float32)
    v = (K[1, 1] * cam_pts[:, 1] / cam_pts[:, 2] + K[1, 2]).astype(np.float32)
    d = cam_pts[:, 2].astype(np.float32)

    # Filter to image bounds
    in_frame = (u >= 0) & (u < img_width) & (v >= 0) & (v < img_height)
    return np.column_stack([u[in_frame], v[in_frame], d[in_frame]])


def _estimate_distance_lidar(
    cx_px: int,
    cy_px: int,
    projected_pts: np.ndarray,
    search_radius: int = 30,
) -> float:
    """
    Find the median depth of Lidar points within `search_radius` pixels
    of the detection centre (cx_px, cy_px).

    Returns depth in metres, or -1.0 if no points found.
    """
    if len(projected_pts) == 0:
        return -1.0

    u, v, d = projected_pts[:, 0], projected_pts[:, 1], projected_pts[:, 2]
    dist_sq = (u - cx_px) ** 2 + (v - cy_px) ** 2
    neighbours = d[dist_sq < search_radius ** 2]

    if len(neighbours) == 0:
        return -1.0

    return float(np.median(neighbours))


def _estimate_distance_pinhole(
    bbox_xyxy: list[int],
    label: str,
    K: np.ndarray,
) -> float:
    """
    Monocular depth fallback using known real-world object height.

    distance = (focal_length × real_height) / pixel_height
    """
    real_h = config.KNOWN_HEIGHTS_M.get(label, 1.5)
    _, y1, _, y2 = bbox_xyxy
    pixel_h = abs(y2 - y1)
    if pixel_h < 1:
        return -1.0
    return float(K[1, 1] * real_h / pixel_h)


# ---------------------------------------------------------------------------
# Traffic light colour classification
# ---------------------------------------------------------------------------

def _classify_traffic_light(bgr_frame: np.ndarray, bbox_xyxy: list[int]) -> str:
    """
    Classify traffic light state by analysing the HSV colour distribution
    inside the bounding box crop.

    Returns: "red" | "green" | "yellow" | "unknown"
    """
    x1, y1, x2, y2 = bbox_xyxy
    h, w = bgr_frame.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w - 1, x2), min(h - 1, y2)

    crop = bgr_frame[y1:y2, x1:x2]
    if crop.size == 0:
        return "unknown"

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

    # Red wraps around 0° / 360° in HSV
    red_lo1 = cv2.inRange(hsv, (0, 120, 100),   (10, 255, 255))
    red_lo2 = cv2.inRange(hsv, (160, 120, 100), (180, 255, 255))
    red_mask = cv2.bitwise_or(red_lo1, red_lo2)

    green_mask   = cv2.inRange(hsv, (40, 80, 80),  (90, 255, 255))
    yellow_mask  = cv2.inRange(hsv, (15, 80, 80),  (35, 255, 255))

    counts = {
        "red":    int(np.sum(red_mask > 0)),
        "green":  int(np.sum(green_mask > 0)),
        "yellow": int(np.sum(yellow_mask > 0)),
    }

    best = max(counts, key=counts.get)
    return best if counts[best] > 20 else "unknown"


# ---------------------------------------------------------------------------
# Main perception class
# ---------------------------------------------------------------------------

class PerceptionBridge:
    """
    YOLO26-powered object detector with Lidar-assisted distance estimation.

    Usage::

        bridge = PerceptionBridge()
        bridge.load_model()

        # In the main loop:
        detections = bridge.detect_objects(bgr_frame, lidar_points)
        for d in detections:
            print(d)
    """

    def __init__(self) -> None:
        self._model: Optional["YOLO"] = None  # type: ignore[assignment]
        self._K: np.ndarray = _build_camera_intrinsics(
            config.CAM_WIDTH, config.CAM_HEIGHT, config.CAM_FOV
        )
        self._device: str = self._resolve_device()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_model(self) -> None:
        """
        Load YOLO26 from local weights or auto-download from Ultralytics Hub.
        If YOLO_USE_TRT=True in config, attempts to load the TRT engine.
        """
        if not _YOLO_AVAILABLE:
            raise ImportError("ultralytics package not installed.")

        model_path = config.YOLO_ENGINE_FILE if config.YOLO_USE_TRT else config.YOLO_MODEL

        if config.YOLO_USE_TRT:
            if not Path(model_path).exists():
                print(f"[PerceptionBridge] TRT engine not found at '{model_path}'. "
                      "Run trt_export.py first, or set YOLO_USE_TRT=False in config.")
                print("[PerceptionBridge] Falling back to PyTorch model …")
                model_path = config.YOLO_MODEL

        print(f"[PerceptionBridge] Loading model: {model_path} on {self._device} …")
        self._model = YOLO(model_path)
        self._model.to(self._device)

        # Warm up the model with a dummy inference to allocate CUDA memory upfront
        dummy = np.zeros(
            (config.CAM_HEIGHT, config.CAM_WIDTH, 3), dtype=np.uint8
        )
        self._model(
            dummy,
            imgsz=config.YOLO_IMG_SIZE,
            conf=config.YOLO_CONF_THRESHOLD,
            verbose=False,
        )
        print(f"[PerceptionBridge] ✓ Model loaded and warmed up.")

    def detect_objects(
        self,
        bgr_frame: np.ndarray,
        lidar_points: Optional[np.ndarray] = None,
    ) -> list[Detection]:
        """
        Run YOLO26 inference on `bgr_frame` and return structured detections.

        Args:
            bgr_frame:     OpenCV BGR frame from the CARLA RGB camera.
            lidar_points:  (N, 4) float32 array from `EnvironmentManager.get_lidar_points()`.
                            Pass None to use pinhole fallback for all distances.

        Returns:
            List of Detection objects, sorted by ascending distance.
        """
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # --- Project Lidar points for this frame ---
        projected_lidar = np.zeros((0, 3), dtype=np.float32)
        if lidar_points is not None and len(lidar_points) > 0:
            projected_lidar = _project_lidar_onto_image(
                lidar_points, self._K, config.CAM_WIDTH, config.CAM_HEIGHT
            )

        # --- YOLO inference ---
        results = self._model(
            bgr_frame,
            imgsz=config.YOLO_IMG_SIZE,
            conf=config.YOLO_CONF_THRESHOLD,
            iou=config.YOLO_IOU_THRESHOLD,
            classes=config.YOLO_CLASSES_OF_INTEREST,
            verbose=False,
            device=self._device,
        )

        detections: list[Detection] = []

        for result in results:
            if result.boxes is None:
                continue

            boxes  = result.boxes.xyxy.cpu().numpy().astype(int)    # (N,4)
            confs  = result.boxes.conf.cpu().numpy()                 # (N,)
            cls_ids = result.boxes.cls.cpu().numpy().astype(int)    # (N,)

            for box, conf, cls_id in zip(boxes, confs, cls_ids):
                if cls_id not in config.YOLO_CLASSES_OF_INTEREST:
                    continue

                label = config.CLASS_LABELS.get(cls_id, str(cls_id))
                cx_px, cy_px = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2

                # Distance estimation: Lidar first, then pinhole fallback
                dist = _estimate_distance_lidar(cx_px, cy_px, projected_lidar)
                if dist < 0:
                    dist = _estimate_distance_pinhole(box.tolist(), label, self._K)

                # Traffic light colour classification
                tl_state = "unknown"
                if label == "Traffic Light":
                    tl_state = _classify_traffic_light(bgr_frame, box.tolist())

                # Camera frame 3D coordinates
                cam_x, cam_y, cam_z = 0.0, 0.0, 0.0
                if dist > 0:
                    cam_z = dist
                    cam_x = float((cx_px - self._K[0, 2]) * dist / self._K[0, 0])
                    cam_y = float((cy_px - self._K[1, 2]) * dist / self._K[1, 1])

                detections.append(Detection(
                    label=label,
                    class_id=int(cls_id),
                    confidence=float(conf),
                    bbox_xyxy=box.tolist(),
                    distance_m=dist,
                    tl_state=tl_state,
                    cam_x=cam_x,
                    cam_y=cam_y,
                    cam_z=cam_z,
                ))

        # Sort by distance (unknown distances go last)
        detections.sort(key=lambda d: d.distance_m if d.distance_m >= 0 else float("inf"))
        return detections

    def draw_detections(
        self,
        bgr_frame: np.ndarray,
        detections: list[Detection],
    ) -> np.ndarray:
        """
        Render bounding boxes and labels on the frame.

        Returns a copy of the frame with overlays drawn.
        """
        out = bgr_frame.copy()
        colour_map = {
            "Pedestrian": (0, 255, 128),    # green-cyan
            "Car":         (255, 180, 0),   # amber
            "Bus":         (255, 100, 0),   # orange
            "Truck":       (200, 0, 255),   # purple
            "Traffic Light": {
                "red": (0, 0, 255),
                "green": (0, 255, 0),
                "yellow": (0, 255, 255),
                "unknown": (200, 200, 200),
            },
        }

        for det in detections:
            x1, y1, x2, y2 = det.bbox_xyxy

            if det.is_traffic_light:
                colour = colour_map["Traffic Light"].get(det.tl_state, (200, 200, 200))
            else:
                colour = colour_map.get(det.label, (255, 255, 255))

            cv2.rectangle(out, (x1, y1), (x2, y2), colour, 2)

            dist_str = f"{det.distance_m:.1f}m" if det.distance_m >= 0 else "?m"
            tl_str = f" [{det.tl_state.upper()}]" if det.is_traffic_light else ""
            label_str = f"{det.label}{tl_str} {det.confidence:.2f} {dist_str}"

            (tw, th), _ = cv2.getTextSize(label_str, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(out, (x1, y1 - th - 6), (x1 + tw + 4, y1), colour, -1)
            cv2.putText(
                out, label_str, (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA,
            )

        return out

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_device() -> str:
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                print(f"[PerceptionBridge] CUDA device: {gpu_name}")
                return "cuda"
        except ImportError:
            pass
        print("[PerceptionBridge] CUDA not available — using CPU.")
        return "cpu"


# ---------------------------------------------------------------------------
# Standalone smoke-test  (run: python perception_bridge.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import time

    print("=== PerceptionBridge Smoke Test ===")
    bridge = PerceptionBridge()
    bridge.load_model()

    # Test with a synthetic black frame (model will find nothing — that's fine)
    dummy_frame = np.zeros((config.CAM_HEIGHT, config.CAM_WIDTH, 3), dtype=np.uint8)
    dummy_lidar = np.random.rand(5000, 4).astype(np.float32) * 30.0

    t0 = time.perf_counter()
    detections = bridge.detect_objects(dummy_frame, dummy_lidar)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    print(f"\nInference time: {elapsed_ms:.1f} ms ({1000/max(elapsed_ms,1):.0f} FPS est.)")
    print(f"Detections: {detections}")

    # If you have a real image, uncomment:
    # frame = cv2.imread("test_image.jpg")
    # dets  = bridge.detect_objects(frame)
    # out   = bridge.draw_detections(frame, dets)
    # cv2.imwrite("test_output.jpg", out)
    # print("Saved test_output.jpg")

    print("\n✓ Smoke test passed!")

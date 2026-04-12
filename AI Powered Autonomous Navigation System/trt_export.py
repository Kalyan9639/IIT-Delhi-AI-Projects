"""
trt_export.py
=============
One-time script to export the YOLO26 PyTorch model (.pt) to a
TensorRT engine (.engine) for maximum performance on RTX 50-series GPUs.

TensorRT is installed via pip (no SDK download required in 2026):
    uv pip install tensorrt

Prerequisites:
    - NVIDIA GPU drivers (latest)
    - CUDA Toolkit 12.x
    - cuDNN (matching CUDA version)
    - Run `uv pip install tensorrt ultralytics` in the (ans) venv

Usage:
    python trt_export.py
    python trt_export.py --model yolo26s.pt --precision fp16
    python trt_export.py --model yolo26n.pt --precision int8
    python trt_export.py --verify

After export, set in config.py:
    YOLO_USE_TRT   = True
    YOLO_ENGINE_FILE = "yolo26n.engine"   # or whichever was exported
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import config


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export YOLO26 .pt → TensorRT .engine"
    )
    parser.add_argument(
        "--model", default=config.YOLO_MODEL,
        help=f"Source .pt weight file (default: {config.YOLO_MODEL})"
    )
    parser.add_argument(
        "--imgsz", type=int, default=config.YOLO_IMG_SIZE,
        help="Inference image size (square) for the engine"
    )
    parser.add_argument(
        "--precision", default="fp16",
        choices=["fp32", "fp16", "int8"],
        help="Quantisation precision (fp16 recommended for RTX 50, int8 for max speed)"
    )
    parser.add_argument(
        "--batch", type=int, default=1,
        help="Batch size baked into the engine (1 = optimal for real-time)"
    )
    parser.add_argument(
        "--workspace", type=int, default=4096,
        help="TensorRT builder workspace in MB (default: 4096)"
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="After export, run a quick inference validation"
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# TensorRT version check
# ---------------------------------------------------------------------------

def check_tensorrt() -> str:
    """Verify TensorRT is importable and return version string."""
    try:
        import tensorrt as trt
        version = trt.__version__
        print(f"[trt_export] ✓ TensorRT version: {version}")
        return version
    except ImportError:
        print("[trt_export] ✗ TensorRT not found.")
        print("  Install via:  uv pip install tensorrt")
        print("  Prerequisites: NVIDIA GPU drivers + CUDA Toolkit 12.x + cuDNN")
        sys.exit(1)


def check_cuda() -> str:
    """Verify CUDA is available via PyTorch."""
    try:
        import torch
        if not torch.cuda.is_available():
            print("[trt_export] ✗ CUDA not available. "
                  "Check GPU drivers and CUDA installation.")
            sys.exit(1)
        gpu = torch.cuda.get_device_name(0)
        print(f"[trt_export] ✓ CUDA device: {gpu}")
        return gpu
    except ImportError:
        print("[trt_export] ✗ PyTorch not installed.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_engine(
    model_path: str,
    imgsz: int,
    precision: str,
    batch: int,
    workspace_mb: int,
) -> Path:
    """
    Export YOLO26 .pt model to TensorRT .engine using Ultralytics export API.

    Returns:
        Path to the generated .engine file.
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        print("[trt_export] ✗ ultralytics not installed. "
              "Run: uv pip install ultralytics")
        sys.exit(1)

    src = Path(model_path)
    if not src.exists():
        print(f"[trt_export] Downloading model: {model_path} …")
        # Ultralytics auto-downloads when YOLO() is called with a model name

    print(f"\n[trt_export] Exporting {model_path} → TensorRT …")
    print(f"  Image size : {imgsz}×{imgsz}")
    print(f"  Precision  : {precision}")
    print(f"  Batch size : {batch}")
    print(f"  Workspace  : {workspace_mb} MB\n")

    model = YOLO(model_path)

    # Ultralytics export() handles the full ONNX→TRT pipeline internally
    export_kwargs = dict(
        format="engine",
        imgsz=imgsz,
        batch=batch,
        workspace=workspace_mb // 1024,   # ultralytics expects GB in some versions
    )

    # Add precision flags
    if precision == "fp16":
        export_kwargs["half"] = True
    elif precision == "int8":
        export_kwargs["int8"] = True
        print("[trt_export] INT8 requires a calibration dataset. "
              "Ultralytics will use COCO validation set by default.")

    t0 = time.perf_counter()
    engine_path = model.export(**export_kwargs)
    elapsed = time.perf_counter() - t0

    if engine_path is None:
        # Older ultralytics versions return None but write to predictable path
        engine_path = str(src.with_suffix(".engine"))

    print(f"\n[trt_export] ✓ Export complete in {elapsed:.1f}s")
    print(f"[trt_export] Engine saved → {engine_path}")
    return Path(str(engine_path))


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_engine(engine_path: Path, imgsz: int) -> None:
    """Run a quick inference to verify the exported engine works."""
    import numpy as np

    print(f"\n[trt_export] Verifying engine: {engine_path} …")
    try:
        from ultralytics import YOLO
        model = YOLO(str(engine_path))

        dummy = np.zeros((imgsz, imgsz, 3), dtype=np.uint8)

        # Warm-up
        for _ in range(3):
            model(dummy, verbose=False)

        # Timed run
        import time
        times = []
        for _ in range(20):
            t0 = time.perf_counter()
            model(dummy, verbose=False)
            times.append((time.perf_counter() - t0) * 1000)

        avg_ms = sum(times) / len(times)
        min_ms = min(times)
        print(f"[trt_export] ✓ Engine verification passed!")
        print(f"  Avg inference : {avg_ms:.2f} ms")
        print(f"  Best inference: {min_ms:.2f} ms")
        print(f"  Est. FPS      : {1000/avg_ms:.1f}")

    except Exception as exc:
        print(f"[trt_export] ✗ Verification failed: {exc}")
        raise


# ---------------------------------------------------------------------------
# Update config hint
# ---------------------------------------------------------------------------

def print_config_hint(engine_path: Path) -> None:
    """Print instructions for enabling TRT in config.py."""
    print("\n" + "=" * 60)
    print("  Next step: enable TensorRT inference in config.py")
    print("=" * 60)
    print(f"\n  Set these values in config.py:\n")
    print(f"    YOLO_USE_TRT     = True")
    print(f"    YOLO_ENGINE_FILE = \"{engine_path.name}\"")
    print(f"\n  Then run: python main_autopilot.py\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = parse_args()

    print("\n" + "=" * 60)
    print("  YOLO26 → TensorRT Engine Exporter")
    print("=" * 60 + "\n")

    # Prerequisite checks
    trt_version = check_tensorrt()
    gpu_name    = check_cuda()

    # Export
    engine_path = export_engine(
        model_path=args.model,
        imgsz=args.imgsz,
        precision=args.precision,
        batch=args.batch,
        workspace_mb=args.workspace,
    )

    # Verify
    if args.verify:
        verify_engine(engine_path, args.imgsz)

    # Config hint
    print_config_hint(engine_path)

# AI-Powered Autonomous Navigation System

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![CARLA](https://img.shields.io/badge/CARLA-0.9.16-EE4C2C?logo=unrealengine&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-EE4C2C?logo=pytorch&logoColor=white)
![YOLO](https://img.shields.io/badge/YOLO-Real--Time%20Perception-00FFFF?logo=YOLO&logoColor=black)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

An end-to-end autonomous driving stack built for the CARLA Simulator. The system implements a robust Sense-Plan-Act pipeline leveraging YOLO for real-time perception, Lidar for spatial awareness, and dynamic PID-based Adaptive Cruise Control (ACC) for intelligent navigation.

<!-- <div align="center">
  <a href="https://youtu.be/4FRGZs6qFhk">
    <img src="https://img.youtube.com/vi/4FRGZs6qFhk/0.jpg" alt="AI Powered Autonomous Navigation System Demo" style="width:100%;">
  </a>
  <p><b>Click above to watch the AI-Powered Autonomous Navigation System in action!</b></p>
</div> -->

[![Watch the Demo](https://img.youtube.com/vi/4FRGZs6qFhk/maxresdefault.jpg)](https://youtu.be/4FRGZs6qFhk)

---

## 🎯 Key Features

- **Spatial Awareness & Lane Filtering**: Uses real-time 3D camera-to-world projection matrices to filter out YOLO detections. The AI understands when a car or traffic light is specifically inside its "Path Corridor," entirely ignoring stopped cars in adjacent lanes or traffic lights for crossing streets.
- **Dynamic Adaptive Cruise Control (ACC)**: Replaces hard-coded brakes with a Time-Headway scale gap. The vehicle dynamically coasts and mimics the speed of lead vehicles, closing the gap seamlessly as traffic slows down.
- **Hybrid Traffic Light Detection**: Combines YOLO's pre-emptive distance vision (for smooth coastal stopping) with CARLA's authoritative API (for exact stop-line enforcement).
- **VRAM-Optimized Multi-Camera Suite**: Supports scalable multi-camera setups dynamically stitched and scaled into a PyGame telemetry view.
- **Synchronous Server Physics**: Runs strictly timed `0.05` delta seconds ensuring exact execution consistency between the game engine and the Python AI loops.

---

## 🛠️ Prerequisites & Software Required

To run this stack natively, a specific combination of software libraries must be set up beforehand:

### 1. CARLA Simulator (0.9.16)
You must download the **CARLA 0.9.16** Windows build natively. 
- Download and extract the package to a dedicated drive (e.g., `D:\Carla\`).
- **DirectX End-User Runtimes**: CARLA relies on older DirectX libraries that are often missing on modern Windows 11 installs. You *must* download and install the **DirectX End-User Runtimes (June 2010)** from Microsoft's official site, otherwise `CarlaUE4.exe` may repeatedly crash on startup.

### 2. CARLA Python API Bridge (`.whl`)
CARLA 0.9.16 does not natively ship with Python 3.12 support. To bridge the gap, you need a precompiled Python 3.12 wheel.
- Download the community-compiled `carla-0.9.16-cp312-cp312-win_amd64.whl`.
- Place this inside the root directory of this project so it can be installed locally.

### 3. Python Environment & Hardware
- **Python 3.12** installed and configured via `uv` (recommended).
- **NVIDIA GPU** (e.g., RTX 50-series) with the latest NVIDIA Drivers, CUDA Toolkit 12.x, and cuDNN installed.

---

## 🚀 Installation & Setup

**Step 1: Set up the Python virtual environment**
Using `uv`, create and activate the local environment:
```powershell
uv venv ans --python 3.12
ans\Scripts\activate
```

**Step 2: Install the dependencies**
Install the core libraries (PyTorch, Ultralytics, PyGame, etc.) as detailed in the requirements file:
```powershell
uv pip install -r requirements.txt
```

**Step 3: Install the CARLA Wheel API**
Point `pip` directly to the downloaded wheel file:
```powershell
uv pip install carla-0.9.16-cp312-cp312-win_amd64.whl
```

---

## 🏎️ Running the Simulation

**Step 1: Spin up the CARLA World Server**
In a separate terminal (or file explorer), launch CARLA. To save VRAM on smaller GPUs, boot in Low Quality headless mode:
```powershell
D:\Carla\CarlaUE4.exe -quality-level=Low -dx12
```
*Wait until the server fully loads and states "Waiting for connection" before proceeding.*

**Step 2: Start the AI Stack**
With your Python environment active, start the autonomous system:
```powershell
python main_autopilot.py
```
This script will spawn the Ego vehicle in `Town03`, populate the environment with NPC cars/pedestrians, instantiate the camera suite, and open the PyGame HUD window.

---

## 📁 Architecture Breakdown

*   **`config.py`**: Central repository for PID gains, ACC thresholds, camera orientations, and VRAM safety clamps.
*   **`environment_manager.py`**: Manages CARLA-side operations. Responsible for map loading, synchronized ticking, NPC spawning via Traffic Manager, and attaching the multi-camera suite.
*   **`perception_bridge.py`**: Intercepts camera/Lidar telemetry, deploys the YOLO model, estimates depths, and structures coordinate matrices into spatial `Detection` objects.
*   **`control_system.py`**: Translates target spatial boundaries into throttle/steer/brake actions using the Longitudinal/Lateral PID controllers. Houses the intelligence for path-corridor filtering and ACC time-gaps.
*   **`main_autopilot.py`**: The overarching loop orchestrator tying the server data, perception, control, and PyGame visualizer together.
*   **`trt_export.py`**: (Optional) Used to re-export standard YOLO `.pt` files to TensorRT `.engine` models for massive inference latency gains.

# Updated PRD: AI-Autonomous Navigation System (v1.2)
**Configuration: Optimized for Stability & Perception Accuracy**

## 1. Project Goal
Develop an autonomous vehicle agent that performs real-time object detection and lane-following in a simulated environment using a modular "Sense-Plan-Act" architecture.

## 2. Environment & Resource Constraints
* **Simulator:** CARLA 0.9.16.
* **Target Map:** `Town03` (Standard city layout with intersections and roundabouts).
* **Hardware:** RTX 50-series (15GB VRAM).
* **VRAM Management Strategy:** * **Map Selection:** Avoid Town 10/Town 11.
    * **Rendering:** Use `-quality-level=Low` for initial development; `-quality-level=Medium` for final demo.
    * **No-Rendering Mode:** Ability to toggle `no_rendering_mode = True` when testing purely logical components (saving ~4GB VRAM).

## 3. Functional Requirements

### FR1: Perception (The "AI Eyes")
* **Model:** YOLO28 (TensorRT-optimized).
* **Resolution:** Camera sensor set to **$1280 \times 720$** (720p). This is the "sweet spot" for 15GB VRAM—high enough for YOLO to see distant lights, but low enough to prevent memory spikes.
* **Classes:** Vehicles, Pedestrians, Traffic Lights (State: Red/Green).

### FR2: Synchronous Logic (The "Brain")
* **Mode:** Must run in **`synchronous_mode = True`**. 
* **Fixed Time-Step:** Set `fixed_delta_seconds = 0.05` (20 FPS). This ensures the physics engine doesn't "break" if the AI takes a few extra milliseconds to process a frame.
* **Workflow:** 1.  World Ticks.
    2.  Camera captures frame.
    3.  YOLO28 processes frame.
    4.  Controller sends command.
    5.  Repeat.

### FR3: Vehicle Control (The "Action")
* **Lateral:** PID Controller for steering (Target: Lane center).
* **Longitudinal:** PID Controller for throttle/brake (Target: 30 km/h or 0 km/h at Red light).

## 4. Specific Agent Instructions (For your Coding AI)

### Module 1: `environment_manager.py`
> *Agent: Write a script to connect to CARLA 0.9.16. Implement a function to switch the map specifically to `Town03`. Set the simulation to synchronous mode with a fixed delta of 0.05 seconds.*

### Module 2: `perception_bridge.py`
> *Agent: Initialize YOLO28 using the Ultralytics library. Create a "Listener" for the CARLA RGB camera that converts the raw 'Carla Image' into a 'NumPy/OpenCV' format for YOLO to read. Ensure the camera FOV is set to 110 degrees for a wide view.*

### Module 3: `control_system.py`
> *Agent: Implement two PID classes. `PID_Longitudinal` (inputs: current_speed, target_speed) and `PID_Lateral` (inputs: current_transform, waypoint_transform). Ensure the control loop is optimized to avoid VRAM overhead.*

## 5. Success Metrics
* **Frame Rate:** Consistent 20 FPS in synchronous mode.
* **Memory:** Total VRAM usage stays under **12GB** during full-load testing.
* **Safety:** Zero collisions in a 5-minute loop of Town03.


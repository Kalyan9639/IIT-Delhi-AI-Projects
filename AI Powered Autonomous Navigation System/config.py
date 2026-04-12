"""
config.py
=========
Central configuration for the AI-Powered Autonomous Navigation System.
Edit ONLY this file to tune the simulation without touching module internals.

Target: CARLA 0.9.16 | YOLO26 | RTX 50-series (15 GB VRAM)
"""

# =============================================================================
#  CARLA SERVER
# =============================================================================
CARLA_HOST: str = "localhost"
CARLA_PORT: int = 2000
CARLA_TIMEOUT: float = 120.0          # seconds to wait for CARLA to respond (60s for slow map loads)

# =============================================================================
#  MAP & RENDERING  (Town03 / Town05 recommended to reduce VRAM vs Town10)
# =============================================================================
TOWN_NAME: str = "Town03"            # "Town03" | "Town05" — flip here to switch
QUALITY_LEVEL: str = "Low"           # "Low" | "Medium" | "Epic"
NO_RENDERING_MODE: bool = False      # True → disables GPU rendering (~4 GB VRAM saved)
                                     #         useful when testing logic only

# =============================================================================
#  SIMULATION TIMING  (Synchronous mode — fixed physics step)
# =============================================================================
SYNC_MODE: bool = True
FIXED_DELTA_SECONDS: float = 0.05   # 20 FPS physics tick

# =============================================================================
#  EGO VEHICLE
# =============================================================================
EGO_VEHICLE_BLUEPRINT: str = "vehicle.tesla.model3"
SPAWN_POINT_INDEX: int = 0           # 0 = use first available spawn point; -1 = random

# =============================================================================
#  SENSORS — 4-camera suite (Front · Front-Left · Front-Right · Rear)
# =============================================================================
CAM_WIDTH: int = 640               # 640x480 across 4 cameras — comfortable for RTX 5060 Laptop
CAM_HEIGHT: int = 480
CAM_FPS: int = 20                    # must match physics tick

# Each entry: (name, location_xyz, rotation_pyr, fov)
# 4-camera suite — optimal coverage for an RTX 5060 Laptop:
#   Front (110°) · Front-Left pillar (90°) · Front-Right pillar (90°) · Rear (110°)
# Upgrade path: add rear_left / rear_right when VRAM budget allows.
CAMERA_SUITE: list = [
    # name               (x,    y,    z)   (pitch, yaw, roll)  fov
    ("front",            (2.0,  0.0,  1.5), (0,     0,   0),   110),   # primary YOLO camera
    ("front_left",       (0.5, -0.8,  1.5), (0,   -45,   0),    90),   # left blind-spot
    ("front_right",      (0.5,  0.8,  1.5), (0,    45,   0),    90),   # right blind-spot
    ("rear",             (-2.0, 0.0,  1.5), (0,   180,   0),   110),   # rear awareness
]

# Primary display camera (shown in pygame window)
PRIMARY_CAMERA: str = "front"

# --- Front-camera properties (used for Lidar projection & distance math) ---
CAM_FOV: float = 110.0               # matches front camera above
CAM_LOCATION: tuple = (2.0, 0.0, 1.5)
CAM_ROTATION: tuple = (0.0, 0.0, 0.0)

# --- Semantic Segmentation Camera (same FOV as front, for GT validation) ---
SEG_CAM_ENABLED: bool = True

# --- Lidar (360° roof-mounted, same as Tesla's Radar + Ultrasonic fusion) ---
LIDAR_CHANNELS: int = 32
LIDAR_RANGE: float = 50.0            # metres
LIDAR_POINTS_PER_SEC: int = 56_000
LIDAR_ROTATION_FREQ: float = 20.0
LIDAR_LOCATION: tuple = (0.0, 0.0, 2.8)

# =============================================================================
#  AI PERCEPTION — YOLO26
# =============================================================================
YOLO_MODEL: str = "yolo26n.pt"       # nano = fastest; swap to yolo26s/m/l/x for accuracy
YOLO_CONF_THRESHOLD: float = 0.45
YOLO_IOU_THRESHOLD: float = 0.45
YOLO_DEVICE: str = "cuda"            # "cuda" | "cpu" — auto falls back to cpu
YOLO_IMG_SIZE: int = 640             # inference resolution (lower = faster, < VRAM)
YOLO_USE_TRT: bool = False           # True = use .engine file (export first via trt_export.py)
YOLO_ENGINE_FILE: str = "yolo26n.engine"

# Classes YOLO must track (must match COCO label IDs or custom trained classes)
# For CARLA testing we map against ultralytics default COCO:
#   0=person, 2=car, 5=bus, 7=truck, 9=traffic light
YOLO_CLASSES_OF_INTEREST: list = [0, 2, 5, 7, 9]
CLASS_LABELS: dict = {
    0: "Pedestrian",
    2: "Car",
    5: "Bus",
    7: "Truck",
    9: "Traffic Light",
}

# =============================================================================
#  TRAFFIC LIGHT MODE
# =============================================================================
# USE_CARLA_TL_API = True  → use vehicle.is_at_traffic_light() (authoritative, no false positives)
# USE_CARLA_TL_API = False → use YOLO colour detection (less accurate, affected by side lights)
USE_CARLA_TL_API: bool = True

# =============================================================================
#  NPC TRAFFIC (CARLA Traffic Manager)
# =============================================================================
NPC_VEHICLES: int = 25             # reduced for RTX 5060 Laptop (was 30) — raise when stable
NPC_PEDESTRIANS: int = 7             # reduced for RTX 5060 Laptop (was 15)
NPC_SAFE_DISTANCE: float = 5.0      # min metres from ego spawn point
TM_PORT: int = 8000                  # Traffic Manager port
TM_GLOBAL_SPEED_DIFF: float = -20.0 # negative = faster than speed limit (e.g. -20 = 20% faster)
TM_IGNORE_LIGHTS_PCT: float = 0.0   # % of NPCs that ignore traffic lights

# =============================================================================
#  DISTANCE ESTIMATION (pinhole fallback when Lidar point unavailable)
# =============================================================================
# Approximate real-world heights (metres) used for monocular depth fallback
KNOWN_HEIGHTS_M: dict = {
    "Pedestrian": 1.75,
    "Car": 1.5,
    "Bus": 3.0,
    "Truck": 3.5,
    "Traffic Light": 0.5,   # just the lens box
}
CAMERA_FOCAL_LENGTH_PX: float = CAM_WIDTH / (2.0 * 1.0)   # recalculated in perception

# =============================================================================
#  VEHICLE CONTROL
# =============================================================================
TARGET_SPEED_KMH: float = 40.0       # increased cruise speed for faster clear-path coverage
STOPPED_SPEED_KMH: float = 0.0

# Adaptive Cruise Control (ACC) & Obstacle thresholds (metres)
ACC_TIME_GAP: float = 1.5           # seconds of time-headway (Distance = Speed_m/s * ACC_TIME_GAP)
ACC_MIN_GAP: float = 2.0            # minimum gap to maintain at a stop
PATH_CORRIDOR_WIDTH: float = 2.5    # meters wide for junction path filtering
OBSTACLE_DECEL_DIST: float = 25.0   # start decelerating earlier for smooth ACC (Traffic Lights / distant cars)
OBSTACLE_STOP_DIST: float = 1.0     # emergency full brake trigger (0.5 - 1m rule strictly enforced)

# PID — Longitudinal (Speed controller) — outputs throttle/brake in [0, 1]
PID_LONG_KP: float = 1.8            # highly aggressive P-gain for rapid "clear lane" acceleration
PID_LONG_KI: float = 0.05
PID_LONG_KD: float = 0.1
PID_LONG_DT: float = FIXED_DELTA_SECONDS

# PID — Lateral (Steering controller) — outputs steering in [-1, 1]
PID_LAT_KP: float = 0.9
PID_LAT_KI: float = 0.01
PID_LAT_KD: float = 0.2
PID_LAT_DT: float = FIXED_DELTA_SECONDS
PID_LAT_MAX_STEERING: float = 0.8   # clamp to avoid overcorrection at low speed

# Waypoint lookahead distance (metres) for lateral control
WAYPOINT_LOOKAHEAD: float = 2.0

# =============================================================================
#  LOGGING & VISUALIZATION
# =============================================================================
LOG_CSV: bool = True
LOG_CSV_FILE: str = "telemetry_log.csv"
PYGAME_DISPLAY: bool = True
PYGAME_WIDTH: int = 1280
PYGAME_HEIGHT: int = 720
OVERLAY_BOXES: bool = True           # draw YOLO bounding boxes on pygame window

# =============================================================================
#  QUICK SELF-TEST  (run: python config.py)
# =============================================================================
if __name__ == "__main__":
    import json, textwrap
    settings = {k: v for k, v in globals().items() if k.isupper()}
    print("\n" + "=" * 60)
    print("  AI Autonomous Nav — Active Configuration")
    print("=" * 60)
    for key, val in settings.items():
        line = f"  {key:<35} = {val}"
        print(textwrap.shorten(line, width=80, placeholder="..."))
    print("=" * 60 + "\n")
    print(f"  [OK] Town          : {TOWN_NAME}")
    print(f"  [OK] Quality Level : {QUALITY_LEVEL}")
    print(f"  [OK] YOLO Model    : {YOLO_MODEL}  (TRT={YOLO_USE_TRT})")
    print(f"  [OK] Camera        : {CAM_WIDTH}x{CAM_HEIGHT} @ {CAM_FPS}FPS | FOV={CAM_FOV}deg")
    print(f"  [OK] Target Speed  : {TARGET_SPEED_KMH} km/h")
    print(f"  [OK] Sync Tick     : {FIXED_DELTA_SECONDS}s  ({int(1/FIXED_DELTA_SECONDS)} FPS)\n")

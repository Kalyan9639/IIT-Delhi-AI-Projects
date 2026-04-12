"""
main_autopilot.py
=================
Entry point for the AI Autonomous Navigation System.

Orchestrates all modules in a tight synchronous loop:
  1. world.tick()              — advance physics
  2. Grab RGB frame + Lidar   — from EnvironmentManager queues
  3. detect_objects()         — YOLO26 inference via PerceptionBridge
  4. compute()                — PID control via AutonomousController
  5. apply_control()          — send command to CARLA vehicle
  6. Pygame overlay           — render detections (optional)
  7. CSV logging              — telemetry for analysis
  8. Repeat

Usage:
    Ensure CARLA 0.9.16 server is running first, then:
        python main_autopilot.py

    Optional flags:
        python main_autopilot.py --town Town05       # switch map
        python main_autopilot.py --no-render         # headless mode
        python main_autopilot.py --no-display        # disable pygame window
        python main_autopilot.py --quality Medium    # change render quality

Compatible with: CARLA 0.9.16 | YOLO26 | Python 3.12
"""

from __future__ import annotations

import argparse
import csv
import signal
import sys
import time
from pathlib import Path

import cv2
import numpy as np

import config
from environment_manager import EnvironmentManager
from perception_bridge import PerceptionBridge
from control_system import AutonomousController, ControlCommand

# Pygame is optional; only imported if PYGAME_DISPLAY is True
_pygame_available = False
try:
    import pygame
    _pygame_available = True
except ImportError:
    print("[main] pygame not installed — display disabled. "
          "Run `uv pip install pygame` to enable.")


# ---------------------------------------------------------------------------
# Telemetry logger
# ---------------------------------------------------------------------------

class TelemetryLogger:
    """Writes per-frame telemetry to a CSV file for post-run analysis."""

    COLUMNS = [
        "frame", "timestamp_s", "speed_kmh",
        "throttle", "steer", "brake",
        "num_detections", "closest_obstacle_m",
        "traffic_light_state",
    ]

    def __init__(self, filepath: str) -> None:
        self._path = Path(filepath)
        self._file = open(self._path, "w", newline="")
        self._writer = csv.DictWriter(self._file, fieldnames=self.COLUMNS)
        self._writer.writeheader()
        self._start_time = time.perf_counter()

    def log(
        self,
        frame: int,
        speed_kmh: float,
        command: ControlCommand,
        detections: list,
    ) -> None:
        closest_obstacle = min(
            (d.distance_m for d in detections
             if d.label in ("Car", "Bus", "Truck", "Pedestrian") and d.distance_m >= 0),
            default=-1.0,
        )
        tl_states = [d.tl_state for d in detections if d.is_traffic_light]
        tl_state = tl_states[0] if tl_states else "none"

        self._writer.writerow({
            "frame":               frame,
            "timestamp_s":         round(time.perf_counter() - self._start_time, 3),
            "speed_kmh":           round(speed_kmh, 2),
            "throttle":            round(command.throttle, 3),
            "steer":               round(command.steer, 3),
            "brake":               round(command.brake, 3),
            "num_detections":      len(detections),
            "closest_obstacle_m":  round(closest_obstacle, 2),
            "traffic_light_state": tl_state,
        })

    def close(self) -> None:
        self._file.close()
        print(f"[TelemetryLogger] Log saved → {self._path.resolve()}")


# ---------------------------------------------------------------------------
# Pygame display
# ---------------------------------------------------------------------------

class DisplayWindow:
    """Pygame window for rendering the ego-camera view with YOLO overlays."""

    def __init__(self, width: int, height: int, title: str = "ANS — Autopilot") -> None:
        if not _pygame_available:
            self._active = False
            return

        pygame.init()
        self._screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self._font = pygame.font.SysFont("monospace", 16)
        self._active = True
        self._clock = pygame.time.Clock()

    def render(
        self,
        bgr_frame: np.ndarray,
        detections: list,
        hud_data: dict,
        perception: PerceptionBridge,
    ) -> bool:
        """
        Render the frame with detection overlays and HUD.

        Returns:
            False if the user closed the window (quit signal), True otherwise.
        """
        if not self._active:
            return True

        # Handle window events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False

        # Draw YOLO boxes on frame
        annotated = perception.draw_detections(bgr_frame, detections)

        # Convert BGR → RGB for pygame and scale to fill the window
        rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        surface = pygame.surfarray.make_surface(rgb.swapaxes(0, 1))
        # Scale camera frame (640×480) up to the full window size (1280×720)
        surface = pygame.transform.scale(
            surface,
            (self._screen.get_width(), self._screen.get_height())
        )
        self._screen.blit(surface, (0, 0))

        # HUD overlay
        y = 12
        for key, val in hud_data.items():
            text = self._font.render(f"  {key}: {val}", True, (220, 255, 100))
            self._screen.blit(text, (10, y))
            y += 20

        pygame.display.flip()
        self._clock.tick(config.CAM_FPS)
        return True

    def close(self) -> None:
        if self._active and _pygame_available:
            pygame.quit()


# ---------------------------------------------------------------------------
# Main autopilot loop
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Autonomous Navigation System -- CARLA 0.9.16 + YOLO26"
    )
    parser.add_argument("--town",       default=config.TOWN_NAME,
                        help="CARLA town to load (default: %(default)s)")
    parser.add_argument("--quality",    default=config.QUALITY_LEVEL,
                        choices=["Low", "Medium", "Epic"],
                        help="Render quality level")
    parser.add_argument("--no-render",  action="store_true",
                        help="Enable CARLA no-rendering mode (~4 GB VRAM saved)")
    parser.add_argument("--no-display", action="store_true",
                        help="Disable pygame display window")
    parser.add_argument("--max-frames", type=int, default=0,
                        help="Stop after N frames (0 = run indefinitely)")
    parser.add_argument("--model",      default=config.YOLO_MODEL,
                        help="YOLO model weight file (default: %(default)s)")
    parser.add_argument("--npcs",       type=int, default=config.NPC_VEHICLES,
                        help="Number of NPC vehicles to spawn (default: %(default)s)")
    parser.add_argument("--pedestrians",type=int, default=config.NPC_PEDESTRIANS,
                        help="Number of NPC pedestrians to spawn (default: %(default)s)")
    parser.add_argument("--no-carla-tl",action="store_true",
                        help="Use YOLO colour detection for TL instead of CARLA API")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Apply CLI overrides to config at runtime
    config.TOWN_NAME         = args.town
    config.QUALITY_LEVEL     = args.quality
    config.NO_RENDERING_MODE = args.no_render
    config.YOLO_MODEL        = args.model
    config.NPC_VEHICLES      = args.npcs
    config.NPC_PEDESTRIANS   = args.pedestrians
    if args.no_carla_tl:
        config.USE_CARLA_TL_API = False

    tl_source = "CARLA API" if config.USE_CARLA_TL_API else "YOLO colour"

    print("\n" + "=" * 60)
    print("  Tesla AI Autonomous Navigation System")
    print(f"  Map: {config.TOWN_NAME} | Quality: {config.QUALITY_LEVEL}")
    print(f"  Model: {config.YOLO_MODEL}")
    print(f"  NPCs: {config.NPC_VEHICLES} vehicles, {config.NPC_PEDESTRIANS} pedestrians")
    print(f"  TL Source: {tl_source}")
    print(f"  Cameras: 4-camera suite (Front / Front-Left / Front-Right / Rear)")
    print("=" * 60 + "\n")

    # Modules
    env         = EnvironmentManager()
    perception  = PerceptionBridge()
    controller  = AutonomousController()
    logger      = TelemetryLogger(config.LOG_CSV_FILE) if config.LOG_CSV else None
    display     = None

    # Shutdown flag (Ctrl-C or SIGTERM)
    _running = True

    def _signal_handler(sig, frame) -> None:
        nonlocal _running
        print("\n[main] Shutdown signal received …")
        _running = False

    signal.signal(signal.SIGINT,  _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Initialise counters BEFORE try so finally can always read them,
    # even if setup() raises before the main loop ever starts.
    frame_count = 0
    total_ms    = 0.0
    loop_start  = time.perf_counter()

    try:
        # --- Setup ---
        env.setup()
        env.spawn_npcs()              # populate map with NPC vehicles + pedestrians
        perception.load_model()
        controller.reset()

        if config.PYGAME_DISPLAY and not args.no_display:
            display = DisplayWindow(config.PYGAME_WIDTH, config.PYGAME_HEIGHT)

        # Warm-up ticks — let CARLA physics settle
        print("[main] Warming up physics (10 ticks) …")
        for _ in range(10):
            env.tick()

        print(f"[main] ▶ Starting autopilot in {config.TOWN_NAME} …\n")

        # ----------------------------------------------------------------
        # MAIN SYNCHRONOUS LOOP
        # ----------------------------------------------------------------
        while _running:
            t_loop = time.perf_counter()

            # --- 1. Advance CARLA physics ---
            world_frame = env.tick()

            # --- 2. Acquire sensor data ---
            fid, rgb_frame = env.get_rgb_frame()
            lidar_pts      = env.get_lidar_points()
            ego_transform  = env.get_ego_transform()
            ego_speed_kmh  = env.get_ego_velocity_kmh()
            waypoint       = env.get_waypoint_ahead()
            carla_map      = env.world.get_map() if env.world else None

            # Move spectator camera to follow ego
            try:
                spec_tf = carla.Transform(
                    ego_transform.location + carla.Location(z=30),
                    carla.Rotation(pitch=-90),
                )
                env.world.get_spectator().set_transform(spec_tf)
            except Exception:
                pass

            # --- 3. Perception: YOLO26 inference on front camera ---
            detections = perception.detect_objects(rgb_frame, lidar_pts)

            # --- 4. Traffic light — CARLA API (authoritative) or YOLO (fallback) ---
            carla_tl_state = env.get_traffic_light_state()  # "red"|"green"|"yellow"|"none"

            # --- 5. Control: PID + safety logic ---
            command = controller.compute(
                ego_transform=ego_transform,
                ego_speed_kmh=ego_speed_kmh,
                waypoint=waypoint,
                detections=detections,
                carla_tl_state=carla_tl_state,
                carla_map=carla_map,
            )

            # --- 6. Apply control to vehicle ---
            env.ego_vehicle.apply_control(command.to_carla())

            # --- 7. Telemetry logging ---
            if logger:
                logger.log(world_frame, ego_speed_kmh, command, detections)

            # --- 8. Pygame display ---
            if display is not None:
                closest_obs = min(
                    (d.distance_m for d in detections
                     if d.label in ("Car","Bus","Truck","Pedestrian")
                     and d.distance_m >= 0),
                    default=-1,
                )
                e_stop = "!! EMERGENCY" if controller._emergency_stop else ""
                tl_src = "API" if config.USE_CARLA_TL_API else "YOLO"
                hud = {
                    "Frame":     world_frame,
                    "Speed":     f"{ego_speed_kmh:.1f} km/h",
                    "Throttle":  f"{command.throttle:.2f}",
                    "Brake":     f"{command.brake:.2f}",
                    "Steer":     f"{command.steer:+.3f}",
                    "Objects":   len(detections),
                    "Closest":   f"{closest_obs:.1f}m" if closest_obs >= 0 else "--",
                    "TL State":  f"{carla_tl_state.upper()} ({tl_src})",
                    "Map":       config.TOWN_NAME,
                    "NPCs":      len(env._npc_list),
                }
                if e_stop:
                    hud["STATUS"] = e_stop
                if not display.render(rgb_frame, detections, hud, perception):
                    print("[main] Window closed by user.")
                    break

            # --- 9. Performance metrics ---
            loop_ms = (time.perf_counter() - t_loop) * 1000
            total_ms += loop_ms
            frame_count += 1

            if frame_count % 100 == 0:
                avg_ms = total_ms / frame_count
                fps    = 1000.0 / max(avg_ms, 1.0)
                print(f"[main] Frame {frame_count:6d} | "
                      f"Loop {loop_ms:5.1f}ms | Avg {avg_ms:5.1f}ms ({fps:.1f}FPS) | "
                      f"Speed {ego_speed_kmh:.1f}km/h | "
                      f"TL={carla_tl_state} | "
                      f"Dets: {len(detections)} | "
                      f"Cmd: T={command.throttle:.2f} S={command.steer:+.3f} B={command.brake:.2f}")

            # --- Max frames exit condition ---
            if args.max_frames > 0 and frame_count >= args.max_frames:
                print(f"[main] Reached max frames ({args.max_frames}).")
                break

    except KeyboardInterrupt:
        print("\n[main] KeyboardInterrupt caught.")
    except Exception as exc:
        print(f"\n[main] FATAL ERROR: {exc}")
        import traceback
        traceback.print_exc()
    finally:
        # ---- Graceful shutdown ----
        print("\n[main] Shutting down …")
        if logger:
            logger.close()
        if display:
            display.close()
        env.teardown()

        elapsed = time.perf_counter() - loop_start
        if frame_count > 0:
            avg_fps = frame_count / max(elapsed, 0.001)
            print(f"[main] Session stats: {frame_count} frames | "
                  f"{elapsed:.1f}s | avg {avg_fps:.1f} FPS")
        print("[main] Clean shutdown complete.")


if __name__ == "__main__":
    main()

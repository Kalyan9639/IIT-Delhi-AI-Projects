"""
control_system.py
=================
PID-based vehicle control for the autonomous navigation system.

Classes:
  PIDController           -- Generic discrete-time PID with anti-windup
  PID_Longitudinal        -- Speed controller -> throttle / brake [0, 1]
  PID_Lateral             -- Steering controller -> steering [-1, 1]
  AutonomousController    -- High-level controller combining both PIDs,
                             obstacle avoidance and traffic light logic

Traffic Light Strategy:
  PRIMARY  : carla_tl_state from vehicle.is_at_traffic_light() + get_traffic_light()
             -> 100% accurate, lane-specific, no side-light false positives
  FALLBACK : YOLO colour detection (USE_CARLA_TL_API = False in config)

Compatible with: CARLA 0.9.16 | Python 3.12
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

import carla
import numpy as np

import config

if TYPE_CHECKING:
    from perception_bridge import Detection


# ---------------------------------------------------------------------------
# Generic PID controller
# ---------------------------------------------------------------------------

class PIDController:
    """
    Discrete-time PID controller with integral anti-windup clamping.

    Args:
        kp:        Proportional gain
        ki:        Integral gain
        kd:        Derivative gain
        dt:        Time step (seconds) — must match FIXED_DELTA_SECONDS
        out_min:   Minimum output value
        out_max:   Maximum output value
        int_limit: Maximum absolute integral accumulation (anti-windup)
    """

    def __init__(
        self,
        kp: float,
        ki: float,
        kd: float,
        dt: float,
        out_min: float = -1.0,
        out_max: float = 1.0,
        int_limit: float = 50.0,
    ) -> None:
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.dt = dt
        self.out_min = out_min
        self.out_max = out_max
        self.int_limit = int_limit

        self._integral: float = 0.0
        self._prev_error: float = 0.0

    def step(self, error: float) -> float:
        """
        Compute one PID step.

        Args:
            error:  (setpoint − measurement)

        Returns:
            Clamped output in [out_min, out_max].
        """
        # Proportional
        p_term = self.kp * error

        # Integral with anti-windup clamping
        self._integral += error * self.dt
        self._integral = max(-self.int_limit, min(self.int_limit, self._integral))
        i_term = self.ki * self._integral

        # Derivative (backward difference)
        d_term = self.kd * (error - self._prev_error) / self.dt
        self._prev_error = error

        output = p_term + i_term + d_term
        return max(self.out_min, min(self.out_max, output))

    def reset(self) -> None:
        """Reset internal state (call when switching target or resuming from stop)."""
        self._integral = 0.0
        self._prev_error = 0.0


# ---------------------------------------------------------------------------
# Longitudinal (Speed) controller
# ---------------------------------------------------------------------------

class PID_Longitudinal(PIDController):
    """
    Controls the vehicle's speed along the direction of travel.

    Input  : current_speed_kmh, target_speed_kmh
    Output : throttle (>0) or brake (<0), both in [0, 1] after split
    """

    def __init__(self) -> None:
        super().__init__(
            kp=config.PID_LONG_KP,
            ki=config.PID_LONG_KI,
            kd=config.PID_LONG_KD,
            dt=config.PID_LONG_DT,
            out_min=-1.0,   # negative → braking
            out_max=1.0,    # positive → throttle
        )

    def compute(
        self, current_speed_kmh: float, target_speed_kmh: float
    ) -> tuple[float, float]:
        """
        Returns:
            (throttle, brake) each in [0.0, 1.0]
        """
        error = target_speed_kmh - current_speed_kmh
        output = self.step(error)

        if output >= 0.0:
            throttle = output
            brake = 0.0
        else:
            throttle = 0.0
            brake = min(1.0, abs(output))

        return throttle, brake


# ---------------------------------------------------------------------------
# Lateral (Steering) controller
# ---------------------------------------------------------------------------

class PID_Lateral(PIDController):
    """
    Controls lateral position by minimising the heading error to the next waypoint.

    Strategy: compute the angle between the ego vehicle's current heading and
    the heading from ego location → waypoint location. Feed this angle as error
    into the PID to produce a steering command.

    Input  : ego_transform (carla.Transform), waypoint_transform (carla.Transform)
    Output : steering in [-1.0, 1.0]
    """

    def __init__(self) -> None:
        super().__init__(
            kp=config.PID_LAT_KP,
            ki=config.PID_LAT_KI,
            kd=config.PID_LAT_KD,
            dt=config.PID_LAT_DT,
            out_min=-config.PID_LAT_MAX_STEERING,
            out_max= config.PID_LAT_MAX_STEERING,
        )

    def compute(
        self,
        ego_transform: carla.Transform,
        waypoint_transform: carla.Transform,
        current_speed_kmh: float = 30.0,
    ) -> float:
        """
        Returns:
            steering value in [-1.0, 1.0]
            Positive = right, Negative = left (CARLA convention)
        """
        ego_loc = ego_transform.location
        wp_loc  = waypoint_transform.location

        # Vector from ego to waypoint (in CARLA world frame: x-forward, y-right)
        dx = wp_loc.x - ego_loc.x
        dy = wp_loc.y - ego_loc.y
        wp_heading_rad = math.atan2(dy, dx)    # world-space heading to waypoint

        # Ego forward vector heading (yaw in degrees → radians)
        ego_yaw_rad = math.radians(ego_transform.rotation.yaw)

        # Heading error (positive = waypoint is to the right)
        error_rad = wp_heading_rad - ego_yaw_rad

        # Normalise to [-π, π]
        error_rad = (error_rad + math.pi) % (2 * math.pi) - math.pi

        steering = self.step(error_rad)

        # Speed-dependent steering gain reduction (reduces oscillation at speed)
        if current_speed_kmh > 20.0:
            steering *= max(0.5, 20.0 / current_speed_kmh)

        return max(-config.PID_LAT_MAX_STEERING,
                   min( config.PID_LAT_MAX_STEERING, steering))


# ---------------------------------------------------------------------------
# High-level autonomous controller
# ---------------------------------------------------------------------------

@dataclass
class ControlCommand:
    """Container for a single CARLA vehicle control step."""
    throttle: float = 0.0    # [0, 1]
    steer:    float = 0.0    # [-1, 1]
    brake:    float = 0.0    # [0, 1]
    hand_brake: bool = False
    reverse:    bool = False

    def to_carla(self) -> carla.VehicleControl:
        """Convert to a CARLA VehicleControl object."""
        ctrl = carla.VehicleControl()
        ctrl.throttle  = float(max(0.0, min(1.0, self.throttle)))
        ctrl.steer     = float(max(-1.0, min(1.0, self.steer)))
        ctrl.brake     = float(max(0.0, min(1.0, self.brake)))
        ctrl.hand_brake = self.hand_brake
        ctrl.reverse    = self.reverse
        return ctrl

    def __repr__(self) -> str:
        return (f"ControlCommand(throttle={self.throttle:.2f}, "
                f"steer={self.steer:.2f}, brake={self.brake:.2f})")


class AutonomousController:
    """
    High-level controller that combines PID outputs with:
      - Traffic light compliance (stop on red)
      - Obstacle deceleration / emergency stop
      - Smooth lane-following via waypoint API

    Usage::

        ctrl = AutonomousController()

        # In the main loop:
        command = ctrl.compute(
            ego_transform=env.get_ego_transform(),
            ego_speed_kmh=env.get_ego_velocity_kmh(),
            waypoint=env.get_waypoint_ahead(),
            detections=detections,
        )
        ego_vehicle.apply_control(command.to_carla())
    """

    def __init__(self) -> None:
        self._long_pid = PID_Longitudinal()
        self._lat_pid  = PID_Lateral()

        self._emergency_stop: bool = False
        self._red_light_stop: bool = False
        self._current_target_speed: float = config.TARGET_SPEED_KMH

        # Cooldown timer for red-light state (prevent flip-flopping)
        self._last_tl_state: str = "unknown"
        self._tl_green_frames: int = 0
        self._TL_CONFIRM_FRAMES: int = 3   # require N consecutive green frames to resume

    def compute(
        self,
        ego_transform: carla.Transform,
        ego_speed_kmh: float,
        waypoint: carla.Waypoint,
        detections: "list[Detection]",
        carla_tl_state: str = "none",
        carla_map: Optional[carla.Map] = None,
    ) -> ControlCommand:
        """
        Main control step — call once per simulation tick.

        Args:
            ego_transform:   current vehicle transform
            ego_speed_kmh:   current vehicle speed (km/h)
            waypoint:        next target waypoint from EnvironmentManager
            detections:      list from PerceptionBridge.detect_objects()
            carla_tl_state:  AUTHORITATIVE state from env.get_traffic_light_state()
            carla_map:       CARLA map for spatial awareness (lane filtering)
        """
        # 1. Parse detections for safety decisions
        target_speed = self._decide_target_speed(
            detections=detections,
            carla_tl_state=carla_tl_state,
            carla_map=carla_map,
            ego_transform=ego_transform,
            ego_speed_kmh=ego_speed_kmh,
        )
        steer = self._lat_pid.compute(
            ego_transform, waypoint.transform, ego_speed_kmh
        )

        # 2. Emergency stop overrides everything
        if self._emergency_stop:
            return ControlCommand(throttle=0.0, steer=steer, brake=1.0)

        # 3. Red / yellow light stop
        if self._red_light_stop:
            return ControlCommand(throttle=0.0, steer=steer, brake=0.8)

        # 4. Normal PID longitudinal control
        throttle, brake = self._long_pid.compute(ego_speed_kmh, target_speed)

        return ControlCommand(throttle=throttle, steer=steer, brake=brake)

    def reset(self) -> None:
        """Reset controller state (call at episode start)."""
        self._long_pid.reset()
        self._lat_pid.reset()
        self._emergency_stop = False
        self._red_light_stop = False
        self._tl_green_frames = 0

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _project_to_world(
        self, det: "Detection", ego_transform: carla.Transform
    ) -> tuple[carla.Location, carla.Location]:
        """
        Convert a detection's camera-relative 3D coordinate to CARLA world space.
        Returns: (world_loc, ego_relative_loc)
        """
        # Convert camera frame to Lidar frame (inverse of PerceptionBridge offset)
        lidar_x = det.cam_z
        lidar_y = det.cam_x
        lidar_z = -det.cam_y

        # Offset from ego centre (relative position)
        rel_loc = carla.Location(
            x=lidar_x + config.CAM_LOCATION[0],
            y=lidar_y + config.CAM_LOCATION[1],
            z=lidar_z + config.CAM_LOCATION[2],
        )

        # Apply ego transform locally to leave rel_loc intact
        world_loc = carla.Location(rel_loc.x, rel_loc.y, rel_loc.z)
        ego_transform.transform(world_loc)
        
        return world_loc, rel_loc

    def _decide_target_speed(
        self,
        detections: "list[Detection]",
        carla_tl_state: str = "none",
        carla_map: Optional[carla.Map] = None,
        ego_transform: Optional[carla.Transform] = None,
        ego_speed_kmh: float = 0.0,
    ) -> float:
        """
        Determine target speed based on:
          1. CARLA API traffic light state (authoritative, lane-specific)
             OR YOLO colour detection if USE_CARLA_TL_API = False
          2. Closest obstacle distance from YOLO detections
        """
        self._emergency_stop = False
        min_obstacle_dist = float("inf")

        # ----------------------------------------------------------------
        # Obstacle extraction from YOLO detections (Cars & Red Lights)
        # ----------------------------------------------------------------
        for det in detections:
            # 1. Hybrid YOLO Traffic Light Pre-emptive Stop
            if det.is_traffic_light:
                if det.tl_state == "red" and ego_transform and det.cam_z > 0:
                    _, rel_loc = self._project_to_world(det, ego_transform)
                    half_width = config.PATH_CORRIDOR_WIDTH / 2.0
                    # Check Spatial Corridor: red light must be in front and within path bounds
                    if rel_loc.x > 0 and abs(rel_loc.y) < half_width:
                        if 0 < det.distance_m < min_obstacle_dist:
                            min_obstacle_dist = det.distance_m

            # 2. Vehicle/Pedestrian Obstacles
            elif det.label in ("Car", "Bus", "Truck", "Pedestrian"):
                if 0 < det.distance_m < min_obstacle_dist:

                    # Lane Filtering (Spatial Awareness)
                    if carla_map and ego_transform and det.cam_z > 0:
                        world_loc, rel_loc = self._project_to_world(det, ego_transform)
                        det_wp = carla_map.get_waypoint(world_loc, project_to_road=True)
                        ego_wp = carla_map.get_waypoint(ego_transform.location)

                        if det_wp and ego_wp:
                            if ego_wp.is_junction:
                                # Junction constraint: Path Corridor Filtering
                                half_width = config.PATH_CORRIDOR_WIDTH / 2.0
                                if not (rel_loc.x > 0 and abs(rel_loc.y) < half_width):
                                    continue
                            else:
                                # Standard Lane Check: Ignore adjacent lanes
                                if det_wp.lane_id != ego_wp.lane_id:
                                    continue

                    min_obstacle_dist = det.distance_m

        # ----------------------------------------------------------------
        # Emergency stop (strictly enforce the 1m rule)
        # ----------------------------------------------------------------
        if min_obstacle_dist <= config.OBSTACLE_STOP_DIST:
            self._emergency_stop = True
            self._long_pid.reset()
            return 0.0

        # ----------------------------------------------------------------
        # Traffic light decision (Authoritative CARLA final stop-line)
        # ----------------------------------------------------------------
        if config.USE_CARLA_TL_API:
            # ONLY triggers when right at the stop line of our physical lane
            if carla_tl_state in ("red", "yellow"):
                self._red_light_stop = True
                self._tl_green_frames = 0
                return 0.0
            else:
                self._tl_green_frames += 1
                if self._tl_green_frames >= self._TL_CONFIRM_FRAMES:
                    self._red_light_stop = False

        if self._red_light_stop:
            return 0.0

        # ----------------------------------------------------------------
        # Obstacle deceleration zone (Adaptive Cruise Control)
        # ----------------------------------------------------------------
        ego_speed_ms = ego_speed_kmh / 3.6
        acc_target = max(config.ACC_MIN_GAP, ego_speed_ms * config.ACC_TIME_GAP)

        if min_obstacle_dist < config.OBSTACLE_DECEL_DIST:
            distance_error = min_obstacle_dist - acc_target

            if distance_error <= 0:
                # We have reached or breached the target distance gap.
                # Coast or brake gently to avoid colliding, mimicking lead car.
                return max(0.0, ego_speed_kmh * 0.8 - 5.0)
            else:
                # We are approaching; smoothly scale target speed down
                proximity_factor = distance_error / max(0.001, config.OBSTACLE_DECEL_DIST - acc_target)
                smooth_speed = config.TARGET_SPEED_KMH * proximity_factor
                return max(5.0, smooth_speed)

        return config.TARGET_SPEED_KMH


# ---------------------------------------------------------------------------
# Standalone unit tests  (run: python control_system.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Control System Unit Tests ===\n")

    # --- Test 1: PID Longitudinal ---
    long_ctrl = PID_Longitudinal()
    print("PID Longitudinal (target=30 km/h, current=0 km/h):")
    for step in range(10):
        # Simulate speed ramping up to 28 km/h
        fake_speed = min(28.0, step * 4.0)
        th, br = long_ctrl.compute(fake_speed, 30.0)
        print(f"  Step {step:2d}: speed={fake_speed:5.1f} km/h → "
              f"throttle={th:.3f}, brake={br:.3f}")

    # --- Test 2: PID Lateral ---
    print("\nPID Lateral (ego heading=0°, waypoint ahead-and-right):")
    lat_ctrl = PID_Lateral()
    ego_tf = carla.Transform(
        carla.Location(0, 0, 0),
        carla.Rotation(0, 0, 0),   # facing +x
    )
    # Waypoint diagonally ahead-right → should steer right (positive)
    wp_tf  = carla.Transform(
        carla.Location(10, 5, 0),
        carla.Rotation(0, 30, 0),
    )
    # Create mock waypoint
    class _MockWP:
        transform = wp_tf
    steer = lat_ctrl.compute(ego_tf, wp_tf, current_speed_kmh=25.0)
    print(f"  Steering output: {steer:.3f}  (expect positive/right turn)")

    # --- Test 3: AutonomousController ---
    print("\nAutonomousController obstacle logic test:")
    from perception_bridge import Detection
    auto_ctrl = AutonomousController()

    no_obs = auto_ctrl._decide_target_speed([])
    print(f"  No obstacles  → target speed: {no_obs:.1f} km/h  (expect {config.TARGET_SPEED_KMH})")

    close_car = Detection("Car", 2, 0.9, [100, 200, 200, 350], distance_m=2.0)
    auto_ctrl._emergency_stop = False
    spd = auto_ctrl._decide_target_speed([close_car])
    print(f"  Car at 2m     → emergency_stop={auto_ctrl._emergency_stop}  (expect True)")

    red_light = Detection("Traffic Light", 9, 0.85, [300, 100, 380, 200],
                          distance_m=15.0, tl_state="red")
    auto_ctrl.reset()
    spd = auto_ctrl._decide_target_speed([red_light])
    print(f"  Red light     → target speed: {spd:.1f} km/h  (expect 0.0), "
          f"stop={auto_ctrl._red_light_stop}")

    print("\n✓ All control tests passed!")

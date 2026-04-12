"""
environment_manager.py
======================
Handles all CARLA-side setup:
  - Client connection & map loading (Town03 / Town05)
  - Synchronous mode with fixed physics step
  - Ego vehicle spawning
  - Tesla-style 360° 8-camera sensor suite
  - Semantic Segmentation camera + 360° Lidar
  - NPC vehicle & pedestrian spawning via Traffic Manager
  - Authoritative traffic light state via CARLA API
  - Thread-safe frame queues for the perception pipeline
  - Clean teardown on exit

Compatible with: CARLA 0.9.16
"""

import queue
import random
import time
from typing import Optional

import carla
import numpy as np

import config


# ---------------------------------------------------------------------------
# Low-level sensor callbacks
# ---------------------------------------------------------------------------

def _rgb_camera_callback(image: carla.Image, frame_queue: queue.Queue) -> None:
    """Convert raw CARLA Image → BGR numpy array and push to queue (non-blocking)."""
    array = np.frombuffer(image.raw_data, dtype=np.uint8)
    array = array.reshape((image.height, image.width, 4))  # BGRA
    bgr = array[:, :, :3].copy()
    try:
        frame_queue.put_nowait((image.frame, bgr))
    except queue.Full:
        pass  # drop stale frame — sync mode delivers a fresh one next tick


def _seg_camera_callback(image: carla.Image, seg_queue: queue.Queue) -> None:
    """Convert semantic segmentation image → colourised BGR array."""
    image.convert(carla.ColorConverter.CityScapesPalette)
    array = np.frombuffer(image.raw_data, dtype=np.uint8)
    array = array.reshape((image.height, image.width, 4))
    try:
        seg_queue.put_nowait((image.frame, array[:, :, :3].copy()))
    except queue.Full:
        pass


def _lidar_callback(
    point_cloud: carla.LidarMeasurement, lidar_queue: queue.Queue
) -> None:
    """Push raw Lidar point cloud (N×4 float32) to queue."""
    points = np.frombuffer(point_cloud.raw_data, dtype=np.float32)
    points = points.reshape(-1, 4)  # [x, y, z, intensity]
    try:
        lidar_queue.put_nowait((point_cloud.frame, points))
    except queue.Full:
        pass


# ---------------------------------------------------------------------------
# EnvironmentManager
# ---------------------------------------------------------------------------

class EnvironmentManager:
    """
    Manages the CARLA simulation environment for the autonomous nav project.

    Key additions over v1:
      - 8-camera Tesla FSD 360° suite (spawned from CAMERA_SUITE config)
      - spawn_npcs() — populates the map with Traffic Manager NPCs
      - get_traffic_light_state() — authoritative CARLA API, no false positives

    Usage::

        env = EnvironmentManager()
        env.setup()
        env.spawn_npcs()                    # optional: populate with traffic
        with env:
            while True:
                env.tick()
                frame = env.get_camera_frame("front")
                tl_state = env.get_traffic_light_state()
                ...
    """

    def __init__(self) -> None:
        self.client: Optional[carla.Client] = None
        self.world: Optional[carla.World] = None
        self.traffic_manager: Optional[carla.TrafficManager] = None
        self.ego_vehicle: Optional[carla.Vehicle] = None
        self.spectator: Optional[carla.Actor] = None

        # 360° camera store: name → (actor, queue)
        self._cameras: dict[str, tuple[carla.Actor, queue.Queue]] = {}

        # Segmentation camera
        self._seg_camera: Optional[carla.Actor] = None
        self.seg_queue: queue.Queue = queue.Queue(maxsize=1)

        # Lidar
        self._lidar: Optional[carla.Actor] = None
        self.lidar_queue: queue.Queue = queue.Queue(maxsize=1)

        # Convenience alias to the primary (front) camera queue
        self.rgb_queue: queue.Queue = queue.Queue(maxsize=1)  # set after setup

        self._original_settings: Optional[carla.WorldSettings] = None
        self._actor_list: list = []   # everything that must be destroyed on exit
        self._npc_list: list = []     # NPC vehicles (separate for easy bulk-destroy)

    # ------------------------------------------------------------------
    # Public API — Lifecycle
    # ------------------------------------------------------------------

    def setup(self) -> None:
        """Full initialization. Call once before the main loop."""
        self._connect()
        self._load_map()
        self._setup_traffic_manager()
        self._apply_world_settings()
        self._spawn_ego_vehicle()
        self._attach_360_cameras()
        self._attach_seg_camera()
        self._attach_lidar()
        self._position_spectator()
        # Wire the primary-camera queue alias
        primary = config.PRIMARY_CAMERA
        if primary in self._cameras:
            self.rgb_queue = self._cameras[primary][1]
        print("[EnvironmentManager] Setup complete — 360 camera suite ready.")

    def spawn_npcs(
        self,
        num_vehicles: int = None,
        num_pedestrians: int = None,
    ) -> None:
        """
        Populate the map with NPC vehicles and pedestrians managed by
        CARLA's Traffic Manager for realistic city traffic.

        Args:
            num_vehicles:    Cars to spawn (None = use config.NPC_VEHICLES)
            num_pedestrians: Walkers to spawn (None = config.NPC_PEDESTRIANS)
        """
        nv = num_vehicles    if num_vehicles    is not None else config.NPC_VEHICLES
        np_ = num_pedestrians if num_pedestrians is not None else config.NPC_PEDESTRIANS

        if nv == 0 and np_ == 0:
            print("[EnvironmentManager] NPC spawning skipped (counts = 0).")
            return

        self._spawn_npc_vehicles(nv)
        self._spawn_npc_pedestrians(np_)

    def teardown(self) -> None:
        """Destroy all spawned actors and restore original world settings."""
        print("[EnvironmentManager] Tearing down ...")

        # Destroy NPCs first (fastest via batch command)
        if self._npc_list:
            print(f"[EnvironmentManager]   Destroying {len(self._npc_list)} NPCs ...")
            self.client.apply_batch([
                carla.command.DestroyActor(a) for a in self._npc_list
            ])
            self._npc_list.clear()

        for actor in reversed(self._actor_list):
            try:
                if actor.is_alive:
                    actor.destroy()
            except Exception as exc:
                print(f"  [WARN] Could not destroy {actor}: {exc}")
        self._actor_list.clear()
        self._cameras.clear()

        if self.world is not None and self._original_settings is not None:
            self.world.apply_settings(self._original_settings)
            print("[EnvironmentManager] World settings restored.")

    # Context manager
    def __enter__(self) -> "EnvironmentManager":
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.teardown()

    # ------------------------------------------------------------------
    # Public API — Per-Tick
    # ------------------------------------------------------------------

    def tick(self) -> int:
        """Advance the CARLA simulation by one fixed-time step.

        Returns:
            World frame ID after the tick.
        """
        return self.world.tick()

    def get_camera_frame(
        self, name: str = None, timeout: float = 2.0
    ) -> tuple[int, np.ndarray]:
        """
        Get the latest frame from a named 360° camera.

        Args:
            name:    Camera name from CAMERA_SUITE (e.g. "front", "rear").
                     None → use PRIMARY_CAMERA from config.
            timeout: Seconds to wait before raising RuntimeError.

        Returns:
            (frame_id, bgr_ndarray  shape=H×W×3)
        """
        name = name or config.PRIMARY_CAMERA
        if name not in self._cameras:
            raise ValueError(
                f"[EnvironmentManager] Unknown camera '{name}'. "
                f"Available: {list(self._cameras.keys())}"
            )
        cam_queue = self._cameras[name][1]
        try:
            return cam_queue.get(timeout=timeout)
        except queue.Empty:
            raise RuntimeError(
                f"[EnvironmentManager] Camera '{name}' frame timed out."
            )

    # Keep backward-compat alias used by perception & main loop
    def get_rgb_frame(self, timeout: float = 2.0) -> tuple[int, np.ndarray]:
        """Alias for get_camera_frame(PRIMARY_CAMERA)."""
        return self.get_camera_frame(config.PRIMARY_CAMERA, timeout)

    def get_all_camera_frames(
        self, timeout: float = 0.5
    ) -> dict[str, np.ndarray]:
        """
        Attempt to retrieve the latest frame from every camera in the suite.

        Returns a dict of {name: bgr_ndarray}. Missing cameras are skipped
        (don't block — useful for building a surround-view composite).
        """
        frames: dict[str, np.ndarray] = {}
        for name, (_, cam_queue) in self._cameras.items():
            try:
                _, frame = cam_queue.get(timeout=timeout)
                frames[name] = frame
            except queue.Empty:
                pass
        return frames

    def get_seg_frame(self, timeout: float = 2.0) -> tuple[int, np.ndarray]:
        try:
            return self.seg_queue.get(timeout=timeout)
        except queue.Empty:
            raise RuntimeError("[EnvironmentManager] Seg frame timed out.")

    def get_lidar_points(self, timeout: float = 2.0) -> np.ndarray:
        """Return latest Lidar cloud as (N, 4) float32 [x,y,z,intensity]."""
        try:
            _, pts = self.lidar_queue.get(timeout=timeout)
            return pts
        except queue.Empty:
            return np.zeros((0, 4), dtype=np.float32)

    def get_ego_transform(self) -> carla.Transform:
        return self.ego_vehicle.get_transform()

    def get_ego_velocity_kmh(self) -> float:
        v = self.ego_vehicle.get_velocity()
        return (v.x**2 + v.y**2 + v.z**2) ** 0.5 * 3.6

    def get_waypoint_ahead(self, distance: float = None) -> carla.Waypoint:
        """Return the lane-centre waypoint `distance` metres ahead."""
        if distance is None:
            distance = config.WAYPOINT_LOOKAHEAD
        ego_loc = self.ego_vehicle.get_location()
        map_obj = self.world.get_map()
        current_wp = map_obj.get_waypoint(
            ego_loc,
            project_to_road=True,
            lane_type=carla.LaneType.Driving,
        )
        next_wps = current_wp.next(distance)
        return next_wps[0] if next_wps else current_wp

    def get_traffic_light_state(self) -> str:
        """
        AUTHORITATIVE traffic light check via the CARLA API.

        This only returns the state of the traffic light that DIRECTLY
        controls the ego vehicle's lane at this intersection — it will
        NEVER pick up side-street or crossing-lane lights.

        Returns:
            "red" | "green" | "yellow" | "none"
            "none" = not at a traffic-light-controlled intersection
        """
        if not self.ego_vehicle.is_at_traffic_light():
            return "none"

        tl = self.ego_vehicle.get_traffic_light()
        if tl is None:
            return "none"

        state = tl.get_state()
        if state == carla.TrafficLightState.Red:
            return "red"
        elif state == carla.TrafficLightState.Green:
            return "green"
        elif state == carla.TrafficLightState.Yellow:
            return "yellow"
        return "none"

    def set_no_rendering(self, enabled: bool) -> None:
        """Toggle CARLA's no-rendering mode at runtime (~4 GB VRAM saved)."""
        settings = self.world.get_settings()
        settings.no_rendering_mode = enabled
        self.world.apply_settings(settings)
        print(f"[EnvironmentManager] No-rendering: {'ON' if enabled else 'OFF'}")

    def camera_names(self) -> list[str]:
        """Return the list of active camera names."""
        return list(self._cameras.keys())

    # ------------------------------------------------------------------
    # Private helpers — Setup
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        print(f"[EnvironmentManager] Connecting to CARLA at "
              f"{config.CARLA_HOST}:{config.CARLA_PORT} ...")
        self.client = carla.Client(config.CARLA_HOST, config.CARLA_PORT)
        self.client.set_timeout(config.CARLA_TIMEOUT)
        print(f"[EnvironmentManager] Connected. Server v{self.client.get_server_version()}")

    def _load_map(self) -> None:
        current_map = self.client.get_world().get_map().name
        target = config.TOWN_NAME
        if target not in current_map:
            print(f"[EnvironmentManager] Loading map: {target} ...")
            self.world = self.client.load_world(target)
            time.sleep(5.0)
        else:
            print(f"[EnvironmentManager] Map already loaded: {current_map}")
            self.world = self.client.get_world()

    def _setup_traffic_manager(self) -> None:
        """Initialize the Traffic Manager (needed for NPC vehicles)."""
        self.traffic_manager = self.client.get_trafficmanager(config.TM_PORT)
        self.traffic_manager.set_global_distance_to_leading_vehicle(2.5)
        self.traffic_manager.global_percentage_speed_difference(
            config.TM_GLOBAL_SPEED_DIFF
        )
        print(f"[EnvironmentManager] Traffic Manager ready on port {config.TM_PORT}.")

    def _apply_world_settings(self) -> None:
        self._original_settings = self.world.get_settings()
        settings = self.world.get_settings()
        if config.SYNC_MODE:
            settings.synchronous_mode = True
            settings.fixed_delta_seconds = config.FIXED_DELTA_SECONDS
            # IMPORTANT: Traffic Manager must also run in sync
            self.traffic_manager.set_synchronous_mode(True)
        if config.NO_RENDERING_MODE:
            settings.no_rendering_mode = True
        self.world.apply_settings(settings)
        print(f"[EnvironmentManager] Sync={settings.synchronous_mode}, "
              f"dt={settings.fixed_delta_seconds}s, "
              f"NoRender={settings.no_rendering_mode}")

    def _spawn_ego_vehicle(self) -> None:
        bp_lib = self.world.get_blueprint_library()
        vehicle_bp = bp_lib.find(config.EGO_VEHICLE_BLUEPRINT)
        vehicle_bp.set_attribute("role_name", "ego")

        spawn_points = self.world.get_map().get_spawn_points()
        if not spawn_points:
            raise RuntimeError("[EnvironmentManager] No spawn points found in map!")

        idx = (config.SPAWN_POINT_INDEX
               if config.SPAWN_POINT_INDEX >= 0
               else random.randint(0, len(spawn_points) - 1))
        spawn_tf = spawn_points[min(idx, len(spawn_points) - 1)]

        self.ego_vehicle = self.world.spawn_actor(vehicle_bp, spawn_tf)
        self._actor_list.append(self.ego_vehicle)

        # Register ego with Traffic Manager but do NOT enable autopilot — we control it
        self.traffic_manager.vehicle_percentage_speed_difference(self.ego_vehicle, 0)
        print(f"[EnvironmentManager] Ego vehicle spawned at {spawn_tf.location}")

    def _attach_360_cameras(self) -> None:
        """Spawn all 8 cameras from the CAMERA_SUITE config."""
        bp_lib = self.world.get_blueprint_library()
        rgb_bp_template = bp_lib.find("sensor.camera.rgb")

        for cam_name, loc_xyz, rot_pyr, fov in config.CAMERA_SUITE:
            cam_bp = bp_lib.find("sensor.camera.rgb")
            cam_bp.set_attribute("image_size_x", str(config.CAM_WIDTH))
            cam_bp.set_attribute("image_size_y", str(config.CAM_HEIGHT))
            cam_bp.set_attribute("fov",          str(fov))
            cam_bp.set_attribute("sensor_tick",  str(1.0 / config.CAM_FPS))

            cam_tf = carla.Transform(
                carla.Location(*loc_xyz),
                carla.Rotation(*rot_pyr),
            )
            cam_actor = self.world.spawn_actor(
                cam_bp, cam_tf, attach_to=self.ego_vehicle
            )
            self._actor_list.append(cam_actor)

            cam_queue: queue.Queue = queue.Queue(maxsize=1)
            cam_actor.listen(
                lambda img, q=cam_queue: _rgb_camera_callback(img, q)
            )
            self._cameras[cam_name] = (cam_actor, cam_queue)

        names = list(self._cameras.keys())
        print(f"[EnvironmentManager] 360 camera suite attached: {names}")

    def _attach_seg_camera(self) -> None:
        if not config.SEG_CAM_ENABLED:
            return
        bp_lib = self.world.get_blueprint_library()
        seg_bp = bp_lib.find("sensor.camera.semantic_segmentation")
        seg_bp.set_attribute("image_size_x", str(config.CAM_WIDTH))
        seg_bp.set_attribute("image_size_y", str(config.CAM_HEIGHT))
        seg_bp.set_attribute("fov",          str(config.CAM_FOV))
        seg_bp.set_attribute("sensor_tick",  str(1.0 / config.CAM_FPS))

        seg_tf = carla.Transform(
            carla.Location(*config.CAM_LOCATION),
            carla.Rotation(*config.CAM_ROTATION),
        )
        self._seg_camera = self.world.spawn_actor(
            seg_bp, seg_tf, attach_to=self.ego_vehicle
        )
        self._actor_list.append(self._seg_camera)
        self._seg_camera.listen(
            lambda img: _seg_camera_callback(img, self.seg_queue)
        )
        print("[EnvironmentManager] Semantic segmentation camera attached.")

    def _attach_lidar(self) -> None:
        bp_lib = self.world.get_blueprint_library()
        lidar_bp = bp_lib.find("sensor.lidar.ray_cast")
        lidar_bp.set_attribute("channels",         str(config.LIDAR_CHANNELS))
        lidar_bp.set_attribute("range",             str(config.LIDAR_RANGE))
        lidar_bp.set_attribute("points_per_second", str(config.LIDAR_POINTS_PER_SEC))
        lidar_bp.set_attribute("rotation_frequency",str(config.LIDAR_ROTATION_FREQ))
        lidar_bp.set_attribute("sensor_tick",       str(config.FIXED_DELTA_SECONDS))

        lidar_tf = carla.Transform(carla.Location(*config.LIDAR_LOCATION))
        self._lidar = self.world.spawn_actor(
            lidar_bp, lidar_tf, attach_to=self.ego_vehicle
        )
        self._actor_list.append(self._lidar)
        self._lidar.listen(lambda pc: _lidar_callback(pc, self.lidar_queue))
        print(f"[EnvironmentManager] Lidar attached "
              f"({config.LIDAR_CHANNELS}ch, range={config.LIDAR_RANGE}m).")

    def _position_spectator(self) -> None:
        self.spectator = self.world.get_spectator()
        ego_tf = self.ego_vehicle.get_transform()
        self.spectator.set_transform(carla.Transform(
            ego_tf.location + carla.Location(z=35),
            carla.Rotation(pitch=-90),
        ))

    # ------------------------------------------------------------------
    # Private helpers — NPC spawning
    # ------------------------------------------------------------------

    def _spawn_npc_vehicles(self, count: int) -> None:
        """Spawn `count` NPC vehicles managed by the Traffic Manager."""
        if count <= 0:
            return

        bp_lib = self.world.get_blueprint_library()
        spawn_points = self.world.get_map().get_spawn_points()
        random.shuffle(spawn_points)

        ego_loc = self.ego_vehicle.get_location()

        # Filter spawn points too close to the ego
        valid_sps = [
            sp for sp in spawn_points
            if sp.location.distance(ego_loc) > config.NPC_SAFE_DISTANCE
        ]

        # Vehicle blueprints — exclude bikes & motorbikes for cleaner traffic
        vehicle_bps = [
            bp for bp in bp_lib.filter("vehicle.*")
            if int(bp.get_attribute("number_of_wheels")) >= 4
        ]

        batch = []
        for i, sp in enumerate(valid_sps[:count]):
            bp = random.choice(vehicle_bps)
            # Randomise colour
            if bp.has_attribute("color"):
                color = random.choice(bp.get_attribute("color").recommended_values)
                bp.set_attribute("color", color)
            bp.set_attribute("role_name", f"npc_{i}")
            batch.append(carla.command.SpawnActor(bp, sp).then(
                carla.command.SetAutopilot(
                    carla.command.FutureActor, True, config.TM_PORT
                )
            ))

        results = self.client.apply_batch_sync(batch, True)
        spawned = 0
        for res in results:
            if not res.error:
                actor = self.world.get_actor(res.actor_id)
                if actor:
                    self.traffic_manager.ignore_lights_percentage(
                        actor, config.TM_IGNORE_LIGHTS_PCT
                    )
                    self._npc_list.append(actor)
                    spawned += 1
            else:
                pass  # spawn point was occupied — skip silently

        print(f"[EnvironmentManager] NPC vehicles spawned: {spawned}/{count}")

    def _spawn_npc_pedestrians(self, count: int) -> None:
        """Spawn `count` NPC walkers with AI controllers."""
        if count <= 0:
            return

        bp_lib = self.world.get_blueprint_library()
        walker_bps = bp_lib.filter("walker.pedestrian.*")
        controller_bp = bp_lib.find("controller.ai.walker")

        ego_loc = self.ego_vehicle.get_location()

        # Step 1 — find valid pedestrian spawn locations
        spawn_locs = []
        for _ in range(count * 3):   # try 3× to get `count` valid locations
            if len(spawn_locs) >= count:
                break
            loc = self.world.get_random_location_from_navigation()
            if loc and loc.distance(ego_loc) > config.NPC_SAFE_DISTANCE:
                spawn_locs.append(carla.Transform(loc))

        # Step 2 — batch-spawn walkers
        batch = [
            carla.command.SpawnActor(
                random.choice(walker_bps),
                tf,
            )
            for tf in spawn_locs[:count]
        ]
        results = self.client.apply_batch_sync(batch, True)

        walker_ids, walker_actors = [], []
        for res in results:
            if not res.error:
                walker_ids.append(res.actor_id)
                actor = self.world.get_actor(res.actor_id)
                if actor:
                    walker_actors.append(actor)
                    self._npc_list.append(actor)

        # Step 3 — spawn AI controllers for each walker
        ctrl_batch = [
            carla.command.SpawnActor(controller_bp, carla.Transform(), wid)
            for wid in walker_ids
        ]
        ctrl_results = self.client.apply_batch_sync(ctrl_batch, True)

        ctrl_actors = []
        for res in ctrl_results:
            if not res.error:
                actor = self.world.get_actor(res.actor_id)
                if actor:
                    ctrl_actors.append(actor)
                    self._npc_list.append(actor)

        # Step 4 — tick once to let controllers initialise, then start them
        self.world.tick()
        for ctrl in ctrl_actors:
            try:
                ctrl.start()
                ctrl.go_to_location(
                    self.world.get_random_location_from_navigation()
                )
                ctrl.set_max_speed(1.2 + random.random() * 0.8)  # 1.2–2.0 m/s
            except Exception:
                pass

        print(f"[EnvironmentManager] NPC pedestrians spawned: {len(walker_actors)}/{count}")


# ---------------------------------------------------------------------------
# Standalone smoke-test  (run: python environment_manager.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import carla  # noqa

    print("=== EnvironmentManager Smoke Test ===")
    print("Make sure CARLA 0.9.16 server is running before proceeding.\n")

    env = EnvironmentManager()
    try:
        env.setup()
        env.spawn_npcs()

        print(f"\nActive cameras: {env.camera_names()}")
        print(f"Capturing 5 frames ...")

        for i in range(5):
            frame_id = env.tick()
            fid, front = env.get_camera_frame("front")
            lidar_pts  = env.get_lidar_points()
            speed      = env.get_ego_velocity_kmh()
            wp         = env.get_waypoint_ahead()
            tl_state   = env.get_traffic_light_state()

            print(f"  Frame {i+1}: id={fid}, "
                  f"front={front.shape}, "
                  f"lidar_pts={len(lidar_pts)}, "
                  f"speed={speed:.1f}km/h, "
                  f"TL={tl_state}, "
                  f"wp={wp.transform.location}")

        print("\nSmoke test passed!")
    finally:
        env.teardown()

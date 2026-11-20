# Changelog -- the MuJoCo body (robot-mujoco)

The body is identified by its digest: a hash over the files that decide how it moves and
what it reports, keyed with its version, the MuJoCo and menagerie versions, the robot and
the world. A saved brain names the body it needs by the release tag
`body-mujoco-<version>-<digest>` (see `body.lock`). Any change to those files moves the
digest; the version moves with it.

## 0.12.1 (`body-mujoco-0.12.1-1a4d3affd7bd`), 2026-11-20

- Documentation only: three docstrings (`body/sensors.py`, `body/sim.py`, `robots/g1/__init__.py`) now refer to
  "the body's development notes" instead of a file name. Nothing the body does or reports changed; the digest moves
  because these are model files. A brain saved against 0.12.0 runs on 0.12.1 unchanged, but names the old tag.

## 0.12.0, 2026-11-07

- `support` (a harness, the experimenter's; `--support` on the bridge, `MujocoSim(support=True)`): the robot's
  root is held at its home pose with zero velocity after every physics substep, like an infant in supported
  sitting. The limbs move without the body's balance at stake: with the arms raised forward into the head
  camera's view (hand-eye babbling, the research project's XXVI.1) the free-standing body falls and the supported
  one does not (a test holds both). The brain is not told of the support; it can infer it, since the pelvis
  IMU's gyro then reads zero. The manifest records it as
  `harness: "support"` (combined with `keep-line` as `keep-line+support`), so a supported body has its own digest.

## 0.11.0 (`body-mujoco-0.11.0-ccee1f8e95c7`), 2026-10-27

- `--record-pose PATH`: the bridge appends `tick x y yaw` every tick to a file for the
  experimenter, to score where the body went (did it stop in front of the thing it was
  sent to?). It never crosses the bridge: no reply carries a pose, and the tests that
  refuse privileged words still pass. The tick restarts at every reset, so read the pose
  while its tick is current.
- Known limit, measured: the keyframe `stand` cannot stop a walking body. It falls about
  50 ticks after a walk ends. To stop, send `walk` with zero velocity: the walking policy
  holds the body still (376 ticks and counting in the measurement). The same applies
  between two skills: hand over on `walk 0`, not `stand`.

## 0.10.1 (`body-mujoco-0.10.1-4ca3dd5650bd`), 2026-10-27

- The follow camera has two views, `--chase-view follow` (behind, low; for open corridors)
  and `above` (60 degrees up; for rooms, where the low view ends inside a wall). For
  videos only; the brain never sees it.

## 0.10.0 (`body-mujoco-0.10.0-160c9fe089d8`), 2026-10-27

- Seven navigation skills as primitives 5-11: `to_door`, `to_wall`, `turn_left`,
  `turn_right`, `turn_around`, `door_left`, `door_right`. A skill runs on the walking gait
  from the body's own odometry and the world's map; the brain chooses which and when. The
  state reply says which skill runs and whether it is done (`skill`).
- The apartment gains side rooms (a bedroom on the left, a bath on the right), so a walk
  has choices at its doors.

## 0.9.0, 2026-10-26

- Worlds as a layer: a `WorldSpec` (rooms, doors, things, slots where pictures hang, a
  schedule that rearranges them by day), built into the scene; `--world apartment` and
  `--world apartment_kitchen` (with a kitchen exported from RoboCasa, CC BY 4.0, see
  `worlds/apartment_kitchen/kitchen_L001_S002/ATTRIBUTION.md`). The hello carries the
  world's truth for the experimenter.
- `--keep-line`: an experimenter's line-keeper that holds a forward walk on its line.
- Two digests were published under 0.9.0 (`4b4b16a85885`, then `15267e00d81b` when the
  kitchen and the line-keeper arrived without a version bump). Use the tag, which names
  both version and digest. From 0.10.0 on, every digest move has its own version.

## 0.8.0 (`body-mujoco-0.8.0-133c43b36853`), 2026-10-26

- The body as a release: `body.lock` (the manifest, the digest, the release tag, the
  Python and lock it was built with); the manifest reports licences (the body Apache-2.0,
  the menagerie and the G1 policy BSD-3-Clause); one version number for the package.

Earlier versions (0.2.0-0.7.0: the G1, protocols 0.2-0.4, the gallery scene) predate this
log.

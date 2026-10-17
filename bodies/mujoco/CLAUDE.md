# bodies/mujoco -- notes for contributors

The MuJoCo body for ubrain: the Unitree G1 humanoid (from the MuJoCo Menagerie),
its sensors, motor primitives (a frozen walking policy among them), a head camera,
an optional gallery scene, and the tick bridge -- a small TCP server a brain talks to.

## Setup

```bash
uv sync                                          # once: MuJoCo 3.12, numpy, the menagerie
uv run python -m body.bridge --port 5555         # serve the body
uv run python -m body.bridge --head-camera --gallery scenes/gallery_cc0 --viewer
uv run pytest
```

ubrain starts it for you (`ubrain.bodies.start_body`); in the ubrain repository it is
`bodies/mujoco`.

## Layout

```
body/        bridge.py (the server), protocol.py + client.py (the protocol, stdlib only),
             sim.py (MuJoCo), sensors.py, primitives.py, manifest.py (the body's identity)
robots/g1/   the G1's spec, its walking policy (numpy, with PROVENANCE.json and LICENSE)
scenes/gallery_cc0/   21 CC0 photographs for the gallery scene, with PROVENANCE.json
tests/
```

## Rules

- **The body's identity is a digest** of its code and robot files (`python -m
  body.manifest`). Any change to `body/*.py` or `robots/**` gives a new body; bump
  `body/__init__.py`'s version with it. These files are `-text` in `.gitattributes`
  so every checkout hashes the same bytes -- leave that be.
- **The brain never feels privileged state.** Forces the experimenter applies, true
  poses and masses are never in a reply; the brain senses only consequences.
- **`protocol.py` and `client.py` are copied byte for byte into ubrain** (and checked
  there): change them only together with a protocol version.
- The gallery panels are visual only (no collision, no mass): walking physics are the
  default scene's exactly (a test holds it).

The development history is kept with the research project, not here.

# bodies/mujoco -- the Unitree G1 body

**The body for [ubrain](https://github.com/untrained-brain/ubrain): a Unitree G1
humanoid in MuJoCo.**

The brain (ubrain) and the body run as two programs that talk over a small local
protocol, the *tick bridge*: each tick the body sends what it senses and the brain
sends back what to do. The brain never imports a simulator, and the body knows
nothing about the brain.

What the body provides:

- the **Unitree G1** humanoid from the [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie);
- **senses**: proprioception (joint angles and velocities, the body's orientation),
  foot contacts, an "upright" flag, a tone it can hear;
- **motor primitives**: stand, pose, sway, and **walk** -- Unitree's frozen walking
  policy, run in numpy -- plus walking with per-joint corrections;
- an optional **head camera**;
- an optional **gallery scene**: 21 public-domain (CC0) photographs standing along
  the walking path, for the vision demos.

## Use it with ubrain

This folder is part of the ubrain repository. Set it up once:

```bash
cd bodies/mujoco
uv sync            # installs MuJoCo, numpy and the Menagerie (a few minutes, once)
```

Then run the robot examples from the ubrain folder; they start this body for you:

```bash
cd ../..
uv run examples/g1_walker.py                                             # lab 4
uv run --extra vision --extra video examples/g1_explorer.py --viewer     # lab 5
```

To use a body elsewhere, set `UBRAIN_BODY` to its folder.

## Run the body on its own

```bash
uv run python -m body.bridge --port 5555                     # serve the body
uv run python -m body.bridge --port 5555 --viewer            # with MuJoCo's viewer
uv run python -m body.bridge --head-camera --gallery scenes/gallery_cc0 --viewer
uv run python -m body.manifest                               # what this body is, and its digest
uv run pytest                                                # the tests
```

Any program that speaks the protocol (`body/protocol.py`, with a ready client in
`body/client.py`, standard library only) can drive it.

## The body's identity

`python -m body.manifest` prints a **digest**: a fingerprint of this body's code,
its robot files and the versions of MuJoCo and numpy. A brain's results are recorded
against it, so a changed body is never mistaken for the old one.

## Requirements

Python 3.12 (uv installs it), Windows, macOS or Linux. No GPU. The viewer needs a
desktop session; elsewhere leave out `--viewer` (the bridge runs without a window by
default, and the ubrain examples take `--headless`).

## Licences

- The G1 model comes from the MuJoCo Menagerie and keeps the Menagerie's licence for
  that model.
- The walking policy (`robots/g1/policy/`) is Unitree's, BSD 3-Clause, with its
  `LICENSE` and provenance.
- The gallery photographs (`scenes/gallery_cc0/`) are CC0; their sources and creators
  are listed in `PROVENANCE.json`.
- The code in this folder: Copyright 2026 Hong Jeong, Apache License 2.0
  (`LICENSE`, `NOTICE`).

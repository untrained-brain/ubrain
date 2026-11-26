# Using ubrain in your own code

ubrain is distributed as **compiled wheels**, in this repository's `wheels/` folder:
one per platform and Python version (Windows x64, macOS Apple Silicon and Intel,
Linux x86_64; Python 3.11, 3.12, 3.13). The installer picks the right one. The only
other dependency is numpy.

## 1. Install it into your project

**From PyPI** (the simplest): `uv add "ubrain==0.50.0.dev1"`, or with pip
`pip install "ubrain==0.50.0.dev1"`. Every version is a pre-release until 1.0, so name it (or
pass `--pre`). The rest of this section installs from the repository's `wheels/` folder
instead, for a machine without PyPI access.

Clone this repository once (it holds the wheels), then point your project at its
`wheels/` folder. Below, `/path/to/ubrain` is where you cloned it.

**With uv** (recommended):

```bash
uv init my-brain-app && cd my-brain-app
```

Tell your project where the wheels are, in its `pyproject.toml`:

```toml
[tool.uv]
find-links = ["/path/to/ubrain/wheels"]
```

Then add ubrain and check it:

```bash
uv add "ubrain==0.50.0.dev1"
uv run python -c "import ubrain; print(ubrain.__version__)"
```

Keep `find-links` in `pyproject.toml` (rather than passing `--find-links` to `uv add`
once): uv needs it every time it re-solves your dependencies, for example when you
add another package. The extras, each only when you need it:

| extra | what it brings | for |
|---|---|---|
| `vision` | torch, transformers (CLIP) | CLIP as a sense: `uv add "ubrain[vision]==0.50.0.dev1"` |
| `video` | imageio with ffmpeg | recording the robot examples as MP4 |
| `plot` | matplotlib | plots of your own runs |

**With pip**, in a virtual environment:

```bash
pip install "ubrain==0.50.0.dev1" --find-links /path/to/ubrain/wheels
```

(Version 0.50.0.dev1 is a pre-release, so name it exactly as above. When ubrain is on
PyPI, `pip install ubrain` will be enough.)

## 2. The whole brain in a few lines

`Brain()` is the whole brain: every region on the route from the senses to the action, wired
once, the same in every copy. You choose a variant (`small`, `standard`, `large`: sizes, never
wiring), attach streams by port class, and tick it with one dictionary in and one out.

```python
import numpy as np
from ubrain import Brain, GaussianCodes

brain = Brain(variant="small", rng=np.random.default_rng(0))
brain.attach("sense", "vision", codec=GaussianCodes(dim=64, seed=1))   # tick key "sense.vision"
brain.attach("reward")                                                 # tick key "reward"
brain.attach("action", n=4)                                            # "action" in the output

reward = None
for t in range(3000):
    picture = world.picture()                                          # your world
    action = brain.tick({"sense.vision": picture, "reward": reward})["action"]
    reward = world.pay(picture, action)                                # in [0, 1]
```

A value is `None` when a stream carries nothing on a tick. The reward credits the latest
action taken before it. `examples/01_whole_brain.py` is this program, with the race's law and
a twin.

## 3. A trained model as a sense

A sense takes a frozen model as its codec: anything with `encode(items)`, of any width. The
brain maps the codes onto its own sphere and keeps its own record of what it meets; nothing is
fitted by your program.

```python
from ubrain.extras.clip import CLIP          # the `vision` extra
brain.attach("sense", "vision", codec=CLIP("image"))
out = brain.tick({"sense.vision": frame})    # an (h, w, 3) uint8 image
```

`examples/08_g1_vision.py` sees through the robot's head camera this way.

## 4. Connect the robot

The MuJoCo G1 runs in its own process (`bodies/mujoco`). `ubrain.bodies.g1.G1` attaches the
body's streams to a whole brain and converts between the body and the brain:

```python
from ubrain.bodies import BodyClient, start_body
from ubrain.bodies.g1 import G1

proc, port = start_body()                      # finds bodies/mujoco (or set UBRAIN_BODY)
body = BodyClient("127.0.0.1", port)
g1 = G1(body.hello)
g1.attach(brain)                               # body.proprio, cue.tone, goal, command
state = body.reset(0)
while True:
    out = brain.tick(g1.streams(state, goal=(0.4, 0.0, 0.0)) | {"sense.vision": ...})
    state = body.act(*g1.act(out))
```

| stream | what it carries | kind |
|---|---|---|
| `body.proprio` | 70 numbers: torso and pelvis IMU, 29 joint angles and velocities | a sense |
| `cue.tone` | a sound the body hears (`G1(hello, cue=False)` leaves it out) | a sense |
| `goal` | the walk your program wants, (vx, vy, wz) | your program's |
| `command` | the walk the brain sends: the goal plus the cerebellum's counter-move | the brain's |

Inside is a certified cerebellum: it predicts the body and learns to brace on the tone (held bit
for bit to the circuit it was certified in). Two helpers are your program's, not senses:
`push_direction(before, during)` reads which way the body was pushed from the pelvis
accelerometer (your program knows when it pushed), and `privileged_contact(state)` returns the
feet's contact forces, which a real humanoid does not have (ask with `want_contact=True`).
`examples/04_g1_brace.py` to `07_g1_lead.py` are the full loops.

## 5. Ask a brain, keep a brain

A brain answers questions about itself, and reading changes nothing:

```python
brain.describe()            # its port classes, the observables read() serves, its guarantees
brain.read("value")         # an observable as the last tick left it (also novel, surprise, source, ...)
brain.datasheet()           # its capacities, from the laws that certified its regions
brain.health()              # what it holds, against those laws
```

It learns all its life, so its state is its knowledge. Save it, and load it with the same
codecs:

```python
path = brain.save("trained.ubrain.npz")
again = Brain.load(path, codecs={"sense.vision": GaussianCodes(dim=64, seed=1)})
```

Loading refuses, with a `ubrain.state.StateError` saying why, a codec that is not the one the
state was learned with, a region whose state changed between ubrain releases, or a file of an
unknown schema. `examples/02_ask.py` and `03_keep.py` show both; `06_g1_keep.py` demonstrates a
trained robot from its saved file.

## 6. Two rules every program needs

- **A sense must change.** The whole brain engages, and chooses, only on what is new or
  surprising. A sense that shows one fixed thing never engages it: its action stays `None`.
- **Make a wrong choice pay nothing.** The whole brain explores only while its values are near
  zero; the Go race picks in proportion to value, so once an action has paid, an action never
  tried is almost never tried. A reward that pays the wrong action half the time is never
  unlearned (`examples/05_g1_choose.py` tells how this was found).

## Where next

- [Concepts](concepts.md): regions, channels, codecs and certificates in more depth.
- The examples are short and meant to be copied; each ends with its check.

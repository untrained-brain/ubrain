# ubrain: Untrained Brain

**Never trained, always learning.**

A brain you can run on a laptop. It learns from experience by local plasticity, as
synapses do: one-shot memories, values learned from reward, a cerebellum that
learns its body. No pre-training, no gradient descent, no dataset. Plug in any
trained AI model (CLIP, a language model) as its senses, and any body (a simulated
humanoid robot, a Gymnasium game) as its interface.

Every behaviour of the brain follows a law written down before it was measured,
and ubrain can tell you, before you run it, what the brain will do with your
model's codes: a **certificate**.

## Five minutes to a learning brain

```bash
git clone https://github.com/untrained-brain/ubrain
cd ubrain
uv run examples/01_whole_brain.py   # the whole brain learns which action each picture asks for
uv run examples/03_keep.py          # save it, load it, and it continues exactly
```

([uv](https://docs.astral.sh/uv/) installs Python and the dependencies for you; numpy is the
only one.)

**On Windows, clone with long paths on**, or the robot's kitchen world stops the checkout
half-way ("Filename too long"):

```bash
git clone -c core.longpaths=true https://github.com/untrained-brain/ubrain
```

(Prefer the clone to the ZIP download: Windows' own unzip has the same 260-character path limit.)

Every example uses the whole brain, `Brain()`, and has the same shape: what it shows, the
question, a twin (the same run with one thing changed), and a check -- its last line is
`CHECK PASS` or `CHECK FAIL`, and its exit code says the same.

| example | the question | needs |
|---|---|---|
| `00_check_setup.py` | is this computer ready for the robot examples? (2 minutes) | the body |
| `01_whole_brain.py` | does the whole brain learn which action each picture asks for? (twin: unrelated pictures) | nothing |
| `02_ask.py` | what does the brain say about itself: describe, read, datasheet, health? | nothing |
| `03_keep.py` | does a saved and loaded brain choose exactly what the original would? | nothing |
| `04_g1_brace.py` | does the whole brain keep the G1 up when a tone warns of a push? (twin: no tone) | the body |
| `05_g1_choose.py` | does it learn which way to turn from a picture? (twin: unrelated pictures) | the body |
| `06_g1_keep.py` | trained, saved and loaded: does the demo brain stay up where a fresh one falls? | the body |
| `07_g1_lead.py` | how long a warning can the cerebellum use? (a prediction written first, and it failed) | the body |
| `08_g1_vision.py` | what does the brain call new, seeing through the head camera with CLIP? (twin: covered camera) | the body, `--extra vision`, the CLIP weights |

"The body" means the robot, set up once: it ships in this repository, in `bodies/mujoco`
(its own environment: MuJoCo, the G1, the photo gallery); `cd bodies/mujoco && uv sync`.
The robot examples take `--viewer` to watch in real time. "The CLIP weights" are fetched
once per machine (about 600 MB).

## Use it in your own code

ubrain ships as compiled wheels in `wheels/` (Windows, macOS, Linux; Python 3.11-3.13).
Install it into your project from this folder -- with uv, record the folder in your
project's `pyproject.toml` and add ubrain:

```toml
[tool.uv]
find-links = ["/path/to/ubrain/wheels"]
```

```bash
uv add "ubrain==0.46.0.dev2"
# or with pip:  pip install "ubrain==0.46.0.dev2" --find-links /path/to/ubrain/wheels
```

The whole brain needs no wiring: choose a variant, attach streams by port class, tick it (a
preview: the whole is not yet certified as a whole; `examples/01_whole_brain.py` shows what it
does and the law beside it):

```python
from ubrain import Brain, GaussianCodes
brain = Brain(variant="small")
brain.attach("sense", "vision", codec=GaussianCodes(dim=64, seed=1))   # any frozen model as the codec
brain.attach("reward")
brain.attach("action", n=4)
action = brain.tick({"sense.vision": 2, "reward": None})["action"]
```

A robot: `ubrain.bodies.g1.G1(hello).attach(brain)` adds the body's streams (`body`, `cue`,
`goal`, `command`); see `examples/04_g1_brace.py`.

Extras, each installed only when you ask for it: `ubrain[vision]` (CLIP as a sense: torch,
transformers), `ubrain[video]` (MP4 recording), `ubrain[plot]` (matplotlib).

## The manual

- [Quickstart](docs/quickstart.md): install, run, what you are looking at
- [Using ubrain in your own code](docs/using.md): install from the wheels, write your own
- [Concepts](docs/concepts.md): regions, wiring, bodies, codecs and certificates
- The examples (`examples/`): each one short, meant to be copied, on the whole brain, ending
  with its check

## Three layers

| layer | what | examples |
|---|---|---|
| **codecs** (plug-in) | frozen AI models that turn the world into codes | CLIP (`ubrain[vision]`) |
| **the brain** | `Brain()`: every region, wired once, stepped one tick at a time; numpy only | hippocampus, cortex, prefrontal cortex, striatum, cerebellum, salience, thalamus, neuromodulators |
| **bodies** (plug-in) | anything that sends senses and takes actions | the MuJoCo G1 (over a small protocol), a Gymnasium game with discrete states (`ubrain.bodies.gym`) |

```python
from ubrain import Brain, GaussianCodes
brain = Brain(variant="small")
brain.attach("sense", "vision", codec=GaussianCodes(dim=64, seed=1))
brain.attach("reward"); brain.attach("action", n=4)
action = brain.tick({"sense.vision": s, "reward": r})["action"]
```

## Status

Pre-release, 0.46.0.dev2: the whole brain, `Brain()`, with seventeen regions. The cerebellum (a forward
model, a timed brace, walking adaptation); the striatum (on an index, or on a situation code
conditioned by a goal); the hippocampus (an episode, and a
store that acts, keyed through the dentate gyrus) and the hand-over from it to the striatum; the cortex's slow store; the
prefrontal cortex's working memory (active and silent); the salience gate and the mode
controller; the thalamus; and three neuromodulators (acetylcholine, noradrenaline,
serotonin). The regions are certified copies from a research engine in which every law is
written down before it is measured; ubrain never changes a region's code by hand. How the
engine is built is the subject of *The Untrained Brain Series*, Volume 2: *Building the
Brain Engine* (in preparation).

Copyright 2026 Hong Jeong. The examples, documentation and profiles are under the
Apache License 2.0 (`LICENSE`); the ubrain package is distributed compiled, under
`LICENSE-BINARY`: free for any use, commercial included; you may ship it unmodified inside
what you build, but not republish it on its own, modify it or reverse-engineer it.
The robot body in `bodies/mujoco` is Apache-2.0, with third-party parts under their own
licences (its `NOTICE`).

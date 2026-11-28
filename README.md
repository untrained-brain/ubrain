# ubrain: Untrained Brain

**Never trained, always learning.**

A brain you can run on a laptop. It learns from experience as it goes: one-shot memories, values
learned from reward, a cerebellum that learns its body, and nights that consolidate the day. No
pre-training, no gradient descent, no dataset. Plug in any trained AI model (CLIP, a language
model) as its senses, and any body (a simulated humanoid robot, a game) as its interface.

## Install

```bash
uv add "ubrain==0.58.0.dev1"
# or with pip:  pip install "ubrain==0.58.0.dev1"      (or: pip install --pre ubrain)
```

Compiled wheels for Windows, macOS and Linux, Python 3.11-3.13; numpy is the only dependency.
Every version is a pre-release until 1.0, so name the version (or allow pre-releases). Extras, each
only when you ask for it: `ubrain[vision]` (CLIP as a sense), `ubrain[video]` (MP4 recording),
`ubrain[plot]` (matplotlib).

## A brain that learns, in ten lines

```python
from ubrain import Brain, GaussianCodes

brain = Brain(variant="small")                                   # the whole brain, wired for you
brain.attach("sense", "vision", codec=GaussianCodes(dim=64, seed=1))   # any frozen model as a sense
brain.attach("reward")
brain.attach("action", n=4)

reward = None
for t in range(2000):
    picture = t % 8                                              # what it sees
    action = brain.tick({"sense.vision": picture, "reward": reward})["action"]
    reward = float(action == picture % 4)                        # the world's answer
```

## What you can do with it

**Let it sleep.** By day the brain keeps every event once; a night consolidates them into its
long-term memory and empties the day's store. Call a night whenever it suits you (when idle, every
so many ticks); a full store forces one by itself.

```python
brain.sleep_pressure      # how full the day's store is, 0 to 1
brain.night()             # consolidate now
```

**Keep it.** A brain learns all its life, so its state is its knowledge. Save it to one file and load
it later; it continues exactly.

```python
brain.save("my_brain.ubrain")
same = Brain.load("my_brain.ubrain", codecs={"sense.vision": GaussianCodes(dim=64, seed=1)})
```

**Ask it.** `brain.read("value")`, `brain.read("prediction_error")`, `brain.read("source")` and the other
observables say what it values, how its last outcome differed from what it expected, and which system chose;
`brain.describe()` lists its parts and which observables it carries (0.58: `novel`, `surprise` and `held` return
with their organs); `brain.health()` checks it against its own laws.

**Look inside.** `ubrain.debug` explains a decision and checks the state, without changing the brain:

```python
from ubrain.debug import trace, check, FlightRecorder
trace(brain, {"sense.vision": 5, "reward": None})["responsible"]   # which parts made this choice
check(brain)                                                       # [] when the state is healthy
```

`FlightRecorder(brain)` keeps the last ticks for a post-mortem; `first_divergence(a, b)` finds where
two brains first differ.

**Give it senses and a body.** A sense is any frozen encoder (`ubrain.Codec`: its name, width and
`encode`); CLIP ships as `ubrain[vision]`. A body sends senses and takes actions over a small protocol:
a simulated Unitree G1 humanoid (in this repository, `bodies/mujoco`) or a Gymnasium game
(`ubrain.bodies.gym`).

**Let it use other AI, under its own control.** `ubrain.agents.AgentPort` lets the brain call other AI
systems as advisers: it asks only when it chooses, treats every reply as a proposal, learns whom to
trust from how proposals turn out, and stops at a daily budget. ubrain holds no keys and ships no
adapter for any hosted service: you bring your own. `ubrain.owner.Owner` puts you above the brain:
commands, a policy of what it may do, and a log of every decision. `ubrain.select.Lexicon` lets it
name what it has received (a sentence, a picture, a movement).

## Examples

```bash
git clone https://github.com/untrained-brain/ubrain
cd ubrain
uv run examples/01_whole_brain.py   # the whole brain learns which action each picture asks for
uv run examples/03_keep.py          # save it, load it, and it continues exactly
```

([uv](https://docs.astral.sh/uv/) installs Python and the dependencies for you.) On Windows, clone
with long paths on, or the robot's world stops the checkout half-way ("Filename too long"):
`git clone -c core.longpaths=true https://github.com/untrained-brain/ubrain`.

Each example is short and meant to be copied: what it shows, the question, a twin (the same run with
one thing changed), and a check -- its last line is `CHECK PASS` or `CHECK FAIL`.

| example | the question | needs |
|---|---|---|
| `00_check_setup.py` | is this computer ready for the robot examples? (2 minutes) | the body |
| `01_whole_brain.py` | does the whole brain learn which action each picture asks for? | nothing |
| `02_ask.py` | what does the brain say about itself: describe, read, datasheet, health? | nothing |
| `03_keep.py` | does a saved and loaded brain choose exactly what the original would? | nothing |
| `04_g1_brace.py` | does the brain keep the G1 up when a tone warns of a push? | the body |
| `05_g1_choose.py` | does it learn which way to turn from a picture? | the body |
| `06_g1_keep.py` | trained, saved and loaded: does the demo brain stay up where a fresh one falls? | the body |
| `07_g1_lead.py` | how long a warning can the cerebellum use? | the body |

"The body" is the robot, set up once from this repository: `cd bodies/mujoco && uv sync` (MuJoCo, the
G1, a photo gallery). The robot examples take `--viewer` to watch in real time. The wheels are also in
this repository's `wheels/` folder, for a machine without PyPI access
(`pip install ubrain==0.58.0.dev1 --find-links /path/to/ubrain/wheels`).

## The manual

- [Quickstart](https://github.com/untrained-brain/ubrain/blob/main/docs/quickstart.md): install, run, what you are looking at
- [Using ubrain in your own code](https://github.com/untrained-brain/ubrain/blob/main/docs/using.md): write your own
- [Concepts](https://github.com/untrained-brain/ubrain/blob/main/docs/concepts.md): the brain's parts, senses, bodies and certificates
- [What's new](https://github.com/untrained-brain/ubrain/blob/main/CHANGELOG.md): each version, and how to use it

## What is inside

| layer | what | examples |
|---|---|---|
| **senses** (plug-in) | frozen AI models that turn the world into codes | CLIP, a sentence encoder, your own |
| **the brain** | `Brain()`: memory (hippocampus, cortex), values and habits (striatum), prediction (cerebellum), attention and modes, working memory, neuromodulators, sleep; numpy only | -- |
| **bodies** (plug-in) | anything that sends senses and takes actions | a simulated G1 humanoid, a Gymnasium game |

Each part of the brain follows a law measured before it is released, and ubrain can tell you before
you run it what the brain will do with your model's codes: a certificate (`ubrain.certify`).

## Status and licence

Pre-release (0.58.0.dev1). The API may still change between versions; the [changelog](CHANGELOG.md)
says what changed and how to use it.

Copyright 2026 Hong Jeong. The examples, documentation and profiles are under the Apache License 2.0
(`LICENSE`); the ubrain package is distributed compiled, under `LICENSE-BINARY`: free for any use,
commercial included; you may ship it unmodified inside what you build, but not republish it on its own,
modify it or reverse-engineer it. The robot body in `bodies/mujoco` is Apache-2.0, with third-party
parts under their own licences (its `NOTICE`).

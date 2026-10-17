# ubrain: Untrained Brain

**Never trained, always learning.**

A brain you can run on a laptop. It learns from experience by local plasticity, as
synapses do: one-shot memories, values learned from reward, a cerebellum that
learns its body. No pre-training, no gradient descent, no dataset. Plug in any
trained AI model (CLIP, a language model) as its senses, and any body (a simulated
humanoid robot, a game) as its interface.

Every behaviour of the brain follows a law written down before it was measured,
and ubrain can tell you, before you run it, what the brain will do with your
model's codes: a **certificate**.

## Five minutes to a learning brain

```bash
git clone https://github.com/untrained-brain/ubrain
cd ubrain
uv run examples/01_bandit.py        # the striatum learns which action pays
uv run examples/02_memory.py        # an episode in the hippocampus, against its certificate
```

([uv](https://docs.astral.sh/uv/) installs Python and the dependencies for you; numpy is the
only one.)

| example | what you see | needs |
|---|---|---|
| `01_bandit.py` | values learned from reward; choice that *matches* payoffs, as animals' does | nothing |
| `02_memory.py` | one-shot memory of an episode; recall falls with load exactly as certified | nothing |
| `03_clip_words.py` | CLIP plugged in as a sense: the brain hears a sentence and recalls it | `--extra vision` |
| `g1_walker.py` | the brain in a Unitree G1 humanoid: it walks, predicts its body, learns to brace | the body |
| `g1_explorer.py` | the G1 walks past a gallery of photos and remembers what it saw | the body, `--extra vision` |

The robot body ships in this repository, in `bodies/mujoco` (its own environment: MuJoCo,
the G1, the photo gallery). Set it up once with `cd bodies/mujoco && uv sync`.

## Use it in your own code

ubrain ships as compiled wheels in `wheels/` (Windows, macOS, Linux; Python 3.11-3.13).
Install it into your project from this folder -- with uv, record the folder in your
project's `pyproject.toml` and add ubrain:

```toml
[tool.uv]
find-links = ["/path/to/ubrain/wheels"]
```

```bash
uv add "ubrain==0.6.0.dev0"
# or with pip:  pip install "ubrain==0.6.0.dev0" --find-links /path/to/ubrain/wheels
```

```python
from ubrain import Brain, Channel, Manifest, profile
body = Manifest("my-app", "v1", (Channel("situation", "event", 3),
                                 Channel("reward", "reward", 1),
                                 Channel("action", "choice", 2)))
brain = Brain(profile("player"), body)
action = brain.tick({"situation": [1, 0, 0], "reward": None})["action"]
```

The full guide -- profiles, your own anatomy, plugging in a model, connecting a robot --
is [Using ubrain in your own code](docs/using.md).

## The manual

- [Quickstart](docs/quickstart.md): install, run, what you are looking at
- [Using ubrain in your own code](docs/using.md): install from the wheels, write your own
- [Concepts](docs/concepts.md): regions, wiring, bodies, codecs and certificates
- [Labs](docs/labs/README.md): five laboratory sessions with exercises
- [For teachers](docs/teachers.md): running the labs with a class

## Three layers

| layer | what | examples |
|---|---|---|
| **codecs** (plug-in) | frozen AI models that turn the world into codes | CLIP (`ubrain[vision]`) |
| **the brain** | regions wired by a profile, stepped one event at a time; numpy only | hippocampus, striatum, cerebellum |
| **bodies** (plug-in) | anything that sends senses and takes actions over a small protocol | the MuJoCo G1 |

```python
from ubrain import Brain, profile
brain = Brain(profile("player"), body_manifest)
action = brain.tick({"situation": s, "reward": r})["action"]
```

## Status

Pre-release, 0.6.0.dev0. The regions are certified copies from a research engine in
which every law is registered before it is measured; ubrain never changes a region's
code by hand. The science is in the textbook *The Untrained Brain* (in preparation).

Copyright 2026 Hong Jeong. The examples, documentation and profiles are under the
Apache License 2.0 (`LICENSE`); the ubrain package is distributed compiled, under
`LICENSE-BINARY`: free for any use, commercial included; you may ship it unmodified inside
what you build, but not republish it on its own, modify it or reverse-engineer it.
The robot body in `bodies/mujoco` is Apache-2.0, with third-party parts under their own
licences (its `NOTICE`).

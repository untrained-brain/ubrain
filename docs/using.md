# Using ubrain in your own code

ubrain is distributed as **compiled wheels**, in this repository's `wheels/` folder:
one per platform and Python version (Windows x64, macOS Apple Silicon and Intel,
Linux x86_64; Python 3.11, 3.12, 3.13). The installer picks the right one. The only
other dependency is numpy.

## 1. Install it into your project

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
uv add "ubrain==0.6.0.dev0"
uv run python -c "import ubrain; print(ubrain.__version__)"
```

Keep `find-links` in `pyproject.toml` (rather than passing `--find-links` to `uv add`
once): uv needs it every time it re-solves your dependencies, for example when you
add another package. For CLIP as a sense: `uv add "ubrain[vision]==0.6.0.dev0"`.

**With pip**, in a virtual environment:

```bash
pip install "ubrain==0.6.0.dev0" --find-links /path/to/ubrain/wheels
```

(Version 0.6.0.dev0 is a pre-release, so name it exactly as above. When ubrain is on
PyPI, `pip install ubrain` will be enough.)

## 2. A brain in a few lines

A brain needs two things: an **anatomy** (a profile: which regions, wired how) and a
**body** (a manifest: the channels it senses and acts on). Then you call
`brain.tick(senses)` once per event and get actions back.

```python
import numpy as np
from ubrain import Brain, Channel, Manifest, profile

# the body: a situation (one of 3), a reward, and an action (one of 2)
body = Manifest("my-app/bandit", "v1", (
    Channel("situation", "event", 3),
    Channel("reward", "reward", 1),
    Channel("action", "choice", 2),
))
brain = Brain(profile("player"), body, rng=np.random.default_rng(0))

rng = np.random.default_rng(1)
reward = None
for t in range(2000):
    s = int(rng.integers(3))
    a = brain.tick({"situation": np.eye(3)[s], "reward": reward})["action"]
    reward = float(rng.random() < (0.8 if a == s % 2 else 0.2))   # your world's rule

print(brain.regions["basal_ganglia.striatum"].Q)                  # what it learned
```

The `player` profile's names (`situation`, `reward`, `action`) are the channels your
manifest must provide. Each profile ships with ubrain:

| profile | regions | your body must provide |
|---|---|---|
| `player` | striatum | `situation` (event), `reward` (reward), `action` (choice) |
| `observer` | hippocampus | `camera` (codec), `recall` (event), `boundary` (event), `memory` (command), `remembered` (choice) |
| `walker` | cerebellum (forward model, brace) | a legged body's `proprio`, `tone`, `goal`, `walk`, `offsets` |
| `explorer` | walker + hippocampus | the walker's channels plus the observer's |

## 3. Your own anatomy

A profile is a small TOML file. Copy one and change it -- rename channels, tune
parameters, combine regions -- then load it with `ubrain.load`:

```toml
# my_player.toml
[brain]
name = "my_player"
contract = "1.0"

[regions."basal_ganglia.striatum"]
eta = 0.05                     # a slower learner
q0 = 0.5

[inputs]
"basal_ganglia.striatum.state"  = "level"      # your channel names
"basal_ganglia.striatum.reward" = "score"

[outputs]
move = "basal_ganglia.striatum"
```

```python
from ubrain import Brain, Channel, Manifest, load
body = Manifest("my-game", "v1", (Channel("level", "event", 5),
                                  Channel("score", "reward", 1),
                                  Channel("move", "choice", 4)))
brain = Brain(load("my_player.toml"), body)
```

The brain checks the wiring against the body when you create it and names anything
that does not fit.

## 4. Plug in a trained model

Any object with `name`, `modality`, `dim`, `digest`, `license` and `encode(items)` is a
codec. Fit it into a `Sense` on a sample of the items it will see (its vocabulary),
check what the brain can hold with it, and plug it into a `codec` channel:

```python
from ubrain import Sense, certify
from ubrain.extras.clip import CLIP            # needs the vision extra

clip = CLIP("text")
words = ["apple", "river", "fox", ...]         # the vocabulary
print(certify(clip, words, d=512).summary())   # what the brain holds with these codes
sense = Sense.fit(clip, words, d=512)
brain = Brain(profile("observer"), body, codecs={"camera": sense})
```

`examples/03_clip_words.py` is the whole program.

## 5. Connect a robot

A body that runs in its own process (the MuJoCo G1 in `bodies/mujoco`) is reached
through `ubrain.bodies`:

```python
from ubrain.bodies import BodyClient, start_body
from ubrain import manifest_from_hello_03

proc, port = start_body()          # finds bodies/mujoco (or set UBRAIN_BODY to the body's folder)
body = BodyClient("127.0.0.1", port)
manifest = manifest_from_hello_03(body.hello)
```

`examples/g1_walker.py` shows the full loop.

## Where next

- [Concepts](concepts.md): regions, channels, codecs and certificates in more depth.
- The examples are short and meant to be copied.

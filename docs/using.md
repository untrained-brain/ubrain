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
uv add "ubrain==0.38.0.dev1"
uv run python -c "import ubrain; print(ubrain.__version__)"
```

Keep `find-links` in `pyproject.toml` (rather than passing `--find-links` to `uv add`
once): uv needs it every time it re-solves your dependencies, for example when you
add another package. The extras, each only when you need it:

| extra | what it brings | for |
|---|---|---|
| `vision` | torch, transformers (CLIP) | CLIP as a sense: `uv add "ubrain[vision]==0.38.0.dev1"` |
| `game` | Gymnasium | a game as the body (`ubrain.bodies.gym`) |
| `video` | imageio with ffmpeg | recording the robot examples as MP4 |
| `plot` | matplotlib | the lab plots |

**With pip**, in a virtual environment:

```bash
pip install "ubrain==0.38.0.dev1" --find-links /path/to/ubrain/wheels
```

(Version 0.38.0.dev1 is a pre-release, so name it exactly as above. When ubrain is on
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
| `chooser` | hippocampal store that acts + striatum + hand-over | the player's channels |
| `corticostriatal` | striatum on a code | `situation` (vector or codec), `goal` (goal, the situation's width), `reward` (reward), `explore` (flag), `action` (choice) |
| `whole` | the route, from the sense to an action | `camera` (codec), `reward` (reward), `goal_slot`, `recall`, `recollect` (events), `action` (choice), `memory`, `recollection` (command), `mode` (choice) |
| `observer` | hippocampus | `camera` (codec), `recall` (event), `boundary` (event), `memory` (command), `remembered` (choice) |
| `rememberer` | hippocampus + cortex | the observer's channels plus `recollect` (event), `recollection` (command), `recollected` (choice) |
| `holder` | prefrontal buffer | `camera` (codec), `recall`, `idle`, `clear` (events), `memory` (command), `remembered` (choice) |
| `attender` | salience gate + mode controller + hippocampus + cortex | the rememberer's channels (no `boundary`: an idle moment ends the episode) plus `mode` (choice, 2) |
| `modulated` | thalamus + the three neuromodulators + salience gate + mode controller + cortex + striatum | `routes`, `goal` (vectors), `attend` (event), `camera`, `known` (codecs), `recollect` (event), `situation`, `reward`; out `workspace`, `attended`, `recollection`, `recollected`, `mode`, `action` |
| `walker` | cerebellum (forward model, brace) | a legged body's `proprio`, `tone`, `goal`, `walk`, `offsets` |
| `adapter` | walker + walking adaptation | the walker's channels plus `clamp` (flag) |
| `explorer` | walker + hippocampus | the walker's channels plus the observer's |

To see a profile's exact wiring, print it: `print(profile("chooser"))`, or read the TOML
files in the folder `python -c "import ubrain.wiring as w; print(w.PROFILES)"` names.
To change one parameter without a file of your own, edit the loaded profile before
building the brain:

```python
w = profile("player")
w.regions["basal_ganglia.striatum"]["eta"] = 0.01      # a slower learner
brain = Brain(w, body)
```

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

## 5. Play a game

Any Gymnasium game whose observations and actions are discrete is a body, through
`ubrain.bodies.gym` (the `game` extra):

```python
import gymnasium as gym
from ubrain import Brain, profile
from ubrain.bodies.gym import GymBody, play

body = GymBody(gym.make("Blackjack-v1", sab=True), reward_range=(-1, 1), reward="return")
brain = Brain(profile("player"), body.manifest)
returns = body.run(brain, episodes=1000, seed=0)     # one summed reward per episode
body.close(brain)                                    # the last outcome reaches the brain
```

`reward_range` maps the game's rewards onto [0, 1], where the brain reads them.
`reward="step"` passes every step's reward; `reward="return"` passes nothing inside an
episode and its total after it -- with the `chooser` profile, which credits every choice
of the episode, that values each move by how the episode ended. `play(env, policy,
episodes)` runs a brainless baseline to compare with. A tuple of discrete observations
(Blackjack's) becomes one situation index; continuous observations are refused.

The brain learns a value from the outcome that follows a choice, not from the value of
the state it leads to, so a reward many moves away from the choice that earned it is
out of reach of the `player` on its own. `examples/04_blackjack.py` and
`examples/05_frozenlake.py` show both what works and where it stops.

## 6. Connect a robot

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

## 7. Save, load and watch a brain (since 0.14; the file names what it needs since 0.15)

A brain learns all its life, so its state is its knowledge. Save it, and load it
against the same body (and the same codecs, if it has senses):

```python
from ubrain import Brain
from ubrain.state import read_header

path = brain.save("player.ubrain.npz")
print(read_header(path))                 # format, ubrain version, wiring, body, ticks, codecs, lineage
again = Brain.load(path, body)           # continues bit for bit where `brain` stopped
```

The file names everything the brain needs to run again: the body's own record (its
versions, how it was launched, the release that holds it), every sense as the fitted
sense itself (the codec's name, digest and licence, the mean and vocabulary), the
wiring and its digest, and the brain's **lineage** -- the content digests of the
states it was loaded from (`brain.lineage`). So a user with the file and the codec
model gets the whole system back:

```python
from ubrain.bodies import start_body_for

proc, body, manifest = start_body_for(path)       # THE body the file names, or a refusal saying which field differs
brain = Brain.load(path, manifest, {"camera": clip})   # the codec model: the fitted sense is in the file
```

Loading refuses, with a `ubrain.state.StateError` saying why, a different body (naming
the field that differs -- its MuJoCo version, its robot's digest -- and the release to
fetch), a codec that is not the one the state was learned with, a region whose state
changed between ubrain releases, or a file of an unknown schema; a schema-1 file (0.14)
is migrated on load. `examples/11_save_and_load.py` shows the continuation, the senses
coming back from the file, the lineage and every refusal.

A saved brain describes itself: `python -m ubrain.card player.ubrain.npz` writes its
model card (the body release, the codecs and licences, how to load it, its lineage,
its datasheet), generated from the file, never typed. With the `hub` extra
(`pip install ubrain[hub]`), `ubrain.extras.hub.push_state(path, "you/your-brain")`
puts the file and its card on the Hugging Face Hub -- private by default -- and
`pull_state` brings one back; the pool of saved brains is the Hub.

A brain can also describe itself. `datasheet_text(brain)` lists its figures in closed
form (an episode's capacity, the buffer's count, the cortex's capacity or horizon, the
brace's lead, the striatum's time constant), each with the conditions it holds under;
`health(brain)` sets what a region holds now against its law; `observe(brain)` returns
read-only copies of each region's state; and `monitor_manifest(brain)` with
`monitor(brain)` turn that state into channels, so that one brain can watch another.

```python
from ubrain.datasheet import datasheet_text
from ubrain.observe import health, observe

print(datasheet_text(brain))
for row in health(brain):
    print(row)
```

The figures are first-order laws. At a small dimension (d near 100) a measurement
lands at or a little above them; the cortex's capacity assumes distinct items (copies of
one item add crosstalk together). `examples/12_monitor_and_datasheet.py` sets each
figure beside a measurement.

## Where next

- [Concepts](concepts.md): regions, channels, codecs and certificates in more depth.
- The examples are short and meant to be copied.

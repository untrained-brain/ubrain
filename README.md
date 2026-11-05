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
uv run examples/01_bandit.py        # the striatum learns which action pays
uv run examples/02_memory.py        # an episode in the hippocampus, against its certificate
uv run --extra game examples/04_blackjack.py   # the same brain plays Blackjack
```

([uv](https://docs.astral.sh/uv/) installs Python and the dependencies for you; numpy is the
only one.)

| example | what you see | needs |
|---|---|---|
| `check_setup.py` | is this computer ready for the robot examples? (2 minutes) | the body |
| `01_bandit.py` | values learned from reward; choice that *matches* payoffs, as animals' does | nothing |
| `02_memory.py` | one-shot memory of an episode; recall falls with load exactly as certified | nothing |
| `03_clip_words.py` | CLIP plugged in as a sense: the brain hears a sentence and recalls it | `--extra vision`, the CLIP weights |
| `04_blackjack.py` | a Gymnasium game as the body: the striatum and the hippocampal store learn Blackjack (about a minute) | `--extra game` |
| `05_frozenlake.py` | the same brain on FrozenLake, and where a one-step learning rule stops | `--extra game` |
| `06_working_memory.py` | a list held in working memory: recall by position follows the count law; rehearsal keeps it | nothing |
| `07_consolidation.py` | the hippocampus replays its episodes into the cortex; the cortex holds hundreds where an episode holds a handful | nothing |
| `08_attention.py` | the salience gate writes only what is novel, at the false-alarm rate it was set to; the modes switch | nothing |
| `09_memory_and_habit.py` | memory acts from one experience, the striatum catches up and overtakes; the hand-over follows the better | nothing |
| `10_neuromodulators.py` | noradrenaline sets what counts as novel, serotonin how long the striatum waits for a reward | nothing |
| `11_save_and_load.py` | a brain saved and loaded continues exactly where it stopped; the file names what it needs (body release, senses, lineage), the sense comes back from the codec model alone, another body is refused; its model card | nothing |
| `12_monitor_and_datasheet.py` | a brain's datasheet (its capacities in closed form), its health, and a brain watching a brain | nothing |
| `g1_walker.py` | the brain in a Unitree G1 humanoid: it walks, predicts its body, learns to brace | the body |
| `lab_cerebellum.py` | change the G1's cerebellum (sparseness, learning rates, the tone's trace) and measure it | the body |
| `g1_bracing.py` | a tone, then a push: muted it falls every time; braced, the cerebellum learns to stay up | the body |
| `g1_explorer.py` | the G1 walks past a gallery of photos and remembers what it saw | the body, `--extra vision`, the CLIP weights |

The examples marked "nothing" or `--extra game` run headless on any laptop. "The body" means
the robot, set up once (below); the robot examples take `--headless` when no window is
wanted. "The CLIP weights" are fetched once per machine (about 600 MB; `03_clip_words.py`
prints the command when they are missing).

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
uv add "ubrain==0.35.0.dev1"
# or with pip:  pip install "ubrain==0.35.0.dev1" --find-links /path/to/ubrain/wheels
```

The whole brain needs no wiring: choose a variant, attach streams by port class (a preview in
0.28: the whole is not yet certified as a whole; `examples/00_whole_brain.py` shows what it does
and the law beside it):

```python
from ubrain import Brain, GaussianCodes, Sense
camera = Sense.fit(GaussianCodes(dim=64, seed=1), range(4), d=128)   # any AI model as the codec
brain = Brain(variant="small")
brain.attach("sense", "vision", codec=camera)
brain.attach("reward")
brain.attach("action", n=4)
action = brain.tick({"sense.vision": 2, "reward": None})["action"]
```

A circuit of chosen regions (a profile) is the experts' layer:

```python
from ubrain import Brain, Channel, Manifest, profile
body = Manifest("my-app", "v1", (Channel("situation", "event", 3),
                                 Channel("reward", "reward", 1),
                                 Channel("action", "choice", 2)))
brain = Brain(profile("player"), body)
action = brain.tick({"situation": [1, 0, 0], "reward": None})["action"]
```

Extras, each installed only when you ask for it: `ubrain[vision]` (CLIP as a sense: torch,
transformers), `ubrain[game]` (Gymnasium games as a body), `ubrain[video]` (MP4 recording),
`ubrain[plot]` (matplotlib, for the lab plots).

The full guide -- the ten profiles, your own anatomy, plugging in a model, playing a game,
connecting a robot -- is [Using ubrain in your own code](docs/using.md).

## The manual

- [Quickstart](docs/quickstart.md): install, run, what you are looking at
- [Using ubrain in your own code](docs/using.md): install from the wheels, write your own
- [Concepts](docs/concepts.md): regions, wiring, bodies, codecs and certificates
- The examples (`examples/`): each one short, meant to be copied, and printing what the
  law predicts beside what the brain did

## Three layers

| layer | what | examples |
|---|---|---|
| **codecs** (plug-in) | frozen AI models that turn the world into codes | CLIP (`ubrain[vision]`) |
| **the brain** | regions wired by a profile, stepped one event at a time; numpy only | hippocampus, cortex, prefrontal cortex, striatum, cerebellum, salience, thalamus, neuromodulators |
| **bodies** (plug-in) | anything that sends senses and takes actions | the MuJoCo G1 (over a small protocol), a Gymnasium game with discrete states (`ubrain.bodies.gym`) |

```python
from ubrain import Brain, profile
brain = Brain(profile("player"), body_manifest)
action = brain.tick({"situation": s, "reward": r})["action"]
```

## Status

Pre-release, 0.35.0.dev1: sixteen regions in thirteen profiles. The cerebellum (a forward
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

# Quickstart

## 1. Install

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) (it brings
Python with it) and git.

```bash
git clone https://github.com/untrained-brain/ubrain       # Windows: git clone -c core.longpaths=true ...
cd ubrain
```

There is nothing else to install: `uv run` builds an environment the first time.

Every example uses the whole brain, `Brain()`, and has the same shape: what it shows, the
question, a twin (the same run with one thing changed, so a difference has a cause), and a
check -- its last line is `CHECK PASS` or `CHECK FAIL`.

## 2. The whole brain, on a laptop

```bash
uv run examples/01_whole_brain.py      # it learns which action each picture asks for
uv run examples/02_ask.py              # it says what it is: describe, read, datasheet, health
uv run examples/03_keep.py             # saved and loaded, it continues exactly
```

`Brain()` is the whole brain, every region wired once and the same in every copy: you choose
a variant (sizes, never wiring) and attach streams by port class -- a sense through a frozen
codec, a reward, an action. The striatum releases actions by the Go race on its values: the
first example sets what the brain earned beside the race's law on the values it learned, and
beside a twin that sees only unrelated pictures. It is a preview: the whole is not yet
certified as a whole.

## 3. Put the brain in a robot

The body is in `bodies/mujoco`, with its own environment. Set it up once, then check:

```bash
cd bodies/mujoco && uv sync && cd ../..      # once: MuJoCo and the G1 (a few minutes)
uv run examples/00_check_setup.py             # walks the robot for 3 s
```

Then:

```bash
uv run examples/04_g1_brace.py     # a tone warns of a push; the cerebellum learns to stay up (twin: no tone)
uv run examples/05_g1_choose.py    # a picture says which way to turn; it learns to (twin: unrelated pictures)
uv run examples/06_g1_keep.py      # train, save, demonstrate the loaded brain (twin: a fresh brain)
uv run examples/07_g1_lead.py      # how long a warning can it use? (a prediction that failed)
```

Add `--viewer` to watch in real time. The whole brain takes the robot through four streams,
attached by `ubrain.bodies.g1.G1`: the body's proprioception, a tone it hears, the walk the
program wants (`goal`) and the walk the brain sends (`command`).

## Where next

- [Using ubrain in your own code](using.md): install from the wheels, the whole brain, a
  model as a sense, the robot, keeping a brain, and two rules every program needs.
- [Concepts](concepts.md): what a region, a body and a codec are.
- The examples (`examples/`): every one above is short and meant to be copied.

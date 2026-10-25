# Quickstart

## 1. Install

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) (it brings
Python with it) and git.

```bash
git clone https://github.com/untrained-brain/ubrain
cd ubrain
```

There is nothing else to install: `uv run` builds an environment the first time.

## 2. A brain that learns from reward

```bash
uv run examples/01_bandit.py
```

The brain sees one of three situations and picks one of three actions; each action
pays off with its own probability. Within a few thousand trials it has learned a
value for every (situation, action) pair, and its choices follow those values. The
printout sets what it learned beside what the world pays.

## 3. A brain that remembers

```bash
uv run examples/02_memory.py
```

The brain hears a list of items once and must recall the first. With 4 items it
never fails; with 32 it mostly does. Before running anything, ubrain prints a
**certificate**: the recall rate the law predicts at each load. The two columns
agree.

## 4. Plug in an AI model

```bash
uv run --extra vision examples/03_clip_words.py
```

This installs torch and CLIP's code (once, a few minutes) and uses CLIP's text
encoder as the brain's sense: the brain hears a sentence word by word and recalls
it. The CLIP checkpoint (about 600 MB) must be in your Hugging Face cache; if it is
not, the example says how to fetch it.

## 5. Let the brain play a game

```bash
uv run --extra game examples/04_blackjack.py     # about a minute
uv run --extra game examples/05_frozenlake.py    # a few seconds
```

This installs Gymnasium (once) and uses a game as the brain's body: the game shows a
situation, the brain picks a move, the game pays a reward. Nothing in the brain was
changed for it. At Blackjack, two anatomies learn: the striatum alone (`player`), and a
memory that acts on hands it has just seen, handing over to the striatum when it is unsure
(`chooser`). Both win more often than a random player already over the first 5,000 hands; neither reaches
the best strategy, because the striatum matches its choices to values rather than always
taking the best. On FrozenLake the reward comes only at the goal, many moves after the
first choice: crediting every move of an episode with how it ended finds the path, while
crediting only the last move does not -- the printout shows both.

## 6. The rest of the brain, on a laptop

```bash
uv run examples/06_working_memory.py      # a list in working memory, recall by position
uv run examples/07_consolidation.py       # the hippocampus replays into the cortex (under a minute)
uv run examples/08_attention.py           # only the novel is written; the modes switch
uv run examples/09_memory_and_habit.py    # memory first, habit later, a hand-over between them
uv run examples/10_neuromodulators.py     # noradrenaline and serotonin as single numbers
uv run examples/11_save_and_load.py       # save a brain, load it, it continues exactly
uv run examples/12_monitor_and_datasheet.py   # a brain's datasheet, health, and a monitor
```

Each prints, before it runs, what ubrain's laws predict, and then what the brain did. Where
a figure has no closed form, the example says it is shown, not predicted.

## 7. Put the brain in a robot

The body is in `bodies/mujoco`, with its own environment. Set it up once:

```bash
cd bodies/mujoco && uv sync && cd ../..      # once: MuJoCo and the G1 (a few minutes)
```

Then:

```bash
uv run examples/g1_walker.py                                   # a viewer window; arrow keys steer
uv run --extra vision --extra video examples/g1_explorer.py --viewer
```

The walker: arrow keys set the walking command, P sounds a tone and then pushes the
robot (press it again and again: the cerebellum learns to brace), B turns bracing on
and off. The explorer walks past 21 photographs and, at the end, recalls them in
order.

## Where next

- [Concepts](concepts.md): what a region, a wiring profile, a body and a codec are.
- The examples (`examples/`): every one above is short and meant to be copied.
- [Using ubrain in your own code](using.md): all ten profiles, your own anatomy, your
  own game or model.

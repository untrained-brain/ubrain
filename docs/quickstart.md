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
it. The CLIP checkpoint must be in your Hugging Face cache; if it is not, the
example says how to fetch it.

## 5. Put the brain in a robot

The body is its own package. Clone it beside ubrain and set it up once:

```bash
cd ..
git clone https://github.com/untrained-brain/ubrain-mujoco
cd ubrain-mujoco && uv sync && cd ../ubrain
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
- [Labs](labs/README.md): five sessions with exercises.

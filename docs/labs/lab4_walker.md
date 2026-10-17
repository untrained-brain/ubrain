# Lab 4 -- A brain in a body: the cerebellum

**Goal:** watch the cerebellum learn to predict its own body, and learn a timed
reflex from a cue.

## Setup (once)

The body is in `bodies/mujoco`; set it up once, from the ubrain folder:

```bash
cd bodies/mujoco && uv sync && cd ../..      # once: MuJoCo and the G1 (a few minutes)
```

## Run

```bash
uv run examples/g1_walker.py
```

A MuJoCo window opens with a Unitree G1 humanoid. The walking itself is a frozen
policy (the robot's "spinal cord"); the brain sits on top. Keys (in the window or the
console): arrows set speed and turning, space stops, R resets, X quits, **P** sounds a
tone and then pushes the robot from the front 0.2 s later, **B** turns bracing on/off.

## What you see

The status line shows `pred`: the cerebellum's error in predicting the body's next
state, as a percentage of the error of predicting "no change". It falls as the robot
walks, jumps when you change the command, and falls again. Press P repeatedly:
`saved` counts pushes survived.

## The idea

**The forward model.** Each tick the cerebellum expands the body's state and command
into thousands of sparse "granule" features and predicts the next state as a linear
read-out of them. The prediction error trains the read-out (the delta rule, climbing
fibres' job). With sparse features the error falls fast and stays stable.

**The timed reflex.** The tone starts a delay line; the push arrives 10 ticks later.
An eligibility trace keeps a fading memory of the tone, so the push can be credited to
"10 ticks after the tone" -- and a counter-move (a step into the push) is learned at
exactly that time. This is eyeblink conditioning, in a humanoid.

## Exercises

1. Walk straight at 0.5 m/s and note `pred` after 5, 10 and 20 seconds. Then turn.
   Why does turning raise the error, and does it come back down?
2. With bracing **off** (B), push 10 times (P) and count falls. Turn it on and repeat.
   Is the difference what you expected?
3. The brain only hears the tone; it never "feels" the push directly, only its
   consequences in the body. Why is that the right design for a brain?
4. **Going further:** headless runs (`--headless --seconds 30 --vx 0.5`) print the same
   line without a window. Run three speeds and plot `pred` against time.

# Concepts

## The brain is untrained

Nothing in ubrain is trained by gradient descent, and there is no dataset. Every
region learns online, from each experience as it happens, by a **local** rule: a
synapse changes using only what its two neurons and, sometimes, a broadcast signal
(a reward, an error) carry. What the brain knows is what it has lived through.

Where trained models are useful -- seeing, reading -- they are plugged in from
outside as **codecs**, frozen. The brain is the part that never trains.

## Regions

A region is a piece of the brain with typed inputs and outputs and its own way of
learning. ubrain serves these today:

| region | what it does | learns by |
|---|---|---|
| `hippocampus.episode` | writes the items of an episode into one vector, each bound to its slot; recalls a slot on a cue | one-shot binding (no learning rate) |
| `basal_ganglia.striatum` | keeps a value per (situation, action); releases actions in proportion to value | the three-factor rule: Q <- Q + eta (r - Q) |
| `cerebellum.forward` | predicts, each tick, what the body's next state will be given the command | the delta rule on a sparse granule expansion |
| `cerebellum.brace` | learns a timed counter-move to a predictable push heralded by a cue | an eligibility trace |

Each region's code comes from a research engine where its law was derived, written
down, and then measured against simulation. ubrain never edits that code.

## Wiring profiles

A **profile** is the brain's anatomy as a short text file: which regions, their
parameters, and what feeds what. Examples: `player` (the striatum alone), `observer`
(the hippocampus alone), `walker` (the cerebellum), `explorer` (walker + hippocampus).

```toml
[regions."basal_ganglia.striatum"]
eta = 0.1

[inputs]
"basal_ganglia.striatum.state"  = "situation"   # region input  <- body channel
"basal_ganglia.striatum.reward" = "reward"

[outputs]
action = "basal_ganglia.striatum"               # body channel  <- region output
```

The `Brain` itself names no region and no channel: change the profile, and the same
brain runs a different anatomy.

## Bodies and channels

A body declares what it carries in a **manifest**: channels, each of a kind.

| kind | meaning | example |
|---|---|---|
| `vector` | a fixed-size array each tick | joint angles |
| `codec` | something a plugged-in model turns into a code | a camera image, a word |
| `event` | a cue that fires sometimes | a tone, "which situation" |
| `flag` | a yes/no state of the body | upright |
| `reward` | a number | a score |
| `goal` | what the rest of the system wants | a walking velocity |
| `command` | a continuous action | walking velocity, joint offsets |
| `choice` | a discrete action | which arm to pull |

`brain.tick(senses) -> actions` is the whole interface: one event in, one set of
actions out. A real robot, a simulator or a game is an adapter that speaks it. The
MuJoCo G1 runs as a separate server in its own environment; ubrain talks to it
through `ubrain.bodies`.

## Codecs, senses and certificates

A **codec** is any object with `encode(items) -> codes` (plus a name, a width, a
digest and a licence). `ubrain.extras.clip.CLIP` is one.

A **Sense** puts a codec in front of the brain: fitted once on a sample of items (its
**vocabulary**), it centres the codes, projects them to the brain's workspace width
and normalises them. With `snap=True` it *recognises*: it reports the known item
nearest to a noisy input (a camera glance), so perception's mistakes and memory's
are kept apart.

A **certificate** (`ubrain.certify(codec, sample)`) is a prediction made before
anything is stored: with these codes, an item of a k-item episode comes back with
probability a(k), beside the same number for ideal white codes. Real models' codes
sit in a narrow cone (all similar to each other); centred, they behave almost like
white codes -- the certificate shows how close.

The certificate holds when the items stored ARE vocabulary codes. A raw camera glance
is not (it is only somewhat like its picture), which is why the explorer recognises
first and then remembers.

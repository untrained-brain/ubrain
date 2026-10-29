# Concepts

## The brain is untrained

Nothing in ubrain is trained by gradient descent, and there is no dataset. Every
region learns online, from each experience as it happens, by a **local** rule: a
synapse changes using only what its two neurons and, sometimes, a broadcast signal
(a reward, an error) carry. What the brain knows is what it has lived through.

Where trained models are useful -- seeing, reading -- they are plugged in from
outside as **codecs**, frozen. The brain is the part that never trains.

## Two primitives: a point and a machine

Everything in the brain is built from two objects. A **content** is a point on one
sphere: every item, episode or key is a unit vector in the brain's workspace width,
and two contents are as alike as the angle between them is small. A **machine** moves
the contents in time: each region is at any moment in one of a few **modes**
(encoding or recalling, the slot a cycle stands at, default or executive, a gate open
or closed); an **event** moves it to another mode; a transition fires only if its
**guard** holds (a comparison of codes against a threshold the region's law derives)
and performs an **action** on the contents (a write, a replay, a decay). Regions are
such machines side by side, some nested, and the neuromodulators are scalars
broadcast to every guard and rate. A tick is one turn of the outer loop; a saved
brain is its modes and its contents; an observation reports one or the other.

A saved brain is the mind, and the mind alone: what it learned, on one body. Three
things with three lifetimes meet in a running system -- the **brain state** (changes
every tick; `Brain.save`/`load`), the **body release** (the body's code, weights,
model and pinned environment; changes when the body changes; fetched by the name the
state carries) and, when a *moment* rather than a life is kept, a **checkpoint** of
both halves at one tick (planned). A state names the other two rather than copying
them, and names its own **lineage**: the states it was loaded from. Versions of a
brain are its lineage, not file names.

A brain holds many episodes from the first tick, and every recall makes two choices:
*which* episode the cue belongs to (limited by what the episodes share, not by how
many there are) and *what* that episode held (limited by the episode's load). The
laws behind both are in the series' first volume.

## Regions

A region is a piece of the brain with typed inputs and outputs and its own way of
learning. ubrain serves these today:

| region | what it does | learns by |
|---|---|---|
| `hippocampus.episode` | writes the items of an episode into one vector, each bound to its slot; recalls a slot on a cue | one-shot binding (no learning rate) |
| `basal_ganglia.striatum` | keeps a value per (situation, action); releases actions in proportion to value. Or, given the situation as a code: a value per action read on the code's granule expansion, conditioned by a goal code; the largest taken (in turn while exploring) | the three-factor rule: Q <- Q + eta (r - Q); on a code, w_a <- w_a + eta (r - Q) phi(z) |
| `cerebellum.forward` | predicts, each tick, what the body's next state will be given the command | the delta rule on a sparse granule expansion |
| `cerebellum.brace` | learns a timed counter-move to a predictable push heralded by a cue | an eligibility trace |
| `cerebellum.adapt` | learns a counter-turn when walking is pushed sideways by a steady field, added to the turning command; a clamp stops the teaching signal | the delta rule, with one learning rate or two (a fast and a slow one: savings, spontaneous recovery) |
| `cortex.store` | the slow store: items written under keys, a replayed episode written as one event, read back by cue or by index; consolidates on idle moments | Hebb's rule with passive decay |
| `prefrontal.buffer` | working memory as persistent activity: a short list held by position, rehearsed in free moments, recalled by position | one-shot binding that fades with each write |
| `prefrontal.silent` | working memory held in synapses instead: the cortical store at a fast decay | Hebb's rule with fast decay |
| `salience.gate` | judges each item against the last few that arrived; novel items are flagged and passed on, familiar ones held back | none (a threshold set from a chosen false-alarm rate) |
| `modes.controller` | the switch between an executive mode (a novel event is a demand: plan and act) and a default mode (idle; consolidation runs) | none (a rule) |
| `hippocampus.episodic_control` | a memory that acts: each (situation, action, outcome) stored at once, the action with the best recalled outcome taken; says when it is confident | one-shot storage that slowly fades |
| `control.handover` | takes memory's action while memory is confident, the striatum's otherwise | none (both learners learn on what was taken) |
| `thalamus.relay` | a gated relay: of several incoming streams, only those matching the goal reach a shared workspace | none (a threshold from a chosen false-alarm rate) |
| `neuromodulator.acetylcholine` | how much of each event's plasticity goes to encoding the present rather than replaying the past | none (a level) |
| `neuromodulator.noradrenaline` | sets the salience gate's threshold from how often things have lately been judged surprising | a running average |
| `neuromodulator.serotonin` | the striatum's patience: how long a choice stays eligible for credit, from the usual time between decisions | a running average |

The three neuromodulators add no new machinery: each is one number turned on an existing
region's knob (`cortex.store.encoding`, `salience.gate.theta`,
`basal_ganglia.striatum.patience`). Left unwired, the knob leaves its region as it was.

Each region's code comes from a research engine where its law was derived, written
down, and then measured against simulation. ubrain never edits that code.

## Wiring profiles

A **profile** is the brain's anatomy as a short text file: which regions, their
parameters, and what feeds what. Ten ship with ubrain:

| profile | the anatomy |
|---|---|
| `player` | the striatum alone: situation and reward in, an action out |
| `chooser` | the player's striatum plus the hippocampal store that acts, and the hand-over between them |
| `corticostriatal` | the striatum on a situation CODE (through the granule expansion), the goal code bound into it: no table, no binning |
| `whole` | the route's code half: every region on one path from the sense to an action -- relayed, judged, held, valued with the goal, handed over, predicted, written at dopamine's gain, replayed; most wires certified part by part, not yet in the whole (`ubrain.route` says which) |
| `observer` | the hippocampus alone: an episode of items, recalled by slot |
| `rememberer` | the observer plus the cortex: an ended episode is replayed into the slow store |
| `holder` | the prefrontal buffer: a short list held in working memory, rehearsed when idle |
| `attender` | the salience gate and the mode controller in front of the hippocampus and the cortex: novel items are encoded, familiar ones skipped, idle moments consolidate |
| `modulated` | the hubs on one brain: the thalamic relay, and the three neuromodulators on the cortex, the salience gate and the striatum |
| `walker` | the cerebellum (forward model and brace) on a legged body |
| `adapter` | the walker plus walking adaptation |
| `explorer` | the walker plus the hippocampus on the head camera |

Regions can be wired to each other as well as to the body: in `chooser`, memory's
confidence holds back the striatum's choice; in `attender`, the gate's novel items are
what the hippocampus stores.

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

A game is a body too. `ubrain.bodies.gym.GymBody` turns any Gymnasium game whose
states and actions are discrete (Blackjack, FrozenLake, ...) into a manifest -- a
`situation` event, a `reward`, a `start` flag, an `action` choice -- and runs the loop.
It knows no game, and the brain was not changed for it.

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

For the laws behind each region, and how the engine that certifies them is built, see
*The Untrained Brain Series*, Volume 2: *Building the Brain Engine*.

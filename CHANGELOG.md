# Changelog

ubrain is pre-release: every version is a `.dev` version, and the API may still
change between them. Each region is certified against the law it was built to
follow before it ships; a version adds regions or capabilities, and never moves a
certified number.

## 0.20.0.dev1 (in development)

- The `companion` profile gains working memory: the prefrontal buffer (gamma_m 0.75, the measured
  decay) holds a list of goals (`goal_item`, `recall_goal`, `goal_clear` -> `goal_memory`,
  `goal_remembered`). On the gallery companion's body, 36 lists of 2-12 goals: recall within 0.7 SD
  of the buffer's law at every length, the span saturating near eight.
- `start_body(chase_view="above")`: the body's follow camera from 60 degrees up (for rooms; the low
  view ends inside walls indoors). Never seen by the brain.

## 0.19.0.dev1

- **Region instances**: a wiring may name `base@tag` (`hippocampus.episode@route`) -- a second
  copy of a region, the same code and certifying laws, its own state and ports.
- **An episode is memory, not a stream**: `Brain.body_reset()` (a fall, a trip home) no longer
  empties `hippocampus.episode`; only its `boundary` event ends it, as `body_reset`'s own rule
  says ("what was learned is kept"). Found by the gallery companion's routes.
- The `companion` profile gains a route episode (`route_item`, `recall_route`, `route_boundary`
  -> `route_memory`, `route_remembered`): skills taken and things seen, in order, recalled
  to walk the way back to a thing.

## 0.18.0.dev1

- `start_body(keep_line=True)`: the body's experimenter holds the walk on its line (harness,
  keyed into the body's digest; the brain never sees the pose); `start_body_for` relaunches it.
  The MuJoCo body gains `apartment_kitchen`: the apartment with a RoboCasa kitchen (CC BY 4.0).

## 0.17.0.dev1

- **A body can live in a world** (the MuJoCo body 0.9.0: `worlds/`, a `WorldSpec` beside the
  robot -- rooms, doors, things and their truth for the experimenter, never the brain):
  `start_body(world="apartment")`; `start_body_for` relaunches the world a saved brain names.

## 0.16.0.dev1

- **The `companion` profile**: the explorer's cerebellum under the attender's memory
  system with the striatum behind it, for a brain that lives in one body for days --
  the day one episode (ended by the application's `boundary`, consolidated then), the
  camera written directly (the application segments events), the salience gate's
  verdict an output (`novel`). Measured on CLIP codes before it was wired: the gate's
  white-code threshold judged half of 12 fresh pictures familiar, so the gate does
  not stand before the episode here; that null on real codes is open upstream.
- `observe()`: the cortex's tick count is reported as `ticks` (it was `writes`).

## 0.15.0.dev1

- **A saved brain names what it needs** (`ubrain.state`, schema 2; UBI-11, UBI-8).
  The file carries the body's own record (its versions, how it was launched, the
  release that holds it), every sense as the fitted sense itself with its codec's
  name, digest and licence, the wiring's digest, each region's state shape, the
  state's content digest and the brain's **lineage** (`Brain.lineage`: the states it
  was loaded from). `Brain.load` takes the codec model alone and rebuilds the sense
  from the file; a refusal of the body names the field that differs and the release
  to fetch; a region whose state changed between releases is refused naming both
  versions; a schema-1 file is migrated on load. The class check is exact (a class
  *defined* in ubrain, a bit generator from the list).
- **`start_body_for(path)`** (`ubrain.bodies`): starts the body a saved brain was
  learned on, as the file records, and refuses another.
- **A model card from the file** (`ubrain.card`: `describe`, `model_card`,
  `python -m ubrain.card`), and the **`hub` extra** (`ubrain.extras.hub`:
  `push_state`, `pull_state`): saved brains on the Hugging Face Hub, private by
  default, public refused before the launch.
- The MuJoCo body reports its licences, carries `body.lock` (its manifest, digest
  and release tag) and one version number (0.8.0; the digest moved with it, as every
  body change moves it). The specification gains UBI-12, checkpoint (proposed).

## 0.14.0.dev1

- **Save and load a brain** (`ubrain.state`): `save(brain, path)`, `Brain.load`,
  `read_header`. A loaded brain continues bit for bit where the saved one stopped,
  for every shipped profile; loading refuses another body, another codec, a foreign
  class or another file schema.
- **Watch a brain** (`ubrain.observe`): read-only taps on every region, lawful health
  checks (`health`), and a brain's state as channels (`monitor_manifest`, `monitor`),
  so a brain can watch a brain.
- **A datasheet** (`ubrain.datasheet`): a brain's figures in closed form (episode and
  buffer capacity, the cortical store's capacity and horizon, the brace's lead, the
  striatum's time constant), each checked against a simulation of its store.
- `start_body` says why a body did not start.
- **The two primitives named** (docs/concepts.md; UBI-2, UBI-10, UBI-11): a brain is
  contents on one sphere and machines of a few modes over it; a tick is one turn of
  the outer loop; a saved state holds the contents and the modes; an observable is
  one or the other. No code changed: `state.py` already saves both.
- The interface specification, draft 0.1, written beside the code (not yet published).

## 0.13.0.dev1

- **A second body: Gymnasium games** (`ubrain.bodies.gym`, the `game` extra). Any
  environment with discrete observations and actions is a body; the player and the
  chooser play Blackjack and FrozenLake with no game code in the brain.
- The first public preview: compiled wheels for Windows, macOS and Linux (CPython
  3.11-3.13), the manual, five labs and the examples.

## 0.12.0.dev0

- **Walking adaptation** (`cerebellum.adapt`, the `adapter` profile): the cerebellum
  learns a counter-turn against a steady push, with one learning rate or two; the
  two-rate learner shows savings and spontaneous recovery.

## 0.11.0.dev0

- **The hubs** (the `modulated` profile): the thalamus as a gated relay onto a
  workspace bus, and acetylcholine, noradrenaline and serotonin, each a scalar on a
  knob of an existing region. Unwired, a region behaves as before.

## 0.10.0.dev0

- **Episodic control** (the `chooser` profile): a hippocampal store that acts from
  one experience, the striatum beside it, and a hand-over between them by the
  store's own crosstalk scale.

## 0.9.0.dev0

- **Noticing and switching** (the `attender` profile): a salience gate that encodes
  only novel items, with its threshold derived from a false-alarm rate, and a mode
  controller between default and executive modes.

## 0.8.0.dev0

- **Working memory** (the `holder` profile): the prefrontal buffer, held by position,
  decaying per write, with rehearsal schedules on idle ticks.

## 0.7.0.dev0

- **The memory system** (the `rememberer` profile): a slow cortical store, and replay
  of a hippocampal episode into it at an event boundary.

## 0.6.0.dev0

- **The explorer**: the G1 walks past pictures and remembers what it saw (the head
  camera as a sense).

## 0.5.0.dev0

- **CLIP as a sense** (the `vision` extra): a frozen image and text encoder, offline
  by default, its checkpoint in its digest.

## 0.4.0.dev0

- **The hippocampal episode** (the `observer` profile): a sense's items bound into
  one episode and recalled by position.

## 0.3.0.dev0

- **Codecs and certificates**: any frozen encoder plugs in as a sense; `certify`
  predicts, before anything is stored, how well the brain will recall that
  encoder's codes.

## 0.2.0.dev0

- **The generic brain**: regions with typed ports, the wiring as configuration, and a
  `Brain` that names no region or channel; the `player` profile (the striatum).

## The first version

- Contract 1.0 (typed channels and a body's manifest), `Brain.tick`, and the
  `walker` profile: the cerebellum's forward model and its cued brace on the MuJoCo
  G1.

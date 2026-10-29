# Changelog

ubrain is pre-release: every version is a `.dev` version, and the API may still
change between them. Each region is certified against the law it was built to
follow before it ships; a version adds regions or capabilities, and never moves a
certified number.

## 0.23.0.dev1 (in development) -- the corticostriatal path

The first circuit law reaches the brain: the striatum values a situation given as a CODE,
never an index, and a goal code conditions it. An application no longer bins its situations
into a table (FB-0020), the situation is the striatum's input port (FB-0024), and the goal
held elsewhere reaches the values (FB-0025).

- `basal_ganglia.striatum` takes `situation` (a code, in place of `state`): its values are
  Q(z, a) = w_a . phi(z), phi the cerebellum's granule expansion (a fixed random projection
  to `d_g` units, the `s` largest kept, centred, unit norm; `features = "raw"` reads the code
  itself), learned by the three-factor rule with phi as the eligibility, from zero. It takes
  `context` (a goal code): the values are read on phi(z (*) g), the goal bound (`context =
  "bind"`) or superposed (`"sum"`). It takes `explore` (a flag): while it is up the actions
  are taken in turn, the schedule the values were measured under; while it is down the
  largest value is taken. With `state` wired the region is the table it was, its saved state
  unchanged.
- `ubrain.datasheet.value_law(phi, X, P, Xt, Pt, eta, n)`: the expected reward of the greedy
  choice between two actions after n learning steps each, for ANY feature map on a sample of
  the world -- the expansion, the raw code, a binned table (the table is the code with one-hot
  features) -- so which read suits a world is computed before a run. The raw code wins where
  the reward is linear in the code, the expansion where it is not, a table of the prototypes
  where the situations are a few clean ones; a bound goal pays where the rewards reverse with
  it. The datasheet's striatum rows name it in code mode.
- The `corticostriatal` profile: the striatum on a `situation` code, the `goal` bound into
  it, `reward`, `explore`.
- Driven through Brain on the research engine's worlds and generators, the code mode learns
  its weights and scores its measured arm scores to 1e-12 (the expansion, the raw code, the
  goal bound and summed); `value_law` is the engine's law to 1e-9.

## 0.22.0.dev1 -- the plumbing tier of the circuits

What already exists, exposed; no new law (every item a parity or a definition). A port map
of 0.21 made by an application built on ubrain (16 regions, 15 region-to-region wires in 11
profiles, seven regions read by none, the striatum fed an index) opened the work on the
circuits -- the joins between regions certified by laws of their own; those laws arrive in
0.23-0.25. This version:

- `cerebellum.forward` has output ports: `prediction` (the predicted change of the 41 sensed
  body variables, the Purkinje read on the last granule code) and `error` (its squared error
  once the body has moved) -- FB-0027. Nothing is wired into them yet.
- `basal_ganglia.striatum` outputs `delta`, the prediction error r - Q of the pairs credited
  on a tick (None without an outcome) -- dopamine as a scalar a profile can broadcast (FB-0026).
- `basal_ganglia.striatum` takes `entity`: with it wired, a decision is made FOR that entity
  and an outcome credits that entity's pending choices only, so one brain deciding for many
  entities in turn, their outcomes interleaved and late, learns exactly what one brain per
  entity would (FB-0018; the credit the trader routed through internals, now a port). Unwired,
  the region is as before.
- `ubrain.portmap`: every region's ports, every region-to-region wire in the shipped
  profiles, the islands; `python -m ubrain.portmap` prints it; `tests/test_portmap` pins the
  islands as `KNOWN_ISLANDS`, so a profile that joins a region or a region left unjoined is a
  deliberate edit (FB-0021).
- The datasheet lists, per brain, every region-to-region wire with whether a law of the
  CIRCUIT certifies it (none yet: "uncertified") and the regions no region reads (UBI-0,
  principle 9: a brain of certified parts is never mistaken for a certified brain).
- UBI-0 principle 9, the brain is synthesized and says so.

## 0.21.0.dev1

- `thalamus.relay` gains `reads`: every route's read off the bus at once (R x d, zeros where the
  gate closed it) -- for a reader that does not know which route holds what it seeks.
- `datasheet.relay_law(d, R, V, rho, alpha, arm)`: the relay's law (gated, open, coin), on the
  datasheet's Gaussian decode (within 0.01 of the exact curve); the relay has datasheet rows.
- The `companion` profile gains attention: the relay over the view's six fixations (`routes`),
  opened by the thing sought (`seek`) -> `attention`, `opened`.
- `start_body(record_pose=path)`: the body appends "tick x y yaw" every tick to the
  experimenter's file, for scoring where the body went. Never sent to the brain (body 0.11.0).
- Known limit, measured on the G1 in the apartment: the relay's gate threshold and its read are
  certified on white codes. On CLIP's codes of real views, unrelated fixations (walls, ceiling)
  pass the gate far more often than `alpha`, and a read decodes to its nearest thing with no
  "not here". Searching with it, the robot stopped right on 10 of 19 trips, against 15 for a
  recogniser with measured confidence floors. A repaired gate and an absence decision are in
  the works; until then, check a relay's finds against a floor of your own.

## 0.20.0.dev1

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

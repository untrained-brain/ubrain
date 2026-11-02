# Changelog

ubrain is pre-release: every version is a `.dev` version, and the API may still
change between them. Each region is certified against the law it was built to
follow before it ships; a version adds regions or capabilities, and never moves a
certified number.


## 0.30.0.dev1 -- the whole brain's laws checked in place; two ports for an observer (2026-11-02)

The whole brain was run in the research engine's integration world (twelve places of two senses, goals
that switch, remapped moves, fresh scenes; one sense, no goal input, 24 seeds at four settings), and the
laws its parts were certified by were evaluated on the trace of its own run, within allowances
calibrated on its own runs. `brain.datasheet()` now carries the outcome as `(whole)` rows:

- **the buffer's law holds in place**, with and without memory;
- **the striatum's values law holds in place without memory**; with memory given a situation index (it
  acts on about 60% of moves) it falls short by about 0.008, of one sign at every setting -- inside the
  allowance, but the calibration's bias was over the bound set before the run, so it is reported as not
  held. The suspected cause is in the law (which moves the striatum takes depends on memory's
  confidence), not in the striatum;
- a pass says the parts learn by their laws on what the whole gives them, not that the whole behaves as
  the research engine's whole: its salience judges about half as much novel and it plans about half as
  often; memory acts more. The episode's, the cortex's, salience's and the modes' laws are not checked in
  the whole yet.

Added:

- `basal_ganglia.striatum.features`: the pattern of this tick's decision (read-only; None without a
  situation code).
- `prefrontal.buffer.latest`: the buffer's read of the position it wrote last, not snapped to the
  vocabulary. A state saved before 0.30 is upgraded to its newest held term.

Fixed:

- The `state` stream's values were documented reversed: 0 is idle (the default mode, replaying), 1 is
  acting on the present. The code was right; the face's class table and the specification's row now say so.
- The prefrontal buffer's datasheet row says "per tick" on the tick clock.
- 0.29.0.dev1's date is 2026-11-02 (it was written as 2026-11-03).


## 0.29.0.dev1 -- the whole brain runs as the research engine's whole tick (2026-11-02)

A part-by-part map found that the whole brain `Brain()` serves was not the research engine's whole
tick, on which the laws in place were measured. This release brings it there, where the route allows.

- **The prefrontal buffer never fills.** `clock = "tick"`: every tick ages it and takes the next
  position of a ring of `slots`; an item present is written there. The whole: gamma_m 0.9, 128
  positions. (Before, it filled after 16 novel items and dropped every later one.) A test holds it to
  the research engine's buffer tick for tick.
- **No discount without a clock.** Serotonin left the whole: its clock read a situation stream the
  whole rarely has, and its patience still discounted every value, to 0.905 of the reward with no
  stream and 0.37 with one. `attach("modulator", "serotonin")` is refused, saying why; serotonin stays
  in the experts' profiles.
- **The memory loop.** Acetylcholine's binary switch, and `cortex.store` `present = "none"`: a busy tick
  encodes into the hippocampus, an idle tick replays one experience into the cortex (gamma 0.995 per
  tick). `hippocampus.episode` `timing = "tag"`: an item waits one tick and is written at the
  prediction error of the move made at it, as the research engine pairs them.
- **The control path.** `modes.controller` `demand = "novel_or_surprise"` and `timing = "tick"` (the
  plan's tick is the chunk's first step, a step ends at its own tick's surprise; k 6); a test holds it
  to the research engine's controller tick for tick. Striatum eta 0.2, episodic control gamma 0.98.
- Every new option defaults to the earlier behaviour: every other profile is bit for bit as before.
- Not yet (they wait for the route): the episode written with every busy tick's situation, memory
  acting only in executive mode, the episodic store keyed by the code, noradrenaline, the supervisor,
  the night.

## 0.28.0.dev2 (in development) -- the whole brain explores: the Go race on codes

- **The whole brain's striatum releases by the Go race on its values** (`release = "race"` in the `whole`
  profile, and so in `Brain()`): an action with probability in proportion to its value floored at 0.001,
  the release of the research engine's whole tick, on which the values law held in the whole brain.
  Values at zero release every action alike, so the race tries what it has not learned; nothing outside
  schedules it. On four pictures with one right action each, `examples/00_whole_brain.py` now earns
  0.98 to 1.00 after its first block, within about 0.01 of the race's law on the values it learned (it
  stayed near one half under 0.28.0.dev1's greedy choice).
- The setting is the code-mode striatum's `release` (`"greedy"`, the default, as the corticostriatal
  circuit was measured; or `"race"`); the datasheet names the race's law when it is set.
- A state saved by an earlier release loads with the greedy choice it had (a region may now declare
  attributes it added since, `_ADDED`, which the loader fills through the region's upgrade).

## 0.28.0.dev1 -- the whole brain, `Brain()` (a preview)

- **`Brain()` is the whole brain** (UBI-14, stage N.1): every region on the route, wired once and the
  same in every copy. You choose a named **variant** (`standard`, d = 512; `small`, d = 128), which
  changes sizes and never wiring, and attach streams by **port class**: `brain.attach("sense", "vision",
  codec=camera)`, `brain.attach("reward")`, `brain.attach("action", n=4)`; `tick` takes and returns
  them by address (`"sense.vision"`). With one sense the whole brain is the `whole` profile, bit for
  bit. `ubrain.face` lists the classes and the variants.
- **Several senses:** each sense is one route of the thalamic relay (up to the variant's `routes`); the
  regions after it read the relay's new `merged` output (with one route its code; with more, the bus at
  unit length), and the memories clean up against every sense's vocabulary bound to its route's key.
- **Neuromodulators from outside:** a `modulator` stream (`"modulator.acetylcholine"`,
  `"modulator.serotonin"`) is its region's level while it carries a value; absent, the region computes
  its own (a new `given` port on both).
- **The interior:** `brain.tap("region.port")` reads any output port as the last tick left it;
  `tick(..., inject={"hippocampus.episode.recall": 3})` delivers a cue to one of the open cue ports;
  `brain.describe()` lists the streams, the cue ports and every region's ports. An input class with no
  stream reads its absent value, and the regions behind it rest.
- A whole brain saves and loads without a manifest: `Brain.load(path, codecs={"sense.vision": camera})`.
- A region port may read a **stack** of channels (a TOML list in a wiring); a width now travels down a
  carried edge as it travels up, so codes without a codec still size the regions after them.
- **A preview, and what it does not yet do:** the whole is not certified as a whole (the research
  engine's next stage). In particular nothing in it explores: its striatum chooses the largest value
  on codes, so on a task with one right action per picture it keeps what first paid (about one half in
  `examples/00_whole_brain.py`). Not yet built: streams attached to a running brain, several agents,
  `goal`, `taken`, and the body's classes (`body`, `cue`, `command`); each is refused with its stage.
  Every profile is unchanged, bit for bit.

## 0.27.0.dev4 -- found by documenting every parameter

- **Watching the whole brain works.** `observe()`, `health()` and `monitor()` failed on any brain with
  the forward model of codes, the `whole` profile included. The forward model now reports its
  judgements, surprises and threshold. Health also checks a region added under a name of its own
  (`salience.gate@x`).
- **Settings are checked:** the striatum's `eta` (0 < eta <= 1), the cortex's `eta`, `gamma` and
  `replay_eta`, and the episode's and the buffer's `slots`. A value outside the range is refused
  when the brain is built, with the range.
- `mute` says what it does and names the regions when it refuses; `datasheet.horizon` documents its -1;
  kind-mismatch messages read "an event port".

## 0.27.0.dev3 -- the code and the specification agree

- **A sum on a choice output is refused** when the brain is built (it used to keep the first term
  silently).
- **An empty port on a command channel reads as zeros** of the channel's width, never as
  not-a-number, and a term of the wrong width is refused (a leading batch axis is allowed).
- **The specification says what the code does:** a bare region name stands for its first declared
  output port; the kind table lists `choice`; every input channel of the manifest is filled each tick;
  the manifest is the body's, and the release lists the brain's ports.
- Every public name has a docstring, except the body client's (it is the body's own file, documented
  with the body's next release). `ubrain.state.snapshot_bytes` is public.

## 0.27.0.dev2 -- found by writing the manual

- **A cortex under acetylcholine without its hippocampus is refused.** 0.27.0.dev1 meant to refuse it at
  build time, but whether a port is wired is not visible then. Such a brain was accepted, and its cortex
  never replayed. The cortex now raises at its first item if `key`, `replay` or `replay_key` is not wired.
- **The `whole` profile's cortex consolidates.** Its cortex had acetylcholine wired without anything to
  encode or replay, so it never stored anything (since 0.24). It is now fed by `hippocampus.replay`, as in
  `modulated`: one experience per event, as the hippocampus holds it. The route carries the new wires.
- The specification's counts and version stamps match this release (UBI-5, UBI-8, the README).

## 0.27.0.dev1 -- the cortex replays what the hippocampus holds

- **A new region, `hippocampus.replay`.** It records each item it is given into one decaying,
  role-bound trace. On every tick it offers one earlier experience: the hippocampus's read of it,
  noisy as the hippocampus holds it, and the key it was encoded under. It also gives the present
  item its key.
- **The cortex under acetylcholine keeps no list of experiences** (`cortex.store` with `encoding`
  wired). Until now it rewrote an exact copy of an earlier experience. It now encodes the present
  under the hippocampus's key and rewrites the experience the hippocampus offers, at 1 - a, under that
  experience's own key. It is certified on its law: recall follows the noisy-copy law, and a replay is
  only as good as the hippocampus's read of it. In the certified world, the older memories recall
  0.06 from a 2048-wide hippocampus and 0.14 from an 8192-wide one, against 0.17 with exact copies.
  The `modulated` profile wires it (d_h 8192).
- **Breaking:** a cortex with `encoding` wired now needs `key`, `replay` and `replay_key` from
  `hippocampus.replay`, and is refused otherwise with an explanation. `modulated` states saved by 0.26
  do not load (their wiring has no hippocampus): start a new brain.
- **`recall i` is the experimenter's probe.** The cortex's list of the keys it used is documented as
  the experimenter's bookkeeping for measuring what the store holds, not as the brain's memory. A
  brain recalls by cue. It works as before.

## 0.26.0.dev2 -- episodic control without a queue

- **Episodic control keeps no list of pending pairs** (`hippocampus.episodic_control`). Until now the
  store kept every (situation, action) since the last outcome in a queue and wrote each at the outcome.
  It now keeps their keys superposed in one fading trace, plus one number for the decay the store will
  take, and writes them in a single step. Binding is linear, so this is the same write: bit for bit on a
  bandit, and to rounding over an episode of several pairs. The measured T-maze and bandit runs are
  reproduced exactly. States saved by 0.25 load (the queue becomes the trace).
- The monitor reports a situation-code striatum's weights (it had tried to read a table it does not have).

## 0.26.0.dev1 -- the striatum's credit as a synaptic tag

- **The striatum keeps one tag per synapse** (`basal_ganglia.striatum` on a state table). Until now it
  kept every choice since the last outcome in an exact list. It now keeps one number per (state, action):
  a choice sets its tag to 1, every tag fades by the patience each tick, and the outcome is learned once
  by every tagged pair, `Q += eta (tag r - Q)`. It is certified on its law: the values settle at a derived
  fixed point, the discounted reward the striatum's own choices earn, so serotonin's patience still
  discounts. **What changes for you:** nothing, unless a pair is chosen twice before its outcome
  (`credit = "episode"`): it is now credited once, with its latest copy, where the list credited every
  copy. Its values then sit slightly higher than before, by an amount the law gives. Patience is read on
  each tick; under a steady patience this is exactly the earlier behaviour.
- **On a situation code** (`situation` wired; the `corticostriatal` and `whole` profiles) the pending
  credit is a tag too: the chosen action's synapses keep the pattern they were used with, and the action
  an eligibility. The updates are exactly the earlier ones. **Breaking:** `credit = "episode"` on a
  situation code is now refused with an explanation. There several situations would share one action's
  synapses, and that tag is not certified yet; no shipped profile used it. Use `credit = "last"`.
- States saved by 0.25 load: the pending list becomes the tags.

## 0.25.0.dev1 -- salience remembers like a brain

- **The salience gate keeps a fading trace** (`salience.gate`, `memory = "trace"`, the new default).
  Until now the gate judged each item against an exact list of the last few items -- a computer queue no
  brain has. It now keeps one fading superposition of everything it has seen, `t <- lam t + z`, and judges
  an item familiar when its cosine with the trace passes a threshold set from a chosen false-alarm rate.
  It is certified on its law, on a stream and inside the whole brain, where the exact list had no law
  that held; the mode controller driven by it follows its law too. **What changes for you:** the gate is
  a little weaker on the very recent past and forgets gracefully instead of at a horizon -- an item seen
  30 events ago is still sometimes recognised, where the list had forgotten it completely. Parameters:
  `lam` (the fade per item, default 0.95), `alpha` (the false-alarm rate) and `kappa` (the codec's
  spectral factor, default 1 for white codes). The `attender`, `companion` and `whole` profiles use it;
  example 08 now teaches it, its law against the measurement for fresh items, recent and old repeats.
- **The exact window stays where its laws are**: `memory = "window"` keeps the earlier behaviour, and the
  `modulated` profile (the noradrenaline world: a criterion noradrenaline sets every tick, a known set of
  codes) names it. **Known limit:** the trace takes no `theta` knob, no `know` input and no
  `remember = false`, and refuses them with an explanation: noradrenaline's laws and the known set's on
  the trace are not certified yet.
- The route's evidence is refreshed: nine wires are now measured inside the running whole brain.
- **Breaking for saved profiles** that set `window` on the gate without `memory`: add `memory = "window"`
  to keep the earlier gate, or remove `window` to take the trace.

## 0.24.0.dev2 -- found from anywhere; the brain's data structures audited

No region's behaviour changes and no certified number moves.

- **Found from anywhere.** When ubrain runs from its source tree, the research engine and the
  MuJoCo body are now found by searching upward from the package, not at a fixed depth: the source
  moved within its research repository (into `brains/`), and the next move will not break the
  lookup. `start_body` finds `bodies/mujoco` wherever the package sits beside it. Installed from a
  wheel, nothing changes.
- **The brain's data structures, audited** (in the source tree; not shipped in the wheel). Brain
  state should be codes, traces and weight matrices. An audit of every container a region keeps
  found nine places where state is exact computer memory instead -- the striatum's pending choices
  and eligibilities kept in dictionaries, episodic control's queue of pairs awaiting their outcome,
  the cortex's index of keys and its exact replay buffer, the prefrontal buffer's exact copies of
  its items, the salience gate's exact window -- storage no brain has, outside the capacity laws.
  **Known limit:** these regions still keep that state; each is listed with the neural form that
  will replace it (a decaying eligibility trace, a fading position-bound cycle, keys from the
  hippocampus, the buffer's superposition, a fading trace for novelty), and each replacement will
  arrive as a certified law in a later version.

## 0.24.0.dev1 -- the whole route; predict, surprise, modulate

The brain is wired from the senses to an action in one profile, and two more circuit laws
reach it: the forward model of codes, whose surprise sees a change of the world's rules that
novelty cannot, and the dopamine broadcast as what the hippocampus writes with.

- **The route** (`ubrain.route`): the research engine's declaration of the path from the
  senses to the body, promoted as data -- one row per wire, its path (data: codes; control:
  scalars and flags), its loop (the tick, the episode, the night, the supervisor), its
  evidence (measured live between its two parts; each part held alone; not built) and
  ubrain's ports where ubrain has the wire.
- **The `whole` profile**, the route's code half: the thalamus relays the sense's code; the
  salience gate judges it; the prefrontal buffer holds the novel items and one of them as the
  goal; the striatum values the relayed code with the goal bound in; the episodic store and
  the striatum are handed over; the forward model predicts the next code from the present one
  and the action taken; the mode controller attends on novelty and abandons a chunk on
  surprise; the hippocampus writes the novel items at the prediction error's gain, ends the
  episode in the default mode and replays it into the cortex, whose writing acetylcholine
  switches. A test holds every wire of the profile to a wire of the route (the application's
  cues aside) and refuses one the route says is not built. **Most of its wires are certified
  part by part, not in the whole**: this profile is what the research engine measures next.
  The port map's islands shrink from seven regions unread and eight unfed to four and four.
- `cerebellum.forward` takes `state` (a code) and `action` (a choice): **the forward model of
  codes**. The action is bound into the state, the context expanded by the granule layer and
  read by the Purkinje map, learned by the delta rule; each tick the prediction made last tick
  is judged against the code that arrived, `surprise` iff their cosine is below the spherical
  null's 1 - alpha quantile, before the map learns. A test holds its surprise rate, driven one
  measured step per two ticks, to the law the research engine measured, evaluated on the
  region's own features. Out ports: `prediction` (now of the mode's width: 41 on the body, d
  on codes), `error`, and `surprise` (a flag; None in the body mode).
- `hippocampus.episode` takes `gain` (an event): each item is written at |gain|, the size of
  the striatum's prediction error when `basal_ganglia.striatum.delta` is wired -- writing at
  dopamine's gain lifts the recall of rare rewarded events and costs common ones, a trade the
  research engine derived and measured, not a free gain. Unwired, or on a tick with no
  outcome, the gain is 1 and the region is as before.
- `thalamus.relay` with one route hands over one code (not a 1 x d batch), and its `passed`
  and `read` carry the routes' sense, so the regions behind it clean up against it.

## 0.23.0.dev1 -- the corticostriatal path

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

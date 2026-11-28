# What's new

ubrain is pre-release: every version is a `.dev` version, and the API may still change between them. Each entry
says what you can do that you could not before, and how. Install a version by naming it:
`uv add "ubrain==0.51.0.dev1"` (or `pip install --pre ubrain`).


## 0.58.0.dev1 -- the whole brain rebuilt from the ground, and an amygdala (2026-11-28)

**The whole brain now holds only organs that pass every test in the whole.** Each organ was tested by its own
published paradigm, with the organ muted against intact. Seven organs of 0.57 kept their own laws but never reached an
act: the salience gate, the prefrontal buffer, the forward model, the mode controller, the episode store,
acetylcholine and the hippocampal replay trace. They are taken out of `Brain()`, together with the senses' binding,
which nothing read. Each comes back one at a time, once something that chooses reads it and its paradigm shows the
difference.

- **Nothing you see changes.** The rebuilt brain acts exactly as the 0.57 brain did, act for act. This was checked
  on two sizes and three seeds, with nights and reversals, with and without the amygdala.
- **What is in it:** the thalamic relay, memory that acts (episodic control) and its hand-over, the striatum's values
  and Go race, noradrenaline and the supervisor that ejects a context, the motor end, and the cortex's long-term
  store that the night fills.
- **Saved brains load onto the new anatomy.** A whole brain saved by 0.57 or earlier loads with the dropped regions
  removed. Everything the rest learned is kept exactly. `brain.lineage[-1]["stripped"]` names what was dropped. Its
  random choices from then on are new draws, so its acts are statistically the same, not identical.
- **Retired with their organs.** Attaching any of these is refused with the reason:
  - the `state` stream (it was the mode controller's);
  - the `acetylcholine` modulator.

  Also removed:
  - the `memory`, `mode` and `recollection` outputs;
  - the cue ports that recalled the episode, the buffer and the cortex.
- **Observables:** `describe()["observables"][k]["carried"]` says whether this brain carries an observable. `novel`,
  `surprise` and `held` are not carried in 0.58, so `read` gives their absent value.
- **Sleep pressure** now measures episodic control's day: the outcomes it has stored since the last night, over its
  own horizon. A night empties it into the long-term store, as before. No night is forced.
- **Each region of the whole brain draws from its own random generator,** keyed by the brain's birth and the region's
  name. It covers both the region's structure at birth and its choices. A region is the same whatever else the anatomy
  holds, and muting one changes only what that region does. Before, one shared generator made a lesion move the acts
  of regions it never touched. Circuits built from a profile keep one generator, as before.
- **The 0.57 anatomy is kept as the `route` profile,** for research: `Brain(profile("route"), manifest)`.

**An amygdala: what matters is remembered longer.**

- **To use it:** call `brain.attach("modulator", "intensity")`, then pass `"modulator.intensity": x` (0 to 1) with
  each reward. It says how intense the outcome was: a shock or a feast is 1, an ordinary outcome near 0.
- **What it does:** the amygdala learns how intense each situation's outcomes are. It strengthens the memory the
  brain acts on, as that memory is written, in proportion. Important situations' choices are kept longer; neutral ones
  are crowded out a little, as in people.
- **Measured in the research engine and on the whole brain:**
  - With the amygdala muted, important situations' later accuracy falls, by 0.046 at 100 trials of delay in the
    whole brain (about 4 standard errors).
  - Neutral situations pay a little at short delays.
  - All four of its laws held in the research engine.
- **Without the stream there is no amygdala.**

## 0.57.0.dev1 -- the striatum can prepare its next act from a prediction (2026-11-28)

- **New input `basal_ganglia.striatum.predicted`, off by default.** Wire it to a prediction of the present situation
  (in the whole brain, `cerebellum.forward.prediction`) and the striatum's Go race gets start levels: an act the
  brain values on the predicted situation starts nearer its threshold. It wins more often and is released sooner. With
  no prediction, or nothing valued on it, the race is the Go race as before. It needs a situation code and
  `release = "race"`, and it raises an error otherwise.
- **New output `basal_ganglia.striatum.rt`: the race's reaction time** when `predicted` is wired (in the race's own
  time units), `None` otherwise. A task can now reward speed.
- **`ubrain.regions.prepared(striatum, prediction)`** gives the start levels the striatum would use.
- **Nothing changes unless you wire it.** `Brain()` does not wire it yet. In the whole brain on a random world the
  forward model's prediction is noise, and the striatum would read it as a confident one. Switching it on waits for a
  measure of how much a prediction should count.
- The race rule is promoted unchanged from the research engine, certified there by its seven laws of the prepared
  race.


## 0.56.0.dev1 -- a brain can grow a new sense while it lives (2026-11-28)

- **`brain.attach("sense", ...)` now works on a living brain.** Every whole brain is built with all the sense routes
  its size allows (4 for `small`, 8 for `standard` and `large`), the unused ones closed. A sense attached later takes
  the next free route: nothing is rebuilt, and nothing the brain has learned is lost. The new sense starts its own
  early period then, as a newborn's would.
- **While the new sense is silent, the brain perceives exactly what it did before,** and keeps everything it learned
  (its later spontaneous acts differ, since the new sense took one draw from its generator). When the new sense speaks,
  it is part of what the brain perceives, and the brain's old memories are cued a little less sharply while it does:
  a familiar situation's code then matches the old one at about 0.71 if the brain had one sense before, about 0.81
  with two, about 0.84 with three.
- **One way of combining senses, whatever their number.** What the brain perceives is the sum of the senses that are
  speaking this tick. Each sense's own mapping onto the brain's sphere keeps the senses apart.
- **Fixed: a brain with several senses of its own fed its memories an out-of-date list of known things** while those
  senses were still settling, and after a save and load it could continue slightly differently. Both are fixed.
- **Saved whole brains from 0.55 or earlier cannot continue under 0.56** (their perception was formed another way).
  Loading one raises an error that says so; start a fresh `Brain()` with the same identity
  (`Brain(identity=...)`) and regrow it from your own record of its life. Circuits built from a profile load as before.


## 0.55.0.dev1 -- memory acts whenever it is sure, in any mode (2026-11-27)

- **Memory is no longer barred when the brain is in its default mode.** Since 0.33 the whole brain's episodic memory
  acted only on executive ticks. On the other ticks, about one in fourteen in a task where something is always asked,
  habit decided instead, and habit is a little less reliable than a sure memory. Now memory acts whenever its votes
  clear the hand-over's criterion, whatever the mode. The brain earns slightly more in every phase of the organ check:
  1.000 / 0.870 / 1.000 (while the rules hold / just after they change / later), against 0.996 / 0.866 / 0.997.
- **What it changes in the organ report:** the forward model and the mode controller no longer cost reward when
  active ("no change" instead of "miscalibrated"). The salience gate, whose benefit came only through that bar, also
  reads "no change". None of the three has a job that pays in that task yet. The modes still decide when the brain
  consolidates and plans.
- **Saved brains:** a whole brain saved by 0.54 or earlier has the bar lifted when it loads. Its state is unchanged;
  from then on memory acts whenever it is sure.


## 0.54.0.dev1 -- an unchanging world no longer blinds a sense for life (2026-11-27)

- **A sense's early period now ends on experience, not on time.** Each sense spends its first inputs learning what
  its world looks like on average, then holds that. Until this version the period ended after a fixed number of
  inputs. A brain shown one unchanging picture through the whole period therefore took that picture as its world's
  average, and could never see it again: the picture coded to nothing, for life. The other things it then met also
  lost much of their distinctness, so its memory of episodes held markedly less.
- **Now an input that repeats what the sense already knows does not count toward the period.** The period ends only
  after enough inputs that differ, as an animal reared in the dark keeps its critical period open. After a whole
  period of one picture, the brain now recognises that picture far more often than before, and its memory of
  episodes holds more, both by the amounts the law predicted before the measurement.
- **Nothing changes in a world that varies:** there every input counts, and a sense behaves exactly as in 0.53, step
  for step.
- **Saved brains get the repair where it changes nothing they lived:** a brain saved by 0.53 or earlier whose sense
  is still in its early period, and whose every input so far differed from the last, takes the new behaviour from its
  next input, holding exactly what it held. That is where the two behaviours agree, so nothing it already saw is coded
  differently. A sense whose period is over, or that has already counted a repeat, keeps the behaviour it lived with
  and continues exactly.


## 0.53.0.dev1 -- a brain knows who it is (2026-11-27)

- **Every brain is an individual.** A fresh `Brain()` is born with its own id and birth time. A saved state records
  the individual it belongs to, so `brain.save(path)` and `Brain.load(path)` carry the same individual on. Two brains
  with the same seed and the same experience are still two individuals: `brain.identity` tells them apart.
- **A copy is a new individual, with its parent recorded.** `Brain.load(path, fork=True, name="twin")` starts a new
  individual from a saved state. Its identity names the parent, the saved state's content digest and its tick count.
  At the moment of forking, the fork's content is exactly its parent's.
- **Name one born elsewhere:** `Brain(identity={"id": ..., "born": ...})`, for an application whose own record of the
  birth is older than its brain's state.
- **One running copy per individual:** `ubrain.identity.Claim(directory)`. `claim(brain)` refuses a second live process
  running the same individual. It also refuses an older state going on as the same individual: that is a fork, or the
  owner's explicit rollback, `claim(brain, rollback=True)`, which is recorded. Call `record(brain)` after each save and
  `release(brain)` at exit.
- **The state file is schema 3.** A file saved by 0.52 or earlier loads and continues exactly as before. It is given
  an id that is the same every time that file is loaded, with its birth unknown and no parent.


## 0.52.0.dev1 -- the brain acts even when nothing around it changes (2026-11-27)

- **It no longer goes still in a world that stands still.** A sense adapts to what never changes, as an eye does to an
  image held perfectly still, so a brain shown one unchanging picture saw nothing, and before this version it then did
  nothing at all, ever, even where one act of its own would have changed the picture. Now, when no part of the brain
  chooses, it makes a spontaneous act now and then, as a baby kicks before any kick has paid. That is how it finds
  the act that works and starts learning. On the classic infant task (an act that makes a mobile move) every brain now
  learns it, against fewer than half before.
- **Nothing changes where the brain already chooses:** a spontaneous act comes only when no part chose, so in a
  world that keeps giving it something to see, the brain does exactly what it did in 0.51.
- **You can see it:** the whole brain has a new part, `motor.spontaneous`; `ubrain.observe.observe(brain)` shows its
  rate and how many acts it has made on its own. A brain saved by 0.51 loads and continues exactly as it was, without
  it.


## 0.51.0.dev1 -- the brain notices when its world has changed (2026-11-27)

- **It switches context when its expectations keep failing.** When actions it expected to pay stop paying, often
  enough to be more than bad luck, the brain treats the world as changed. It starts a fresh context for its habits
  and clears the long-term memory the old world wrote, so it learns the new rules instead of slowly unlearning the
  old ones. Just after a change it now earns markedly more on the same task (0.86 against 0.68 before). Nothing to
  call: it happens in `brain.tick()`.
- **You can see it:** the whole brain has a new part, `prefrontal.supervisor`; `ubrain.observe.observe(brain)` shows
  how often it has switched, and `ubrain.debug.trace` tests it with the other parts when it explains a
  choice.
- **Every new brain has it, whatever its size.** A brain saved by 0.50 loads and continues exactly as it was, without
  the supervisor: a saved brain keeps the anatomy it was saved with.


## 0.50.0.dev2 -- the README and this page, rewritten for users (2026-11-26)

- **Documentation only;** the brain is the same as 0.50.0.dev1. The README now shows how to use ubrain: install, a
  brain that learns in ten lines, sleep, saving and loading, asking it, looking inside, senses and bodies, and other
  AI under its control. This page says what each version lets you do.


## 0.50.0.dev1 -- long-term memory that decides, and knows when to let go (2026-11-26)

- **Memory now lasts past the night and reaches decisions.** Each night the brain moves what it learned about its
  actions (which choice paid where) into a long-term store; by day it decides from both. In a world that holds still
  it chooses better than before; nothing to call -- it happens in `brain.night()`.
- **It lets go when the world changes.** When the long-term memory's predictions start failing more often than the
  day's, the brain forgets it faster, so old habits do not hold it back after a change.
- **Brains saved by 0.49 load and continue:** their long-term store starts empty.


## 0.49.0.dev2 -- a fix for the debugger (2026-11-26)

- `ubrain.debug.trace` no longer changes the brain it inspects (it could, on a whole brain with a learning sense).
  Upgrade if you use the debugger.


## 0.49.0.dev1 -- see inside a running brain (2026-11-26)

- **`ubrain.debug`**, read-only on the brain it looks at:
  - `FlightRecorder(brain, n=256)` keeps the last ticks (senses, every output, the actions); call
    `rec.capture(senses, actions)` after each tick and `rec.dump(path)` when something goes wrong;
  - `trace(brain, senses)` tells which parts made a decision (each muted in turn on a copy);
  - `first_divergence(a, b)` finds where two brains first differ (two versions, or before and after a change);
  - `check(brain)` lists problems in the state (non-finite numbers, runaway values); `[]` when healthy.


## 0.48.0.dev1 -- the brain sleeps (2026-11-26)

- **`brain.night()`** consolidates the day: every episode the brain kept by day is written into its long-term memory
  and the day's store is emptied. Shorter days are remembered better, so call it as often as suits you.
- **`brain.sleep_pressure`** says how full the day's store is (0 to 1); a full store forces a night by itself, so
  nothing is lost if you never call one.
- A whole brain's actions are unchanged by this release until its first night.


## 0.47.0.dev1 -- the brain in charge of what plugs into it (2026-11-25)

- **`ubrain.agents.AgentPort`:** other AI systems as the brain's advisers. An agent is anything with
  `propose(request) -> {"text": ...}`. The brain calls one only when it asks, treats the reply as a proposal, learns
  whom to trust from how proposals turn out (`port.outcome(call, value)`), and stops at a daily budget. ubrain holds
  no keys and ships no adapter for any hosted service: bring your own.
- **`ubrain.owner.Owner`:** you above the brain -- commands, a policy (whether agents may be called, the budget,
  actions it may never take alone), a log of every command and decision, and `state()` for a console.
- **`ubrain.select.Lexicon`:** the brain names what it has received (a sentence, a picture, a movement): `add(item,
  code)` while it learns, `select(code)` to say the nearest.


## 0.46.0.dev3 -- on PyPI (2026-11-15)

- `uv add "ubrain==0.46.0.dev3"` or `pip install --pre ubrain`: compiled wheels for Windows, macOS and Linux. The
  robot, the examples and the docs stay in the GitHub repository.


## 0.46.0.dev2 -- a body without a cue (2026-11-15)

- **A fix:** a whole brain with a `body` but no `cue` no longer stops at its first tick; without a cue there is nothing
  to brace for, so the brain simply walks to its goal.


## 0.46.0.dev1 -- the whole brain takes the body (2026-11-15)

- **Four new port classes for `Brain()`:** `body` (the body's sensing, a vector), `cue` (an event to time, such as a
  tone before a push), `goal` (the walk you want) and `command` (the walk the brain sends: the goal plus the
  cerebellum's timed counter-move). The whole brain drives the simulated G1 humanoid:
  `ubrain.bodies.g1.G1(hello).attach(brain)` adds the streams; see `examples/04_g1_brace.py`.


## Earlier versions

Each earlier version's notes are on its release on GitHub (the tags `ubrain-0.45.0.dev1` and before).

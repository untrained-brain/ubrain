# What's new

ubrain is pre-release: every version is a `.dev` version, and the API may still change between them. Each entry
says what you can do that you could not before, and how. Install a version by naming it:
`uv add "ubrain==0.51.0.dev1"` (or `pip install --pre ubrain`).


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

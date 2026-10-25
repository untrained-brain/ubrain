"""12 -- a brain's datasheet, its health, and its monitor (no robot, no GPU; a few seconds).

    uv run examples/12_monitor_and_datasheet.py

A processor's datasheet states its configuration and the performance it
guarantees under stated conditions. A brain's does the same, except that its
figures come from the laws behind its regions, so `datasheet_text(brain)` can be
printed for a configuration before it has run a single tick. Here the `holder`
profile: prefrontal working memory, a decaying buffer of 16 positions. Each item
is bound to its position's role and added to one vector, and every write first
multiplies what is there by gamma; position j is read by unbinding its role and
taking the nearest item the sense knows. Its figure is the COUNT LAW: item j of a
list of L carries weight gamma^(L-1-j), and the expected number recalled right is
the sum over the list of the decode law at that weight (`buffer_count`).

`health(brain)` sets what a region holds against the law it is certified by: the
hippocampal episode's load against its capacity (the largest episode the decode
law reads at 90%), with the law's accuracy at the present load in the note.

`observe(brain)` returns read-only copies of what each region holds; reading
changes nothing in the brain. `monitor_manifest(brain)` turns every scalar it
observes into a channel of width one, and `monitor(brain)` gives this tick's
values -- a body's senses in the interface's own terms, so a second brain can be
built on that manifest and take the first brain's interior as its senses.
"""


import math

import numpy as np

from ubrain import Brain, Channel, GaussianCodes, Manifest, Sense, Wiring, profile  # noqa: E402
from ubrain.datasheet import buffer_count, datasheet, datasheet_text  # noqa: E402
from ubrain.observe import capacity, decode_law, health, monitor, monitor_manifest, observe  # noqa: E402

D, V = 128, 500              # the workspace dimension and the sense's vocabulary
LISTS, BRAINS = 40, 10       # lists of 16 per brain, and brains (each draws its own roles)
EPISODES = 400


def _holder(sense, seed):
    body = Manifest("example/holder", "none", (
        Channel("camera", "codec", 1), Channel("recall", "event", 16), Channel("idle", "event", 1),
        Channel("clear", "event", 1), Channel("memory", "command", D), Channel("remembered", "choice", V)))
    return Brain(profile("holder"), body, codecs={"camera": sense}, rng=np.random.default_rng(seed))


def _observer(sense, seed):
    body = Manifest("example/observer", "none", (
        Channel("camera", "codec", 1), Channel("recall", "event", 64), Channel("boundary", "event", 1),
        Channel("memory", "command", D), Channel("remembered", "choice", V)))
    return Brain(profile("observer"), body, codecs={"camera": sense}, rng=np.random.default_rng(seed))


def main() -> None:
    sense = Sense.fit(GaussianCodes(dim=D), np.arange(V), d=D)
    rng = np.random.default_rng(0)

    # 1. the datasheet, before anything runs
    brain = _holder(sense, 0)
    print(datasheet_text(brain))
    row = next(r for r in datasheet(brain) if r["region"] == "prefrontal.buffer")
    st = brain.regions["prefrontal.buffer"]
    law = buffer_count(st.slots, st.gamma_m, D, V)
    print(f"\nprediction, {row['law']}: {law:.2f} of a list of {st.slots} recalled "
          f"(the datasheet's {row['value']}, unrounded)")

    # 2. measured on the running brain: present a list, recall every position, clear
    counts = []
    for b in range(BRAINS):
        brain = _holder(sense, b)
        for _ in range(LISTS):
            items = rng.choice(V, st.slots, replace=False)
            for it in items:
                brain.tick({"camera": int(it)})
            got = [brain.tick({"recall": j, "clear": 0 if j == st.slots - 1 else None})["remembered"]
                   for j in range(st.slots)]
            counts.append(sum(int(g == it) for g, it in zip(got, items)))
    counts = np.array(counts)
    print(f"measured on {counts.size} lists ({BRAINS} brains):  {counts.mean():.2f} recalled  "
          f"(+-{counts.std() / math.sqrt(counts.size):.2f})")

    # 3. the taps: copies of what the buffer holds, mid-list
    brain = _holder(sense, 99)
    for it in rng.choice(V, 6, replace=False):
        brain.tick({"camera": int(it)})
    print(f"\nobserve(), six items into a list: {observe(brain)['prefrontal.buffer']}")

    # 4. health: an episode against its capacity
    print("\nhealth() of the observer's episode (the decode law; white codes):")
    print("   load   ok     capacity   law at this load   measured (first slot)")
    cap = capacity(D, V)                                  # what health() checks the load against
    for k in (cap, 2 * cap):
        hits = 0
        for e in range(EPISODES):
            seer = _observer(sense, 1000 + e)
            seen = rng.choice(V, k, replace=False)
            for it in seen:
                seer.tick({"camera": int(it)})
            f = next(x for x in health(seer) if x["region"] == "hippocampus.episode")
            hits += seer.tick({"recall": 0})["remembered"] == seen[0]
        p = decode_law(k, D, V)
        print(f"   {k:4d}   {str(f['ok']):5s}  {f['law']:4d}       {p:.3f}              "
              f"{hits / EPISODES:.3f} (+-{math.sqrt(p * (1 - p) / EPISODES):.3f})")
    print(f"   note: {f['note']}")

    # 5. the monitor: a brain's interior as channels, and a brain that watches it
    brain = _holder(sense, 5)
    watched = monitor_manifest(brain)
    print(f"\nmonitor_manifest(): body {watched.body}, {len(watched.channels)} channels: "
          + ", ".join(c.name for c in watched.channels))
    watcher = Brain(Wiring("watcher", "1.0", regions={}, inputs={}, outputs={}), watched)
    trace = []
    for it in rng.choice(V, 20, replace=False):
        brain.tick({"camera": int(it)})
        senses = monitor(brain)
        watcher.tick(senses)
        trace.append(int(senses["prefrontal.buffer.held"][0]))
    print(f"the watcher ticked {watcher.ticks} times on the holder's monitor; "
          f"'prefrontal.buffer.held' it saw: {trace}")
    print(f"  (16 positions: items past them are dropped -- 'dropped' reads "
          f"{int(monitor(brain)['prefrontal.buffer.dropped'][0])})")
    print("\nTry: set the buffer's decay nearer one (w = profile(\"holder\"); "
          "w.regions[\"prefrontal.buffer\"][\"gamma_m\"] = 0.9) and print the datasheet again: "
          "how many more items does the count law promise, and does the brain deliver them?")


if __name__ == "__main__":
    main()

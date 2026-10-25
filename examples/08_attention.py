"""08 -- what the salience gate lets in, and the modes it switches (no robot, no GPU; ~10 s).

    uv run examples/08_attention.py

The `attender` profile puts a gate in front of memory. Each item a sense delivers is
judged against the last `window` items that ARRIVED (8 here) by the salience
network's novelty statistic, 1 - (the largest cosine to any of them). Below a
threshold theta the item is FAMILIAR and skipped; above it, it is NOVEL and is
written into the hippocampal episode. Nothing is trained: theta is derived from one
number, alpha = the probability that a FRESH item is mistaken for a familiar one.

The law checked here is the statistic's exact null. Two unrelated unit codes in d
dimensions have a cosine whose law is known exactly (a Beta law on the sphere), so a
fresh item against n distinct remembered codes is judged familiar with probability

    P(familiar | fresh, n) = 1 - (1 - t)^n,     t = P(cos > 1 - theta),

which is alpha when the window holds n = 8 distinct codes and less when it holds
repeats. Three kinds of item arrive:
  * fresh items -- judged familiar at the null rate above;
  * recent repeats (seen within the last 8 arrivals) -- novelty exactly 0, so ALWAYS
    familiar: the gate's skip;
  * old repeats (seen, but longer ago than the window) -- the gate has no memory of
    them, so they are judged exactly like fresh items and let in again.

A novel item is also a DEMAND on the mode controller (the network triangle): the
system plans and stays in executive mode while novel items keep coming, and falls
back to the default mode when nothing new is pending. The first default-mode (idle)
tick ends the episode, which is replayed into the cortex under fresh index keys.
The mode switching is SHOWN, not predicted (it is a rule, not a law: every plan
serves a demand). What the cortex can then recall is predicted by the decode law at
each episode's load (the replay hands on what the episode recalls), times the matrix
store's decode law at the number of memories it then holds.
"""


import numpy as np

from ubrain import Brain, Channel, Manifest, Wiring, profile  # noqa: E402
from ubrain.codecs import GaussianCodes, Sense  # noqa: E402
from ubrain.datasheet import weighted_law  # noqa: E402
from ubrain.observe import decode_law  # noqa: E402
from ubrain.regions import familiar_threshold, spherical_tail  # noqa: E402

V, D = 8000, 512             # the sense's vocabulary and the workspace dimension
BURSTS, BURST, GAP = 400, 16, 10    # bursts of 16 items, each followed by 10 quiet ticks
P_RECENT, P_OLD = 0.25, 0.10        # the chance an item repeats one from the window / from before it


def make_stream(rng, window):
    """A list of (item, kind) per tick, kind in 'fresh', 'recent', 'old' (None: a quiet tick)."""
    ticks, arrived, fresh = [], [], 0
    for _ in range(BURSTS):
        for _ in range(BURST):
            u = rng.random()
            older = arrived[:-window][-56:]                  # seen up to 56 arrivals before the window ...
            older = [x for x in older if x not in arrived[-window:]]   # ... and not since
            if arrived and u < P_RECENT:
                item, kind = arrived[-int(rng.integers(1, min(window, len(arrived)) + 1))], "recent"
            elif older and u < P_RECENT + P_OLD:
                item, kind = older[int(rng.integers(len(older)))], "old"
            else:
                item, kind = fresh, "fresh"
                fresh += 1
            arrived.append(item)
            ticks.append((item, kind))
        ticks += [(None, None)] * GAP
    return ticks


def main() -> None:
    w = profile("attender")
    window, alpha = w.regions["salience.gate"]["window"], w.regions["salience.gate"]["alpha"]
    theta = familiar_threshold(D, window, alpha)
    t = spherical_tail(1.0 - theta, D)
    print(f"the gate: window {window}, alpha {alpha}, d {D}")
    print(f"  derived threshold theta = {theta:.4f} (familiar when 1 - max cos < theta)")
    print(f"  P(a fresh item judged familiar | n distinct codes in the window) = 1 - (1 - {t:.5f})^n")
    print(f"  at n = {window}: {1 - (1 - t) ** window:.4f}  (= alpha); a recent repeat: 1 (novelty 0)\n")

    sense = Sense.fit(GaussianCodes(dim=D, seed=1), np.arange(V), d=D)
    body = Manifest("example/attender", "none", (
        Channel("camera", "codec", 1), Channel("recall", "event", 64), Channel("recollect", "event", 1),
        Channel("memory", "command", D), Channel("remembered", "choice", V),
        Channel("recollection", "command", D), Channel("recollected", "choice", V),
        Channel("mode", "choice", 2), Channel("novel", "choice", 2)))
    wiring = Wiring(w.name, w.contract, w.regions, w.inputs, {**w.outputs, "novel": "salience.gate.novel"})
    brain = Brain(wiring, body, codecs={"camera": sense}, rng=np.random.default_rng(0))
    episode = brain.regions["hippocampus.episode"]

    stream = make_stream(np.random.default_rng(1), window)
    window_items: list[int] = []
    judged = {k: [] for k in ("fresh", "recent", "old")}     # (familiar?, predicted P(familiar))
    admitted, loads, trace = [], [], []
    for item, kind in stream:
        load = episode.n
        out = brain.tick({"camera": item})
        if item is not None:
            n = len(set(window_items))
            p = 1.0 if kind == "recent" else 1.0 - (1.0 - t) ** n
            judged[kind].append((not out["novel"], p))
            if out["novel"]:
                admitted.append(item)
            window_items = (window_items + [item])[-window:]
        if out["mode"] == 0 and load > 0:
            loads.append(load)                                # this idle tick replayed an episode of `load`
        if len(trace) < 2 * (BURST + GAP):
            trace.append(({"fresh": "F", "recent": "r", "old": "o", None: "."}[kind],
                          " " if item is None else ("+" if out["novel"] else "-"),
                          "E" if out["mode"] == 1 else "d"))

    print("the first two bursts, one column per tick")
    print("  item   " + "".join(c[0] for c in trace) + "   F fresh, r recent repeat, o old repeat, . none")
    print("  gate   " + "".join(c[1] for c in trace) + "   + novel (written), - familiar (skipped)")
    print("  mode   " + "".join(c[2] for c in trace) + "   E executive, d default mode (idle: replay)\n")

    print("judged familiar      predicted    measured     (n)")
    for kind, label in (("fresh", "fresh items"), ("recent", "recent repeats"), ("old", "old repeats")):
        fam = np.array([f for f, _ in judged[kind]], dtype=float)
        pred = float(np.mean([p for _, p in judged[kind]]))
        pm = np.sqrt(pred * (1 - pred) / fam.size)
        print(f"  {label:16s}   {pred:.4f}      {fam.mean():.4f}     ({fam.size})  (+-{pm:.4f})")

    ctl = brain.observe()["modes.controller"]
    modes_seen = [c[2] for c in trace]
    print(f"\nmodes: {ctl['demands']} demands (novel items), {ctl['plans']} plans, "
          f"{ctl['served_plans']} of them serving a demand; "
          f"{len(loads)} episodes replayed, of {min(loads)} to {max(loads)} items")
    print(f"  executive share of the first two bursts' ticks: {modes_seen.count('E') / len(modes_seen):.2f}")

    store = brain.regions["cortex.store"]
    got = np.array([brain.tick({"recollect": i})["recollected"] for i in range(len(store.keys))])
    right = float(np.mean(got == np.array(admitted)))
    ep_law = float(np.sum([k * decode_law(k, D, V) for k in loads]) / np.sum(loads))
    cx_law = weighted_law(1.0, len(admitted), D * D, V, d_self=D)
    pred = ep_law * cx_law
    print(f"\nthe cortex after the replays: {len(store.keys)} memories, one per admitted item")
    print(f"  recalled right   predicted {pred:.3f}   measured {right:.3f}   (+-{np.sqrt(pred * (1 - pred) / len(admitted)):.3f})")
    print(f"  (the episode's decode law at each load, {ep_law:.3f}, times the cortex's at "
          f"{len(admitted)} pairs, {cx_law:.4f})")
    print("\nTry: set w.regions[\"salience.gate\"][\"alpha\"] = 0.2, or the window to 32. How many fresh "
          "items are lost, and do old repeats (lag past the window) still get in?")


if __name__ == "__main__":
    main()

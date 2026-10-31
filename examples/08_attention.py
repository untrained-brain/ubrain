"""08 -- what the salience gate lets in, and the modes it switches (no robot, no GPU; ~10 s).

    uv run examples/08_attention.py

The `attender` profile puts a gate in front of memory. The gate keeps one FADING TRACE of
every item it has seen, t <- lam t + z (lam = 0.95 here), and judges each item that arrives by its
cosine with the trace: at or above a threshold phi the item is FAMILIAR and skipped; below it, it
is NOVEL and is written into the hippocampal episode. Nothing is trained: phi is derived from one
number, alpha = the probability that a FRESH item is mistaken for a familiar one.

The law checked here. Each item's past copies sum to a weight A in the trace (a copy seen k items
ago weighs lam^k); S is the sum of every item's squared weight. An item's cosine with the trace is
A / sqrt(S) plus the other items' crosstalk, of variance (S - A^2) / d, so

    P(familiar) = P(N(0, 1) > (phi sqrt(S) - A) / sqrt((S - A^2) / d)),

which is alpha for a fresh item (A = 0). Three kinds of item arrive:
  * fresh items -- judged familiar at alpha;
  * recent repeats (seen within the last 8 arrivals) -- a heavy copy in the trace: almost always
    familiar, the gate's skip;
  * old repeats (seen 9 to 64 arrivals back) -- a faded copy: sometimes still familiar. An exact
    window of 8 items would have forgotten them all at once; the trace forgets them gracefully.

A novel item is also a DEMAND on the mode controller (the network triangle): the
system plans and stays in executive mode while novel items keep coming, and falls
back to the default mode when nothing new is pending. The first default-mode (idle)
tick ends the episode, which is replayed into the cortex under fresh index keys.
The mode switching is SHOWN, not predicted (it is a rule, not a law: every plan
serves a demand). What the cortex can then recall is predicted by the decode law at
each episode's load (the replay hands on what the episode recalls), times the matrix
store's decode law at the number of memories it then holds.
"""


from statistics import NormalDist

import numpy as np

from ubrain import Brain, Channel, Manifest, Wiring, profile  # noqa: E402
from ubrain.codecs import GaussianCodes, Sense  # noqa: E402
from ubrain.datasheet import weighted_law  # noqa: E402
from ubrain.observe import decode_law  # noqa: E402

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
    lam, alpha = w.regions["salience.gate"]["lam"], w.regions["salience.gate"]["alpha"]
    window = 8                                            # "recent": within the last 8 arrivals
    phi = NormalDist().inv_cdf(1.0 - alpha) / np.sqrt(D)
    print(f"the gate: a fading trace, lam {lam}, alpha {alpha}, d {D}")
    print(f"  derived threshold phi = {phi:.4f} (familiar when cos(item, trace) >= phi; a fresh item's "
          f"cosine is N(0, 1/d), so P(fresh judged familiar) = alpha)\n")

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
    weight: dict[int, float] = {}                         # each item's summed weight in the trace
    judged = {k: [] for k in ("fresh", "recent", "old")}     # (familiar?, predicted P(familiar))
    admitted, loads, trace = [], [], []
    for item, kind in stream:
        load = episode.n
        if item is not None:
            A = weight.get(item, 0.0)
            S = sum(a * a for a in weight.values())
            if S == 0.0:
                p = 0.0
            else:
                sd = np.sqrt(max(S - A * A, 1e-12) / D)
                p = 1.0 - NormalDist().cdf((phi * np.sqrt(S) - A) / sd)
        out = brain.tick({"camera": item})
        if item is not None:
            judged[kind].append((not out["novel"], p))
            if out["novel"]:
                admitted.append(item)
            weight = {k: lam * a for k, a in weight.items() if lam * a > 1e-6}
            weight[item] = weight.get(item, 0.0) + 1.0
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
    print("\nTry: set w.regions[\"salience.gate\"][\"lam\"] = 0.8 (a fast fade) or 0.99 (a slow one). How "
          "many old repeats are still recognised, and how many fresh items are lost?")


if __name__ == "__main__":
    main()

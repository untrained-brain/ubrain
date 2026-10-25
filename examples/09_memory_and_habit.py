"""09 -- memory first, habit later: the hand-over on a bandit (no robot, no GPU; ~30 s).

    uv run examples/09_memory_and_habit.py

A body shows one of S = 256 situations; in each, one of two actions pays 1 with
probability 0.7 and the other with 0.3. Two controllers learn from every outcome:

  * the hippocampus (episodic control): every (situation, action, outcome) is bound
    into ONE decaying vector, x <- gamma x + key_{s,a} (*) (+-z). At a decision each
    action's vote is read back from x and the best is taken -- greedy, from a single
    experience. But every vote also carries the crosstalk of all the other pairs the
    store holds, and old outcomes fade by gamma per outcome;
  * the striatum (the player of example 01): a value per (situation, action), moved
    by Q <- Q + eta (r - Q), released by the Go race.

The `chooser` profile joins them with a hand-over: memory acts while its votes'
top-two margin clears its own crosstalk scale ||x|| sqrt(2/d) (read off the store,
no estimate in it), and the striatum acts otherwise. The same body is also run on
memory alone (the chooser with no criterion: the store always acts) and on the
striatum alone (the `player` profile).

What is predicted, before the run, by ubrain's own figures:
  * on a situation's first visit nobody knows anything: every controller is a coin,
    reward rate (0.7 + 0.3) / 2 = 0.5;
  * the striatum learns with a time constant of 1/eta visits per situation (the
    datasheet), and long after it, its choice settles at MATCHING (example 01's law):
    action a with probability p_a / sum p, so a reward rate of sum p^2 / sum p.
What is SHOWN, not predicted (ubrain carries no closed form for it): memory's own
curve -- ahead after one experience, then held down by crosstalk and forgetting, so
that the striatum, slower but cleaner, overtakes it late -- and the hand-over, which
follows whichever is better at the time, a little short of it: its criterion asks
whether memory can tell its arms apart, not whether memory is right.
"""


import numpy as np

from ubrain import Brain, Channel, Manifest, Wiring, profile  # noqa: E402
from ubrain.datasheet import datasheet  # noqa: E402

S, A = 256, 2
P_GOOD, P_BAD = 0.7, 0.3
TRIALS, SEEDS = 20000, 5
BUCKETS = ((1, 1), (2, 3), (4, 10), (11, 30), (31, 60), (61, 10 ** 9))   # visits to the situation


def wiring(arm: str) -> Wiring:
    if arm == "striatum":
        return profile("player")
    w = profile("chooser")
    regions = {r: dict(p) for r, p in w.regions.items()}
    if arm == "memory":
        regions["hippocampus.episodic_control"].pop("kappa")   # no criterion: the store always acts
    return Wiring(w.name, w.contract, regions, w.inputs, w.outputs)


def run(arm: str, seed: int):
    """Reward and visit number per trial, and the brain at the end."""
    body = Manifest("example/bandit", "none", (Channel("situation", "event", S),
                                               Channel("reward", "reward", 1),
                                               Channel("action", "choice", A)))
    brain = Brain(wiring(arm), body, rng=np.random.default_rng([seed, 1]))
    rng = np.random.default_rng([seed, 2])                     # the world: the same for every arm
    good = rng.integers(A, size=S)
    seen = np.zeros(S, dtype=int)
    reward, visit = np.zeros(TRIALS), np.zeros(TRIALS, dtype=int)
    r = None
    for t in range(TRIALS):
        s = int(rng.integers(S))
        seen[s] += 1
        a = brain.tick({"situation": s, "reward": r})["action"]
        r = int(rng.random() < (P_GOOD if a == good[s] else P_BAD))
        reward[t], visit[t] = r, seen[s]
    brain.tick({"reward": r})
    return reward, visit, brain


def main() -> None:
    p = np.array([P_GOOD, P_BAD])
    probe = Brain(profile("player"), Manifest("example/bandit", "none", (
        Channel("situation", "event", S), Channel("reward", "reward", 1), Channel("action", "choice", A))))
    tau = next(row for row in datasheet(probe) if row["region"] == "basal_ganglia.striatum")
    first, matching = float(p.mean()), float((p * p).sum() / p.sum())
    print(f"predicted: first visit {first:.3f} for every controller; the striatum's "
          f"{tau['figure']} = {tau['value']}, and long after it, matching: {matching:.3f}")
    print(f"           (the best possible is {P_GOOD:.3f}; {S} situations, {TRIALS} trials, {SEEDS} seeds)\n")

    arms = ("hand-over", "memory", "striatum")
    rows, ends = {}, {}
    for arm in arms:
        R, Vt = [], []
        for seed in range(SEEDS):
            reward, visit, brain = run(arm.replace("hand-over", "chooser"), seed)
            R.append(reward)
            Vt.append(visit)
        ends[arm] = brain
        R, Vt = np.concatenate(R), np.concatenate(Vt)
        rows[arm] = [(R[(Vt >= lo) & (Vt <= hi)].mean(), int(np.sum((Vt >= lo) & (Vt <= hi))))
                     for lo, hi in BUCKETS]

    print("reward rate by visit to the situation (+- one binomial standard error)")
    print("  visit       " + "".join(f"{a:>17s}" for a in arms))
    for i, (lo, hi) in enumerate(BUCKETS):
        label = f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10 ** 9 else f"{lo}+")
        cells = "".join(f"   {m:.3f} (+-{np.sqrt(m * (1 - m) / n):.3f})" for m, n in (rows[a][i] for a in arms))
        print(f"  {label:8s}" + cells)

    mL, nL = rows["striatum"][-1]
    print("\nprediction against measurement")
    for arm in arms:
        m, n = rows[arm][0]
        print(f"  first visit, {arm:9s}  predicted {first:.3f}   measured {m:.3f}   "
              f"(+-{np.sqrt(first * (1 - first) / n):.3f})")
    print(f"  visits 61+,  striatum   predicted {matching:.3f}   measured {mL:.3f}   "
          f"(+-{np.sqrt(matching * (1 - matching) / nL):.3f})")

    st = ends["hand-over"].regions["hippocampus.episodic_control"]
    print(f"\nthe hand-over's criterion at the end (last seed): crosstalk scale ||x|| sqrt(2/d) = "
          f"{st.crosstalk_scale():.3f} (d {st.d}); memory acted on {st.acted / st.decisions:.2f} "
          f"of its {st.decisions} decisions, the striatum on the rest")
    print("\nTry: S = 16 (few pairs, little crosstalk: does memory stay ahead?), or a larger "
          "store: regions[\"hippocampus.episodic_control\"][\"d\"] = 1024 in wiring().")


if __name__ == "__main__":
    main()

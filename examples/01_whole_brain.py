"""01_whole_brain: the whole brain learns which action each picture asks for (needs: nothing).

    uv run examples/01_whole_brain.py

What it shows  Brain() is the whole brain: every region on the route from the senses to the action,
               wired once, the same in every copy. A program attaches streams by port class (a sense
               through a frozen codec, a reward, an action) and ticks it; it never wires it.
The world      four pictures; picture p asks for action right[p] of four; the right one pays 1. The
               pictures reach the brain through a fixed random codec (any frozen model would do).
The question   does it learn the rule? The law beside it: the striatum releases an action with
               probability in proportion to its value (the Go race), so the striatum alone would earn
               the right action's share of the values.
The twin       the same brain shown a fresh, unrelated picture every trial: always new, so it engages,
               but it carries nothing about which action is right. (Shown one FIXED picture instead, a
               whole brain never engages and never chooses at all: a sense must change.)
The check      the brain that sees earns more than 0.9 in its last block; the blind twin less than 0.5.
"""

from __future__ import annotations

import numpy as np

from ubrain import Brain, GaussianCodes

PICTURES, ACTIONS, TRIALS, BLOCK = 4, 4, 3000, 500
FLOOR = 1e-3                                    # the race's floor on a value


def brain_and_world(seed: int = 1):
    brain = Brain(variant="small", rng=np.random.default_rng(seed))
    brain.attach("sense", "vision", codec=GaussianCodes(dim=64, seed=1))   # -> key "sense.vision"
    brain.attach("reward")                                                 # -> key "reward"
    brain.attach("action", n=ACTIONS)                                      # -> "action" out
    return brain


def race_law(brain, right) -> float:
    """The striatum alone, by the Go race on its values now (an implementation tap, for study)."""
    st = brain.regions["basal_ganglia.striatum"]
    code = brain.codecs["sense.vision"]
    share = []
    for p in range(PICTURES):
        q = np.clip(st.W @ st.phi(code([p])[0]), FLOOR, None)
        share.append(q[right[p]] / q.sum())
    return float(np.mean(share))


def run(sees: bool) -> tuple[list[float], list[float]]:
    rng = np.random.default_rng(0)
    brain = brain_and_world()
    right = rng.permutation(ACTIONS)            # picture p asks for action right[p]
    r, paid, law = None, [], []
    for t in range(TRIALS):
        p = int(rng.integers(PICTURES))
        a = brain.tick({"sense.vision": p if sees else PICTURES + t, "reward": r})["action"]
        r = float(a == right[p]) if a is not None else 0.0
        paid.append(r)
        if sees and t % BLOCK == BLOCK - 1:
            law.append(race_law(brain, right))
    blocks = [float(np.mean(paid[b:b + BLOCK])) for b in range(0, TRIALS, BLOCK)]
    return blocks, law


def main(argv=None) -> int:
    seeing, law = run(sees=True)
    blind, _ = run(sees=False)
    print(f"{PICTURES} pictures, {ACTIONS} actions, chance {1 / ACTIONS:.2f}; blocks of {BLOCK} trials")
    print("  block   sees   the striatum alone (race law)   blind twin")
    for k, (s, l, b) in enumerate(zip(seeing, law, blind)):
        print(f"  {k + 1:5d}   {s:.3f}   {l:.3f}                           {b:.3f}")
    ok = seeing[-1] > 0.9 and blind[-1] < 0.5
    print("CHECK", "PASS" if ok else "FAIL", f"(sees {seeing[-1]:.3f} > 0.9; blind {blind[-1]:.3f} < 0.5)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

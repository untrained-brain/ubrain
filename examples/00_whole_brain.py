"""00 -- the whole brain: no wiring, streams attached by class (a few seconds).

    uv run examples/00_whole_brain.py

`Brain()` is the whole brain, every region on the route from the senses to the body,
wired once and the same in every copy. You choose a variant (sizes, never wiring) and
attach streams by port class: a sense through a codec, a reward, an action. The
thalamus relays the sense, the salience gate notices what is new, working memory holds
it, the striatum values it, the hippocampus remembers it and replays it into the
cortex, the cerebellum predicts what comes next, the mode controller switches between
the present and the past -- you wire none of it.

The world: one of four pictures is shown; each asks for its own action of four, and
the right one pays 1. The pictures reach the brain as codes from a fixed random codec
(any AI model would do).

The law, checked here: the striatum releases an action by the Go race, with probability
in proportion to its value (floored at 0.001), so values at zero release every action
alike -- the race explores what it has not learned -- and once learned, the expected
reward is the right action's share of the values, averaged over the pictures. The
research engine measured that law in the whole brain (the values law in place). The
printout sets the reward the brain earned beside the law evaluated on the values it
learned (at the middle of each block: the first block's earnings include the learning).
"""

import numpy as np

from ubrain import Brain, GaussianCodes, Sense

PICTURES, ACTIONS, TRIALS, BLOCK = 4, 4, 3000, 500
FLOOR = 1e-3                                    # the race's floor on a value


def race_law(brain, camera, right) -> float:
    """The expected reward of the Go race on the striatum's values now: per picture, the
    right action's floored value over the sum of all, averaged over the pictures."""
    st = brain.regions["basal_ganglia.striatum"]
    share = []
    for p in range(PICTURES):
        q = np.clip(st.W @ st.phi(camera([p])[0]), FLOOR, None)
        share.append(q[right[p]] / q.sum())
    return float(np.mean(share))


def main() -> None:
    rng = np.random.default_rng(0)
    camera = Sense.fit(GaussianCodes(dim=64, seed=1), range(PICTURES), d=128)
    brain = Brain(variant="small", rng=np.random.default_rng(1))
    brain.attach("sense", "vision", codec=camera)
    brain.attach("reward")
    brain.attach("action", n=ACTIONS)
    right = rng.permutation(ACTIONS)              # picture p asks for action right[p]
    r, paid, law = None, [], []
    for t in range(TRIALS):
        p = int(rng.integers(PICTURES))
        a = brain.tick({"sense.vision": p, "reward": r})["action"]
        r = float(a == right[p]) if a is not None else 0.0
        paid.append(r)
        if t % BLOCK == BLOCK // 2:               # the law at the middle of each block
            law.append(race_law(brain, camera, right))
    print(f"the whole brain, variant {brain.describe()['instance']['variant']!r}: "
          f"{len(brain.regions)} regions, wired by none of this script")
    print("  trials           earned   the race's law on the values (mid-block)")
    for k, b in enumerate(range(0, TRIALS, BLOCK)):
        print(f"  {b:5d}-{b + BLOCK - 1:5d}      {np.mean(paid[b:b + BLOCK]):.3f}    {law[k]:.3f}")
    print(f"  chance: {1 / ACTIONS:.2f}")
    print(f"inside (tap): the mode {brain.tap('modes.controller.mode')}, "
          f"acetylcholine {brain.tap('neuromodulator.acetylcholine.level')}")


if __name__ == "__main__":
    main()

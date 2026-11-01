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
(any AI model would do). The printout shows the reward rate rising from chance
(0.25), and a look inside through `tap`.

What it does not do yet, and why: it settles near one half, not near one. The striatum
in the whole chooses the largest value, and nothing in the whole explores, so in each
picture it keeps the first action that paid. Its law was measured with an exploration
schedule given from outside; what explores inside the whole brain is the next stage of
the research engine, and until it is certified `Brain()` is a preview.
"""

import numpy as np

from ubrain import Brain, GaussianCodes, Sense

PICTURES, ACTIONS, TRIALS, BLOCK = 4, 4, 3000, 500


def main() -> None:
    rng = np.random.default_rng(0)
    camera = Sense.fit(GaussianCodes(dim=64, seed=1), range(PICTURES), d=128)
    brain = Brain(variant="small", rng=np.random.default_rng(1))
    brain.attach("sense", "vision", codec=camera)
    brain.attach("reward")
    brain.attach("action", n=ACTIONS)
    right = rng.permutation(ACTIONS)              # picture p asks for action right[p]
    r, paid = None, []
    for t in range(TRIALS):
        p = int(rng.integers(PICTURES))
        a = brain.tick({"sense.vision": p, "reward": r})["action"]
        r = float(a == right[p]) if a is not None else 0.0
        paid.append(r)
    print(f"the whole brain, variant {brain.describe()['variant']!r}: "
          f"{len(brain.regions)} regions, wired by none of this script")
    for b in range(0, TRIALS, BLOCK):
        print(f"  trials {b:5d}-{b + BLOCK - 1:5d}: reward rate {np.mean(paid[b:b + BLOCK]):.2f}")
    print(f"  chance: {1 / ACTIONS:.2f}; nothing in the whole explores yet, so it keeps what first paid")
    print(f"inside (tap): the mode {brain.tap('modes.controller.mode')}, "
          f"acetylcholine {brain.tap('neuromodulator.acetylcholine.level')}, "
          f"the striatum's last prediction error {brain.tap('basal_ganglia.striatum.delta')}")


if __name__ == "__main__":
    main()

"""05 -- the same brain walks FrozenLake, and where its learning rule stops (a few seconds).

    uv run --extra game examples/05_frozenlake.py           # pip install ubrain[game]

Gymnasium's FrozenLake-v1, 4x4, NOT slippery: 16 squares, four moves, holes that end the
episode, and a reward of 1 only on reaching the goal (an episode is cut at 100 moves).
The adapter (`ubrain.bodies.gym.GymBody`) is the one Blackjack used.

The brain has no temporal-difference chain: a value is learned from the outcome that
arrives after a choice, never from the value of the square the move leads to. So:

  * `player` as shipped (reward = "step", credit to the last choice): every move but the
    last pays 0 now, so every value falls to 0 and the race chooses uniformly -- a random
    walk that finds the goal about one time in a hundred. A reward far from the choice
    that earned it is beyond a one-step rule; that is the rule, not a bug to tune away.
  * `chooser` (reward = "return", every choice of the episode credited with how it
    ended): Monte Carlo credit, no chain needed on a short deterministic episode. The
    store remembers which moves were on the path that reached the goal and acts on them,
    and the walk settles on the goal.

On the SLIPPERY lake (is_slippery=True) the same credit applies but the outcome of a
path is mostly chance, and nothing here is claimed for it.
"""

import numpy as np

from ubrain import Brain, profile
from ubrain.bodies.gym import GymBody, play

EPISODES = 3_000
BLOCK = 200


def main() -> None:
    import gymnasium as gym

    def lake():
        return gym.make("FrozenLake-v1", map_name="4x4", is_slippery=False)

    print(f"FrozenLake-v1 4x4, not slippery, {EPISODES} episodes; success rate over the first and "
          f"last {BLOCK}\n")
    for name, reward in (("player", "step"), ("chooser", "return")):
        for seed in (0, 1, 2):
            body = GymBody(lake(), reward_range=(0, 1), reward=reward)
            brain = Brain(profile(name), body.manifest, rng=np.random.default_rng(seed))
            r = np.asarray(body.run(brain, EPISODES, seed=seed))
            body.close(brain)
            print(f"{name:8s} reward={reward:6s} seed {seed}: first {r[:BLOCK].mean():.3f}  "
                  f"last {r[-BLOCK:].mean():.3f}")
    rng = np.random.default_rng(3)
    print(f"\nrandom policy: {np.mean(play(lake(), lambda o: int(rng.integers(4)), EPISODES, seed=0)):.3f}")


if __name__ == "__main__":
    main()

"""04 -- the same brain plays Blackjack (a Gymnasium game as a body; no GPU).

    uv run --extra game examples/04_blackjack.py            # pip install ubrain[game]

The body is Gymnasium's Blackjack-v1 (sab=True: Sutton and Barto's rules), wrapped by
the generic adapter `ubrain.bodies.gym.GymBody`, which knows no game: the observation
(player sum 0..31, dealer card 0..10, usable ace 0..1) becomes one of 704 situations,
the action is stick (0) or hit (1), and the hand's outcome -1 / 0 / +1 is mapped onto
0 / 0.5 / 1 and passed after the hand (reward = "return"). Not one line of brain code
was changed for it; the two anatomies are the shipped profiles:

  * `player`: the striatum alone, a value per (situation, action) by the three-factor
    rule, Q <- Q + eta (r - Q), choosing by the Go race (P(a) = Q_a / sum Q). As shipped
    it credits the LAST choice before an outcome, so in a hand of several hits only the
    final decision learns.
  * `chooser`: the hippocampal store that acts while it can tell its arms apart, the
    striatum otherwise; both credit EVERY choice of the hand with how it ended (Monte
    Carlo credit: the hand is short and its end is the only reward).

What to expect, and its limits (seeds as below; 100,000 hands, about a minute):

    player   first  win 0.344  draw 0.058  loss 0.597
             last   win 0.411  draw 0.062  loss 0.527
    chooser  first  win 0.364  draw 0.055  loss 0.581
             last   win 0.363  draw 0.067  loss 0.569   (memory acts on 0.36 of decisions)
    random          win 0.286  draw 0.042  loss 0.673
    stick 20        win 0.294  draw 0.055  loss 0.650

Both beat the random policy and the "stick on 20" baseline from the first block on. The
chooser is ahead EARLY -- the store acts one-shot on hands it has just seen -- and then
stays flat, and the striatum alone overtakes it: 704 x 2 pairs in one decaying
256-dimensional trace (a window of about 200 outcomes at gamma 0.995) is the many-context
case where the striatum wins late, and the hand-over's criterion measures the
store's separability, not its reliability, so memory keeps a share of decisions
it no longer earns. Neither reaches the optimal (basic) strategy -- about 0.43 wins /
0.09 draws / 0.48 losses under these rules -- because the race matches choice to value
instead of maximising: the brain's laws, not tuning, set the ceiling.
"""

import numpy as np

from ubrain import Brain, profile
from ubrain.bodies.gym import GymBody, play

HANDS = 100_000
BLOCK = 5_000
BASE = 50_000      # hands for the two baselines


def rates(returns) -> str:
    x = np.asarray(returns)
    return f"win {np.mean(x > 0):.3f}  draw {np.mean(x == 0):.3f}  loss {np.mean(x < 0):.3f}"


def main() -> None:
    import gymnasium as gym

    print(f"Blackjack-v1 (sab), {HANDS} hands; outcome rates over the first and last {BLOCK}\n")
    for name in ("player", "chooser"):
        body = GymBody(gym.make("Blackjack-v1", sab=True), reward_range=(-1, 1), reward="return")
        brain = Brain(profile(name), body.manifest, rng=np.random.default_rng(1))
        returns = body.run(brain, HANDS, seed=0)
        body.close(brain)
        print(f"{name:8s} first  {rates(returns[:BLOCK])}")
        print(f"{'':8s} last   {rates(returns[-BLOCK:])}")
        if name == "chooser":
            h = brain.regions["control.handover"]
            print(f"{'':8s} memory acted on {h.on_memory / h.decisions:.2f} of its decisions")
    env = gym.make("Blackjack-v1", sab=True)
    rng = np.random.default_rng(2)
    print(f"\n{'random':8s}        {rates(play(env, lambda o: int(rng.integers(2)), BASE, seed=0))}")
    print(f"{'stick 20':8s}        {rates(play(env, lambda o: 0 if o[0] >= 20 else 1, BASE, seed=0))}")
    print("\nTry: reward='step' (every hit pays 0.5 now, a one-step value), or the player with "
          "credit = \"episode\" (w = profile(\"player\"); "
          "w.regions[\"basal_ganglia.striatum\"][\"credit\"] = \"episode\").")


if __name__ == "__main__":
    main()

"""01 -- the striatum learns which action pays (no robot, no GPU; a few seconds).

    uv run examples/01_bandit.py

A "body" shows one of three situations; in each, every action pays 1 with its own
probability. The `player` profile's striatum keeps a value per (situation, action),
moves it toward each outcome by the three-factor rule, Q <- Q + eta (r - Q), and
releases actions by the Go race: each action's unit runs to threshold at a rate
proportional to its value, so action a wins with probability Q_a / sum_b Q_b.

Two laws, each measured in the research engine and checked here:
  * the values converge to the payoff probabilities, Q_a -> p_a (slowly for actions
    the race rarely picks: few outcomes to learn from);
  * so choice settles at p_a / sum_b p_b: MATCHING, not "always the best" -- the
    race spends some choices on worse actions, as animals do.
"""


import numpy as np

from ubrain import Brain, Channel, Manifest, profile  # noqa: E402

PAY = np.array([[0.8, 0.4, 0.1],        # situation 0: action 0 pays most often
                [0.2, 0.7, 0.2],        # situation 1: action 1
                [0.3, 0.3, 0.9]])       # situation 2: action 2
S, A = PAY.shape
TRIALS = 6000


def main() -> None:
    rng = np.random.default_rng(0)
    body = Manifest("example/bandit", "none", (Channel("situation", "event", S),
                                               Channel("reward", "reward", 1),
                                               Channel("action", "choice", A)))
    brain = Brain(profile("player"), body, rng=np.random.default_rng(1))
    counts = np.zeros((S, A))
    r, earned = None, 0
    for t in range(TRIALS):
        s = int(rng.integers(S))
        a = brain.tick({"situation": np.eye(S)[s], "reward": r})["action"]
        r = float(rng.random() < PAY[s, a])
        earned += r
        if t >= TRIALS // 2:
            counts[s, a] += 1
        if (t + 1) % 1000 == 0:
            print(f"trials {t + 1:5d}: reward rate so far {earned / (t + 1):.3f}")
    brain.tick({"reward": r})                     # the last outcome
    Q = brain.regions["basal_ganglia.striatum"].Q
    alloc = counts / counts.sum(axis=1, keepdims=True)
    print("\nlearned values Q (rows: situations)       payoff probabilities p")
    for s in range(S):
        print("  " + "  ".join(f"{q:.2f}" for q in Q[s]) + "          " + "  ".join(f"{p:.2f}" for p in PAY[s]))
    print("\nchoice in the second half                predicted p_a / sum p")
    for s in range(S):
        print("  " + "  ".join(f"{x:.2f}" for x in alloc[s]) + "          "
              + "  ".join(f"{x:.2f}" for x in PAY[s] / PAY[s].sum()))
    print("\nTry: a higher or lower eta (w = profile(\"player\"); "
          "w.regions[\"basal_ganglia.striatum\"][\"eta\"] = 0.01; Brain(w, ...)), or change PAY. "
          "How fast do the values settle, and how close is choice to the prediction?")


if __name__ == "__main__":
    main()

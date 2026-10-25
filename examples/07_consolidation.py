"""07 -- consolidation: the hippocampus hands its episodes to the cortex (no robot, no GPU; under a minute).

    uv run examples/07_consolidation.py

The `rememberer` profile is the memory system. The hippocampus writes what the sense
delivers into one episode vector, slot by slot, in one shot (as in 02_memory). When
the episode ends -- a boundary -- it retrieves every slot and REPLAYS the retrieved
items into the cortex, then clears itself. The cortex is a slow store: one d x d
weight matrix, written by Hebb's rule W += z k^T under a fresh random index key k for
each replayed item, and read by z = W k. A cue asks for the n-th consolidated memory:
read under its key, then take the nearest item the sense knows. The cortex stores
what the hippocampus retrieved, errors included, not what was seen.

Two laws, both computed before anything is stored, then checked:
  * the episode (a vector store) reads an item of a k-item episode at the decode
    law's rate in dimension d (`decode_law`);
  * the cortex (a matrix store) holding N different pairs reads one at the same law
    in the effective dimension d^2 (`weighted_law(1, N, d*d, V, d_self=d)`): a key's
    crosstalk is a product of two overlaps, so the matrix holds hundreds of items
    where one episode holds a handful (`matrix_capacity` against `episode_capacity`).
A memory seen and recalled from the cortex needs both stages right, so the end-to-end
rate is the product of the two. Every item of a run is a different one, as the law's
N pairs are. The laws are first-order Gaussian forms; at a dimension as small as this
one expect the measurement at or a little above them.
"""


import numpy as np

from ubrain import Brain, Channel, Manifest, profile  # noqa: E402
from ubrain.codecs import GaussianCodes, Sense  # noqa: E402
from ubrain.datasheet import episode_capacity, matrix_capacity, weighted_law  # noqa: E402
from ubrain.observe import decode_law  # noqa: E402

V, D = 4000, 128             # the sense's vocabulary and the workspace dimension
K = 4                        # items per episode
EPISODES = (50, 100, 150, 200, 300, 450, 600)   # episodes consolidated per brain: N = K x episodes
BRAINS = 3                   # brains per row


def main() -> None:
    hip = decode_law(K, D, V)
    print(f"the laws at d={D}, V={V}: one episode holds {episode_capacity(D, V)} items at 90%, "
          f"the cortex {matrix_capacity(D, V)} pairs at 90%;")
    print(f"an item of a {K}-item episode is retrieved by the hippocampus at {hip:.3f}\n")

    sense = Sense.fit(GaussianCodes(dim=D), np.arange(V), d=D)
    N_max = K * max(EPISODES)
    body = Manifest("example/rememberer", "none", (
        Channel("camera", "codec", 1), Channel("recall", "event", K),
        Channel("boundary", "event", 1), Channel("recollect", "event", N_max),
        Channel("memory", "command", D), Channel("remembered", "choice", V),
        Channel("recollection", "command", D), Channel("recollected", "choice", V)))
    rng = np.random.default_rng(0)
    print("  pairs N   hippocampus (law)        cortex, faithful (law)   seen, end to end (product)")
    for E in EPISODES:
        N = K * E
        ctx = weighted_law(1.0, N, D * D, V, d_self=D)
        n_hip = n_faith = n_seen = 0
        for b in range(BRAINS):
            brain = Brain(profile("rememberer"), body, codecs={"camera": sense},
                          rng=np.random.default_rng([E, b, 7]))
            seen = [int(x) for x in rng.permutation(V)[:N]]      # N different items
            retrieved = []
            for e in range(E):
                ep = seen[e * K:(e + 1) * K]
                for it in ep:
                    brain.tick({"camera": it})
                retrieved += [brain.tick({"recall": i})["remembered"] for i in range(K)]
                brain.tick({"boundary": True})            # replay into the cortex, clear the episode
            got = [brain.tick({"recollect": n})["recollected"] for n in range(N)]
            n_hip += sum(r == s for r, s in zip(retrieved, seen))
            n_faith += sum(g == r for g, r in zip(got, retrieved))
            n_seen += sum(g == s for g, s in zip(got, seen))
        n = N * BRAINS
        pm = lambda p: np.sqrt(p * (1 - p) / n)          # noqa: E731
        print(f"  {N:7d}   {n_hip / n:.3f} ({hip:.3f} +-{pm(hip):.3f})    "
              f"{n_faith / n:.3f} ({ctx:.3f} +-{pm(ctx):.3f})    "
              f"{n_seen / n:.3f} ({hip * ctx:.3f} +-{pm(hip * ctx):.3f})")
    print("\nTry: K = 8, or D = 256. The episode's capacity grows with d, the cortex's with the square "
          "of d: which stage now limits the end-to-end rate?")


if __name__ == "__main__":
    main()

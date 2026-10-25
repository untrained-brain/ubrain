"""06 -- working memory: how many items the prefrontal buffer holds (no robot, no GPU; a few seconds).

    uv run examples/06_working_memory.py

The `holder` profile keeps a list in the prefrontal active buffer, working memory as
persistent activity. Item j of the list is bound to position j's role, protected by
its position and added to ONE vector; before every write the whole vector fades by
gamma (0.75 here), so the newest item has weight 1, the one before it 0.75, the one
before that 0.56, and so on. A cue names a position: undo its protection, unbind its
role, and take the nearest item the sense knows. There is no cleanup memory behind
it, so old, faint items drown in the crosstalk of the newer ones.

The law being checked is the count law of a decaying vector store: item j, at weight
w_j = gamma^(L-1-j) among squared weights summing to S, is read right with the decode
law's probability at the vector's dimension d against the V items the sense knows;
the expected number held is the sum over the list. `buffer_count` computes it before
anything is stored. Then a full cycle of rehearsal (one idle event per item, the
oldest first) re-adds every held term: each weight is multiplied by the same factor,
the profile is restored, and the law predicts the same count again. (The profile
sets 16 rehearsals per list, one full cycle of its 16 positions.)
"""


import numpy as np

from ubrain import Brain, Channel, Manifest, profile  # noqa: E402
from ubrain.codecs import GaussianCodes, Sense  # noqa: E402
from ubrain.datasheet import buffer_count, weighted_law  # noqa: E402

V, D = 256, 512              # the sense's vocabulary and the buffer's dimension
TRIALS = 1000


def main() -> None:
    wiring = profile("holder")
    buf = wiring.regions["prefrontal.buffer"]
    L, GAMMA = int(buf["slots"]), float(buf["gamma_m"])   # a full list, at the profile's decay
    w = GAMMA ** np.arange(L - 1, -1, -1)                 # position j's weight, the last heaviest
    S = float(np.sum(w * w))
    law = np.array([weighted_law(float(wj), S, D, V) for wj in w])
    count = buffer_count(L, GAMMA, D, V)
    print(f"the count law: a list of {L} at decay {GAMMA} in d={D} against V={V} "
          f"holds {count:.2f} items on average\n")

    sense = Sense.fit(GaussianCodes(dim=D), np.arange(V), d=D)
    body = Manifest("example/holder", "none", (
        Channel("camera", "codec", 1), Channel("recall", "event", L),
        Channel("idle", "event", 1), Channel("clear", "event", 1),
        Channel("memory", "command", D), Channel("remembered", "choice", V)))
    rng = np.random.default_rng(0)
    hits = np.zeros((2, L))                    # [before, after rehearsal] x position
    counts = np.zeros((2, TRIALS))
    for t in range(TRIALS):
        brain = Brain(wiring, body, codecs={"camera": sense}, rng=np.random.default_rng([t, 6]))
        seen = rng.choice(V, size=L, replace=False)
        for it in seen:
            brain.tick({"camera": int(it)})
        for stage in (0, 1):
            if stage == 1:
                for _ in range(L):             # one full cycle: items 0, 1, ..., L-1 re-added
                    brain.tick({"idle": True})
            ok = np.array([brain.tick({"recall": j})["remembered"] == seen[j] for j in range(L)])
            hits[stage] += ok
            counts[stage, t] = ok.sum()

    sd = np.sqrt(law * (1 - law) / TRIALS)
    print("position  age  weight   law     presented         after one rehearsal cycle")
    for j in range(L):
        print(f"   {j:2d}     {L - 1 - j:2d}   {w[j]:.3f}   {law[j]:.3f}   "
              f"{hits[0, j] / TRIALS:.3f} (+-{sd[j]:.3f})    {hits[1, j] / TRIALS:.3f} (+-{sd[j]:.3f})")
    for stage, name in ((0, "presented"), (1, "after rehearsal")):
        se = counts[stage].std(ddof=1) / np.sqrt(TRIALS)
        print(f"\nitems held, {name:16s}: law {count:.2f}   measured {counts[stage].mean():.2f} (+-{se:.2f})", end="")
    print("\n\nTry: a slower decay (in main, set buf[\"gamma_m\"] = 0.9 before it is read), or double D. "
          "Which buys more items held, and does the law follow?")


if __name__ == "__main__":
    main()

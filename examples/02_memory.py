"""02 -- an episode in the hippocampus, and the certificate that predicts it (no GPU).

    uv run examples/02_memory.py

The `observer` profile writes each item a sense delivers into one episode: item i
is bound to slot i's role, protected by its position and summed into ONE vector.
A cue recalls a slot: undo the protection, unbind the role, and take the nearest
item the sense knows. The more items share the vector, the more they interfere.

Here the sense is the null codec, white Gaussian codes; `certify` says, before
anything is stored, how often the first item of a k-item episode comes back
(EC-MIX-02's law). Then the brain is run, and the two are set side by side.
"""


import numpy as np

from ubrain import Brain, Channel, Manifest, profile  # noqa: E402
from ubrain.codecs import GaussianCodes, Sense, certify  # noqa: E402

V, D = 500, 128              # the sense's vocabulary and the workspace dimension
KS = (4, 8, 16, 24, 32)
EPISODES = 200


def main() -> None:
    codec = GaussianCodes(dim=D)
    items = np.arange(V)
    print("certifying (the law, evaluated on these codes) ...")
    cert = certify(codec, items, d=D, ks=KS, n_trials=3000)
    print(cert.summary())
    sense = Sense.fit(codec, items, d=D)
    body = Manifest("example/observer", "none", (
        Channel("camera", "codec", 1), Channel("recall", "event", 64), Channel("boundary", "event", 1),
        Channel("memory", "command", D), Channel("remembered", "choice", V)))
    rng = np.random.default_rng(0)
    print("\nrunning the brain: the first item of a k-item episode, recalled")
    print("   k   certificate   measured")
    for k, law in zip(KS, cert.accuracy):
        hits = 0
        for e in range(EPISODES):
            brain = Brain(profile("observer"), body, codecs={"camera": sense}, rng=np.random.default_rng([e, k]))
            seen = rng.integers(0, V, size=k)
            for it in seen:
                brain.tick({"camera": int(it)})
            hits += brain.tick({"recall": 0})["remembered"] == seen[0]
        print(f"  {k:3d}     {law:.3f}       {hits / EPISODES:.3f}   (+-{np.sqrt(law * (1 - law) / EPISODES):.3f})")
    print("\nTry: double D. Where does the capacity at 90% move? (The law: capacity grows in proportion to D.)")


if __name__ == "__main__":
    main()

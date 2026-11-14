"""03_keep: save the whole brain, load it, and it continues exactly (needs: nothing).

    uv run examples/03_keep.py

What it shows  a brain learns all its life, so its state IS its knowledge: brain.save(path) writes it to
               one file, Brain.load(path, codecs=...) rebuilds it. The file names the senses' codecs, and
               a brain is refused a codec it did not learn with: another eye would recognise nothing.
The question   does a loaded brain choose exactly what the original would have?
The twin       the original brain, ticking on beside its loaded copy on the same stream.
The check      loading without the codec, or with another codec, is refused; over 500 more ticks the two
               brains' choices differ 0 times.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np

from ubrain import Brain, GaussianCodes

CODEC = dict(dim=64, seed=1)


def main(argv=None) -> int:
    brain = Brain(variant="small", rng=np.random.default_rng(1))
    brain.attach("sense", "vision", codec=GaussianCodes(**CODEC))
    brain.attach("reward")
    brain.attach("action", n=4)
    rng = np.random.default_rng(0)
    right, r = rng.integers(4, size=4), None
    for _ in range(1000):
        p = int(rng.integers(4))
        act = brain.tick({"sense.vision": p, "reward": r})["action"]
        r = float(act == right[p]) if act is not None else 0.0
    refused = 0
    with tempfile.TemporaryDirectory() as tmp:
        path = brain.save(Path(tmp) / "student.ubrain.npz")
        print(f"saved after 1000 ticks: {Path(path).stat().st_size / 1e6:.1f} MB")
        for label, codecs in (("no codec", None), ("another codec", {"sense.vision": GaussianCodes(dim=64, seed=2)})):
            try:
                Brain.load(path, codecs=codecs)
                print(f"  loaded with {label}: accepted")
            except Exception as e:                                  # noqa: BLE001
                refused += 1
                print(f"  loaded with {label}: refused ({type(e).__name__})")
        twin = Brain.load(path, codecs={"sense.vision": GaussianCodes(**CODEC)})
        print(f"  loaded with its own codec: accepted; lineage {len(twin.lineage)} saved state(s)")
        world, rs, differ = np.random.default_rng(1), [r, r], 0
        for _ in range(500):
            p = int(world.integers(4))
            a1 = brain.tick({"sense.vision": p, "reward": rs[0]})["action"]
            a2 = twin.tick({"sense.vision": p, "reward": rs[1]})["action"]
            differ += a1 != a2
            rs = [float(a1 == right[p]), float(a2 == right[p])]
    print(f"500 more ticks, the original and the loaded copy side by side: {differ} choices differ")
    ok = refused == 2 and differ == 0
    print("CHECK", "PASS" if ok else "FAIL", f"(refused {refused} of 2; choices differ {differ})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

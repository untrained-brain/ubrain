"""11 -- a brain saved, loaded, and continued bit for bit (no robot, no GPU; a few seconds).

    uv run examples/11_save_and_load.py

A brain learns all its life, so its state IS its knowledge. `brain.save(path)`
writes everything the brain holds into one .npz file -- every region's matrices,
tables and buffers, every random generator (the brain's and each region's), the
tick count, which regions are muted, and the last tick's outputs (a recurrent
edge reads them next tick). `Brain.load(path, manifest, codecs)` rebuilds a brain
from it that continues EXACTLY: run beside the brain that never stopped, on the
same senses, it makes the same choices and ends in the same state, byte for byte.
There is no law to predict here; the claim is identity, and it is checked as such.

The file names what the brain NEEDS, not only what it was: its wiring and the
wiring's digest, the body's manifest with the body's own record (versions, launch,
the release to fetch), every codec plugged in as the fitted sense itself (name,
digest, licence, the mean and vocabulary), and the brain's lineage -- the states it
was loaded from. `read_header` shows that without rebuilding anything; `load` takes
the codec MODEL alone and rebuilds the sense from the file; and it refuses a body
or a codec that is not the one the state was learned with (StateError, with the
reason -- for a body, the field that differs). The file is read with
allow_pickle=False, and only ubrain's own classes are rebuilt from it, so loading a
state runs no code of the file's choosing. `python -m ubrain.card <file>` writes the
brain's model card from the file.

The learner is example 1's: the `player` profile on a three-armed bandit.
"""


import tempfile
from pathlib import Path

import numpy as np

from ubrain import Brain, Channel, GaussianCodes, Manifest, Sense, profile  # noqa: E402
from ubrain.state import StateError, load, read_header, snapshot_bytes  # noqa: E402

PAY = np.array([[0.8, 0.4, 0.1],
                [0.2, 0.7, 0.2],
                [0.3, 0.3, 0.9]])
S, A = PAY.shape
BEFORE, AFTER = 3000, 3000          # trials learned before the save, and run after it


def _bandit():
    return Manifest("example/bandit", "none", (Channel("situation", "event", S),
                                               Channel("reward", "reward", 1),
                                               Channel("action", "choice", A)))


def _run(brain, situations, coins, r=None):
    """The world: situation s[t]; the action pays when coin[t] < PAY[s, a]. The same
    draws for every brain, so two brains see the same senses while they agree."""
    acts = []
    for s, u in zip(situations, coins):
        a = brain.tick({"situation": np.eye(S)[s], "reward": r})["action"]
        r = float(u < PAY[s, a])
        acts.append(a)
    return acts, r


def main() -> None:
    rng = np.random.default_rng(0)
    world = (rng.integers(S, size=BEFORE + AFTER), rng.random(BEFORE + AFTER))
    body = _bandit()
    brain = Brain(profile("player"), body, rng=np.random.default_rng(1))
    _, r = _run(brain, world[0][:BEFORE], world[1][:BEFORE])
    with tempfile.TemporaryDirectory() as tmp:
        path = brain.save(Path(tmp) / "player.ubrain.npz")
        h = read_header(path)
        print(f"saved after {BEFORE} trials: {path.name}, {path.stat().st_size} bytes")
        print(f"  header: format {h['format']} schema {h['schema']}, ubrain {h['ubrain']}, "
              f"wiring {h['wiring']['name']}, body {h['manifest']['body']} ({h['manifest']['digest']}), "
              f"ticks {h['ticks']}, codecs {sorted(h['codecs']) or 'none'}")

        loaded = Brain.load(path, body)                    # a new object, built from the file alone
        same_at_save = snapshot_bytes(loaded) == snapshot_bytes(brain)
        acts_a, _ = _run(brain, world[0][BEFORE:], world[1][BEFORE:], r)
        acts_b, _ = _run(loaded, world[0][BEFORE:], world[1][BEFORE:], r)
        agree = sum(a == b for a, b in zip(acts_a, acts_b))
        print("\nthe brain that never stopped, and the one loaded from the file, on the same senses:")
        print(f"  identical state at the save:             {same_at_save}")
        print(f"  choices that agree over {AFTER} more trials: {agree} of {AFTER}  (expected: all)")
        print(f"  identical state at the end:              {snapshot_bytes(loaded) == snapshot_bytes(brain)}")
        Q = loaded.regions["basal_ganglia.striatum"].Q
        print("  learned values, row 0, both brains:      "
              + " ".join(f"{q:.6f}" for q in Q[0]) + "  |  "
              + " ".join(f"{q:.6f}" for q in brain.regions["basal_ganglia.striatum"].Q[0]))

        print("\nthe refusals:")
        other = Manifest("example/another-bandit", "none", body.channels)
        try:
            Brain.load(path, other)
        except StateError as e:
            print(f"  another body:  StateError: {e}")
        sense = Sense.fit(GaussianCodes(dim=64, seed=2), range(40), d=64)
        seer_body = Manifest("example/observer", "none", (
            Channel("camera", "codec", 1), Channel("recall", "event", 16), Channel("boundary", "event", 1),
            Channel("memory", "command", 64), Channel("remembered", "choice", 40)))
        seer = Brain(profile("observer"), seer_body, codecs={"camera": sense}, rng=np.random.default_rng(2))
        for i in range(5):
            seer.tick({"camera": i})
        seer_path = seer.save(Path(tmp) / "observer.ubrain.npz")
        refit = Sense.fit(GaussianCodes(dim=64, seed=9), range(40), d=64)
        try:
            load(seer_path, seer_body, {"camera": refit})
        except StateError as e:
            print(f"  another codec: StateError: {e}")
        back = load(seer_path, seer_body, {"camera": sense})
        got = [back.tick({"recall": j})["remembered"] for j in range(5)]
        ref = [seer.tick({"recall": j})["remembered"] for j in range(5)]
        print(f"  the same codec: loaded; slots 0-4 recall {got}, the brain that never stopped {ref} "
              f"(items 0-4 were seen; a slip is the episode's own crosstalk, the same in both)")

        print("\nthe file names what the brain needs (schema 2):")
        hs = read_header(seer_path)
        rec = hs["codecs"]["camera"]
        print(f"  codec on 'camera': {rec['codec']['name']} ({rec['codec']['digest']}, licence {rec['codec']['license']}); "
              f"the fitted sense is in the file: mean, vocabulary of {len(rec['items'])} items, d={rec['d']}")
        from_model = load(seer_path, seer_body, {"camera": sense.codec})      # the model alone
        from_sense = load(seer_path, seer_body, {"camera": sense})            # the fitted sense, as before
        print(f"  loaded with the codec MODEL alone, the sense rebuilt from the file: "
              f"identical to a load with the fitted sense {snapshot_bytes(from_model) == snapshot_bytes(from_sense)}")
        print(f"  wiring {hs['wiring']['name']} ({hs['wiring_digest']}), content digest {hs['state_digest']}, "
              f"lineage {hs['lineage']} (a first generation)")
        for i in range(5, 10):                                                 # it lives on, then is saved again
            from_model.tick({"camera": i})
        gen2 = from_model.save(Path(tmp) / "observer.gen2.ubrain.npz")
        gen3 = Brain.load(gen2, seer_body, {"camera": sense})
        print("  saved again and loaded: lineage now "
              + " -> ".join(e["state_digest"] for e in gen3.lineage) + f"  ({len(gen3.lineage)} ancestors)")
        from ubrain.card import model_card
        card = model_card(gen2, gen3)
        print("  its model card (python -m ubrain.card <file>), first lines:")
        for line in card.splitlines()[:12]:
            print("    " + line)
    print(f"\nthe temporary directory is gone: {not Path(tmp).exists()}")
    print("\nTry: save the brain, keep only the file, and load it in a new Python session "
          "(Brain.load(path, manifest)): it picks up on the next trial as if never stopped.")


if __name__ == "__main__":
    main()

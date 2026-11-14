"""00_check_setup: is this computer ready for the robot examples? (about 2 minutes)

    uv run examples/00_check_setup.py

Run it at home before the class. It checks Python and ubrain, finds the G1 body and its
environment, starts the body, and lets the whole brain (Brain()) walk the robot for 3 seconds.
Every line ends in OK or in what to do; the last line is the CHECK, as in every example.
"""

from __future__ import annotations

import platform
import sys
import time
from pathlib import Path


def line(what: str, ok: bool, fix: str = "") -> bool:
    print(f"  {what:44s} {'OK' if ok else 'PROBLEM'}")
    if not ok and fix:
        print(f"      -> {fix}")
    return ok


def main() -> int:
    print(f"checking this computer ({platform.system()} {platform.machine()}, Python "
          f"{platform.python_version()})")
    good = line("Python 3.11, 3.12 or 3.13", (3, 11) <= sys.version_info[:2] <= (3, 13),
                "run the examples with `uv run`, which picks a suitable Python")
    try:
        import numpy  # noqa: F401
        import ubrain
        good &= line(f"ubrain {ubrain.__version__} installed", True)
    except Exception as e:                                   # noqa: BLE001
        line("ubrain installed", False, f"run from the ubrain folder with `uv run` ({e})")
        return 1
    from ubrain.bodies import find_body
    try:
        body_dir = find_body()
        good &= line("the G1 body found", True)
    except FileNotFoundError:
        line("the G1 body found", False, "run this from the ubrain folder (it holds bodies/mujoco)")
        return 1
    synced = (body_dir / ".venv").is_dir()
    good &= line("the body's environment set up", synced,
                 "cd bodies/mujoco && uv sync   (once; a few minutes)")
    if not synced:
        return 1
    print("  starting the body and walking 3 s ...")
    from ubrain import Brain, GaussianCodes
    from ubrain.bodies import BodyClient, kill_tree, start_body
    from ubrain.bodies.g1 import G1
    proc = None
    try:
        t0 = time.perf_counter()
        proc, port = start_body(echo=False)
        body = BodyClient("127.0.0.1", port)
        g1 = G1(body.hello)
        brain = Brain(variant="small")
        brain.attach("sense", "cue", codec=GaussianCodes(dim=32, seed=3))
        brain.attach("action", n=2)
        g1.attach(brain)
        state = body.reset(0)
        for _ in range(150):
            out = brain.tick(g1.streams(state, (0.5, 0.0, 0.0)) | {"sense.cue": 0})
            state = body.act(*g1.act(out))
        body.close()
        good &= line("the G1 walks for 3 s", bool(state["upright"]), "send the full output to your teacher")
        print(f"      ({time.perf_counter() - t0:.0f} s including start-up)")
    except Exception as e:                                   # noqa: BLE001
        line("the G1 walks for 3 s", False, f"send this to your teacher: {type(e).__name__}: {e}")
        good = False
    finally:
        if proc is not None:
            kill_tree(proc)
    print("\nREADY for the robot examples." if good else "\nNot ready yet: fix the PROBLEM lines above.")
    print("CHECK", "PASS" if good else "FAIL")
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())

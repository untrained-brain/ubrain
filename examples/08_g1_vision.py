"""08_g1_vision: the whole brain sees through the G1's head camera and notices what is new (needs: the
body, `--extra vision`, the CLIP weights).

    uv run --extra vision examples/08_g1_vision.py
    uv run --extra vision examples/08_g1_vision.py --viewer

What it shows  a trained model plugs in as a sense: CLIP codes the head camera's frame, and the whole brain
               maps the codes onto its own sphere and keeps its own record of what it meets
               (G1(hello, camera=CLIP("image")) attaches it as sense.vision). The robot walks down a gallery
               of 21 photographs; every 10th tick a frame goes to the brain.
The question   which glances does the whole brain's salience gate call new (read("novel"))? The whole brain
               engages, and chooses, only on what is new or surprising.
The twin       the same walk with the camera covered: a black frame every glance.
The check      the brain that sees calls at least 5 glances new; the covered twin at most 2.
"""

from __future__ import annotations

import argparse
import time

import numpy as np

from ubrain import Brain
from ubrain.bodies import BodyClient, kill_tree, start_body
from ubrain.bodies.g1 import G1, upright


def walk(body, clip, seconds: float, covered: bool, viewer: bool) -> str:
    """'N' for a glance called new, '.' for one seen before."""
    g1 = G1(body.hello, camera=clip, cue=False)
    brain = Brain(variant="standard", rng=np.random.default_rng(1))
    brain.attach("action", n=2)
    g1.attach(brain)                                  # body.proprio, goal, command, sense.vision
    state, marks, t0 = body.reset(0), "", time.perf_counter()
    for t in range(int(seconds * 50)):
        ins = g1.streams(state, (0.5, 0.0, 0.0))
        look = t % 10 == 0 and "sense.vision" in ins
        if not look:
            ins.pop("sense.vision", None)
        elif covered:
            ins["sense.vision"] = np.zeros_like(ins["sense.vision"])
        out = brain.tick(ins)
        if look:
            marks += "N" if brain.read("novel") else "."
        state = body.act(*g1.act(out), want_image=(t + 1) % 10 == 0, image_size=(224, 224))
        if viewer:
            time.sleep(max(0.0, t0 + (t + 1) * 0.02 - time.perf_counter()))
        if not upright(state):
            state = body.reset(0)
            brain.body_reset()
    return marks


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="the whole brain sees and notices what is new")
    ap.add_argument("--seconds", type=float, default=40.0)
    ap.add_argument("--viewer", action="store_true")
    a = ap.parse_args(argv)
    from ubrain.extras.clip import CLIP
    clip = CLIP("image")
    proc, port = start_body(viewer=a.viewer, head_camera=True, gallery=True)
    try:
        with BodyClient("127.0.0.1", port) as body:
            seeing = walk(body, clip, a.seconds, False, a.viewer)
            covered = walk(body, clip, a.seconds, True, a.viewer)
    finally:
        kill_tree(proc)
    ns, nc = seeing.count("N"), covered.count("N")
    print(f"sees     {len(seeing)} glances, {ns} new:  {seeing}")
    print(f"covered  {len(covered)} glances, {nc} new:  {covered}")
    ok = ns >= 5 and nc <= 2
    print("CHECK", "PASS" if ok else "FAIL", f"(sees {ns} >= 5 new; covered {nc} <= 2)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

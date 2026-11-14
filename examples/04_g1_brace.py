"""04_g1_brace: the whole brain drives the G1 and learns to brace on a tone (needs: the body).

    uv run examples/04_g1_brace.py
    uv run examples/04_g1_brace.py --viewer

What it shows  the whole brain takes the G1's body through four streams, attached by
               ubrain.bodies.g1.G1: body.proprio (70 numbers of proprioception), cue.tone (a sound it
               hears), goal (the walk the program wants) and command (the walk the brain sends: the goal
               plus the cerebellum's counter-move). Inside, the walker's certified cerebellum, held bit
               for bit to it (tests/test_whole_body.py: the whole does not disturb the certified circuit).
The world      walking at 0.4 m/s; every 4 s a tone, and 0.2 s later a push of 250 N from the front.
The question   does the cerebellum learn to keep the robot up from the tone alone?
The twin       the same brain without the cue stream: it cannot hear the tone.
The check      the brain that hears falls at least 5 times fewer than the twin in 20 pushes.
"""

from __future__ import annotations

import argparse
import time

import numpy as np

from ubrain import Brain, GaussianCodes
from ubrain.bodies import BodyClient, kill_tree, start_body
from ubrain.bodies.g1 import G1, upright

TRIAL, TONE_AT, DELAY, PUSH_N = 200, 150, 10, 250.0     # ticks (4 s), the tone, its lead, newtons


def pushes(body, hears: bool, n: int, vx: float, viewer: bool) -> str:
    """n pushes after a tone; '.' stayed up, 'X' fell."""
    g1 = G1(body.hello, cue=hears)
    brain = Brain(variant="small", rng=np.random.default_rng(1))
    brain.attach("sense", "cue", codec=GaussianCodes(dim=32, seed=3))   # a whole brain needs a sense
    brain.attach("action", n=2)                                         # ... and an action
    g1.attach(brain)                                                    # body.proprio, cue.tone, goal, command
    state, marks, t0, tick = body.reset(0), "", time.perf_counter(), 0
    for _ in range(n):
        fell = False
        for k in range(TRIAL):
            out = brain.tick(g1.streams(state, (vx, 0.0, 0.0)) | {"sense.cue": 0})
            if k == TONE_AT:                         # the experimenter's hand: the tone, then the push
                body._send({"type": "world", "tone": True,
                            "push": {"force": [PUSH_N, 0.0], "delay": DELAY, "ticks": 5}})
            state = body.act(*g1.act(out))
            tick += 1
            if viewer:
                time.sleep(max(0.0, t0 + tick * 0.02 - time.perf_counter()))
            if not upright(state):
                fell = True
                state = body.reset(0)
                brain.body_reset()
        marks += "X" if fell else "."
    if hears:
        r = brain.regions["cerebellum.forward@body"].stride_ratio
        print(f"  the cerebellum's prediction error at the end: {100 * r:.1f}% of predicting no change")
    return marks


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="the whole brain braces the G1 on a tone")
    ap.add_argument("--pushes", type=int, default=20)
    ap.add_argument("--vx", type=float, default=0.4)
    ap.add_argument("--viewer", action="store_true")
    a = ap.parse_args(argv)
    proc, port = start_body(viewer=a.viewer)
    try:
        with BodyClient("127.0.0.1", port) as body:
            heard = pushes(body, True, a.pushes, a.vx, a.viewer)
            deaf = pushes(body, False, a.pushes, a.vx, a.viewer)
    finally:
        kill_tree(proc)
    fa, fb = heard.count("X"), deaf.count("X")
    print(f"hears the tone  {heard}   falls {fa}")
    print(f"the twin, deaf  {deaf}   falls {fb}      (X fell, . stayed up)")
    ok = fb - fa >= 5
    print("CHECK", "PASS" if ok else "FAIL", f"(deaf {fb} - hears {fa} >= 5)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

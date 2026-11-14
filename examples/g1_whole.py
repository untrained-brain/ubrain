"""g1_whole: the whole brain in the G1 -- Brain() with the body's streams (0.46, PREVIEW).

    uv run examples/g1_whole.py                    # headless, lockstep: a report
    uv run examples/g1_whole.py --viewer           # watch it, real time

Until 0.45 the G1 ran on a profile (a circuit of chosen regions). Here it runs on the WHOLE brain:
`Brain(variant=...)` with the G1's streams attached by `ubrain.bodies.g1.G1` -- the body's
proprioception, the tone, the walk the program wants (`goal`) and the walk the brain sends (`command`).
Inside, the whole brain's cerebellum predicts the body and learns to brace on the tone, exactly as the
walker profile does (held bit for bit by tests/test_whole_body.py: the whole does not disturb the
certified circuit; that is a preview claim, not a certification of the whole).

Every 4 s a tone sounds and 0.2 s later the walking robot is pushed from the front (250 N). The brain only
hears the tone; its cerebellum learns the counter-move and the robot starts to stay up.

A whole brain still needs a sense and an action attached. Here the sense sees one fixed thing, so nothing
is new and the brain stays disengaged: it does not choose (its action is None). A whole brain chooses when
what it senses is new or surprising -- give it a sense that changes (examples/00_whole_brain.py).

It needs the body (bodies/mujoco, `uv sync`ed once).
"""

from __future__ import annotations

import argparse
import time

import numpy as np

from ubrain import Brain, GaussianCodes
from ubrain.bodies import BodyClient, kill_tree, start_body
from ubrain.bodies.g1 import G1, upright

TRIAL = 200                              # ticks per push (4 s at 50 Hz)
TONE_AT = 150                            # the tone, then the push PUSH_DELAY ticks later
PUSH_DELAY = 10                          # 0.2 s
PUSH_N = 250.0                           # newtons, from the front


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="the whole brain in the G1")
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--vx", type=float, default=0.4)
    ap.add_argument("--viewer", action="store_true")
    ap.add_argument("--variant", default="small")
    a = ap.parse_args(argv)

    proc, port = start_body(viewer=a.viewer)
    try:
        with BodyClient("127.0.0.1", port) as body:
            g1 = G1(body.hello)
            brain = Brain(variant=a.variant, rng=np.random.default_rng(1))
            brain.attach("sense", "cue", codec=GaussianCodes(dim=32, seed=3))   # one fixed thing seen
            brain.attach("action", n=2)
            g1.attach(brain)                              # body.proprio, cue.tone, goal, command
            state = body.reset(0)
            goal, t0, tick = (a.vx, 0.0, 0.0), time.perf_counter(), 0
            stayed, ratios = [], []
            for trial in range(a.trials):
                fell = False
                for k in range(TRIAL):
                    out = brain.tick(g1.streams(state, goal) | {"sense.cue": 0})
                    if k == TONE_AT:                     # the experimenter's hand: tone, then push
                        body._send({"type": "world", "tone": True,
                                    "push": {"force": [PUSH_N, 0.0], "delay": PUSH_DELAY, "ticks": 5}})
                    state = body.act(*g1.act(out))
                    tick += 1
                    if not upright(state):
                        fell = True
                        state = body.reset(0)
                        brain.body_reset()
                    if a.viewer:
                        time.sleep(max(0.0, t0 + tick * 0.02 - time.perf_counter()))
                stayed.append(not fell)
                r = brain.regions["cerebellum.forward@body"].stride_ratio   # built at the first tick
                ratios.append(None if r is None else round(100 * r, 1))
            print(f"{a.trials} pushes of {PUSH_N:.0f} N, each 0.2 s after a tone, walking at {a.vx} m/s")
            print("stayed up: " + "".join("." if s else "X" for s in stayed) + "   (X fell)")
            print(f"brace trials learned from: {brain.regions['cerebellum.brace'].trials}")
            print(f"the cerebellum's prediction error, % of predicting no change, per push: {ratios}")
            print(f"the whole's classes: {', '.join(brain.describe()['classes'])}")
    finally:
        kill_tree(proc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

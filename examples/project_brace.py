"""project_brace: how long a warning can the cerebellum learn to use? -- a project start (0.46).

    uv run examples/project_brace.py                  # four leads, a fresh brain each; the check
    uv run examples/project_brace.py --leads 5 10 20 40 60

A capstone-shaped example: a question, a prediction written first from a law, a sweep, a check.

  the question  a tone comes LEAD ticks before each push (250 N from the front). For which leads does the
                whole brain's cerebellum learn to stay up?
  the law       the brace keeps a fading trace of the tone, multiplied by tau = 0.9 every tick (week 16's
                eligibility trace). After LEAD ticks the trace is 0.9^LEAD: 0.59 at 5, 0.35 at 10, 0.12 at 20,
                0.015 at 40. A counter-move is learned in proportion to the trace when the push lands.
  the prediction (written before the run) the falls rise with the lead; at 40 ticks the brain learns
                little and falls about as often as one that hears no tone.
  FALSIFIED     measured (20 pushes, a fresh brain each): lead 5: 7 falls; 10: 3; 20: 4; 40: 4; no tone: 14.
                The SHORTEST lead is the worst and a 40-tick lead (trace 0.015) works nearly as well as 10.
                So "the trace at the push" is not how this brace learns. Why? That is a project: read week
                16's lab and ubrain's cerebellum.brace (tap its ports), predict again, measure again.
  the twin      a brain with no tone at all (no cue stream).
  the check     what the data does support: every lead has at least 5 falls fewer than the no-tone twin.
"""

from __future__ import annotations

import argparse

import numpy as np

from ubrain import Brain, GaussianCodes
from ubrain.bodies import BodyClient, kill_tree, start_body
from ubrain.bodies.g1 import G1, upright

TRIAL, PUSH_AT, PUSH_N, VX, TAU = 200, 160, 250.0, 0.4, 0.9


def falls(body, lead: int | None, n: int) -> str:
    """n pushes; the tone `lead` ticks before each (None: no tone, no cue stream). '.' up, 'X' fell."""
    g1 = G1(body.hello, cue=lead is not None)
    brain = Brain(variant="small", rng=np.random.default_rng(1))
    brain.attach("sense", "cue", codec=GaussianCodes(dim=32, seed=3))
    brain.attach("action", n=2)
    g1.attach(brain)
    state, marks = body.reset(0), ""
    for _ in range(n):
        fell = False
        for k in range(TRIAL):
            out = brain.tick(g1.streams(state, (VX, 0.0, 0.0)) | {"sense.cue": 0})
            if lead is not None and k == PUSH_AT - lead:
                body._send({"type": "world", "tone": True,
                            "push": {"force": [PUSH_N, 0.0], "delay": lead, "ticks": 5}})
            elif lead is None and k == PUSH_AT - 1:
                body._send({"type": "world", "push": {"force": [PUSH_N, 0.0], "delay": 1, "ticks": 5}})
            state = body.act(*g1.act(out))
            if not upright(state):
                fell = True
                state = body.reset(0)
                brain.body_reset()
        marks += "X" if fell else "."
    return marks


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="how long a warning can the cerebellum use?")
    ap.add_argument("--leads", type=int, nargs="+", default=[5, 10, 20, 40])
    ap.add_argument("--pushes", type=int, default=20)
    a = ap.parse_args(argv)
    proc, port = start_body(echo=False)
    rows = {}
    try:
        with BodyClient("127.0.0.1", port) as body:
            for lead in a.leads + [None]:
                rows[lead] = falls(body, lead, a.pushes)
                name = "no tone " if lead is None else f"lead {lead:3d}"
                trace = "" if lead is None else f"   trace at the push {TAU ** lead:.3f}"
                print(f"{name}  {rows[lead]}   falls {rows[lead].count('X'):2d}{trace}", flush=True)
    finally:
        kill_tree(proc)
    f = {k: v.count("X") for k, v in rows.items()}
    worst = max(f[k] for k in a.leads)
    ok = f[None] - worst >= 5
    print("CHECK", "PASS" if ok else "FAIL", f"(no tone {f[None]} - the worst lead {worst} >= 5)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

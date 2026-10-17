"""lab_cerebellum: change the G1's cerebellum and watch what changes.

    uv run examples/lab_cerebellum.py                         # 30 s walk, the defaults
    uv run examples/lab_cerebellum.py --viewer                # watch it (real time)
    uv run examples/lab_cerebellum.py --active 16             # a sparser granule code
    uv run examples/lab_cerebellum.py --pushes 12             # tone + push, learn to brace
    uv run examples/lab_cerebellum.py --pushes 12 --tau 0.5   # a shorter memory of the tone
    uv run --extra plot examples/lab_cerebellum.py --plot     # also save a PNG of the curve

The Unitree G1 walks with a frozen walking policy (its "spinal cord"). On top of it runs
the cerebellum, in two parts you can change:

THE FORWARD MODEL predicts, every tick (50 per second), how the body will move next.
    --granules N      number of granule cells: the body state + command is expanded
                      into this many features (default 2048)
    --active K        how many granule cells may fire at once: the k most active win
                      (sparse coding; default 128)
    --eta-forward E   learning rate of the Purkinje read-out (delta rule; default 0.5)
    --seed S          the random wiring from mossy fibres to granule cells (default 0)
  Measured: the prediction error as a share of the error of predicting "no change"
  (100% = no better than not predicting). It is printed every second.

THE BRACE learns to move into a push that a tone announces (eyeblink conditioning).
    --pushes N        how many tone-then-push trials (default 0: just walk)
    --force F         the push, newtons (default 250; below about 220 the robot never
                      falls, near 265 it nearly always does)
    --delay D         ticks from the tone to the push (default 10 = 0.2 s)
    --tau T           how slowly the trace of the tone fades, per tick (default 0.9)
    --eta-brace E     how fast the counter-move is learned, per trial (default 0.3)
    --bracing off     the cerebellum still learns, but its counter-move is not sent
  Measured: for every push, whether the robot fell (X) or stayed up (.).

And the walk:  --vx (m/s forward, 0.5)  --wz (turning, rad/s, 0)  --seconds (30)

Every run prints a summary and appends one row to results.csv (the parameters and the
results), so a group can compare runs, or a class can collect them in one table.

It needs the body (bodies/mujoco, `uv sync` there once).
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from ubrain import Brain, Wiring, act_03, manifest_from_hello_03, profile, senses_from_state_03
from ubrain.bodies import BodyClient, kill_tree, start_body

HZ = 50
EVERY = 200        # ticks between pushes (4 s)
HOLD = 60          # ticks a fallen robot stays down before it is set back up


def build_brain(a, manifest) -> Brain:
    """The walker profile, with this run's cerebellum parameters."""
    w = profile("walker")
    regions = {
        "cerebellum.forward": {"d_g": a.granules, "s": a.active, "eta": a.eta_forward, "seed": a.seed},
        "cerebellum.brace": {"tau": a.tau, "eta": a.eta_brace},
    }
    wiring = Wiring(w.name, w.contract, regions=regions, inputs=dict(w.inputs), outputs=dict(w.outputs))
    brain = Brain(wiring, manifest)
    brain.bracing = a.bracing == "on"
    return brain


def sparkline(values, lo=0.0, hi=1.0) -> str:
    bars = " .:-=+*#%@"
    out = ""
    for v in values:
        x = 0 if v is None else (min(max(v, lo), hi) - lo) / (hi - lo)
        out += bars[min(int(x * (len(bars) - 1) + 0.5), len(bars) - 1)]
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n".join(__doc__.split("\n")[8:]))
    ap.add_argument("--viewer", action="store_true", help="show the robot (real time)")
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--vx", type=float, default=0.5)
    ap.add_argument("--wz", type=float, default=0.0)
    ap.add_argument("--granules", type=int, default=2048)
    ap.add_argument("--active", type=int, default=128)
    ap.add_argument("--eta-forward", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--pushes", type=int, default=0)
    ap.add_argument("--force", type=float, default=250.0)
    ap.add_argument("--delay", type=int, default=10)
    ap.add_argument("--tau", type=float, default=0.9)
    ap.add_argument("--eta-brace", type=float, default=0.3)
    ap.add_argument("--bracing", choices=("on", "off"), default="on")
    ap.add_argument("--name", default="", help="a label for this run in results.csv (your group, your idea)")
    ap.add_argument("--plot", action="store_true", help="save a PNG of the run (needs --extra plot)")
    a = ap.parse_args(argv)
    if not 1 <= a.active <= a.granules:
        ap.error("--active must be between 1 and --granules")

    proc, port = start_body(viewer=a.viewer)
    curve, pushes, falls_walking = [], [], 0
    try:
        body = BodyClient("127.0.0.1", port)
        m = manifest_from_hello_03(body.hello)
        brain = build_brain(a, m)
        state = body.reset(0)
        goal = (a.vx, 0.0, a.wz)
        n_ticks = int(a.seconds * HZ)
        t, since_reset, watch, down = 0, 0, None, None
        t0 = time.perf_counter()
        print(f"walking {a.seconds:.0f} s at {a.vx} m/s; forward model {a.granules} granules, "
              f"{a.active} active, eta {a.eta_forward}; brace tau {a.tau}, eta {a.eta_brace}, "
              f"{a.pushes} pushes of {a.force:.0f} N, bracing {a.bracing}")
        print("   time   prediction error (% of 'no change')   pushes")
        while t < n_ticks or (a.pushes and len(pushes) < a.pushes and t < n_ticks + 60 * EVERY):
            want_push = (a.pushes and len(pushes) + (watch is not None) < a.pushes
                         and watch is None and down is None and since_reset % EVERY == 100
                         and state["upright"])
            if want_push:
                body._send({"type": "world", "tone": True,
                            "push": {"force": [a.force, 0.0], "delay": a.delay, "ticks": 5}})
                watch = state["tick"] + a.delay + 100
            senses = senses_from_state_03(state) | {"goal": goal}
            state = body.act(*act_03(m, brain.tick(senses)))
            t += 1
            since_reset += 1
            if down is not None and state["tick"] >= down:
                state = body.reset(0)
                brain.body_reset()
                since_reset, down = 0, None
            elif not state["upright"] and down is None:
                if watch is not None:
                    pushes.append(1)
                else:
                    falls_walking += 1
                watch, down = None, state["tick"] + HOLD
            elif watch is not None and state["tick"] >= watch:
                pushes.append(0)
                watch = None
            if t % HZ == 0:
                r = brain.forward.stride_ratio
                curve.append(r)
                print(f"  {t // HZ:4d} s   {('%5.1f %%' % (100 * r)) if r is not None else '  (watching the first stride)'}"
                      f"   {''.join('X' if x else '.' for x in pushes)}", flush=True)
            if a.viewer:
                lag = t0 + t / HZ - time.perf_counter()
                if lag > 0:
                    time.sleep(lag)
        body.close()
    finally:
        kill_tree(proc)

    seen = [r for r in curve if r is not None]
    last = float(np.mean(seen[-5:])) if seen else None
    print("\nprediction error over the run (each mark one second, taller = worse):")
    print("  [" + sparkline(curve) + "]")
    if last is not None:
        print(f"  last 5 s: {100 * last:.1f} % of predicting no change")
    if a.pushes:
        print(f"pushes: {''.join('X' if x else '.' for x in pushes)}   fell {sum(pushes)} of {len(pushes)}"
              f"   (X fell, . stayed up)")
    if falls_walking:
        print(f"falls without a push: {falls_walking}")

    row = {"when": datetime.now().isoformat(timespec="seconds"), "name": a.name,
           "seconds": a.seconds, "vx": a.vx, "wz": a.wz, "granules": a.granules, "active": a.active,
           "eta_forward": a.eta_forward, "seed": a.seed, "pushes": a.pushes, "force": a.force,
           "delay": a.delay, "tau": a.tau, "eta_brace": a.eta_brace, "bracing": a.bracing,
           "error_last5s_pct": None if last is None else round(100 * last, 2),
           "fell": sum(pushes), "push_record": "".join("X" if x else "." for x in pushes),
           "falls_without_push": falls_walking}
    new = not Path("results.csv").exists()
    with open("results.csv", "a", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(row))
        if new:
            wr.writeheader()
        wr.writerow(row)
    Path("last_run.json").write_text(json.dumps({**row, "curve": curve}, indent=1), encoding="utf-8")
    print("saved: one row in results.csv, the whole curve in last_run.json")

    if a.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 3.2))
        xs = [i + 1 for i, r in enumerate(curve) if r is not None]
        ax.plot(xs, [100 * r for r in curve if r is not None], lw=2)
        ax.set_xlabel("time (s)")
        ax.set_ylabel("prediction error\n(% of 'no change')")
        ax.set_ylim(0, 110)
        ax.set_title(f"{a.active} of {a.granules} granules active, eta {a.eta_forward}")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        out = f"run_{datetime.now().strftime('%H%M%S')}.png"
        fig.savefig(out, dpi=130)
        print("plot:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

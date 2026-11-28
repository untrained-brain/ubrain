"""02_ask: ask the whole brain what it is and what it holds (needs: nothing).

    uv run examples/02_ask.py
    uv run examples/02_ask.py --variant large

What it shows  a brain answers questions about itself, before and after it runs, and reading changes
               nothing:
                 describe()   its port classes, the observables read() serves, its guarantees
                 read(name)   an observable as the last tick left it (value, prediction_error, source, ...)
                 datasheet()  its capacities, from the laws that certified its regions
                 health()     what it holds, against those laws
The question   which datasheet rows does a larger variant change? (A variant sizes regions, never
               their wiring.)
The twin       the same questions to a brain of another variant (--variant).
The check      describe() is the same before and after 300 ticks, and health() has no warning.
"""

from __future__ import annotations

import argparse

import numpy as np

from ubrain import Brain, GaussianCodes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ask the whole brain about itself")
    ap.add_argument("--variant", default="small", help="small | standard | large")
    a = ap.parse_args(argv)
    brain = Brain(variant=a.variant, rng=np.random.default_rng(1))
    brain.attach("sense", "vision", codec=GaussianCodes(dim=64, seed=1))
    brain.attach("reward")
    brain.attach("action", n=4)
    before = brain.describe()
    print(f"implementation {before['implementation']}; interface {before['interface']}")
    print("port classes built:", ", ".join(before["classes"]))
    carried = [k for k, o in before["observables"].items() if o.get("carried", True)]
    print("observables read() serves:", ", ".join(carried))
    print("not carried by this brain (read() gives their absent value):",
          ", ".join(k for k in before["observables"] if k not in carried) or "none")
    rng = np.random.default_rng(0)
    right, r = rng.integers(4, size=4), None
    for _ in range(300):
        p = int(rng.integers(4))
        act = brain.tick({"sense.vision": p, "reward": r})["action"]
        r = float(act == right[p]) if act is not None else 0.0
    print("after 300 ticks, read():")
    for name in carried:
        v = brain.read(name)
        print(f"  {name:18s} {v if not isinstance(v, np.ndarray) else f'array {v.shape}'}")
    print(f"the datasheet, variant {a.variant!r}:")
    for row in brain.datasheet():
        print(f"  {row['region']:32s} {str(row['figure'])[:44]:44s} {str(row['value'])[:30]}")
    warnings = [h for h in brain.health() if not h.get("ok", True)]
    after = brain.describe()
    same = {k: before[k] for k in ("classes", "observables", "guarantees")} == \
           {k: after[k] for k in ("classes", "observables", "guarantees")}
    ok = same and not warnings
    print("CHECK", "PASS" if ok else "FAIL", f"(describe unchanged: {same}; health warnings: {len(warnings)})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

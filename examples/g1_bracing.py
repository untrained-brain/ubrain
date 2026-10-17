"""g1_bracing: the G1 learns to brace against a push it hears coming.

    uv run --extra video examples/g1_bracing.py --record bracing      # writes bracing.mp4
    uv run examples/g1_bracing.py                                      # the counts only

A tone sounds; 0.2 s later the walking robot is pushed from the front. The brain only
HEARS the tone -- it never feels the push, only what the push does to its body. Its
cerebellum keeps a fading trace of the tone (an eligibility trace) and learns the
counter-move that, made just before the push lands, keeps the robot up: classical
(eyeblink) conditioning in a humanoid.

Two runs on the same body, one push every 4 s:
  1. bracing MUTED (the cerebellum learns, but its output is silenced): the push wins;
  2. a fresh brain with bracing ON: the first push wins -- nothing is learned yet --
     and then the robot braces.
After a fall the robot is shown down for a moment and set back on its feet.

It needs the body (bodies/mujoco, `uv sync`ed once). With --record, the body records
a camera following the robot (never seen by the brain) and the video is composed
with the counts: MP4 through imageio[ffmpeg] (`--extra video`).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from ubrain import Brain, act_03, manifest_from_hello_03, profile, senses_from_state_03
from ubrain.bodies import BodyClient, kill_tree, start_body

DELAY = 10          # ticks from the tone to the push (0.2 s)
EVERY = 200         # ticks between pushes (4 s)
HOLD = 60           # ticks a fallen robot is shown down before it is reset


SEG = [-1]          # resets so far: the body's tick restarts at every reset


def _log(log, phase, event, tick, **kw):
    log.append({"phase": phase, "event": event, "seg": SEG[0], "tick": int(tick), **kw})


def run(body, m, bracing: bool, n_push: int, force: float, log: list, phase: str) -> list[int]:
    """One run; returns 1 (fell) or 0 (stayed up) per push; logs events by (segment, tick)."""
    brain = Brain(profile("walker"), m)
    brain.bracing = bracing
    state = body.reset(0)
    SEG[0] += 1
    _log(log, phase, "start", state["tick"])
    goal = (0.5, 0.0, 0.0)
    out, t, watch, down = [], 0, None, None
    while len(out) < n_push:
        if watch is None and down is None and t % EVERY == 100 and state["upright"]:
            body._send({"type": "world", "tone": True,
                        "push": {"force": [force, 0.0], "delay": DELAY, "ticks": 5}})
            _log(log, phase, "tone", state["tick"])
            watch = state["tick"] + DELAY + 100
        state = body.act(*act_03(m, brain.tick(senses_from_state_03(state) | {"goal": goal})))
        t += 1
        if down is not None and state["tick"] >= down:                 # back on its feet
            state = body.reset(0)
            SEG[0] += 1
            brain.body_reset()
            t, down = 0, None
        elif watch is not None and not state["upright"]:
            out.append(1)
            _log(log, phase, "fell", state["tick"])
            watch, down = None, state["tick"] + HOLD
        elif watch is not None and state["tick"] >= watch:
            out.append(0)
            _log(log, phase, "stayed", state["tick"])
            watch = None
    return out


def compose(chase_base: str, log: list, path: Path, n_a: int, n_b: int) -> Path:
    """The follow camera, with the run's title, the tone and push, and the counts."""
    from PIL import Image, ImageDraw, ImageFont
    info = json.loads(Path(chase_base + ".json").read_text(encoding="utf-8"))
    w, h, ticks = info["width"], info["height"], info["ticks"]
    chase = np.fromfile(chase_base + ".rgb", dtype=np.uint8).reshape(len(ticks), h, w, 3)
    try:
        big, font = ImageFont.load_default(size=34), ImageFont.load_default(size=26)
    except TypeError:
        big = font = ImageFont.load_default()
    # the body's tick restarts at every reset: a tick lower than the last starts a
    # new segment, and events are replayed in (segment, tick) order
    titles = {"muted": "1. Bracing muted: the push wins",
              "on": "2. A fresh brain, bracing on: it learns to brace"}
    pending = sorted(log, key=lambda e: (e["seg"], e["tick"]))
    k, seg, last = 0, 0, -1
    phase, fell, stayed, tone_at, banner, frames = "muted", 0, 0, None, None, []
    for i, tick in enumerate(ticks):
        if tick < last:
            seg += 1
        last = tick
        while k < len(pending) and (pending[k]["seg"], pending[k]["tick"]) <= (seg, tick):
            e = pending[k]
            k += 1
            if e["event"] == "start":
                phase, fell, stayed, banner = e["phase"], 0, 0, None
            elif e["event"] == "tone":
                tone_at = i
            elif e["event"] == "fell":
                fell, banner = fell + 1, ("FELL", i)
            elif e["event"] == "stayed":
                stayed, banner = stayed + 1, ("STAYED UP", i)
        im = Image.new("RGB", (1280, 720), (18, 22, 30))
        d = ImageDraw.Draw(im)
        im.paste(Image.fromarray(chase[i]).resize((1120, 630)), (80, 70))
        d.text((80, 18), titles[phase], fill=(235, 235, 235), font=big)
        n = fell + stayed
        d.text((900, 90), f"pushes {n}", fill=(235, 235, 235), font=font)
        d.text((900, 124), f"fell  {fell}", fill=(255, 120, 110), font=font)
        d.text((900, 158), f"stayed up  {stayed}", fill=(140, 230, 140), font=font)
        # overlays are timed in frames: the follow camera records one every 2 ticks
        if tone_at is not None and 0 <= i - tone_at < 13:
            d.text((100, 90), "tone ...", fill=(255, 210, 0), font=big)
            if 2 * (i - tone_at) >= DELAY:
                d.text((100, 134), "PUSH", fill=(255, 120, 110), font=big)
        if banner is not None and i - banner[1] < 40:
            col = (255, 120, 110) if banner[0] == "FELL" else (140, 230, 140)
            d.text((560, 600), banner[0], fill=col, font=big)
        frames.append(np.asarray(im))
    end = frames[-1]
    frames += [end] * 50
    try:
        import imageio.v2 as iio
        iio.mimwrite(path.with_suffix(".mp4"), frames, fps=25, macro_block_size=8, quality=5)
        return path.with_suffix(".mp4")
    except Exception:
        ims = [Image.fromarray(f).resize((640, 360)) for f in frames[::5]]
        ims[0].save(path.with_suffix(".gif"), save_all=True, append_images=ims[1:], duration=200, loop=0)
        return path.with_suffix(".gif")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--force", type=float, default=250.0, help="the push, in newtons")
    ap.add_argument("--muted", type=int, default=5, help="pushes with bracing muted")
    ap.add_argument("--on", type=int, default=12, help="pushes with bracing on")
    ap.add_argument("--record", default=None, help="write the video here (.mp4, else .gif)")
    a = ap.parse_args(argv)

    chase = str(Path(a.record).resolve()) + "_chase" if a.record else None
    proc, port = start_body(record_chase=chase)
    log: list = []
    try:
        body = BodyClient("127.0.0.1", port)
        m = manifest_from_hello_03(body.hello)
        t0 = time.perf_counter()
        off = run(body, m, False, a.muted, a.force, log, "muted")
        on = run(body, m, True, a.on, a.force, log, "on")
        body.close()
        if chase:
            for _ in range(100):
                if Path(chase + ".json").is_file():
                    break
                time.sleep(0.1)
    finally:
        kill_tree(proc)
    sym = lambda xs: "".join("X" if x else "." for x in xs)      # noqa: E731
    print(f"push {a.force:.0f} N, {time.perf_counter() - t0:.0f} s")
    print(f"bracing muted: fell {sum(off)} of {len(off)}   {sym(off)}")
    print(f"bracing on:    fell {sum(on)} of {len(on)}   {sym(on)}   (X fell, . stayed up)")
    if a.record:
        print("video:", compose(chase, log, Path(a.record), a.muted, a.on))
        for ext in (".rgb", ".json"):
            Path(chase + ext).unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

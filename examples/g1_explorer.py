"""g1_explorer: the G1 walks past a gallery and remembers what it saw.

    uv run --extra vision --extra video examples/g1_explorer.py --viewer     # watch it, real time
    uv run --extra vision examples/g1_explorer.py --headless                 # lockstep, then a report
    uv run --extra vision --extra video examples/g1_explorer.py --headless --seconds 40 --record walk

The `vision` extra brings CLIP (torch); `video` the MP4 writer. It needs the body: a
the body in bodies/mujoco, `uv sync`ed once.

What happens:
  * the body serves the gallery scene (21 CC0 photos along the walking line, see
    bodies/mujoco/scenes/gallery_cc0) and a head camera;
  * the brain is `ubrain.Brain` with the `explorer` profile -- the walker's cerebellum
    and the hippocampal episode -- and CLIP plugged into its camera channel through a
    `Sense` fitted on the gallery's pictures (its vocabulary: what a memory is
    cleaned up against);
  * every GLANCE ticks the app takes a frame and looks at one half of it (a fovea:
    the half with more structure), and passes it to the brain when a new thing has
    been SEEN: the same picture recognised on STEADY glances in a row (event
    segmentation; a one-frame flicker is not an event), not already in the episode;
  * at the end the brain recalls every slot, and the report sets what it remembers
    beside the order the pictures stand in, and beside its certificate.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import time
from pathlib import Path

import numpy as np


from ubrain.bodies import BodyClient, find_body, kill_tree  # noqa: E402
from ubrain.bodies import start_body as _start_body  # noqa: E402
from ubrain import Brain, Channel, act_03, manifest_from_hello_03, profile, senses_from_state_03  # noqa: E402
from ubrain.codecs import Sense, certify  # noqa: E402

GLANCE = 10              # ticks between frames (5 per second at 50 Hz)
STEADY = 3               # glances in a row on the same picture before it counts as seen
MIN_STD = 20.0           # a half-frame this flat holds no picture
D = 512                  # the workspace dimension: CLIP's own, no projection


def fovea(frame: np.ndarray) -> tuple[np.ndarray, float, str]:
    """The half of the frame with more structure (the larger grey-level spread)."""
    w = frame.shape[1] // 2
    halves = {"left": frame[:, :w], "right": frame[:, w:]}
    spread = {k: float(v.mean(axis=2).std()) for k, v in halves.items()}
    side = max(spread, key=spread.get)
    return halves[side], spread[side], side


class Recorder:
    """The robot's-eye video: each glance becomes a frame -- the head camera with the
    attended half boxed, what it takes the picture to be, and the episode so far as
    thumbnails -- then a closing sequence of the recall, slot by slot. MP4 through
    imageio[ffmpeg] when installed, else an animated GIF (Pillow alone)."""

    W, H, EYE = 1280, 720, 560

    def __init__(self, pictures, names):
        from PIL import Image, ImageFont
        self.Image = Image
        self.thumbs = {n: Image.open(p).convert("RGB").resize((96, 96)) for p, n in zip(pictures, names)}
        try:
            self.font = ImageFont.load_default(size=26)
            self.small = ImageFont.load_default(size=18)
        except TypeError:                                  # Pillow < 10.1
            self.font = self.small = ImageFont.load_default()
        self.frames = []

    def _canvas(self):
        from PIL import ImageDraw
        im = self.Image.new("RGB", (self.W, self.H), (18, 22, 30))
        return im, ImageDraw.Draw(im)

    def _memory(self, im, d, stored, top=360, title="memory (one episode)"):
        d.text((640, top - 40), title, fill=(200, 200, 200), font=self.small)
        for i, n in enumerate(stored):
            x, y = 640 + (i % 6) * 104, top + (i // 6) * 130
            im.paste(self.thumbs[n], (x, y))
            d.text((x, y + 100), f"{i}: {n}", fill=(220, 220, 220), font=self.small)

    def glance(self, frame, side, guess, run, stored, t):
        im, d = self._canvas()
        eye = self.Image.fromarray(frame).resize((self.EYE, self.EYE))
        im.paste(eye, (40, 80))
        x0 = 40 if side == "left" else 40 + self.EYE // 2
        d.rectangle([x0, 80, x0 + self.EYE // 2, 80 + self.EYE], outline=(255, 210, 0), width=4)
        d.text((40, 30), f"the G1's head camera   t = {t / 50:5.1f} s", fill=(230, 230, 230), font=self.font)
        d.text((640, 90), "looks like:", fill=(180, 180, 180), font=self.font)
        d.text((640, 130), f"{guess}  ({run}/{STEADY})", fill=(255, 210, 0), font=self.font)
        im.paste(self.thumbs[guess].resize((150, 150)), (900, 80))
        self._memory(im, d, stored)
        self.frames.append(np.asarray(im))

    def recall(self, stored, recalled):
        for k in range(len(recalled) + 1):
            im, d = self._canvas()
            d.text((40, 30), "walk over. the cue recalls each slot of the episode:", fill=(230, 230, 230),
                   font=self.font)
            self._memory(im, d, stored, top=120, title="written while walking")
            self._memory(im, d, recalled[:k], top=430, title="recalled")
            for _ in range(3):
                self.frames.append(np.asarray(im))

    def save(self, path: Path, fps: int = 5) -> Path:
        path = Path(path)
        try:
            import imageio.v2 as iio
            iio.mimwrite(path.with_suffix(".mp4"), self.frames, fps=fps, macro_block_size=8)
            return path.with_suffix(".mp4")
        except Exception:
            ims = [self.Image.fromarray(f).resize((640, 360)) for f in self.frames]
            ims[0].save(path.with_suffix(".gif"), save_all=True, append_images=ims[1:],
                        duration=int(1000 / fps), loop=0)
            return path.with_suffix(".gif")


def lcs(a: list, b: list) -> int:
    t = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            t[i + 1][j + 1] = t[i][j] + 1 if x == y else max(t[i][j + 1], t[i + 1][j])
    return t[-1][-1]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--viewer", action="store_true")
    ap.add_argument("--port", type=int, default=5571)
    ap.add_argument("--vx", type=float, default=0.5)
    ap.add_argument("--seconds", type=float, default=58.0)
    ap.add_argument("--verbose", action="store_true", help="print every glance")
    ap.add_argument("--realtime", action="store_true",
                    help="pace the walk at 50 Hz wall clock (the default with --viewer)")
    ap.add_argument("--record", default=None, help="save the robot's-eye video here (.mp4, else .gif)")
    a = ap.parse_args(argv)
    realtime = a.realtime or a.viewer

    from ubrain.extras.clip import CLIP
    pictures = sorted((find_body() / "scenes" / "gallery_cc0").glob("*.png"))
    names = [p.stem.split("_", 1)[1] for p in pictures]
    clip = CLIP("image")
    # a recognising sense (snap): what it reports is the known picture nearest the glance
    sense = Sense.fit(clip, pictures, d=D, snap=True)
    print(certify(clip, pictures, d=D, ks=(4, 8, 12, 16, 21), n_trials=2000).summary(), flush=True)

    rec = Recorder(pictures, names) if a.record else None
    proc, _ = _start_body(a.port, viewer=a.viewer, head_camera=True, gallery=True)
    try:
        client = None
        for _ in range(50):
            try:
                client = BodyClient("127.0.0.1", a.port)
                break
            except OSError:
                time.sleep(0.2)
        hello = client.hello
        m = manifest_from_hello_03(hello).with_channels(
            Channel("recall", "event", 64), Channel("boundary", "event", 1),
            Channel("memory", "command", D), Channel("remembered", "choice", len(pictures)))
        brain = Brain(profile("explorer"), m, codecs={"camera": sense}, rng=np.random.default_rng(0))
        state = client.reset(0)
        goal = (a.vx, 0.0, 0.0)
        stored, glances, run, run_of = [], 0, 0, None
        n_ticks = int(a.seconds * 50)
        t0 = time.perf_counter()
        for t in range(n_ticks):
            senses = senses_from_state_03(state) | {"goal": goal}
            frame = senses.pop("camera", None)
            if frame is not None:
                glances += 1
                half, spread, side = fovea(frame)
                code = sense.raw([half])[0]
                fam = sense.vocabulary @ code
                guess = names[int(np.argmax(fam))]
                # Event segmentation: a thing counts as seen once the same picture has
                # been recognised on STEADY glances running, and is written once.
                run, run_of = (run + 1, run_of) if guess == run_of else (1, guess)
                new = spread >= MIN_STD and run == STEADY and guess not in stored
                if a.verbose:
                    print(f"  t={t:5d} {side:5s} spread {spread:5.1f} familiar {float(fam.max()):+.2f} "
                          f"looks like {guess:10s} run {run} {'STORE' if new else ''}", flush=True)
                if new:
                    senses["camera"] = half
                    stored.append(guess)
                if rec is not None:
                    rec.glance(frame, side, guess, run, stored, t)
            if not state["upright"]:
                print(f"fell at tick {t}", flush=True)
                break
            action = brain.tick(senses)
            state = client.act(*act_03(m, action), want_image=(t + 1) % GLANCE == 0,
                               image_size=(224, 224))
            if realtime:
                lag = t0 + (t + 1) / 50 - time.perf_counter()
                if lag > 0:
                    time.sleep(lag)
        ep = brain.regions["hippocampus.episode"]
        recalled = []
        for i in range(ep.n):
            out = brain.tick({"recall": i})
            recalled.append(names[out["remembered"]])
        dt = time.perf_counter() - t0
        client.close()
    finally:
        kill_tree(proc)

    print(f"\nwalked {t + 1} ticks ({(t + 1) / 50:.0f} s simulated, {dt:.0f} s wall), "
          f"{glances} glances, {len(stored)} written into one episode")
    print("written :", " ".join(stored))
    print("recalled:", " ".join(recalled))
    print("standing:", " ".join(names))
    same = sum(x == y for x, y in zip(stored, recalled))
    print(f"recall of what was written: {same}/{len(stored)} slots")
    print(f"the walk's memory against the gallery's order: {lcs(recalled, names)}/{len(names)} "
          "pictures in order")
    if rec is not None:
        rec.recall(stored, recalled)
        print("video:", rec.save(Path(a.record)), f"({len(rec.frames)} frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

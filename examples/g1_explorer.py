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
    """The demonstration video. While walking it keeps each glance (the head camera's
    frame, the attended half, what CLIP takes it for, the episode so far) with the
    body's tick. At the end it composes, at 25 frames a second, the robot seen from a
    camera following it (recorded by the body: --record-chase) beside its mind: the
    eye with its attended half boxed, CLIP's guess, and the memory filling up; then
    the recall, slot by slot. Without the follow camera it writes the eye-only video.
    MP4 through imageio[ffmpeg] when installed, else an animated GIF (Pillow alone)."""

    W, H = 1600, 900
    FPS = 25

    def __init__(self, pictures, names):
        from PIL import Image, ImageDraw, ImageFont
        self.Image, self.ImageDraw = Image, ImageDraw
        self.pics = {n: Image.open(p).convert("RGB") for p, n in zip(pictures, names)}
        try:
            self.big = ImageFont.load_default(size=30)
            self.font = ImageFont.load_default(size=24)
            self.small = ImageFont.load_default(size=15)
        except TypeError:                                  # Pillow < 10.1
            self.big = self.font = self.small = ImageFont.load_default()
        self.glances: list[dict] = []
        self.written: list[str] = []
        self.recalled: list[str] = []
        self.frames: list = []

    def glance(self, frame, side, guess, run, stored, tick):
        self.glances.append({"tick": int(tick), "frame": frame, "side": side, "guess": guess,
                             "run": run, "stored": list(stored)})

    def recall(self, stored, recalled):
        self.written, self.recalled = list(stored), list(recalled)

    # -- drawing ---------------------------------------------------------------
    def _thumb(self, name, size):
        return self.pics[name].resize((size, size))

    def _strip(self, im, d, names, y, size=66, title="memory: one episode, written as it walks"):
        d.text((40, y - 26), title, fill=(190, 190, 190), font=self.small)
        for i, n in enumerate(names):
            x = 40 + i * (size + 8)
            im.paste(self._thumb(n, size), (x, y))
            d.text((x, y + size + 2), f"{i}:{n}"[:11], fill=(210, 210, 210), font=self.small)

    def _mind(self, im, d, g, x0=1040, y0=70, eye=360):
        d.text((x0, y0 - 40), "the robot's eye", fill=(230, 230, 230), font=self.font)
        im.paste(self.Image.fromarray(g["frame"]).resize((eye, eye)), (x0, y0))
        bx = x0 if g["side"] == "left" else x0 + eye // 2
        d.rectangle([bx, y0, bx + eye // 2, y0 + eye], outline=(255, 210, 0), width=4)
        d.text((x0, y0 + eye + 14), "CLIP: looks like", fill=(180, 180, 180), font=self.font)
        d.text((x0, y0 + eye + 46), f"{g['guess']}   ({g['run']}/{STEADY} steady)",
               fill=(255, 210, 0), font=self.font)
        im.paste(self._thumb(g["guess"], 120), (x0 + eye - 120, y0 + eye + 14))

    def _walk_frame(self, chase, tick, g):
        im = self.Image.new("RGB", (self.W, self.H), (18, 22, 30))
        d = self.ImageDraw.Draw(im)
        d.text((40, 24), f"Unitree G1 with an untrained brain   t = {tick / 50:5.1f} s",
               fill=(235, 235, 235), font=self.big)
        im.paste(self.Image.fromarray(chase).resize((960, 540)), (40, 70))
        if g is not None:
            self._mind(im, d, g)
        self._strip(im, d, g["stored"] if g else [], 680)
        return np.asarray(im)

    def _recall_frames(self):
        out = []
        for k in range(len(self.recalled) + 1):
            im = self.Image.new("RGB", (self.W, self.H), (18, 22, 30))
            d = self.ImageDraw.Draw(im)
            d.text((40, 24), "Walk over. A cue recalls each slot of the one episode:",
                   fill=(235, 235, 235), font=self.big)
            self._strip(im, d, self.written, 180, size=66, title="written while walking")
            self._strip(im, d, self.recalled[:k], 420, size=66, title="recalled from the episode")
            if k == len(self.recalled):
                same = sum(a == b for a, b in zip(self.written, self.recalled))
                d.text((40, 620), f"{same} of {len(self.written)} recalled exactly; seen once, never trained.",
                       fill=(255, 210, 0), font=self.font)
            hold = self.FPS * (3 if k == len(self.recalled) else 1) // 2
            out += [np.asarray(im)] * hold
        return out

    def compose(self, chase_base: str | None) -> int:
        """Build the frames; returns how many came from the follow camera."""
        import json
        meta = Path(chase_base + ".json") if chase_base else None
        if meta is not None and meta.is_file():
            info = json.loads(meta.read_text(encoding="utf-8"))
            w, h, ticks = info["width"], info["height"], info["ticks"]
            raw = np.fromfile(chase_base + ".rgb", dtype=np.uint8)
            chase = raw.reshape(len(ticks), h, w, 3)
            gi = -1
            for i, tick in enumerate(ticks):
                while gi + 1 < len(self.glances) and self.glances[gi + 1]["tick"] <= tick:
                    gi += 1
                self.frames.append(self._walk_frame(chase[i], tick, self.glances[gi] if gi >= 0 else None))
            n_chase = len(ticks)
        else:                                          # the eye alone, one frame per glance
            for g in self.glances:
                im = self.Image.new("RGB", (self.W, self.H), (18, 22, 30))
                d = self.ImageDraw.Draw(im)
                self._mind(im, d, g, x0=40, y0=70, eye=560)
                self._strip(im, d, g["stored"], 760)
                self.frames += [np.asarray(im)] * (self.FPS // 5)
            n_chase = 0
        self.frames += self._recall_frames()
        return n_chase

    def save(self, path: Path) -> Path:
        path = Path(path)
        try:
            import imageio.v2 as iio
            # quality 5: about 5 MB for a 45-second walk at 1600x900, light enough for a web page
            iio.mimwrite(path.with_suffix(".mp4"), self.frames, fps=self.FPS, macro_block_size=8,
                         quality=5)
            return path.with_suffix(".mp4")
        except Exception:
            ims = [self.Image.fromarray(f).resize((800, 450)) for f in self.frames[::5]]
            ims[0].save(path.with_suffix(".gif"), save_all=True, append_images=ims[1:],
                        duration=int(5000 / self.FPS), loop=0)
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
    chase = str(Path(a.record).resolve()) + "_chase" if a.record else None
    proc, _ = _start_body(a.port, viewer=a.viewer, head_camera=True, gallery=True, record_chase=chase)
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
                    rec.glance(frame, side, guess, run, stored, state["tick"])
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
        if chase:                                  # the body writes its recording as the session ends
            for _ in range(100):
                if Path(chase + ".json").is_file():
                    break
                time.sleep(0.1)
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
        n_chase = rec.compose(chase)
        print("video:", rec.save(Path(a.record)), f"({len(rec.frames)} frames, "
              f"{n_chase} from the follow camera)")
        for ext in (".rgb", ".json"):                  # the raw recording, now in the video
            Path(chase + ext).unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

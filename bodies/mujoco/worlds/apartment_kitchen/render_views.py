"""Render one view of each of the kitchen's appliances -- what a walker on the line sees
when it looks at it -- into `views/`, for the eyes' vocabulary (2026-10-26, W2).

    cd bodies/mujoco && uv run python -m worlds.apartment_kitchen.render_views

The world's pictures are their own image files; an appliance has none, so its "file" is
a rendering from the world itself: from a point on the walking line a little before it,
at head height, aimed at it with a narrow field (a fovea's crop). These files are part of
the world (hashed into its digest) and are made once, deterministically.
"""

from __future__ import annotations

from pathlib import Path

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
VIEWS = HERE / "views"
SIZE = 224
ALSO = (2.0, 1.5)                        # the walker's earlier views, metres before it
BACK, HEAD_Z, FOVY = 1.0, 1.25, 55.0     # the view: 1 m before it on the line, at head height
                                         # (0.5 m showed the fridge as red surface only)


def main(argv=None) -> int:
    import argparse
    import worlds
    from body.sim import MujocoSim
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--kitchen", type=Path, default=None, help="another exported kitchen folder (trial)")
    ap.add_argument("--out", type=Path, default=None, help="where its views go (trial)")
    a = ap.parse_args(argv)
    global VIEWS
    if a.kitchen is not None:
        from worlds.apartment_kitchen import make
        w = make(a.kitchen, "views")
        VIEWS = a.out or (a.kitchen / "views")
    else:
        w = worlds.get("apartment_kitchen")
    sim = MujocoSim("g1", world=w)
    m, d = sim.model, sim.data
    m.vis.global_.fovy = FOVY
    mujoco.mj_forward(m, d)
    r = mujoco.Renderer(m, SIZE, SIZE)
    VIEWS.mkdir(exist_ok=True)
    for t in w.things:
        if t.kind != "appliance":
            continue
        # the canonical view (BACK m before it), then the walker's earlier views of it
        # (`name@2.0.png`, ...): the eyes average a thing's views into one prototype
        for back, fname in [(BACK, f"{t.name}.png")] + [(b, f"{t.name}@{b:.1f}.png") for b in ALSO]:
            eye = np.array([t.x - back, 0.0, HEAD_Z])
            target = np.array([t.x, t.y, t.z])
            v = target - eye
            cam = mujoco.MjvCamera()
            cam.type = mujoco.mjtCamera.mjCAMERA_FREE
            cam.lookat[:] = target
            cam.distance = float(np.linalg.norm(v))
            cam.azimuth = float(np.degrees(np.arctan2(v[1], v[0])))
            cam.elevation = float(np.degrees(np.arctan2(v[2], np.hypot(v[0], v[1]))))
            r.update_scene(d, camera=cam)
            _save_png(VIEWS / fname, r.render())
        print(f"{t.name:11s} at ({t.x:.2f}, {t.y:+.2f}, {t.z:.2f}) -> views/{t.name}.png + {len(ALSO)} more")
    r.close()
    sim.close()
    return 0


def _save_png(path: Path, img: np.ndarray) -> None:
    """A PNG writer with the standard library only (the body's environment has no pillow)."""
    import struct
    import zlib
    h, w, _ = img.shape
    raw = b"".join(b"\x00" + np.ascontiguousarray(img[y]).tobytes() for y in range(h))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    path.write_bytes(png)


if __name__ == "__main__":
    raise SystemExit(main())

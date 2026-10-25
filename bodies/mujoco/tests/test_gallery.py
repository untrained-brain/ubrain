"""The gallery scene: picture panels along the walking line, seen by the head
camera and felt by nothing."""

from pathlib import Path

import mujoco
import numpy as np
import pytest

from body.manifest import gallery_digest, manifest, manifest_digest
from body.sim import MujocoSim, gallery_layout

SCENES = Path(__file__).resolve().parents[1] / "scenes" / "gallery_cc0"


def _images(tmp_path, n=6):
    """Pictures for the gallery: the body's own CC0 pictures when present, else
    small PNGs written here (a PNG is all a texture needs)."""
    found = sorted(SCENES.glob("*.png"))[:n]
    if len(found) == n:
        return [str(f) for f in found]
    import struct
    import zlib
    out = []
    for i in range(n):
        w = h = 8
        raw = b"".join(b"\x00" + bytes([(40 * i) % 256, 100, 200]) * w for _ in range(h))
        png = b"\x89PNG\r\n\x1a\n"
        for tag, data in ((b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)),
                          (b"IDAT", zlib.compress(raw)), (b"IEND", b"")):
            png += struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))
        f = tmp_path / f"p{i}.png"
        f.write_bytes(png)
        out.append(str(f))
    return out


def test_the_panels_are_felt_by_nothing(tmp_path):
    sim = MujocoSim("g1", gallery=_images(tmp_path))
    ids = [mujoco.mj_name2id(sim.model, mujoco.mjtObj.mjOBJ_GEOM, f"gallery_panel{i}") for i in range(6)]
    assert all(i >= 0 for i in ids)
    assert all(sim.model.geom_contype[i] == 0 and sim.model.geom_conaffinity[i] == 0 for i in ids)
    assert all(sim.model.geom_bodyid[i] == 0 for i in ids)          # the world body: no mass


def test_walking_physics_are_the_default_scenes_exactly(tmp_path):
    """The same seed and the same commands give the same body, tick for tick."""
    a = MujocoSim("g1", seed=3)
    b = MujocoSim("g1", seed=3, gallery=_images(tmp_path))
    rng = np.random.default_rng(0)
    for _ in range(200):
        ctrl = a.home_ctrl + 0.05 * rng.standard_normal(a.nu)
        a.step(ctrl)
        b.step(ctrl)
    assert np.array_equal(a.data.qpos, b.data.qpos) and np.array_equal(a.data.qvel, b.data.qvel)


def test_the_gallery_is_part_of_the_bodys_identity(tmp_path):
    imgs = _images(tmp_path)
    assert gallery_digest(None) == "none"
    d0 = manifest_digest(manifest("g1"))
    d1 = manifest_digest(manifest("g1", gallery=imgs))
    d2 = manifest_digest(manifest("g1", gallery=imgs[:3]))
    assert len({d0, d1, d2}) == 3


def test_the_layout_alternates_sides_and_marches_ahead():
    lay = gallery_layout(4)
    assert [round(y, 3) for _, y, _ in lay] == [0.65, -0.65, 0.65, -0.65]
    assert all(yaw * y > 0 for _, y, yaw in lay)       # each turned toward the walker
    assert all(lay[i + 1][0] > lay[i][0] for i in range(3))


def test_the_bridge_announces_its_gallery(tmp_path):
    from body.bridge import BodyServer
    imgs = _images(tmp_path, n=4)
    srv = BodyServer(port=0, gallery=imgs)
    try:
        h = srv.hello()
        assert [g["index"] for g in h["gallery"]] == [0, 1, 2, 3]
        assert h["gallery"][1]["y"] < 0 < h["gallery"][0]["y"]
        plain = BodyServer(port=0)
        assert plain.hello()["gallery"] == []
        plain.shutdown()
    finally:
        srv.shutdown()

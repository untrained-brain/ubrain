import json

import numpy as np
import pytest

from body import protocol
from body.bridge import BodyServer
from body.client import BodyClient, decode_image
from body.sensors import PRIVILEGED


@pytest.fixture(scope="module")
def server():
    srv = BodyServer(port=0, seed=0).start()
    yield srv
    srv.shutdown()


def test_hello_carries_identity_and_layout(server):
    with BodyClient(server.host, server.port) as c:
        h = c.hello
        assert h["protocol"] == protocol.PROTOCOL_VERSION == "0.4"
        assert h["simulator"] == "mujoco" and h["robot"] == "g1"
        assert h["manifest"]["robot"] == "g1" and h["manifest"]["simulator"] == "mujoco"
        assert h["control_hz"] == 50
        assert h["manifest_digest"] == server.digest
        assert h["proprio_dim"] == 70 and h["contact_dim"] == 12
        assert [p["name"] for p in h["primitives"]] == ["stand", "pose", "sway", "walk", "walk_offset", "to_door", "to_wall", "turn_left", "turn_right", "turn_around", "door_left", "door_right"]


def test_reset_and_act_round_trip(server):
    with BodyClient(server.host, server.port) as c:
        s0 = c.reset(seed=5)
        assert s0["tick"] == 0 and len(s0["proprio"]) == 70 and s0["upright"]
        s1 = c.act("stand")
        assert s1["tick"] == 1 and s1["contact"] is None and s1["image"] is None
        s2 = c.act(2, [0.2, 50], want_contact=True)
        assert s2["tick"] == 2 and len(s2["contact"]) == 12
        assert s2["manifest_digest"] == server.digest


def test_reset_is_reproducible_across_connections(server):
    def run():
        with BodyClient(server.host, server.port) as c:
            c.reset(seed=11)
            for _ in range(30):
                s = c.act("sway", [0.25, 30])
            return np.array(s["proprio"])
    assert np.array_equal(run(), run())


def test_no_privileged_word_ever_crosses_the_bridge(server):
    with BodyClient(server.host, server.port) as c:
        blobs = [json.dumps(c.hello), json.dumps(c.reset(0)),
                 json.dumps(c.act("stand", want_contact=True))]
    for word in PRIVILEGED:
        for b in blobs:
            assert word not in b, word
    # and the protocol offers no request type that could ask for it: `world` (0.3)
    # changes the world and answers with nothing but its own receipt
    assert set(protocol.REQUEST_TYPES) == {"reset", "act", "close", "world"}
    with BodyClient(server.host, server.port) as c:
        c.reset(0)
        ok = c._send({"type": "world", "tone": True,
                      "push": {"force": [100.0, 0.0], "delay": 0, "ticks": 1}})
    assert set(ok) == {"type", "tick"} and ok["type"] == "ok"


def test_malformed_requests_return_errors_not_death(server):
    with BodyClient(server.host, server.port) as c:
        with pytest.raises(RuntimeError):
            c.act(99)
        with pytest.raises(RuntimeError):
            c.act("sway", [0.1])
        # the body is still alive afterwards
        assert c.act("stand")["tick"] >= 1


def test_image_request_renders_or_is_reported():
    try:
        srv = BodyServer(port=0, seed=0, head_camera=True).start()
    except Exception as e:
        pytest.skip(f"head camera model unavailable: {e}")
    try:
        with BodyClient(srv.host, srv.port) as c:
            assert c.hello["has_head_camera"]
            c.reset(0)
            try:
                s = c.act("stand", want_image=True, image_size=(48, 64))
            except RuntimeError as e:  # renderer unavailable in this session
                pytest.skip(f"renderer unavailable: {e}")
            shape, raw = decode_image(s["image"])
            img = np.frombuffer(raw, dtype=np.uint8).reshape(shape)
            assert img.shape == (48, 64, 3)
    finally:
        srv.shutdown()


def test_the_follow_camera_records_frames_and_their_ticks(tmp_path):
    """--record-chase: raw frames and their ticks, written when the session ends;
    nothing of it reaches a reply."""
    import json
    rec = str(tmp_path / "walk")
    srv = BodyServer(port=0, seed=0, record_chase=rec, chase_every=2).start()
    try:
        with BodyClient(srv.host, srv.port) as c:
            c.reset(0)
            for _ in range(8):
                s = c.act("stand")
                assert "chase" not in json.dumps(s)
    except RuntimeError as e:
        srv.shutdown()
        pytest.skip(f"renderer unavailable: {e}")
    srv.shutdown()
    meta = json.loads((tmp_path / "walk.json").read_text())
    n = len(meta["ticks"])
    assert n == 4 and all(t % 2 == 0 for t in meta["ticks"])
    assert (tmp_path / "walk.rgb").stat().st_size == n * meta["width"] * meta["height"] * 3


def test_the_pose_record_is_the_experimenters_and_never_a_reply(tmp_path):
    """--record-pose: one "tick x y yaw" line per tick to the experimenter's file (for
    scoring an arrival); the replies stay as they were."""
    path = tmp_path / "pose.txt"
    srv = BodyServer(port=0, seed=0, record_pose=str(path)).start()
    try:
        with BodyClient(srv.host, srv.port) as c:
            c.reset(0)
            replies = [c.act("walk", [0.5, 0.0, 0.0]) for _ in range(20)]
    finally:
        srv.shutdown()
    rows = [line.split() for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 20 and all(len(r) == 4 for r in rows)
    assert [int(r[0]) for r in rows] == [r["tick"] for r in replies]
    assert all("pose" not in json.dumps(r) for r in replies)

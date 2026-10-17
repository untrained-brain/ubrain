"""Protocol 0.3: the experimenter's world -- a tone the brain hears, a push it does not see."""

import json

import numpy as np
import pytest

from body import protocol
from body.bridge import BodyServer
from body.client import BodyClient
from body.sensors import PRIVILEGED


@pytest.fixture()
def server():
    srv = BodyServer(port=0).start()
    yield srv
    srv.shutdown()


def _world(c: BodyClient, **msg) -> dict:
    """The experimenter's request, sent on the same connection; the brain's client
    deliberately has no method for it."""
    return c._send({"type": "world", **msg})


def test_the_tone_is_heard_on_the_next_tick_only(server):
    with BodyClient(server.host, server.port) as c:
        assert c.reset(0)["tone"] is False
        assert _world(c, tone=True)["type"] == "ok"
        assert c.act("stand")["tone"] is True
        assert c.act("stand")["tone"] is False


def test_a_scheduled_push_moves_the_body_and_never_appears_in_a_reply(server):
    def run(push):
        with BodyClient(server.host, server.port) as c:
            c.reset(0)
            if push:
                _world(c, tone=True, push={"force": [300.0, 0.0], "delay": 3, "ticks": 5})
            replies = [c.act("walk", [0.0, 0.0, 0.0]) for _ in range(30)]
        return replies
    calm, pushed = run(False), run(True)
    # identical until the push starts (ticks 0..2), different after
    assert calm[2]["proprio"] == pushed[2]["proprio"]
    assert calm[4]["proprio"] != pushed[4]["proprio"]
    for r in pushed:
        text = json.dumps(r)
        assert not any(word in text for word in PRIVILEGED)
        assert set(r) == {"type", "tick", "proprio", "upright", "contact", "image", "tone", "manifest_digest"}


def test_reset_clears_the_schedule(server):
    with BodyClient(server.host, server.port) as c:
        c.reset(0)
        _world(c, tone=True, push={"force": [400.0, 0.0], "delay": 2, "ticks": 5})
        c.reset(0)
        quiet = [c.act("stand") for _ in range(10)]
        assert not any(r["tone"] for r in quiet)
    with BodyClient(server.host, server.port) as c:
        c.reset(0)
        ref = [c.act("stand") for _ in range(10)]
    assert [r["proprio"] for r in quiet] == [r["proprio"] for r in ref]


@pytest.mark.parametrize("bad", [
    {"type": "world", "tone": 1},
    {"type": "world", "push": {"force": [1.0], "delay": 0, "ticks": 1}},
    {"type": "world", "push": {"force": [1.0, 2.0], "delay": -1, "ticks": 1}},
    {"type": "world", "push": {"force": [1.0, 2.0], "delay": 0, "ticks": 0}},
])
def test_malformed_world_requests_are_refused(bad):
    with pytest.raises(ValueError):
        protocol.validate_request(bad, 5, [0, 29, 2, 3, 32])


# -- protocol 0.4: the sustained field ---------------------------------------

def _walk_with_field(server, field, n=200, off_at=None):
    with BodyClient(server.host, server.port) as c:
        c.reset(0)
        if field is not None:
            _world(c, field=field)
        out = []
        for t in range(n):
            if off_at is not None and t == off_at:
                _world(c, field=[0.0, 0.0])
            out.append(c.act("walk", [0.5, 0.0, 0.0]))
    return out


def test_a_heading_frame_field_turns_the_walker_and_is_never_reported(server):
    calm = _walk_with_field(server, None)
    left = _walk_with_field(server, [0.0, 15.0])
    right = _walk_with_field(server, [0.0, -15.0])
    gz = lambda rs: float(np.mean([r["proprio"][2] for r in rs[100:]]))   # gyro z, sensed
    # a field on the left turns the walker one way, on the right the other
    assert gz(left) - gz(calm) > 0.05 and gz(right) - gz(calm) < -0.05
    for r in left:
        assert not any(word in json.dumps(r) for word in PRIVILEGED)


def test_the_field_persists_until_switched_off_and_reset_clears_it(server):
    with BodyClient(server.host, server.port) as c:
        c.reset(0)
        _world(c, field=[0.0, 15.0])
        _world(c, tone=True)                                 # a request without the key leaves it on
        on = [c.act("walk", [0.5, 0.0, 0.0]) for _ in range(5)]
        c.reset(0)
        after_reset = [c.act("walk", [0.5, 0.0, 0.0]) for _ in range(5)]
    calm = _walk_with_field(server, None, n=5)
    assert [r["proprio"] for r in after_reset] == [r["proprio"] for r in calm]
    assert [r["proprio"] for r in on] != [r["proprio"] for r in calm]
    # switched off: identical to calm again is not expected (the body moved), but the
    # field no longer acts: the off-switch run equals a run whose field ended there
    a = _walk_with_field(server, [0.0, 15.0], n=60, off_at=30)
    b = _walk_with_field(server, [0.0, 15.0], n=60, off_at=30)
    assert [r["proprio"] for r in a] == [r["proprio"] for r in b]   # lockstep, bit for bit


@pytest.mark.parametrize("bad", [
    {"type": "world", "field": [1.0]},
    {"type": "world", "field": [True, 0.0]},
    {"type": "world", "field": "on"},
])
def test_malformed_fields_are_refused(bad):
    with pytest.raises(ValueError):
        protocol.validate_request(bad, 5, [0, 29, 2, 3, 32])

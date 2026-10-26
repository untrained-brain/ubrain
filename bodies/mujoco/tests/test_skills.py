"""W4: the navigation skills -- frozen, the body's own; the brain chooses which and in what
order. Each skill driven through the bridge, as a client would, to its `done`; no pose
ever in the client's hands."""

import numpy as np

from body.bridge import BodyServer
from body.client import BodyClient


def _run(c, srv, name: str, limit: int = 3000):
    for t in range(limit):
        st = c.act(name)
        if st["skill"]["done"] and st["skill"]["skill"] == name:
            return st, t
        assert st["upright"], f"{name} fell at tick {t}"
    raise AssertionError(f"{name} not done in {limit} ticks")


def _pose(srv):
    return srv.sim.navigator.pose()


def test_a_route_with_choices_through_the_apartment():
    """hall -> living -> the bedroom's door on the left -> bedroom; turn around -> back
    into the living room."""
    srv = BodyServer(port=0, world="apartment").start()
    try:
        with BodyClient("127.0.0.1", srv.port) as c:
            c.reset(0)
            w = srv.sim.world
            _run(c, srv, "to_door")                                  # through the hall's door
            x, y, _ = _pose(srv)
            assert w.room_of(x, y) == "living"
            c.act("stand")
            _run(c, srv, "door_left")                                # on to the bedroom's door, in
            assert abs(_pose(srv)[2] - np.pi / 2) < 0.1
            x, y, _ = _pose(srv)
            assert w.room_of(x, y) == "bedroom", (x, y)
            c.act("stand")
            _run(c, srv, "turn_around")
            assert abs(abs(_pose(srv)[2]) - np.pi / 2) < 0.1
            c.act("stand")
            _run(c, srv, "to_door")
            x, y, _ = _pose(srv)
            assert w.room_of(x, y) == "living", (x, y)
    finally:
        srv.shutdown()


def test_to_wall_stops_short_of_the_wall_and_the_state_reports_the_skill():
    srv = BodyServer(port=0, world="apartment").start()
    try:
        with BodyClient("127.0.0.1", srv.port) as c:
            c.reset(0)
            st = c.act("to_wall")
            assert st["skill"] == {"skill": "to_wall", "done": False}
            _run(c, srv, "to_wall")
            x, y, _ = _pose(srv)
            hall = srv.sim.world.rooms[0]
            assert 0.6 < hall.x1 - x < 1.4 and srv.sim.world.room_of(x, y) == "hall"
    finally:
        srv.shutdown()


def test_a_route_is_skills_only_hall_to_bath():
    """to_door (into the living room), to_door (into the study), door_right (the bath)."""
    srv = BodyServer(port=0, world="apartment").start()
    try:
        with BodyClient("127.0.0.1", srv.port) as c:
            c.reset(0)
            for skill in ("to_door", "to_door", "door_right"):
                _run(c, srv, skill)
                c.act("stand")
            x, y, _ = _pose(srv)
            assert srv.sim.world.room_of(x, y) == "bath", (x, y)
    finally:
        srv.shutdown()

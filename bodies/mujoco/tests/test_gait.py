"""The frozen locomotion policy as the G1's `walk` primitive (robots/g1/gait.py)."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from body import protocol
from body.bridge import BodyServer
from body.client import BodyClient
from body.primitives import Controller, by_name
from body.sim import MujocoSim
from robots.g1.gait import LEG_KP, POLICY_FILE, LocomotionPolicy

import robots

G1 = robots.get("g1")
WALK = by_name("walk", G1).index
WALK_OFF = by_name("walk_offset", G1).index
STAND = by_name("stand", G1).index


def test_weights_are_the_recorded_file():
    prov = json.loads((Path(POLICY_FILE).parent / "PROVENANCE.json").read_text())
    assert hashlib.sha256(Path(POLICY_FILE).read_bytes()).hexdigest() == prov["npz_sha256"]
    assert (Path(POLICY_FILE).parent / "LICENSE").read_text().startswith("BSD 3-Clause License")


def test_numpy_policy_matches_torch():
    pol = LocomotionPolicy()
    x, y = pol.parity
    out = np.stack([pol.step(xi) for xi in x])
    assert np.abs(out - y).max() < 1e-4


@pytest.fixture()
def body():
    s = MujocoSim("g1", seed=0)
    yield s, Controller(s)
    s.close()


def _walk(s, ctl, ticks, params, prim=WALK):
    for _ in range(ticks):
        s.step(ctl.ctrl(prim, params, s.tick))
        assert s.upright()


def test_walks_ten_metres_at_half_a_metre_per_second(body):
    s, ctl = body
    _walk(s, ctl, 1000, [0.5, 0.0, 0.0])
    assert s.data.qpos[0] > 9.0 and abs(s.data.qpos[1]) < 1.0


def test_stands_in_place_on_a_zero_command(body):
    s, ctl = body
    _walk(s, ctl, 500, [0.0, 0.0, 0.0])
    assert np.hypot(*s.data.qpos[:2]) < 0.6


def test_gains_are_the_policys_while_walking_and_restored_after(body):
    s, ctl = body
    kp0 = s.model.actuator_gainprm[:12, 0].copy()
    ctl.ctrl(WALK, [0.0, 0.0, 0.0], 0)
    assert np.array_equal(s.model.actuator_gainprm[:12, 0], LEG_KP)
    ctl.ctrl(STAND, [], 1)
    assert np.array_equal(s.model.actuator_gainprm[:12, 0], kp0)


def test_zero_offset_is_the_plain_walk():
    runs = []
    for prim, params in ((WALK, [0.4, 0.0, 0.0]), (WALK_OFF, [0.4, 0.0, 0.0] + [0.0] * 29)):
        s = MujocoSim("g1", seed=0)
        ctl = Controller(s)
        _walk(s, ctl, 100, params, prim)
        runs.append(s.data.qpos.copy())
        s.close()
    assert np.array_equal(runs[0], runs[1])


def test_walk_over_the_bridge_is_bit_identical_twice():
    finals = []
    for _ in range(2):
        srv = BodyServer(port=0).start()
        try:
            with BodyClient(srv.host, srv.port) as c:
                c.reset(0)
                for _ in range(100):
                    st = c.act(WALK, [0.4, 0.0, 0.0])
                finals.append(st["proprio"])
        finally:
            srv.shutdown()
    assert finals[0] == finals[1]
    assert protocol.PROTOCOL_VERSION == "0.4"

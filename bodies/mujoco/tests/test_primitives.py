import numpy as np
import pytest

import robots
from body.primitives import Controller, by_name
from body.sim import MujocoSim

G1 = robots.get("g1")


@pytest.fixture(scope="module")
def ctl():
    s = MujocoSim("g1", seed=0)
    yield Controller(s)
    s.close()


def test_codebook_is_the_robots_and_indexed_in_order():
    assert [p.index for p in G1.primitives] == list(range(len(G1.primitives)))
    assert by_name("stand", G1).n_params == 0
    assert by_name("pose", G1).n_params == 29
    assert by_name("sway", G1).n_params == 2
    assert by_name("walk", G1).n_params == 3
    assert by_name("walk_offset", G1).n_params == 32
    assert G1.param_counts == [0, 29, 2, 3, 32, 0, 0, 0, 0, 0, 0, 0]   # W4: seven skills
    with pytest.raises(KeyError):
        by_name("reach", G1)


def test_stand_is_the_keyframe_and_inside_the_ctrl_range(ctl):
    c = ctl.ctrl(0, [], 0)
    assert np.array_equal(c, np.clip(ctl.home, ctl.lo, ctl.hi))
    assert np.all(c >= ctl.lo) and np.all(c <= ctl.hi)


def test_pose_offsets_are_clipped(ctl):
    c = ctl.ctrl(1, np.full(29, 100.0), 0)
    assert np.all(c <= ctl.hi)
    assert np.all(np.isfinite(c))


def test_sway_moves_only_the_waist_yaw(ctl):
    waist = ctl.actuator("waist_yaw_joint")
    c0 = ctl.ctrl(2, [0.3, 40], 0)
    c10 = ctl.ctrl(2, [0.3, 40], 10)  # quarter period: sin = 1
    diff = c10 - c0
    moved = np.flatnonzero(np.abs(diff) > 1e-12)
    assert moved.tolist() == [waist]
    assert abs(diff[waist] - 0.3) < 1e-9


def test_bad_requests_raise(ctl):
    with pytest.raises(ValueError):
        ctl.ctrl(99, [], 0)
    with pytest.raises(ValueError):
        ctl.ctrl(2, [0.1], 0)
    with pytest.raises(ValueError):
        ctl.ctrl(2, [0.1, 0], 0)
    with pytest.raises(RuntimeError):
        ctl.actuator("no_such_joint")

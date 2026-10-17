import numpy as np
import pytest

import robots
from body.primitives import Controller, by_name
from body.sensors import contact_dim, contact_forces, proprio_dim, proprio_layout, proprioception
from body.sim import CONTROL_HZ, PHYSICS_DT, SIMULATOR, SUBSTEPS, MujocoSim

G1 = robots.get("g1")


@pytest.fixture(scope="module")
def sim():
    s = MujocoSim("g1", seed=0)
    yield s
    s.close()


def test_tick_clock():
    assert SIMULATOR == "mujoco"
    assert CONTROL_HZ == 50 and PHYSICS_DT == 0.002 and SUBSTEPS == 10


def test_spec_resolves_by_name_or_passes_through():
    assert robots.get("g1") is G1 and robots.get(G1) is G1
    with pytest.raises(KeyError):
        robots.get("nonesuch")


def test_model_shape(sim):
    assert sim.spec is G1 and sim.robot == "g1"
    assert sim.nu == 29 == G1.n_joints
    assert sim.model.opt.timestep == PHYSICS_DT
    assert sim.key_home >= 0
    assert sim.home_ctrl.shape == (29,)


def test_stand_holds_for_two_seconds(sim):
    sim.reset(0)
    ctl = Controller(sim)
    h0 = sim.base_height
    for _ in range(2 * CONTROL_HZ):
        sim.step(ctl.ctrl(by_name("stand", G1).index, [], sim.tick))
    assert sim.tick == 100
    assert sim.upright(), (sim.torso_up, sim.base_height)
    assert abs(sim.base_height - h0) < 0.05


def test_proprioception_layout(sim):
    v = proprioception(sim)
    assert v.shape == (proprio_dim(G1),) == (70,)
    assert sum(d for _n, d in proprio_layout(G1)) == 70
    assert np.all(np.isfinite(v))
    # standing on the floor: the accelerometers read about g on some axis
    acc = v[3:6]
    assert 5.0 < np.linalg.norm(acc) < 15.0


def test_contact_forces_carry_the_weight_when_standing(sim):
    sim.reset(0)
    ctl = Controller(sim)
    for _ in range(CONTROL_HZ):
        sim.step(ctl.ctrl(0, [], sim.tick))
    c = contact_forces(sim)
    assert c.shape == (contact_dim(G1),) == (12,)
    total_normal = c[0] + c[6]  # contact-frame normal components, summed over feet
    mass = float(sim.model.body_subtreemass[1])  # pelvis subtree = the whole robot
    assert 0.5 * mass * 9.81 < total_normal < 1.5 * mass * 9.81


def test_two_sims_same_seed_same_ctrl_are_bit_identical():
    a, b = MujocoSim(G1, seed=7), MujocoSim("g1", seed=7)
    try:
        ca, cb = Controller(a), Controller(b)
        for _ in range(60):
            a.step(ca.ctrl(2, [0.3, 40], a.tick))
            b.step(cb.ctrl(2, [0.3, 40], b.tick))
        assert np.array_equal(proprioception(a), proprioception(b))
        assert a.tick == b.tick == 60
    finally:
        a.close(); b.close()


def test_push_is_privileged_and_cleared(sim):
    sim.reset(3)
    f = sim.push()
    assert f.shape == (2,)
    assert np.any(sim.data.xfrc_applied != 0)
    sim.clear_push()
    assert not np.any(sim.data.xfrc_applied != 0)


def test_head_camera_renders_or_is_skipped():
    try:
        s = MujocoSim("g1", seed=0, head_camera=True)
    except Exception as e:  # MjSpec camera path unavailable in this MuJoCo build
        pytest.skip(f"head camera model unavailable: {e}")
    try:
        try:
            img = s.render(width=64, height=48)
        except Exception as e:  # no OpenGL context on this machine/session
            pytest.skip(f"renderer unavailable: {e}")
        assert img.shape == (48, 64, 3) and img.dtype == np.uint8
        assert img.std() > 1.0  # not a blank frame
    finally:
        s.close()

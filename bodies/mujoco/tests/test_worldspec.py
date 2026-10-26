"""WorldSpec: the world as a named layer -- built into the model, announced as truth to
the experimenter, keyed into the body's identity, never sent to the brain."""

import json

import mujoco

import worlds
from body.bridge import BodyServer
from body.client import BodyClient
from body.manifest import manifest, manifest_digest
from body.sim import MujocoSim
from body.worldspec import truth, world_digest


def test_the_apartment_builds_rooms_doors_and_things():
    w = worlds.get("apartment")
    assert [r.name for r in w.rooms] == ["hall", "living", "study", "bedroom", "bath"]
    assert len(w.things) == 21 and len(w.slots) == 19 and len(w.junctions) == 4
    hung = [t for t in w.things if t.room]                         # day 0: the first nineteen
    assert [t.index for t in hung] == list(range(19)) and all(w.room_of(t.x, t.y) == t.room for t in hung)
    assert [t.room for t in hung][15:] == ["bedroom", "bedroom", "bath", "bath"]
    sim = MujocoSim("g1", world="apartment", head_camera=True)
    for name in ("wall_left", "door_hall_living_l", "floor_study", "thing0", "thing14"):
        assert mujoco.mj_name2id(sim.model, mujoco.mjtObj.mjOBJ_GEOM, name) >= 0, name
    sim.close()


def test_the_world_is_part_of_the_bodys_identity():
    bare, apt = manifest("g1"), manifest("g1", world="apartment")
    assert bare["world"] == "none" and bare["world_digest"] == "none"
    assert apt["world"] == "apartment" and len(apt["world_digest"]) == 12
    assert manifest_digest(bare) != manifest_digest(apt)
    assert world_digest(worlds.get("apartment")) == apt["world_digest"]
    assert any(k.startswith("world:") for k in apt["licenses"])


def test_the_truth_goes_to_the_experimenter_not_into_the_manifest():
    srv = BodyServer(port=0, world="apartment", head_camera=True).start()
    try:
        with BodyClient("127.0.0.1", srv.port) as c:
            h = c.hello
            assert h["world"]["name"] == "apartment" and len(h["world"]["things"]) == 21
            assert len(h["world"]["slots"]) == 19 and h["world"]["schedule"]["0"] == list(range(19))
            assert "things" not in json.dumps(h["manifest"])            # the brain's record has no truth
    finally:
        srv.shutdown()
    assert truth(None) == {}


def test_the_kitchen_is_the_fourth_room():
    w = worlds.get("apartment_kitchen")
    assert [r.name for r in w.rooms] == ["hall", "living", "study", "kitchen", "bedroom", "bath"]
    assert len(w.junctions) == 5
    names = [t.name for t in w.things if t.kind == "appliance"]
    assert set(names) == {"sink", "dishwasher", "stove", "microwave", "fridge"}
    assert all(w.room_of(t.x, t.y) == "kitchen" for t in w.things if t.kind == "appliance")
    sim = MujocoSim("g1", world="apartment_kitchen")
    assert mujoco.mj_name2id(sim.model, mujoco.mjtObj.mjOBJ_BODY, "kitchen/fridge_main_group_main") >= 0
    assert mujoco.mj_name2id(sim.model, mujoco.mjtObj.mjOBJ_BODY, "kitchen/wall_left_room_main") < 0
    sim.close()


def test_the_line_keeper_is_part_of_the_bodys_identity_and_holds_the_line():
    assert manifest_digest(manifest("g1", harness="keep-line")) != manifest_digest(manifest("g1"))
    srv = BodyServer(port=0, world="apartment", keep_line=True).start()
    try:
        with BodyClient("127.0.0.1", srv.port) as c:
            idx = c.primitives["walk_offset"]["index"]
            n = c.primitives["walk_offset"]["n_params"] - 3
            c.reset(0)
            for _ in range(1000):                                   # 20 s at 0.5 m/s
                st = c.act(idx, [0.5, 0.0, 0.0] + [0.0] * n)
            assert st["upright"]
            assert abs(float(srv.sim.data.qpos[1])) < 0.15         # the line held (W0: 0.40 drift without)
    finally:
        srv.shutdown()


def test_the_change_schedule_rehangs_the_pictures_at_reset():
    import numpy as np
    from body.worldspec import arrangement
    w = worlds.get("apartment")
    d0, d3 = arrangement(w, 0), arrangement(w, 3)
    assert d0 == list(range(19)) and len(set(d3)) == 19 and d3 != d0 and arrangement(w, 3) == d3
    sim = MujocoSim("g1", world="apartment")
    gid = lambda i: mujoco.mj_name2id(sim.model, mujoco.mjtObj.mjOBJ_GEOM, f"thing{i}")
    sim.reset(3)
    for slot, i in zip(w.slots, d3):                                # each of the day's pictures on its hook
        assert np.allclose(sim.model.geom_pos[gid(i)], (slot.x, slot.y, slot.z))
    for i in set(range(21)) - set(d3):                               # the others hidden
        assert sim.model.geom_pos[gid(i)][2] < -5
    sim.reset(0)
    assert np.allclose(sim.model.geom_pos[gid(0)], (w.slots[0].x, w.slots[0].y, w.slots[0].z))
    assert sim.arrangement == d0
    sim.close()

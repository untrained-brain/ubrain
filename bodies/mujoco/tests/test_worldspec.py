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
    assert [r.name for r in w.rooms] == ["hall", "living", "study"]
    assert len(w.things) == 15 and len(w.junctions) == 2
    assert all(w.room_of(t.x, t.y) == t.room for t in w.things)
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
            assert h["world"]["name"] == "apartment" and len(h["world"]["things"]) == 15
            assert "things" not in json.dumps(h["manifest"])            # the brain's record has no truth
    finally:
        srv.shutdown()
    assert truth(None) == {}

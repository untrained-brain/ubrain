import json

import robots
from body import manifest as M


def test_manifest_has_every_keyed_field_and_a_stable_digest():
    m = M.manifest()
    for k in M.KEYED:
        assert k in m and m[k], k
    assert m["simulator"] == "mujoco"
    assert m["robot"] == "g1" and m["menagerie_robot"] == "unitree_g1"
    assert m["mujoco"] == "3.12.0"
    assert m["menagerie_version"] == "2026.9.0"
    assert len(m["menagerie_commit"]) >= 7
    d1 = M.manifest_digest(m)
    d2 = M.manifest_digest(json.loads(json.dumps(m)))
    assert d1 == d2 and len(d1) == 12


def test_platform_is_reported_but_does_not_move_the_digest():
    m = M.manifest()
    m2 = dict(m, platform="somewhere-else")
    assert M.manifest_digest(m) == M.manifest_digest(m2)


def test_robot_and_simulator_move_the_digest():
    m = M.manifest()
    assert M.manifest_digest(dict(m, robot="h1")) != M.manifest_digest(m)
    assert M.manifest_digest(dict(m, simulator="isaac")) != M.manifest_digest(m)
    assert M.manifest_digest(dict(m, robot_digest="000000000000")) != M.manifest_digest(m)


def test_every_model_file_exists_and_a_byte_moves_the_package_digest(tmp_path, monkeypatch):
    for name in M.MODEL_FILES:
        assert (M.PACKAGE_DIR / name).is_file(), name
    before = M.package_digest()
    # copy the package files aside, flip one byte, recompute against the copy
    for name in M.MODEL_FILES:
        (tmp_path / name).write_bytes((M.PACKAGE_DIR / name).read_bytes())
    p = tmp_path / M.MODEL_FILES[-1]
    p.write_bytes(p.read_bytes() + b"#")
    monkeypatch.setattr(M, "PACKAGE_DIR", tmp_path)
    assert M.package_digest() != before


def test_robot_digest_covers_the_robot_package():
    g1 = robots.get("g1")
    files = M.robot_files(g1)
    assert files and all(f.suffix in M.ROBOT_SUFFIXES for f in files)
    assert files[0].parent.name == "g1"
    # the frozen gait's weights move the digest like code does
    assert any(f.name == "unitree_g1_motion.npz" for f in files)
    assert len(M.robot_digest(g1)) == 12

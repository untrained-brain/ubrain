"""The apartment: the first world with structure (2026-10-26).

Three rooms in a row -- hall, living room, study -- joined by doorways on the walking
line, so a robot walking straight passes through every door; fifteen of the gallery's
CC0 pictures hang in them, five per room, alternately left and right, turned toward the
approaching walker (the gallery's measured geometry: 0.65 m off the line, yaw 0.6).
Solid walls (they collide and they hide the next room until the door), a floor colour
per room. What it adds over the corridor: places that are rooms, things that belong to
a room, doors where the view changes -- the structure "what was in the study?" and the
first junction tasks need. A side room off the living room (a junction with a choice)
is the next step, for rung 4.
"""

from __future__ import annotations

from pathlib import Path

import mujoco
import numpy as np

from body.worldspec import Junction, Room, Thing, WorldSpec

HERE = Path(__file__).resolve().parent
PICTURES = HERE.parents[1] / "scenes" / "gallery_cc0"

ROOM_LEN, HALF_W = 6.0, 1.6           # each room 6 m along the line, 3.2 m wide
DOOR_HALF, WALL_H, WALL_T = 0.6, 2.4, 0.08
X0 = -1.0                             # the hall starts behind the robot's start
PER_ROOM = 5
SIDE, YAW, Z, HALF = 0.65, 0.6, 1.05, 0.45     # the gallery's panel geometry
FLOORS = {"hall": (0.55, 0.50, 0.45), "living": (0.45, 0.52, 0.60), "study": (0.52, 0.58, 0.45)}

ROOMS = tuple(Room(name, X0 + i * ROOM_LEN, -HALF_W, X0 + (i + 1) * ROOM_LEN, HALF_W)
              for i, name in enumerate(("hall", "living", "study")))
_FILES = sorted(PICTURES.glob("*.png"))[:len(ROOMS) * PER_ROOM]


def _things() -> tuple[Thing, ...]:
    out = []
    for k, f in enumerate(_FILES):
        room = ROOMS[k // PER_ROOM]
        j = k % PER_ROOM
        side = 1.0 if k % 2 == 0 else -1.0
        out.append(Thing(index=k, name=f.stem.split("_", 1)[1], kind="picture", room=room.name,
                         x=room.x0 + 1.4 + 1.0 * j, y=side * SIDE, z=Z, yaw=side * YAW, picture=f.name))
    return tuple(out)


JUNCTIONS = tuple(Junction(f"door_{a.name}_{b.name}", a.x1, 0.0, (a.name, b.name))
                  for a, b in zip(ROOMS, ROOMS[1:]))


def _box(parent, name, pos, size, rgba, collide=True):
    g = parent.add_geom()
    g.name, g.type = name, mujoco.mjtGeom.mjGEOM_BOX
    g.pos, g.size, g.rgba = list(pos), list(size), list(rgba)
    if not collide:
        g.contype, g.conaffinity = 0, 0
    return g


def build(mjspec, spec: "WorldSpec") -> None:
    """Walls, doorways, floors and the pictures, added to the robot's model."""
    mjspec.visual.headlight.ambient = [spec.light[0]] * 3
    mjspec.visual.headlight.diffuse = [spec.light[1]] * 3
    wb = mjspec.worldbody
    wall = (0.85, 0.85, 0.82, 1.0)
    x_end = ROOMS[-1].x1
    length = x_end - X0
    for s, sign in (("left", 1.0), ("right", -1.0)):             # the long side walls
        _box(wb, f"wall_{s}", (X0 + length / 2, sign * (HALF_W + WALL_T), WALL_H / 2),
             (length / 2, WALL_T, WALL_H / 2), wall)
    _box(wb, "wall_back", (X0 - WALL_T, 0.0, WALL_H / 2), (WALL_T, HALF_W + 2 * WALL_T, WALL_H / 2), wall)
    _box(wb, "wall_end", (x_end + WALL_T, 0.0, WALL_H / 2), (WALL_T, HALF_W + 2 * WALL_T, WALL_H / 2), wall)
    jamb = (HALF_W - DOOR_HALF) / 2
    for j in spec.junctions:                                    # cross walls with a doorway
        for s, sign in (("l", 1.0), ("r", -1.0)):
            _box(wb, f"{j.name}_{s}", (j.x, sign * (DOOR_HALF + jamb), WALL_H / 2),
                 (WALL_T, jamb, WALL_H / 2), wall)
        _box(wb, f"{j.name}_lintel", (j.x, 0.0, WALL_H - 0.2), (WALL_T, DOOR_HALF, 0.2), wall)
    for r in spec.rooms:                                        # a floor colour per room (visual only)
        _box(wb, f"floor_{r.name}", ((r.x0 + r.x1) / 2, 0.0, 0.001), ((r.x1 - r.x0) / 2, HALF_W, 0.001),
             (*FLOORS[r.name], 1.0), collide=False)
    for t in spec.things:                                       # the pictures (visual only)
        tex = mjspec.add_texture()
        tex.name, tex.type, tex.file = f"thing_tex{t.index}", mujoco.mjtTexture.mjTEXTURE_2D, str(PICTURES / t.picture)
        mat = mjspec.add_material()
        mat.name = f"thing_mat{t.index}"
        mat.textures[mujoco.mjtTextureRole.mjTEXROLE_RGB] = tex.name
        g = _box(wb, f"thing{t.index}", (t.x, t.y, t.z), (0.01, HALF, HALF), (1, 1, 1, 1), collide=False)
        g.quat = [np.cos(t.yaw / 2), 0.0, 0.0, np.sin(t.yaw / 2)]
        g.material = mat.name


SPEC = WorldSpec(
    name="apartment",
    doc=__doc__.split("\n\n")[0],
    package="worlds.apartment",
    rooms=ROOMS,
    things=_things(),
    junctions=JUNCTIONS,
    build=build,
    licenses={"pictures": "CC0 (scenes/gallery_cc0/PROVENANCE.json)", "world": "Apache-2.0"},
    data_files=tuple(str(f) for f in _FILES),
)

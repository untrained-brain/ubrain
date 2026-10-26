"""WorldSpec: the environment as a named layer, beside the robot. Model file.

A body was simulator + robot + an afterthought of a scene. The world gets the robot's
status (2026-10-26, apps/gallery_companion/WORLD.md): a package under `worlds/` exports
a `WorldSpec` -- how to build the scene into the robot's model, the THINGS in it with
their truth (what, where, in which room), its ROOMS and JUNCTIONS (doors: where a choice
is made), and the licences of what it shows. Its digest joins the body's manifest, so
every result and every saved brain names the world it lived in.

The truth is the experimenter's: the bridge announces it in `hello` for the app that
scores the brain (as it announced the gallery), and the brain never receives it -- it
meets the world only through its senses and its primitives.
"""

from __future__ import annotations

import hashlib
import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

__all__ = ["Room", "Thing", "Junction", "Slot", "WorldSpec", "world_files", "world_digest", "truth",
           "arrangement", "arrange"]


@dataclass(frozen=True)
class Room:
    name: str
    x0: float
    y0: float
    x1: float
    y1: float

    def contains(self, x: float, y: float) -> bool:
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1


@dataclass(frozen=True)
class Thing:
    """Something the robot may see: its index (the order the app's vocabulary uses),
    name, kind, room, and pose (x, y, z, yaw). `picture` names the image file shown."""
    index: int
    name: str
    kind: str
    room: str
    x: float
    y: float
    z: float
    yaw: float
    picture: str | None = None
    file: str | None = None        # what shows it to the eyes, relative to the body's root (a
    #                               # picture file, or a view rendered from the world): the
    #                               # experimenter's vocabulary, announced in the truth


@dataclass(frozen=True)
class Junction:
    """A doorway: where the robot passes from one room to another, and where -- with
    more than two exits -- a choice is made."""
    name: str
    x: float
    y: float
    rooms: tuple[str, ...]


@dataclass(frozen=True)
class Slot:
    """A place a thing can stand (a picture's hook): the world's change schedule says which
    thing stands in each slot on a given day (the reset's seed)."""
    x: float
    y: float
    z: float
    yaw: float


HIDDEN_Z = -10.0                       # where a thing not hung today waits (below the floor, unseen)
SCHEDULE_DAYS = 30                     # the schedule announced in the truth


@dataclass(frozen=True)
class WorldSpec:
    name: str
    doc: str
    package: str                                   # "worlds.apartment", for the digest
    rooms: tuple[Room, ...]
    things: tuple[Thing, ...]
    junctions: tuple[Junction, ...]
    build: Callable                                # build(mjspec, spec) adds the scene
    licenses: dict = field(default_factory=dict)
    light: tuple[float, float] = (0.5, 0.8)        # headlight ambient, diffuse
    data_files: tuple[str, ...] = ()               # files outside the package it shows (pictures)
    slots: tuple[Slot, ...] = ()                   # where movable things can stand
    schedule: Callable | None = None               # seed -> the thing index standing in each slot

    def room_of(self, x: float, y: float) -> str | None:
        for r in self.rooms:
            if r.contains(x, y):
                return r.name
        return None


def world_files(spec: WorldSpec) -> tuple[Path, ...]:
    """The world package's code and data, sorted, then the files it shows."""
    root = Path(importlib.import_module(spec.package).__file__).resolve().parent
    own = sorted((p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in (".py", ".json", ".xml", ".png", ".obj", ".stl", ".msh", ".jpg", ".jpeg")
                  and "__pycache__" not in p.parts), key=lambda p: p.relative_to(root).as_posix())
    return tuple(own) + tuple(Path(f) for f in spec.data_files)


def world_digest(spec: WorldSpec | None) -> str:
    """sha256 over the world's files (names relative to the package, then the shown
    files by name), first 12 hex characters; "none" for no world."""
    if spec is None:
        return "none"
    root = Path(importlib.import_module(spec.package).__file__).resolve().parent
    h = hashlib.sha256()
    for p in world_files(spec):
        name = p.relative_to(root).as_posix() if root in p.parents else p.name
        h.update(name.encode())
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()[:12]


def truth(spec: WorldSpec | None) -> dict:
    """The world's truth as plain data, for the experimenter (the app), never the brain."""
    if spec is None:
        return {}
    return {"name": spec.name,
            "rooms": [{"name": r.name, "x0": r.x0, "y0": r.y0, "x1": r.x1, "y1": r.y1} for r in spec.rooms],
            "things": [{"index": t.index, "name": t.name, "kind": t.kind, "room": t.room,
                        "x": t.x, "y": t.y, "z": t.z, "yaw": t.yaw, "file": t.file} for t in spec.things],
            "junctions": [{"name": j.name, "x": j.x, "y": j.y, "rooms": list(j.rooms)} for j in spec.junctions],
            "slots": [{"x": sl.x, "y": sl.y, "z": sl.z, "yaw": sl.yaw} for sl in spec.slots],
            "schedule": {str(d): arrangement(spec, d) for d in range(SCHEDULE_DAYS)} if spec.slots else {},
            "licenses": dict(spec.licenses)}


def arrangement(spec: WorldSpec | None, seed: int) -> list[int]:
    """Which thing stands in each slot on the day `seed` (empty for a world without slots)."""
    if spec is None or not spec.slots or spec.schedule is None:
        return []
    return [int(i) for i in spec.schedule(int(seed))]


def arrange(spec: WorldSpec | None, model, seed: int) -> list[int]:
    """Hang the day's things: each movable thing's geom (named `thing<index>`) is moved to
    its slot, or below the floor when it is not hung today. World state, set at reset -- not
    identity: the schedule is the world's code, so the digest names it already."""
    import mujoco
    arr = arrangement(spec, seed)
    if not arr:
        return arr
    where = {thing: slot for slot, thing in zip(spec.slots, arr)}
    for t in spec.things:
        if t.kind != "picture":
            continue
        gid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, f"thing{t.index}")
        if gid < 0:
            continue
        sl = where.get(t.index)
        if sl is None:
            model.geom_pos[gid] = (0.0, 0.0, HIDDEN_Z)
        else:
            model.geom_pos[gid] = (sl.x, sl.y, sl.z)
            model.geom_quat[gid] = (np.cos(sl.yaw / 2), 0.0, 0.0, np.sin(sl.yaw / 2))
    return arr

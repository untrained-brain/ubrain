"""Navigation skills: frozen, the body's own -- the brain chooses which and in what order,
the body knows how. Model file (2026-10-27, W4).

A skill is a short controller over the walking gait: from the body's pose (its own
odometry, here read from the sim) and the world's map (its doors and rooms -- the frozen
skill's privileged part, as a real robot's would come from seeing the doors), it gives the
walk velocity tick by tick until it is done. The brain never receives a pose or a map; it
chooses skills and feels where they take it.

    to_door       walk straight through the next door ahead, stop 0.9 m past it
    to_wall       walk straight, stop 1.0 m before the wall ahead
    door_left     walk on to the next door on the left, turn, go through it (0.9 m past)
    door_right    ... on the right
    turn_left     turn on the spot to the next quarter to the left
    turn_right    ... to the right
    turn_around   ... half a turn

A skill starts when its primitive is first sent (or sent again after another primitive);
`status()` says which is running and whether it is done. Headings are quarters of a turn
(the apartment's axes), so a forward skill also squares the walk onto its line.
"""

from __future__ import annotations

import numpy as np

__all__ = ["SKILLS", "Navigator"]

SKILLS = ("to_door", "to_wall", "turn_left", "turn_right", "turn_around", "door_left", "door_right")
V_WALK, V_NEAR = 0.5, 0.25                       # m/s; slower within NEAR of the target
NEAR = 0.6
W_TURN = 0.8                                     # rad/s on the spot
YAW_TOL = 0.06                                   # rad: a turn is done within this
GAIN_YAW, GAIN_LAT, W_MAX = 1.5, 1.2, 0.6        # the line-keeper's gains, on the skill's own line
PAST_DOOR, BEFORE_WALL = 0.9, 1.0


def _wrap(a: float) -> float:
    return float((a + np.pi) % (2 * np.pi) - np.pi)


class Navigator:
    def __init__(self, sim) -> None:
        self.sim = sim
        self.active: str | None = None
        self.done = False
        self._last_tick: int | None = None
        self._target = None                      # (x, y) for a forward skill
        self._heading = 0.0                      # the line's direction (a quarter turn)
        self._then: list = []                    # a compound skill's remaining phases

    # -- the body's own pose -------------------------------------------------------
    def pose(self) -> tuple[float, float, float]:
        q = self.sim.data.qpos
        w, x, y, z = (float(v) for v in q[3:7])
        return float(q[0]), float(q[1]), float(np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))

    def _quarter(self, yaw: float) -> float:
        return float(np.round(yaw / (np.pi / 2)) * (np.pi / 2))

    # -- the map ---------------------------------------------------------------------
    def _wall_ahead(self, x: float, y: float, h: float) -> float:
        """Distance along h to the boundary of the room the body stands in."""
        w = self.sim.world
        room = next((r for r in w.rooms if r.contains(x, y)), None) if w is not None else None
        if room is None:
            return 0.0
        c, s = np.cos(h), np.sin(h)
        if abs(c) > 0.5:
            return (room.x1 - x) if c > 0 else (x - room.x0)
        return (room.y1 - y) if s > 0 else (y - room.y0)

    def _door_beside(self, x: float, y: float, h: float, side: float):
        """The nearest door ahead on one side (+1 left, -1 right): a junction whose offset
        from the line is to that side, at the room's edge."""
        w = self.sim.world
        if w is None:
            return None
        c, s = np.cos(h), np.sin(h)
        best = None
        for j in w.junctions:
            dx, dy = j.x - x, j.y - y
            along, lat = dx * c + dy * s, -dx * s + dy * c
            if along > -0.2 and side * lat > 0.9 and (best is None or along < best[0]):
                best = (along, j)
        return None if best is None else best[1]

    def _door_ahead(self, x: float, y: float, h: float):
        """The nearest door straight ahead within the room's reach (lateral 0.9 m)."""
        w = self.sim.world
        if w is None:
            return None
        c, s = np.cos(h), np.sin(h)
        best = None
        for j in w.junctions:
            dx, dy = j.x - x, j.y - y
            along, lat = dx * c + dy * s, -dx * s + dy * c
            if along > 0.3 and abs(lat) < 0.9 and (best is None or along < best[0]):
                best = (along, j)
        return None if best is None else best[1]

    # -- skills ------------------------------------------------------------------------
    def start(self, name: str) -> None:
        if name not in SKILLS:
            raise ValueError(f"unknown skill {name!r}")
        x, y, yaw = self.pose()
        h = self._quarter(yaw)
        self.active, self.done = name, False
        self._then = []
        if name in ("door_left", "door_right"):
            side = 1.0 if name == "door_left" else -1.0
            j = self._door_beside(x, y, h, side)
            if j is None:                         # no such door ahead: done where it stands
                self._target, self._heading, self.done = None, h, True
                return
            c, s = np.cos(h), np.sin(h)
            along = (j.x - x) * c + (j.y - y) * s
            self._target, self._heading = (x + along * c, y + along * s), h     # abreast of the door
            h2 = _wrap(h + side * np.pi / 2)
            self._then = [("turn", h2, None),
                          ("forward", h2, (j.x + PAST_DOOR * np.cos(h2), j.y + PAST_DOOR * np.sin(h2)))]
        elif name == "to_door":
            j = self._door_ahead(x, y, h)
            if j is None:                         # no door ahead: as far as the wall allows
                d = max(0.0, self._wall_ahead(x, y, h) - BEFORE_WALL)
                self._target = (x + d * np.cos(h), y + d * np.sin(h))
            else:
                self._target = (j.x + PAST_DOOR * np.cos(h), j.y + PAST_DOOR * np.sin(h))
            self._heading = h
        elif name == "to_wall":
            d = max(0.0, self._wall_ahead(x, y, h) - BEFORE_WALL)
            self._target, self._heading = (x + d * np.cos(h), y + d * np.sin(h)), h
        else:
            turn = {"turn_left": np.pi / 2, "turn_right": -np.pi / 2, "turn_around": np.pi}[name]
            self._target, self._heading = None, _wrap(h + turn)

    def command(self, name: str, tick: int) -> tuple[float, float, float]:
        """The walk velocity (vx, vy, wz) for this tick of skill `name`."""
        if name != self.active or self._last_tick is None or tick != self._last_tick + 1:
            self.start(name)
        self._last_tick = tick
        if self.done:
            return 0.0, 0.0, 0.0
        x, y, yaw = self.pose()
        e = _wrap(self._heading - yaw)
        if self._target is None:                  # a turn on the spot
            if abs(e) < YAW_TOL:
                return self._next_phase()
            return 0.0, 0.0, float(np.sign(e) * W_TURN)
        c, s = np.cos(self._heading), np.sin(self._heading)
        dx, dy = self._target[0] - x, self._target[1] - y
        left, lateral = dx * c + dy * s, -(dx * -s + dy * c)   # still to go; offset left of the line
        if left <= 0.0:
            return self._next_phase()
        wz = float(np.clip(GAIN_YAW * e - GAIN_LAT * lateral, -W_MAX, W_MAX))
        return (V_NEAR if left < NEAR else V_WALK), 0.0, wz

    def _next_phase(self) -> tuple[float, float, float]:
        """A phase is done: the compound skill's next, or the skill is done."""
        if self._then:
            kind, h, target = self._then.pop(0)
            self._heading, self._target = h, (target if kind == "forward" else None)
        else:
            self.done = True
        return 0.0, 0.0, 0.0

    def status(self) -> dict:
        return {"skill": self.active, "done": bool(self.done)}

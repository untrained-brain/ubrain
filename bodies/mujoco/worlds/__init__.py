"""The worlds a body can live in: one package per world, each exporting `SPEC`, a
`body.worldspec.WorldSpec`. `get("apartment")` resolves a name; a spec passes
through; None is the bare scene. Adding a world is adding a package here and its name
to WORLDS -- `body/` does not change.
"""

from __future__ import annotations

import importlib

from body.worldspec import WorldSpec

__all__ = ["WORLDS", "get"]

WORLDS = ("apartment", "apartment_kitchen")


def get(world: str | WorldSpec | None) -> WorldSpec | None:
    if world is None or isinstance(world, WorldSpec):
        return world
    if world not in WORLDS:
        raise KeyError(f"unknown world {world!r}; have {WORLDS}")
    return importlib.import_module(f"worlds.{world}").SPEC

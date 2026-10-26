"""The apartment with a kitchen: the apartment's three rooms, then -- through a fourth
doorway at the end of the study -- a RoboCasa kitchen (2026-10-26, W0).

The kitchen is RoboCasa365's layout 1, style 2 (a one-wall kitchen: sink, dishwasher,
stove, microwave, fridge along the left wall, cabinets above and below, about 3 x 5.5 m
of floor; style 2 chosen over styles 1-10 by how well CLIP tells its appliances apart,
`apps/gallery_companion/w2_style_trial.py`), exported once in RoboCasa's own environment by
`apps/gallery_companion/w0_export_kitchen.py` into `kitchen_L001_S002/` -- the MJCF and
the 50 files it uses (30.9 MB), copied, with relative paths -- and built here by
`MjSpec.attach` under the body's MuJoCo. Its left wall is removed (the apartment's
doorway wall stands there), the counter-accessory props were left out at export, and the
kitchen is raised 1 mm so its floor does not z-fight the scene's. Its appliances are
things with truth, beside the 15 pictures.

Licences: RoboCasa's code MIT, its assets CC BY 4.0 (RoboCasa, Nasiriany et al.) --
`kitchen_L001_S002/ATTRIBUTION.md`; the pictures CC0.
"""

from __future__ import annotations

import json
from pathlib import Path

import mujoco
import numpy as np

from body.worldspec import Junction, Room, Thing, WorldSpec
from worlds import apartment as A

HERE = Path(__file__).resolve().parent
KITCHEN = HERE / "kitchen_L001_S002"
XML = KITCHEN / "kitchen.xml"

# the kitchen's own frame: x 0..5.6 along the counters, y 0 (counter wall) .. -3.0 (front)
KX = A.ROOMS[-1].x1                    # it starts where the study ends
KY = 1.5                               # its y 0..-3 becomes 1.5..-1.5, the apartment's width
KZ = 0.001                             # above the scene's floor
K_LEN = 5.6
REMOVE = ("wall_left_room_main", "wall_left_backing_room_main")   # the side the doorway replaces
APPLIANCES = ("Sink", "Dishwasher", "Stove", "Microwave", "FridgeBottomFreezer")

ROOMS = A.ROOMS + (Room("kitchen", KX, -A.HALF_W, KX + K_LEN, A.HALF_W),)
JUNCTIONS = tuple(Junction(f"door_{a.name}_{b.name}", a.x1, 0.0, (a.name, b.name))
                  for a, b in zip(ROOMS, ROOMS[1:]))


def _appliances(kitchen: Path = KITCHEN, views: str = "worlds/apartment_kitchen/views") -> tuple[Thing, ...]:
    info = json.loads((kitchen / "export.json").read_text(encoding="utf-8"))
    out, k = [], len(A.SPEC.things)
    # indexed in walking order, as the pictures are (the app's perception check reads index
    # order as the order along the line)
    fixtures = sorted((f for f in info["fixtures"] if f["class"] in APPLIANCES and f["pos"] is not None),
                      key=lambda f: (f["pos"][0], f["pos"][2]))
    for f in fixtures:
        if True:
            x, y, z = f["pos"]
            name = f["class"].lower().replace("bottomfreezer", "")
            out.append(Thing(index=k, name=name, kind="appliance", room="kitchen",
                             x=round(KX + x, 3), y=round(KY + y, 3), z=round(KZ + z, 3), yaw=0.0,
                             file=f"{views}/{name}.png"))   # render_views.py
            k += 1
    return tuple(out)


def build(mjspec, spec: "WorldSpec", xml: Path = XML) -> None:
    A.build(mjspec, spec, end_wall=False)
    kitchen = mujoco.MjSpec.from_file(str(xml))
    for name in REMOVE:
        kitchen.delete(kitchen.body(name))
    f = mjspec.worldbody.add_frame()
    f.pos = [KX, KY, KZ]
    mjspec.attach(kitchen, prefix="kitchen/", frame=f)


SPEC = WorldSpec(
    name="apartment_kitchen",
    doc=__doc__.split("\n\n")[0],
    package="worlds.apartment_kitchen",
    rooms=ROOMS,
    things=A.SPEC.things + _appliances(),
    junctions=JUNCTIONS,
    build=build,
    licenses={"pictures": "CC0 (scenes/gallery_cc0/PROVENANCE.json)", "world": "Apache-2.0",
              "kitchen": "RoboCasa: code MIT, assets CC BY 4.0 (kitchen_L001_S002/ATTRIBUTION.md)"},
    data_files=A.SPEC.data_files,
)


def make(kitchen_dir: Path, views: str) -> WorldSpec:
    """The same world around another exported kitchen (a style or layout under trial):
    measurement only -- the registered world is SPEC."""
    kitchen_dir = Path(kitchen_dir)
    return WorldSpec(name=f"apartment_kitchen:{kitchen_dir.name}", doc=SPEC.doc, package=SPEC.package,
                     rooms=ROOMS, things=A.SPEC.things + _appliances(kitchen_dir, views), junctions=JUNCTIONS,
                     build=lambda mjspec, spec: build(mjspec, spec, kitchen_dir / "kitchen.xml"),
                     licenses=SPEC.licenses, data_files=SPEC.data_files)

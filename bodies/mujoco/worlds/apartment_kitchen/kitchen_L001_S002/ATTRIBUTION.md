# Attribution

This folder holds one kitchen scene exported from **RoboCasa** (RoboCasa365), layout 1,
style 2, with its counter-accessory props left out: `kitchen.xml` and the 50 asset files
it uses under `assets/`, copied unchanged (sha256 of each in `assets.json`; what was built
in `export.json`).

- Source: https://github.com/robocasa/robocasa, commit `2ce1aec` (2026-10-21), with
  robosuite `5ce6643`; exported by `apps/gallery_companion/w0_export_kitchen.py` in
  RoboCasa's own environment (MuJoCo 3.3.1).
- Code: MIT License, Copyright (c) 2026 the RoboCasa Team.
- Assets: Creative Commons Attribution 4.0 International (CC BY 4.0),
  https://creativecommons.org/licenses/by/4.0/ -- by the RoboCasa team: Soroush Nasiriany,
  Sepehr Nasiriany, Abhiram Maddukuri, Yuke Zhu, et al. *RoboCasa: Large-Scale Simulation of
  Everyday Tasks for Generalist Robots* (RSS 2024); *RoboCasa365* (ICLR 2026).
- Changes: the export (one arena, fixtures merged, paths made relative); nothing in the
  asset files themselves.

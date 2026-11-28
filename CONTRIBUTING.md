# ubrain labs -- notes for contributors

This repository holds the examples, the manual and the labs for ubrain, the
Untrained Brain, together with the compiled ubrain package (`wheels/`). The package
itself is distributed compiled; its source is not part of this repository.

```
examples/   00_check_setup, 01_whole_brain, 02_ask, 03_keep, 04_g1_brace, 05_g1_choose,
            06_g1_keep, 07_g1_lead -- all on the whole brain, Brain(); each ends
            with CHECK PASS or CHECK FAIL
docs/       quickstart, using, concepts
wheels/     the compiled ubrain package: Windows x64, macOS (Apple Silicon and Intel),
            Linux x86_64 (glibc 2.28+), each for Python 3.11, 3.12 and 3.13
```

- `uv run examples/<name>.py` installs ubrain from `wheels/` and runs; extras:
  `--extra vision` (CLIP), `--extra video` (MP4 recording), `--extra plot` (matplotlib).
- The robot examples need the body, `bodies/mujoco` (its own environment: `uv sync` there once).
- Examples and docs: Apache-2.0 (LICENSE). The compiled package: LICENSE-BINARY.
- Report problems as issues with the command you ran and its full output.

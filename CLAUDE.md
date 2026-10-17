# ubrain labs -- notes for contributors

This repository holds the examples, the manual and the labs for ubrain, the
Untrained Brain, together with the compiled ubrain package (`wheels/`). The package
itself is distributed compiled; its source is not part of this repository.

```
examples/   01_bandit, 02_memory, 03_clip_words, g1_walker, g1_explorer
docs/       quickstart, concepts, labs (five), teachers
wheels/     the compiled ubrain package: Windows x64, macOS (Apple Silicon and Intel),
            Linux x86_64 (glibc 2.28+), each for Python 3.11, 3.12 and 3.13
```

- `uv run examples/<name>.py` installs ubrain from `wheels/` and runs; extras:
  `--extra vision` (CLIP), `--extra video` (MP4 recording).
- The robot examples need the body package, ubrain-mujoco, beside this folder.
- Examples and docs: Apache-2.0 (LICENSE). The compiled package: LICENSE-BINARY.
- Report problems as issues with the command you ran and its full output.

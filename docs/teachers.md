# For teachers: running the labs with a class

## Before the first session

- **Each student needs:** a laptop (Windows, macOS or Linux), git, and
  [uv](https://docs.astral.sh/uv/getting-started/installation/). No GPU. About 3 GB of
  disk for labs 3-5 (torch and CLIP).
- **Access.** While the repositories are private, add each student's GitHub account
  to the `untrained-brain` organisation's `ubrain` and `ubrain-mujoco` repositories with
  **read** access (Settings -> Collaborators and teams). After the public release no
  account is needed.
- **The CLIP checkpoint** (labs 3 and 5) is fetched once per machine:
  `uv run --extra vision python -c "from huggingface_hub import snapshot_download; snapshot_download('openai/clip-vit-base-patch32')"`
  (about 600 MB, run inside the ubrain folder). Ask students to do it at home before lab 3.
- **Try every lab yourself** on one student-like machine; first runs install things
  and take minutes.

## Timing

| session | lab | first run takes | then |
|---|---|---|---|
| 1 | Learning from reward | under a minute | instant |
| 2 | One-shot memory | under a minute | ~10 s per run |
| 3 | Codecs | a few minutes (torch) | ~30 s per run |
| 4 | The walker | a few minutes (MuJoCo) | real time |
| 5 | The explorer | -- | ~20 s headless, real time with the viewer |

## How the labs are built

Each lab: run one example, read what the law says, then exercises. Several exercises
ask for a **prediction written down before running** -- that is the habit to build. The
examples are short, readable scripts; students are expected to edit them.

## Known rough edges (pre-release)

- The G1 drifts off the gallery after about 14 photos (lab 5, exercise 3 uses this).
- The viewer window must be opened from a desktop session; on a remote server use
  `--headless`.
- On Windows, if a run is interrupted, a body server may keep its port; examples pick
  a free port by default, and closing the console ends it.

## Getting help

Open an issue or a discussion on the `ubrain` repository with the command you ran and
the full output.

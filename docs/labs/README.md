# Labs

Five sessions, each about 90 minutes. Each lab runs one example, explains the law
behind what you see, and ends with exercises: some ask you to predict a number
before you measure it. The first three need only a laptop; labs 4 and 5 need the
robot body (`bodies/mujoco`, set up once with `uv sync` there).

| lab | region | example | needs |
|---|---|---|---|
| [1. Learning from reward](lab1_striatum.md) | striatum | `01_bandit.py` | nothing |
| [2. One-shot memory and its capacity](lab2_hippocampus.md) | hippocampus | `02_memory.py` | nothing |
| [3. Plugging in a trained model](lab3_codecs.md) | codecs + hippocampus | `03_clip_words.py` | `--extra vision` |
| [4. A brain in a body](lab4_walker.md) | cerebellum | `g1_walker.py` | the body |
| [5. Seeing and remembering](lab5_explorer.md) | all of the above | `g1_explorer.py` | the body, `--extra vision` |

**The habit these labs teach:** write your prediction down before you run. A brain
built from laws can be predicted, and the interesting moments are where your
prediction and the measurement disagree.

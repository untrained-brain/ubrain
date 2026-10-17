"""03 -- plug a trained model in: CLIP reads words, the brain remembers a sentence.

    uv run --extra vision examples/03_clip_words.py

The brain is untrained; vision and language come from frozen models you plug in.
Here CLIP's text encoder is the sense. `certify` first reports what the brain can
hold with CLIP's codes (they sit in a cone, and are near-white once centred); then
the `observer` profile hears a sentence word by word and recalls it slot by slot.
The first run loads CLIP from the Hugging Face cache (it must be there already, or
pass local_only=False to CLIP to allow the one download).
"""


import numpy as np

from ubrain import Brain, Channel, Manifest, profile  # noqa: E402
from ubrain.codecs import Sense, certify  # noqa: E402

WORDS = """apple banana orange grape lemon cherry bread cheese butter milk coffee tea water soup
rice egg fish chicken cake cookie dog cat horse cow sheep pig bird owl eagle duck fox wolf bear lion
tiger mouse rabbit frog snake bee butterfly tree flower grass leaf river lake sea mountain hill
forest desert island beach sun moon star cloud rain snow wind storm house door window roof wall
chair table bed lamp clock mirror cup plate knife spoon fork bottle box bag shoe hat coat shirt
dress glove ring watch phone book pen pencil paper letter map key coin car bus train bicycle boat
ship plane rocket road bridge tower castle church school library market garden park street city
village farm doctor teacher student king queen child mother father friend soldier farmer baker
red blue green yellow black white small large old young happy sad quick slow warm cold
run walk jump swim sing read write sleep eat drink open close build break find give""".split()
SENTENCE = "the old farmer saw a red fox near the river".split()


def main() -> None:
    from ubrain.extras.clip import CLIP
    clip = CLIP("text")
    vocab = sorted(set(WORDS) | set(SENTENCE))
    print(f"certifying CLIP's codes for {len(vocab)} words (about half a minute on a laptop) ...",
          flush=True)
    print(certify(clip, vocab, d=512, ks=(4, 8, 16), n_trials=2000).summary())
    sense = Sense.fit(clip, vocab, d=512)
    body = Manifest("example/listener", "none", (
        Channel("camera", "codec", 1, codec="text"), Channel("recall", "event", 64),
        Channel("boundary", "event", 1), Channel("memory", "command", 512),
        Channel("remembered", "choice", len(vocab))))
    brain = Brain(profile("observer"), body, codecs={"camera": sense}, rng=np.random.default_rng(0))
    for w in SENTENCE:
        brain.tick({"camera": w})
    recalled = [vocab[brain.tick({"recall": i})["remembered"]] for i in range(len(SENTENCE))]
    print("\nheard   :", " ".join(SENTENCE))
    print("recalled:", " ".join(recalled))
    print("\nTry: a longer sentence. When do words start coming back wrong, and does the "
          "certificate say so first?")


if __name__ == "__main__":
    main()

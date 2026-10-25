"""10 -- neuromodulators as scalars on existing knobs (no robot, no GPU; about 20 s).

    uv run examples/10_neuromodulators.py

The `modulated` profile adds four hubs to a brain that notices, remembers and
chooses. None of them is new machinery: each neuromodulator is ONE NUMBER written
onto a port an existing region already has, and a region with that port unwired
behaves exactly as it did without the modulator.

  * the thalamus relays several incoming streams onto a shared workspace bus,
    opening a route only when its content matches a goal;
  * acetylcholine splits the cortex's plasticity on every event: a share a of it
    encodes the present, 1 - a replays one earlier experience;
  * noradrenaline sets the criterion of the salience gate, which judges what is novel;
  * serotonin sets the striatum's patience (example 1's striatum).

This example runs the last two, where ubrain's own code gives the prediction.

NORADRENALINE. The gate judges each arrival against M known codes in d dimensions:
a fresh code is novel, a repeat of a known code seen through noise sigma is
familiar, and an arrival is novel with probability pi. For every threshold the
two error rates are exact (no draws; `ubrain.regions.novelty_rates`), so the
criterion that errs least at rate pi is a number (`novelty_criterion`), and so is
its error. Noradrenaline's level is the running rate of JUDGED surprise,
level <- level + eta (judged novel - level), and the criterion is the one for that
level. With eta = 0 the criterion is fixed at the level it was given. Adapting, the
level settles where it equals the rate of surprise its own criterion judges -- a
fixed point, found here by running the update on the same exact rates.

SEROTONIN. One situation, two actions: a small reward soon or a large one late.
A choice's eligibility decays by the patience g = exp(-1/tau) on every tick until
its outcome, so the striatum's values settle at Q_a = r_a g^D_a (D_a the delay)
and the Go race chooses large-late with probability

    P(late) = g^D_L / (r_S g^D_S + g^D_L).

Low serotonin (small tau) is impulsivity, as a number. With kappa > 0, tau follows
the measured time between decisions, tau <- tau + kappa (ticks since the last -
tau), and settles where tau equals the mean trial time its own choices produce.
"""


import math

import numpy as np

from ubrain import Brain, Channel, FrozenCodes, Manifest, Sense, profile  # noqa: E402
from ubrain.promoted.cls.hrr import normalize  # noqa: E402
from ubrain.promoted.control.salience import noisy_repeat  # noqa: E402
from ubrain.regions import NE_THETAS, novelty_criterion, novelty_rates  # noqa: E402

N_EVENTS = 4000              # arrivals per noradrenaline run
R_S, D_S, D_L, GAP = 0.4, 2, 8, 2   # small reward 0.4 after 2 ticks, 1.0 after 8; 2 ticks between trials
TRIALS = 2400                # per serotonin run; the second half is measured


def _manifest(d, V):
    return Manifest("example/modulated", "none", (
        Channel("routes", "vector", d), Channel("goal", "vector", d), Channel("attend", "event", 4),
        Channel("camera", "codec", 1), Channel("known", "vector", d),
        Channel("recollect", "event", 64), Channel("situation", "event", 1),
        Channel("reward", "reward", 1), Channel("workspace", "command", d),
        Channel("attended", "command", d), Channel("recollection", "command", d),
        Channel("recollected", "choice", V), Channel("mode", "choice", 2),
        Channel("action", "choice", 2)))


def _world(d, M, sigma, pis, rng):
    """M known unit codes, then one arrival per event: fresh with probability pis[t],
    else a noisy repeat of a known code. A camera sense that passes the codes as they
    are (zero mean, no projection: the gate sees exactly these unit codes)."""
    known = normalize(rng.standard_normal((M, d)))
    novel = rng.random(len(pis)) < pis
    codes = np.array([normalize(rng.standard_normal(d)) if nv else
                      noisy_repeat(known[rng.integers(M)], sigma, rng) for nv in novel])
    E = np.vstack([known, codes])
    sense = Sense(FrozenCodes(E), mean=np.zeros(d), d=d, vocabulary=E, items=list(range(len(E))))
    return known, novel, sense


def _judge(w, d, M, sigma, pis, seed):
    rng = np.random.default_rng(seed)
    known, novel, sense = _world(d, M, sigma, pis, rng)
    brain = Brain(w, _manifest(d, sense.vocabulary.shape[0]), codecs={"camera": sense},
                  rng=np.random.default_rng(seed + 1))
    brain.tick({"known": known})                          # taught as familiar, never judged
    gate, ne = brain.regions["salience.gate"], brain.regions["neuromodulator.noradrenaline"]
    errs, levels = [], []
    for t in range(len(pis)):
        before = gate.novel                               # the gate's count of novel verdicts
        brain.tick({"camera": M + t})
        errs.append((gate.novel > before) != novel[t])
        levels.append(ne.level)
    return np.array(errs, dtype=float), np.array(levels)


def _err(pi, k, d, M, sigma):
    ff, rn = novelty_rates(d, M, sigma)
    return pi * ff[k] + (1 - pi) * rn[k]


def _level_fixed_point(pi, level, eta, d, M, sigma):
    """Where the level settles: the update level <- level + eta (judged - level) with
    the judged rate replaced by its exact expectation under the level's own criterion,
    iterated from the level the brain starts the new stream with (a deterministic
    path; the brain's own level wanders about it by sampling)."""
    ff, rn = novelty_rates(d, M, sigma)
    for _ in range(20000):
        k = novelty_criterion(level, d, M, sigma)
        level += eta * (pi * (1 - ff[k]) + (1 - pi) * rn[k] - level)
    return level


def noradrenaline() -> None:
    w0 = profile("modulated")
    ne = w0.regions["neuromodulator.noradrenaline"]
    d, M, sigma, eta = ne["d"], ne["M"], ne["sigma"], ne["eta"]
    print(f"NORADRENALINE: the gate judges {M} known codes, d={d}, repeats at noise sigma={sigma}")
    print("  arm                           criterion   error predicted   error measured")
    rows = []
    for pi in (0.1, 0.5):                                 # a fixed criterion, tuned to the rate
        w = profile("modulated")
        w.regions["neuromodulator.noradrenaline"].update(eta=0.0, level=pi)
        k = novelty_criterion(pi, d, M, sigma)
        errs, _ = _judge(w, d, M, sigma, np.full(N_EVENTS, pi), seed=int(pi * 100))
        rows.append((f"fixed at {pi}, stream at {pi}", NE_THETAS[k], _err(pi, k, d, M, sigma), errs))
    # the rate rises from 0.1 to 0.5 half way; a criterion fixed at 0.1 against the adaptive one
    pis = np.where(np.arange(N_EVENTS) < N_EVENTS // 2, 0.1, 0.5)
    late = slice(N_EVENTS // 2 + 500, N_EVENTS)           # after the change, once the level has moved
    w = profile("modulated")
    w.regions["neuromodulator.noradrenaline"].update(eta=0.0, level=0.1)
    k = novelty_criterion(0.1, d, M, sigma)
    errs, _ = _judge(w, d, M, sigma, pis, seed=7)
    rows.append(("fixed at 0.1, stream at 0.5", NE_THETAS[k], _err(0.5, k, d, M, sigma), errs[late]))
    errs, levels = _judge(profile("modulated"), d, M, sigma, pis, seed=7)
    L = _level_fixed_point(0.5, levels[N_EVENTS // 2 - 1], eta, d, M, sigma)
    k = novelty_criterion(L, d, M, sigma)
    rows.append((f"adaptive (eta {eta}), at 0.5", NE_THETAS[k], _err(0.5, k, d, M, sigma), errs[late]))
    for name, theta, law, e in rows:
        se = math.sqrt(law * (1 - law) / e.size)
        print(f"  {name:28s}  {theta:.3f}       {law:.3f}             {e.mean():.3f} (+-{se:.3f})")
    print(f"  adaptive level after the change: predicted {L:.3f} (its fixed point), "
          f"measured {levels[late].mean():.3f} (mean; sd {levels[late].std():.3f})")


def _patience_run(tau, kappa, seed):
    w = profile("modulated")
    w.regions["neuromodulator.serotonin"].update(tau=tau, kappa=kappa)
    s = Sense.fit(FrozenCodes(np.random.default_rng(0).standard_normal((8, 256))), range(8))
    brain = Brain(w, _manifest(256, 8), codecs={"camera": s}, rng=np.random.default_rng(seed))
    clock, due, late, taus = 0, None, [], []

    def tick(senses):
        nonlocal clock, due
        if due is not None and due[0] == clock:
            senses = senses | {"reward": due[1]}
            due = None
        clock += 1
        return brain.tick(senses)

    for t in range(TRIALS):
        cue = clock
        a = tick({"situation": 0})["action"]
        delay, r = (D_S, R_S) if a == 0 else (D_L, 1.0)
        due = (cue + delay, r)
        while clock < cue + delay + GAP:
            tick({})
        if t >= TRIALS // 2:
            late.append(a)
            taus.append(brain.regions["neuromodulator.serotonin"].tau)
    return np.array(late, dtype=float), np.array(taus)


def p_late(tau):
    g = math.exp(-1.0 / tau)
    return g ** D_L / (R_S * g ** D_S + g ** D_L)


def serotonin() -> None:
    print(f"\nSEROTONIN: small {R_S} after {D_S} ticks, or 1.0 after {D_L}; {GAP} ticks between trials")
    print("  patience                         P(late) predicted   P(late) measured")
    for tau, name in ((2.0, "low serotonin"), (10.0, "high serotonin")):
        x, _ = _patience_run(tau, 0.0, seed=int(tau))
        law = p_late(tau)
        print(f"  {f'tau {tau:4.1f} fixed ({name})':31s}  {law:.3f}               "
              f"{x.mean():.3f} (+-{math.sqrt(law * (1 - law) / x.size):.3f})")
    kappa = profile("modulated").regions["neuromodulator.serotonin"]["kappa"]
    lo, hi = D_S + GAP, D_L + GAP                          # tau* = mean trial time under tau*'s own choices
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if D_S + GAP + p_late(mid) * (D_L - D_S) > mid else (lo, mid)
    tau_star = 0.5 * (lo + hi)
    x, taus = _patience_run(4.0, kappa, seed=3)
    law = p_late(tau_star)
    print(f"  {f'tau adaptive (kappa {kappa})':31s}  {law:.3f}               "
          f"{x.mean():.3f} (+-{math.sqrt(law * (1 - law) / x.size):.3f}; binomial -- tau's slow "
          f"wander widens it)")
    print(f"  adaptive tau: predicted {tau_star:.2f} ticks (the mean trial time it produces), "
          f"measured {taus.mean():.2f} (mean; sd {taus.std():.2f})")


def main() -> None:
    noradrenaline()
    serotonin()
    print("\nTry: set the noradrenaline eta to 0.1 (w.regions[\"neuromodulator.noradrenaline\"][\"eta\"] = 0.1) "
          "and watch the level after the change: fast adaptation counts the surprise its own criterion "
          "decides, and runs away toward judging nothing novel (no closed form here for its path).")


if __name__ == "__main__":
    main()

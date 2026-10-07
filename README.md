# POD model

A data-driven alternative to the hand-built harmonic model
(`../harmonic_model`), using POD (Proper Orthogonal Decomposition - the
SVD of the snapshot data) to find whatever shapes best explain the
force data's variance, instead of assuming they are exactly cos/sin
waves at orders 0, 8, 16, 24.

## Why this exists

The harmonic model works because the force pattern across the 48 teeth
is almost exactly a sum of 4 known spatial harmonics - but that fact
was found by manually inspecting an FFT of the data and recognizing the
physics. POD asks the opposite question: **with no assumptions at all
about what shape the data should have, what does the data itself say
its dominant patterns are?**

Two kinds of modes come out of this (hence the name of this folder -
"spatial and temporal PODs"):

- **Spatial modes**: fixed shapes across the 48 teeth, found by taking
  the SVD of the force data. Each one is a direction in 48-dimensional
  "tooth space" that captures as much of the data's variance as
  possible, given what the previous modes already captured.
- **Temporal modes**: for a fixed torque, how strongly each spatial
  mode is present changes as the rotor turns - that trace, plotted
  against electrical angle, is the temporal side of the decomposition.
  (It's "temporal" in the classical POD sense of "the other axis of the
  snapshot matrix" - here that axis is electrical angle, not time, as
  requested.)

## What was found

Running `pod_analysis.py` and `model.py`'s own fitting step gives a
clean, independent confirmation of everything the harmonic model
assumed, found with zero physics input:

- A plain SVD of the (tooth x angle) data at one torque needs only
  **4-6 modes to explain essentially 100% of the variance** (80%, 10%,
  9%, 0.3%, ... - see `pod_spectrum_*.png`). Everything past mode 4 is
  noise-level.
- The dominant spatial modes, compared against plain cos/sin waves,
  line up almost exactly with **orders 0, 8, 16, and 24** - the exact
  same orders the harmonic model was built around (see
  `pod_modes_*.png`). Orders 8 and 16 each show up as **two** separate
  modes with near-equal variance share - the expected signature of a
  pure rotating wave (a spatial pattern that rotates with angle is
  mathematically rank-2, not rank-1 - see model.py's docstring).
- Fitting the full predictive model (`PODModel.fit`, which has to
  *discover* each mode's natural rotation speed rather than being told
  it) comes back with exactly **[0, 8, 8, 16, 16, 24]** for both Fr and
  Ft - matching the hand-picked orders with no prompting.
- Mode 1's spatial shape isn't perfectly flat (the "order 0" direction
  has a small ripple), and its coefficient wobbles with the same
  **24-cycles-per-360-degree rhythm** found independently while
  improving the harmonic model (see `../harmonic_model/README.md`) -
  a third, independent confirmation of that modulation effect.

In short: POD rediscovered the harmonic model's entire basis from
scratch, which is strong independent evidence that basis is a property
of the actual machine physics, not a lucky guess.

## How the predictive model works (`model.py`)

Mirrors `harmonic_model/model.py`'s three steps, with one basis swapped
out for a learned one:

1. **Spatial POD** (instead of an exact Fourier transform): stack every
   training snapshot into one big matrix and take its SVD. Keep enough
   modes to explain `config.VARIANCE_TO_EXPLAIN` of the variance.
2. **Temporal fit** (instead of a known rotation rate): project every
   snapshot onto the modes to get one coefficient per mode per
   snapshot. Each mode's natural rotation speed is *discovered* by
   checking which frequency best explains how its coefficient moves
   through an angle sweep (`discover_dominant_frequency`), then the
   same modulation sidebands used in the harmonic model
   (`MODULATION_STEP` / `MODULATION_COUNT`) are layered on top.
3. **Torque fit**: a cubic spline through the numbers across the
   torque levels actually present in the data - identical to the
   harmonic model.

Predicting reverses this: read the curves for the query torque, turn
them into mode coefficients at the query angle, and combine with the
spatial modes to get the 48 tooth forces back.

## Module layout

| File | What's in it |
|---|---|
| `config.py` | Settings - data path, variance-to-explain threshold, modulation rhythm, split fractions, output folder. |
| `data.py` | Loading the CSV, both test splits (same as `harmonic_model/data.py`), and `snapshot_matrix_per_torque` for the classical per-torque 2D POD. |
| `model.py` | `PODModel` - the predictive model. |
| `evaluate.py` | `r2_breakdown` - the shared scoring function. |
| `plots.py` | Shared drawing helpers: error heatmaps, spatial mode shapes, temporal traces, singular value spectra. |
| `pod_analysis.py` | The exploratory script - runs a classical 2D SVD at one torque and plots spatial/temporal modes against the matching harmonics, then reports what the full model discovers. **Run this first** if you want to see what POD finds, not just use the model. |
| `bakeoff.py` | Compares the POD model, the harmonic model, and the interpolation baseline under both test splits. |
| `results/` | Everything the scripts above save. Safe to delete; everything regenerates. |

This package depends on `harmonic_model` for one thing only:
`bakeoff.py`'s comparison columns, which it skips gracefully (with a
printed note) if `harmonic_model` isn't importable. `pod_analysis.py`
and `model.py` are fully self-contained.

## How to run things

```bash
# See what POD finds in the data - mode shapes, singular value spectrum,
# discovered frequencies - before using the model for anything:
python3 pod_model/pod_analysis.py

# Compare the POD model, the harmonic model, and the interpolation
# baseline, under both test splits:
python3 pod_model/bakeoff.py
```

`pod_analysis.py` has `TORQUE_TO_ANALYZE` and `N_MODES_TO_SHOW` near the
top if you want to look at a different torque or more modes.

## Results (from `bakeoff.py`, current code)

**Interpolating within a known torque:**

| Model | Overall R² | Fr R² | Ft R² |
|---|---|---|---|
| Harmonic model | 0.9999 | 0.9999 | 0.9997 |
| POD model | 0.9836 | 0.9559 | 0.9816 |
| Interpolation baseline | 0.8781 | 0.6788 | 0.8466 |

**Predicting a torque never seen at all (mean over all 12 held-out torques):**

| Model | Mean R² |
|---|---|
| Harmonic model | 0.9822 |
| POD model | 0.9822 |
| Interpolation baseline | 0.9252 |

The leave-one-torque-out numbers are **essentially identical** between
the two physics-grade models (differences only in the 4th decimal
place) - strong evidence they converged on the same underlying
description of the data by two independent routes.

The angle-block split tells a different, informative story: POD is
measurably behind the harmonic model there (0.9836 vs 0.9999). The
likely reason is a real, structural difference between the two
approaches, not a bug: the angle-block split removes the *same*
middle stretch of angles from *every* torque's training data, so the
POD basis itself - which has to be learned from whatever training data
exists - is being computed from a systematically incomplete angle
sweep. The harmonic model's basis (plain sin/cos) doesn't have this
weakness, because it was never learned from data in the first place.
**This is the central trade-off between the two approaches**: POD
needs no hand-identified physics and generalizes just as well across
torque, but its accuracy is coupled to how completely the training data
covers the space the basis has to be learned from - the harmonic
model's exact basis has no such dependency.

## Known limitations

- Same data limitations as the harmonic model: angle only covers
  0°-90° of the electrical cycle, single RPM only (see
  `../harmonic_model/README.md` for details - both apply here too).
- **Basis quality depends on training data coverage** (see above) - the
  one real weakness POD has that the harmonic model doesn't.
- `discover_dominant_frequency` searches integer frequencies 0-30 by
  brute force. That comfortably covers every order seen in this
  dataset (0, 8, 16, 24), but would need widening if a future dataset
  (e.g. a different pole/slot count) has meaningful content above
  order 30.

"""
Compares three ways of modeling this dataset, head to head:

  1. The POD model (model.py) - the data-driven approach, basis found
     by SVD rather than assumed.
  2. The hand-built harmonic model (../harmonic_model) - the same idea,
     but with the spatial basis fixed to exact cos/sin waves at orders
     0, 8, 16, 24 instead of discovered from data.
  3. The interpolation baseline (../harmonic_model/baseline.py) - the
     simplest possible "no physics, no learning" approach.

Two tests are run, same as harmonic_model/bakeoff.py:
  - The angle-block split: hide a middle chunk of angles at each torque
    level, ask the model to fill it in.
  - Leave-one-torque-out: hide an entire torque level, ask the model to
    predict it having never seen that torque at all.
"""

import csv
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import r2_score

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pod_model import config  # noqa: E402
from pod_model.model import PODModel  # noqa: E402
from pod_model.data import load_data, build_force_matrix, split_by_angle_blocks, leave_one_torque_out_splits  # noqa: E402
from pod_model.evaluate import r2_breakdown  # noqa: E402

try:
    from harmonic_model.model import HarmonicModel
    from harmonic_model.baseline import InterpolationBaseline
    HARMONIC_MODEL_AVAILABLE = True
except ImportError as _error:
    HARMONIC_MODEL_AVAILABLE = False
    print(f"(could not import harmonic_model, skipping that comparison: {_error})")


def run_angle_block_test(df, forces, torques, angles_deg):
    print("\n" + "=" * 70)
    print("TEST 1: angle-block split (interpolate within a known torque)")
    print("=" * 70)
    results = []

    train_rows, _val_rows, test_rows = split_by_angle_blocks(df)
    train_mask = df.index.isin(train_rows)
    test_mask = df.index.isin(test_rows)

    pod = PODModel()
    pod.fit(forces[train_mask], torques[train_mask], angles_deg[train_mask])
    pred = pod.predict(torques[test_mask], angles_deg[test_mask])
    metrics = r2_breakdown(forces[test_mask], pred)
    print(f"  POD model              overall R2={metrics['r2_overall']:.4f}  "
          f"Fr R2={metrics['r2_fr']:.4f}  Ft R2={metrics['r2_ft']:.4f}")
    results.append({"test": "angle_block", "model": "pod", **metrics})

    if HARMONIC_MODEL_AVAILABLE:
        harmonic = HarmonicModel()
        harmonic.fit(forces[train_mask], torques[train_mask], angles_deg[train_mask])
        pred = harmonic.predict(torques[test_mask], angles_deg[test_mask])
        metrics = r2_breakdown(forces[test_mask], pred)
        print(f"  Harmonic model          overall R2={metrics['r2_overall']:.4f}  "
              f"Fr R2={metrics['r2_fr']:.4f}  Ft R2={metrics['r2_ft']:.4f}")
        results.append({"test": "angle_block", "model": "harmonic", **metrics})

        baseline = InterpolationBaseline()
        baseline.fit(forces[train_mask], torques[train_mask], angles_deg[train_mask])
        pred = baseline.predict(torques[test_mask], angles_deg[test_mask])
        metrics = r2_breakdown(forces[test_mask], pred)
        print(f"  Interpolation baseline  overall R2={metrics['r2_overall']:.4f}  "
              f"Fr R2={metrics['r2_fr']:.4f}  Ft R2={metrics['r2_ft']:.4f}")
        results.append({"test": "angle_block", "model": "interpolation_baseline", **metrics})

    return results


def run_leave_one_torque_out_test(torques, forces, angles_deg):
    print("\n" + "=" * 70)
    print("TEST 2: leave-one-torque-out (predict a torque never seen during training)")
    print("=" * 70)
    header = f"  {'held-out T':>12}  {'POD R2':>10}"
    if HARMONIC_MODEL_AVAILABLE:
        header += f"  {'harmonic R2':>12}  {'interpolation R2':>18}"
    print(header)

    results = []
    pod_r2, harmonic_r2, baseline_r2 = [], [], []
    for T, train_mask, test_mask in leave_one_torque_out_splits(torques):
        pod = PODModel()
        pod.fit(forces[train_mask], torques[train_mask], angles_deg[train_mask])
        pred_p = pod.predict(torques[test_mask], angles_deg[test_mask])
        r2_p = r2_score(forces[test_mask].ravel(), pred_p.ravel())
        pod_r2.append(r2_p)
        results.append({"test": "leave_one_torque_out", "model": "pod", "held_out_torque": T, "r2_overall": r2_p})

        line = f"  {T:>12.0f}  {r2_p:>10.4f}"

        if HARMONIC_MODEL_AVAILABLE:
            harmonic = HarmonicModel()
            harmonic.fit(forces[train_mask], torques[train_mask], angles_deg[train_mask])
            pred_h = harmonic.predict(torques[test_mask], angles_deg[test_mask])
            r2_h = r2_score(forces[test_mask].ravel(), pred_h.ravel())
            harmonic_r2.append(r2_h)
            results.append({"test": "leave_one_torque_out", "model": "harmonic",
                             "held_out_torque": T, "r2_overall": r2_h})

            baseline = InterpolationBaseline()
            baseline.fit(forces[train_mask], torques[train_mask], angles_deg[train_mask])
            pred_b = baseline.predict(torques[test_mask], angles_deg[test_mask])
            r2_b = r2_score(forces[test_mask].ravel(), pred_b.ravel())
            baseline_r2.append(r2_b)
            results.append({"test": "leave_one_torque_out", "model": "interpolation_baseline",
                             "held_out_torque": T, "r2_overall": r2_b})

            line += f"  {r2_h:>12.4f}  {r2_b:>18.4f}"

        print(line)

    print(f"\n  mean overall R2, POD model:              {np.mean(pod_r2):.4f}")
    if HARMONIC_MODEL_AVAILABLE:
        print(f"  mean overall R2, harmonic model:         {np.mean(harmonic_r2):.4f}")
        print(f"  mean overall R2, interpolation baseline: {np.mean(baseline_r2):.4f}")
    return results


def main():
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading the dataset...")
    df = load_data()
    forces, torques, angles_deg = build_force_matrix(df)

    results = []
    results += run_angle_block_test(df, forces, torques, angles_deg)
    results += run_leave_one_torque_out_test(torques, forces, angles_deg)

    log_path = config.OUTPUT_DIR / "bakeoff_log.csv"
    fieldnames = sorted({k for row in results for k in row.keys()})
    with open(log_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\nFull results written to {log_path}")


if __name__ == "__main__":
    main()

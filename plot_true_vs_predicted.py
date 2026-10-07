"""
Shows the real FEA data next to the POD model's prediction for one
torque level, so the two can be compared directly rather than only
looking at an error number. Same idea, same layout as
../harmonic_model/plot_true_vs_predicted.py, for direct comparison
between the two approaches.

By default this torque is held out while fitting - the model never
sees it at all - so what's shown is a genuine test of the model, the
same situation as the leave-one-torque-out numbers in bakeoff.py. Set
HOLD_OUT_TORQUE = False to instead see how well the model fits a
torque it was allowed to train on.

Produces two pictures:
  1. Heatmaps - true data next to predicted data, angle on one axis and
     tooth number on the other, for Fr and Ft.
  2. A line plot at one chosen angle, true vs predicted force at every
     tooth - easier to read exact differences than a heatmap is.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pod_model import config, PODModel, load_full_dataset, r2_breakdown  # noqa: E402
from pod_model.plots import draw_value_heatmap, draw_line_comparison  # noqa: E402

TORQUE_TO_PLOT = 450
HOLD_OUT_TORQUE = True  # True = model never saw this torque during fitting (the honest test)
ANGLE_FOR_LINE_PLOT = None  # None = pick the middle angle automatically


def fit_model(forces, torques, angles_deg, exclude_torque=None):
    mask = np.ones(len(torques), dtype=bool) if exclude_torque is None else torques != exclude_torque
    model = PODModel()
    model.fit(forces[mask], torques[mask], angles_deg[mask])
    return model


def plot_heatmaps(true_forces, predicted_forces, angles_deg, n_teeth, torque, held_out, out_dir):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    status = "held out - model never trained on this torque" if held_out else "included in training"
    fig.suptitle(f"POD model: true vs predicted forces - torque = {torque:g} Nm ({status})",
                 fontsize=13, fontweight="bold")

    for row, (label, columns) in enumerate([("Fr (radial force)", slice(0, n_teeth)),
                                              ("Ft (tangential force)", slice(n_teeth, None))]):
        true_grid = true_forces[:, columns]
        pred_grid = predicted_forces[:, columns]
        shared_min = min(true_grid.min(), pred_grid.min())
        shared_max = max(true_grid.max(), pred_grid.max())
        draw_value_heatmap(axes[row, 0], true_grid, angles_deg, n_teeth,
                           f"{label} - True (FEA data)", shared_min, shared_max)
        draw_value_heatmap(axes[row, 1], pred_grid, angles_deg, n_teeth,
                           f"{label} - Predicted", shared_min, shared_max)

    plt.tight_layout()
    out_path = out_dir / f"true_vs_predicted_heatmap_T{torque:g}.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved -> {out_path}")


def plot_line_comparison(true_forces, predicted_forces, angles_deg, n_teeth, torque, angle_choice, out_dir):
    row_index = np.argmin(np.abs(angles_deg - angle_choice))
    actual_angle = angles_deg[row_index]

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    fig.suptitle(f"POD model: true vs predicted, one angle slice - torque = {torque:g} Nm, "
                 f"angle = {actual_angle:.1f} deg", fontsize=13, fontweight="bold")

    for ax, label, columns in zip(axes, ["Fr (radial force)", "Ft (tangential force)"],
                                   [slice(0, n_teeth), slice(n_teeth, None)]):
        draw_line_comparison(ax, true_forces[row_index, columns], predicted_forces[row_index, columns],
                             n_teeth, label)

    plt.tight_layout()
    out_path = out_dir / f"true_vs_predicted_line_T{torque:g}.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved -> {out_path}")


def main():
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading the dataset...")
    forces, torques, angles_deg = load_full_dataset()

    exclude_torque = TORQUE_TO_PLOT if HOLD_OUT_TORQUE else None
    print(f"Fitting the POD model "
          f"({'excluding' if HOLD_OUT_TORQUE else 'including'} torque={TORQUE_TO_PLOT})...")
    model = fit_model(forces, torques, angles_deg, exclude_torque=exclude_torque)
    for channel in ["Fr", "Ft"]:
        print(f"  {channel}: kept {model.n_modes(channel)} modes, "
              f"discovered frequencies: {model.mode_frequencies[channel]}")

    mask = torques == TORQUE_TO_PLOT
    if not mask.any():
        raise ValueError(f"No rows at torque={TORQUE_TO_PLOT}. Available: {sorted(set(torques.tolist()))}")

    true_forces = forces[mask]
    predicted_forces = model.predict(torques[mask], angles_deg[mask])
    angles_here = angles_deg[mask]
    n_teeth = config.N_TEETH

    metrics = r2_breakdown(true_forces, predicted_forces, n_teeth)
    print(f"\nAt torque={TORQUE_TO_PLOT} Nm ({mask.sum()} rows): "
          f"overall R2={metrics['r2_overall']:.4f}  Fr R2={metrics['r2_fr']:.4f}  Ft R2={metrics['r2_ft']:.4f}")

    plot_heatmaps(true_forces, predicted_forces, angles_here, n_teeth, TORQUE_TO_PLOT,
                  HOLD_OUT_TORQUE, config.OUTPUT_DIR)

    angle_choice = ANGLE_FOR_LINE_PLOT if ANGLE_FOR_LINE_PLOT is not None else float(np.median(angles_here))
    plot_line_comparison(true_forces, predicted_forces, angles_here, n_teeth, TORQUE_TO_PLOT,
                         angle_choice, config.OUTPUT_DIR)


if __name__ == "__main__":
    main()

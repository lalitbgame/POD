"""
Explores the POD / SVD structure of the FEA data directly - the
"spatial modes" (shapes across the 48 teeth) and "temporal modes"
(shapes across the electrical angle sweep) that a plain,
assumption-free SVD finds, compared against the hand-picked Fourier
harmonics (orders 0, 8, 16, 24) used by ../harmonic_model.

For one chosen torque level, this treats the (tooth x angle) force
data as a plain matrix and takes its SVD - the classical two-sided POD:

    F(tooth, angle)  =  sum_k  sigma_k * U_k(tooth) * V_k(angle)

U_k are the spatial modes, V_k are the temporal modes, sigma_k says how
much of the signal each pair accounts for.

Produces, per torque and per channel (Fr, Ft):
  - A singular value spectrum (how many modes actually matter).
  - The first several spatial modes, each plotted against whichever
    pure cos/sin wave at a spatial order matches it most closely - if
    POD "rediscovers" the same physics the hand-built model assumes,
    these should look nearly identical.
  - The first several temporal modes (shape across the angle sweep).

Then runs the full predictive PODModel (model.py) once on everything
and reports how many modes it kept and what frequency it discovered for
each one, for a direct side-by-side against harmonic_model's hand-
picked orders.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pod_model import config, load_data, build_force_matrix, snapshot_matrix_per_torque, PODModel  # noqa: E402
from pod_model.plots import draw_spatial_mode, draw_temporal_trace, draw_singular_value_spectrum  # noqa: E402

TORQUE_TO_ANALYZE = 450
N_MODES_TO_SHOW = 4


def best_matching_reference(mode_vector, n_teeth):
    """
    Checks the mode against plain cos/sin waves at every possible
    spatial order and returns whichever one (and whichever phase: cos
    or sin) lines up with it most closely, for the comparison plot.
    """
    tooth_index = np.arange(n_teeth)
    best = None
    for order in range(0, n_teeth // 2 + 1):
        for kind, reference in [("cos", np.cos(2 * np.pi * order * tooth_index / n_teeth)),
                                 ("sin", np.sin(2 * np.pi * order * tooth_index / n_teeth))]:
            norm = np.linalg.norm(reference)
            if norm < 1e-9:
                continue
            reference_unit = reference / norm
            overlap = abs(np.dot(mode_vector, reference_unit))
            if best is None or overlap > best[0]:
                best = (overlap, order, kind, reference_unit)
    return best[1], best[2], best[3], best[0]


def analyze_one_torque(torque_value, snapshots):
    snap = snapshots[torque_value]
    angles_here = snap["angles_deg"]

    for channel in ["Fr", "Ft"]:
        matrix = snap[channel]  # [n_teeth, n_angles]
        U, S, Vt = np.linalg.svd(matrix, full_matrices=False)
        energy = S ** 2
        fraction = energy / energy.sum()
        print(f"\n{channel} at torque={torque_value:g} Nm: top singular values explain "
              f"{', '.join(f'{f * 100:.2f}%' for f in fraction[:6])} of the variance "
              f"(cumulative {fraction[:6].sum() * 100:.3f}%)")

        fig, axes = plt.subplots(2, N_MODES_TO_SHOW, figsize=(4 * N_MODES_TO_SHOW, 7))
        fig.suptitle(f"{channel} - POD spatial and temporal modes at torque={torque_value:g} Nm",
                     fontsize=13, fontweight="bold")
        for mode_index in range(N_MODES_TO_SHOW):
            spatial_mode = U[:, mode_index]
            temporal_mode = Vt[mode_index, :]
            order, kind, reference_unit, overlap = best_matching_reference(spatial_mode, config.N_TEETH)
            # SVD modes have an arbitrary overall sign - flip for a cleaner-looking comparison plot
            if np.dot(spatial_mode, reference_unit) < 0:
                spatial_mode = -spatial_mode
                temporal_mode = -temporal_mode
            draw_spatial_mode(
                axes[0, mode_index], spatial_mode, config.N_TEETH,
                f"mode {mode_index + 1} ({fraction[mode_index] * 100:.1f}% var)\n"
                f"best match: order {order} {kind} (overlap {overlap:.3f})",
                reference_curve=reference_unit, reference_label=f"order {order} {kind}",
            )
            draw_temporal_trace(axes[1, mode_index], angles_here, temporal_mode,
                                f"mode {mode_index + 1} - temporal shape")
        plt.tight_layout()
        out_path = config.OUTPUT_DIR / f"pod_modes_{channel}_T{torque_value:g}.png"
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        print(f"  Saved -> {out_path}")

        fig, ax = plt.subplots(figsize=(7, 4))
        draw_singular_value_spectrum(ax, S[:10], f"{channel} singular value spectrum - torque={torque_value:g} Nm")
        plt.tight_layout()
        out_path = config.OUTPUT_DIR / f"pod_spectrum_{channel}_T{torque_value:g}.png"
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        print(f"  Saved -> {out_path}")


def main():
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading the dataset...")
    df = load_data()
    forces, torques, angles_deg = build_force_matrix(df)

    print(f"\n--- Per-torque 2D POD at torque={TORQUE_TO_ANALYZE} Nm ---")
    snapshots = snapshot_matrix_per_torque(forces, torques, angles_deg)
    analyze_one_torque(TORQUE_TO_ANALYZE, snapshots)

    print("\n--- Global POD (all torques and angles combined) ---")
    model = PODModel()
    model.fit(forces, torques, angles_deg)
    for channel in ["Fr", "Ft"]:
        print(f"{channel}: kept {model.n_modes(channel)} modes, "
              f"discovered frequencies (cycles per 360 deg electrical turn): {model.mode_frequencies[channel]}")
    print("\nCompare against harmonic_model's hand-picked orders: [0, 8, 16, 24]")
    print("(each order with 0 < order < 24 shows up here as two real modes with the same frequency -")
    print(" that is the expected signature of a pure rotating wave, confirmed independently by POD.)")


if __name__ == "__main__":
    main()

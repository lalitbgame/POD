"""
Drawing helpers shared by the scripts in this package, so the heatmap
and mode-shape style only has to be defined once.
"""

import matplotlib.pyplot as plt
import numpy as np


def _angle_ticks(angles_sorted):
    step = max(1, len(angles_sorted) // 10)
    positions = np.arange(0, len(angles_sorted), step)
    labels = [f"{a:.0f}" for a in angles_sorted[::step]]
    return positions, labels


def draw_error_heatmap(ax, true_values, predicted_values, angles_deg, n_teeth, title):
    """One red heatmap of |true - predicted|, angle on the y-axis, tooth number on the x-axis."""
    order = np.argsort(angles_deg)
    angles_sorted = angles_deg[order]
    tooth_numbers = np.arange(1, n_teeth + 1)
    error = np.abs(true_values - predicted_values)[order]

    im = ax.imshow(error, aspect="auto", cmap="Reds", origin="lower", vmin=0)
    plt.colorbar(im, ax=ax, label="Absolute error (N)")
    ax.set_xticks(np.arange(0, n_teeth, 4))
    ax.set_xticklabels(tooth_numbers[0:n_teeth:4], fontsize=8)
    positions, labels = _angle_ticks(angles_sorted)
    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel("Tooth number")
    ax.set_ylabel("Electrical angle (deg)")
    ax.set_title(title)
    ax.text(0.02, 0.98, f"mean={error.mean():.1f} N\nmax={error.max():.1f} N",
            transform=ax.transAxes, va="top", ha="left", fontsize=8,
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
    return error


def draw_value_heatmap(ax, values, angles_deg, n_teeth, title, vmin, vmax):
    """One heatmap of raw force values (not error) - for true-vs-predicted side-by-side views."""
    order = np.argsort(angles_deg)
    angles_sorted = angles_deg[order]
    tooth_numbers = np.arange(1, n_teeth + 1)
    grid = values[order]

    im = ax.imshow(grid, aspect="auto", cmap="RdBu_r", origin="lower", vmin=vmin, vmax=vmax)
    plt.colorbar(im, ax=ax, label="Force (N)")
    ax.set_xticks(np.arange(0, n_teeth, 4))
    ax.set_xticklabels(tooth_numbers[0:n_teeth:4], fontsize=8)
    positions, labels = _angle_ticks(angles_sorted)
    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel("Tooth number")
    ax.set_ylabel("Electrical angle (deg)")
    ax.set_title(title)


def draw_line_comparison(ax, true_row, predicted_row, n_teeth, title):
    """One line plot: true vs predicted force across the 48 teeth, for a single angle."""
    tooth_numbers = np.arange(1, n_teeth + 1)
    ax.plot(tooth_numbers, true_row, "o-", label="True (FEA data)", color="#185FA5", lw=1.6, ms=4)
    ax.plot(tooth_numbers, predicted_row, "s--", label="Predicted", color="#D85A30", lw=1.4, ms=3)
    ax.set_xlabel("Tooth number")
    ax.set_ylabel("Force (N)")
    ax.set_title(title)
    ax.legend()
    ax.grid(alpha=0.3)


def draw_spatial_mode(ax, mode_vector, n_teeth, title, reference_curve=None, reference_label=None):
    """
    One POD spatial mode's shape across the 48 teeth, as a line plot.
    If reference_curve is given (e.g. a plain cos/sin wave at the
    matching harmonic order), it's drawn alongside for comparison - the
    two should look almost identical if POD rediscovered the same
    physics the hand-built harmonic model assumes.
    """
    tooth_numbers = np.arange(1, n_teeth + 1)
    ax.plot(tooth_numbers, mode_vector, "o-", color="#185FA5", lw=1.6, ms=3, label="POD spatial mode")
    if reference_curve is not None:
        ax.plot(tooth_numbers, reference_curve, "--", color="#D85A30", lw=1.4,
                label=reference_label or "reference harmonic")
        ax.legend(fontsize=8)
    ax.set_xlabel("Tooth number")
    ax.set_ylabel("Mode value (unit length)")
    ax.set_title(title)
    ax.grid(alpha=0.3)


def draw_temporal_trace(ax, angle_deg, coefficient_values, title, fitted_values=None):
    """
    One POD mode's coefficient as a function of electrical angle, at a
    single torque - this is the "temporal" side of the decomposition.
    If fitted_values is given (the model's own reconstruction), it's
    overlaid for comparison.
    """
    order = np.argsort(angle_deg)
    ax.plot(angle_deg[order], coefficient_values[order], "o-", color="#185FA5", lw=1.4, ms=3,
            label="POD coefficient (data)")
    if fitted_values is not None:
        ax.plot(angle_deg[order], fitted_values[order], "--", color="#D85A30", lw=1.4, label="fitted curve")
        ax.legend(fontsize=8)
    ax.set_xlabel("Electrical angle (deg)")
    ax.set_ylabel("Coefficient value")
    ax.set_title(title)
    ax.grid(alpha=0.3)


def draw_singular_value_spectrum(ax, singular_values, title):
    """How much of the data's variance each POD mode explains, and the running total."""
    energy = singular_values ** 2
    fraction = energy / energy.sum()
    cumulative = np.cumsum(fraction)

    mode_numbers = np.arange(1, len(singular_values) + 1)
    ax.bar(mode_numbers, fraction * 100, color="#185FA5", alpha=0.7, label="this mode's share")
    ax2 = ax.twinx()
    ax2.plot(mode_numbers, cumulative * 100, "o-", color="#D85A30", label="running total")
    ax2.set_ylabel("Cumulative variance explained (%)")
    ax2.set_ylim(0, 105)

    ax.set_xlabel("Mode number")
    ax.set_ylabel("Variance explained (%)")
    ax.set_xticks(mode_numbers)
    ax.set_title(title)
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="center right")

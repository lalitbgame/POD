"""
A data-driven alternative to harmonic_model/model.py's hand-picked
Fourier basis. Instead of assuming the 48-tooth force pattern is a sum
of cos/sin waves at orders 0, 8, 16, 24 (found by inspecting the data
and recognizing the physics), POD (Proper Orthogonal Decomposition -
the SVD of the snapshot data) finds whatever spatial shapes over the 48
teeth best explain the data's variance, with no assumption about what
those shapes should look like. See pod_analysis.py to see how closely
the two methods actually agree.

The model works in three steps, mirroring harmonic_model/model.py:

  1. SPATIAL POD: stack every training snapshot as a row of a big
     [n_rows x 48] matrix (separately for Fr and Ft) and take its SVD.
     The right singular vectors are the "spatial modes" - fixed shapes
     over the 48 teeth, ranked by how much of the data's variance each
     one explains. Keep just enough to cover config.VARIANCE_TO_EXPLAIN.
  2. TEMPORAL FIT: project every snapshot onto these modes to get one
     coefficient per mode per snapshot. Each coefficient is then a plain
     real-valued function of (torque, angle) - unlike the hand-built
     model, where the equivalent quantity is a known Fourier
     coefficient, here the mode's own natural rotation speed isn't known
     ahead of time, so it's discovered by checking which frequency best
     explains how the coefficient moves through an angle sweep (see
     discover_dominant_frequency). The same "second rhythm" used in the
     hand-built model (MODULATION_STEP / MODULATION_COUNT) is then
     layered on top, exactly as there.
  3. TORQUE FIT: fit a smooth curve through the resulting numbers across
     the torque levels, so a torque value can be looked up even if it
     wasn't one of the original FEA runs.

Predicting a new (torque, angle) reverses this: read the numbers off
the curves for that torque, turn them back into mode coefficients at
that angle, and turn the coefficients back into 48 tooth forces by
combining them with the spatial modes.
"""

import numpy as np
from scipy.interpolate import CubicSpline

from . import config


def compute_pod_basis(matrix, variance_to_explain=config.VARIANCE_TO_EXPLAIN):
    """
    matrix: [n_snapshots, n_teeth] - one row per (torque, angle) snapshot.
    Returns (spatial_modes, singular_values). spatial_modes is
    [n_teeth, n_modes] - each column is one orthonormal spatial shape,
    kept just deep enough to explain variance_to_explain of the data's
    total energy.
    """
    _U, S, Vt = np.linalg.svd(matrix, full_matrices=False)
    energy = S ** 2
    explained = np.cumsum(energy) / energy.sum()
    n_modes = int(np.searchsorted(explained, variance_to_explain) + 1)
    n_modes = min(n_modes, len(S))
    return Vt[:n_modes].T, S[:n_modes]


def discover_dominant_frequency(angle_rad, values, candidate_frequencies=range(0, 31)):
    """
    Tries each candidate frequency (cycles per 360 degrees of electrical
    angle) and returns whichever one best explains how this mode's
    coefficient changes with angle - judged by how much of its
    variation a plain cos/sin pair at that frequency can explain.
    """
    best_freq, best_r2 = 0, -np.inf
    for f in candidate_frequencies:
        design = np.column_stack([np.cos(f * angle_rad), np.sin(f * angle_rad)])
        coeffs, *_ = np.linalg.lstsq(design, values, rcond=None)
        fitted = design @ coeffs
        residual = np.sum((values - fitted) ** 2)
        total = np.sum((values - values.mean()) ** 2) + 1e-12
        r2 = 1 - residual / total
        if r2 > best_r2:
            best_r2, best_freq = r2, f
    return best_freq, best_r2


def frequencies_for_mode(home_frequency, step=config.MODULATION_STEP, count=config.MODULATION_COUNT):
    """The small group of rotation speeds used to describe one mode's coefficient, mirroring harmonic_model."""
    return [home_frequency + step * m for m in range(-count, count + 1)]


def fit_wave_numbers(frequencies, angle_rad, values):
    """Least-squares fit of a real-valued signal as a sum of cos/sin pairs. Returns a list of (P, Q), one per frequency."""
    cos_terms = [np.cos(f * angle_rad) for f in frequencies]
    sin_terms = [np.sin(f * angle_rad) for f in frequencies]
    design = np.column_stack(cos_terms + sin_terms)
    solved = np.linalg.lstsq(design, values, rcond=None)[0]
    n = len(frequencies)
    return list(zip(solved[:n], solved[n:]))


def wave_numbers_to_values(frequencies, PQ_list, angle_rad):
    total = np.zeros_like(angle_rad)
    for frequency, (P, Q) in zip(frequencies, PQ_list):
        total = total + P * np.cos(frequency * angle_rad) + Q * np.sin(frequency * angle_rad)
    return total


class PODModel:
    """
    fit(...) finds the data-driven spatial modes (POD/SVD) and learns
    how strongly each one is present as a function of torque and angle.
    predict(...) turns (torque, angle) pairs into 48-tooth force vectors
    for Fr and Ft.
    """

    def __init__(self, n_teeth=config.N_TEETH, variance_to_explain=config.VARIANCE_TO_EXPLAIN):
        self.n_teeth = n_teeth
        self.variance_to_explain = variance_to_explain
        self.spatial_modes = {}     # channel -> [n_teeth, n_modes]
        self.mode_frequencies = {}  # channel -> [n_modes] discovered home frequency per mode
        self.curves = {}            # channel -> [ {"terms": [...], "torque_range": (...)}, ... ] one per mode

    def fit(self, forces, torques, angles_deg):
        angle_rad = np.deg2rad(angles_deg)
        torque_levels = np.unique(torques)

        for channel_index, channel_name in enumerate(["Fr", "Ft"]):
            start = channel_index * self.n_teeth
            matrix = forces[:, start:start + self.n_teeth]

            spatial_modes, _singular_values = compute_pod_basis(matrix, self.variance_to_explain)
            self.spatial_modes[channel_name] = spatial_modes
            coefficients = matrix @ spatial_modes  # [n_rows, n_modes]

            n_modes = spatial_modes.shape[1]
            self.mode_frequencies[channel_name] = []
            self.curves[channel_name] = []

            for mode_index in range(n_modes):
                a = coefficients[:, mode_index]
                # Use whichever torque shows this mode most strongly (biggest
                # spread across the angle sweep) to discover its frequency -
                # gives the cleanest signal to search.
                strongest_torque = max(torque_levels, key=lambda T: a[torques == T].std())
                mask0 = torques == strongest_torque
                home_frequency, _r2 = discover_dominant_frequency(angle_rad[mask0], a[mask0])
                self.mode_frequencies[channel_name].append(home_frequency)
                frequencies = frequencies_for_mode(home_frequency)

                torque_points = []
                PQ_per_torque = []
                for T in torque_levels:
                    mask = torques == T
                    if mask.sum() < 2 * len(frequencies):
                        continue
                    PQ_per_torque.append(fit_wave_numbers(frequencies, angle_rad[mask], a[mask]))
                    torque_points.append(T)

                mode_curves = []
                for freq_index, frequency in enumerate(frequencies):
                    P_points = [pq[freq_index][0] for pq in PQ_per_torque]
                    Q_points = [pq[freq_index][1] for pq in PQ_per_torque]
                    mode_curves.append({
                        "frequency": frequency,
                        "P": CubicSpline(torque_points, P_points, extrapolate=True),
                        "Q": CubicSpline(torque_points, Q_points, extrapolate=True),
                    })
                self.curves[channel_name].append({
                    "terms": mode_curves,
                    "torque_range": (min(torque_points), max(torque_points)),
                })

    def predict(self, torques, angles_deg):
        """Returns a [n_rows, 2*n_teeth] array, Fr then Ft."""
        angle_rad = np.deg2rad(angles_deg)
        n_rows = len(torques)
        output = np.zeros((n_rows, 2 * self.n_teeth), dtype=np.float32)

        for channel_index, channel_name in enumerate(["Fr", "Ft"]):
            spatial_modes = self.spatial_modes[channel_name]
            n_modes = spatial_modes.shape[1]
            coefficients = np.zeros((n_rows, n_modes))

            for mode_index, mode in enumerate(self.curves[channel_name]):
                frequencies = [term["frequency"] for term in mode["terms"]]
                PQ_list = [(term["P"](torques), term["Q"](torques)) for term in mode["terms"]]
                coefficients[:, mode_index] = wave_numbers_to_values(frequencies, PQ_list, angle_rad)

            reconstructed = coefficients @ spatial_modes.T  # [n_rows, n_teeth]
            start = channel_index * self.n_teeth
            output[:, start:start + self.n_teeth] = reconstructed

        return output

    def n_modes(self, channel="Fr"):
        return self.spatial_modes[channel].shape[1]

    def torque_coverage(self, channel="Fr"):
        """The torque range the curves were actually fit on - outside this, predict() is extrapolating."""
        return self.curves[channel][0]["torque_range"]

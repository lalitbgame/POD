"""
Loading the FEA dataset and splitting it two different ways for
testing. Same data, same two splits as harmonic_model/data.py (kept as
a separate copy here rather than a cross-import, so this package stands
on its own) - see that package's README for why each split exists.
"""

import numpy as np
import pandas as pd

from . import config


def load_data(data_path=None):
    data_path = data_path or config.DATA_PATH
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} rows from {data_path}")
    return df


def build_force_matrix(df, n_teeth=config.N_TEETH):
    """Returns (forces, torques, angles_deg): forces is [n_rows, 2*n_teeth], Fr then Ft."""
    fr_cols = [f"FR_{i + 1}" for i in range(n_teeth)]
    ft_cols = [f"FT_{i + 1}" for i in range(n_teeth)]
    forces = np.hstack([df[fr_cols].to_numpy(), df[ft_cols].to_numpy()]).astype(np.float32)
    torques = df["Torque (Nm)"].to_numpy()
    angles_deg = df["Electrical Angle"].to_numpy()
    return forces, torques, angles_deg


def load_full_dataset(data_path=None, n_teeth=config.N_TEETH):
    """Convenience wrapper: load the CSV and immediately split out forces/torques/angles."""
    df = load_data(data_path)
    return build_force_matrix(df, n_teeth)


def split_by_angle_blocks(df, train_fraction=config.TRAIN_FRACTION, val_fraction=config.VAL_FRACTION):
    """
    A plain random split would put, say, angle=45.0 in training and
    angle=45.1 in the test set - those two rows are nearly identical, so
    the test score would look better than the model really is. Instead,
    for each torque level, sort rows by angle and cut out one contiguous
    block of angles for testing and another for validation, with the
    test block in the middle (training data on both sides).

    Returns three arrays of row labels (matching df's index): train, val, test.
    """
    train_rows, val_rows, test_rows = [], [], []

    for _torque, group in df.groupby("Torque (Nm)"):
        ordered = group.sort_values("Electrical Angle")
        n = len(ordered)
        n_test = int(n * (1 - train_fraction - val_fraction))
        n_val = int(n * val_fraction)

        row_positions = ordered.index.to_numpy()
        test_start = (n - n_test - n_val) // 2
        test_end = test_start + n_test
        val_end = test_end + n_val

        test_rows.extend(row_positions[test_start:test_end])
        val_rows.extend(row_positions[test_end:val_end])
        train_rows.extend(row_positions[:test_start])
        train_rows.extend(row_positions[val_end:])

    return np.array(train_rows), np.array(val_rows), np.array(test_rows)


def leave_one_torque_out_splits(torques):
    """
    Yields (held_out_torque, train_mask, test_mask) once per torque
    level found in the data.
    """
    for torque_value in np.unique(torques):
        test_mask = torques == torque_value
        train_mask = ~test_mask
        yield torque_value, train_mask, test_mask


def snapshot_matrix_per_torque(forces, torques, angles_deg, n_teeth=config.N_TEETH):
    """
    Arranges one torque level's data as a proper [tooth x angle] matrix
    (sorted by angle), separately for Fr and Ft - the classical POD
    "snapshot matrix" shape, one column per angle snapshot.

    Returns {torque_value: {"Fr": [n_teeth x n_angles], "Ft": [...],
    "angles_deg": sorted angle values}}.
    """
    matrices = {}
    for torque_value in np.unique(torques):
        mask = torques == torque_value
        order = np.argsort(angles_deg[mask])
        angles_sorted = angles_deg[mask][order]
        fr = forces[mask, :n_teeth][order].T   # [n_teeth x n_angles]
        ft = forces[mask, n_teeth:][order].T
        matrices[torque_value] = {"Fr": fr, "Ft": ft, "angles_deg": angles_sorted}
    return matrices

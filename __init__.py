"""
A POD (Proper Orthogonal Decomposition) based alternative to both the
hand-built harmonic model (../harmonic_model) and the neural network
pipeline (../train_model.py) for predicting motor forces (Fr, Ft on 48
teeth) from torque and electrical angle. See README.md.

Typical usage:

    from pod_model import PODModel, load_full_dataset

    forces, torques, angles_deg = load_full_dataset()
    model = PODModel()
    model.fit(forces, torques, angles_deg)
    predicted = model.predict(torques, angles_deg)
"""

from .model import PODModel
from .data import (
    load_data,
    build_force_matrix,
    load_full_dataset,
    split_by_angle_blocks,
    leave_one_torque_out_splits,
    snapshot_matrix_per_torque,
)
from .evaluate import r2_breakdown

__all__ = [
    "PODModel",
    "load_data",
    "build_force_matrix",
    "load_full_dataset",
    "split_by_angle_blocks",
    "leave_one_torque_out_splits",
    "snapshot_matrix_per_torque",
    "r2_breakdown",
]

"""
Central settings for the POD model package. Change values here instead
of hunting through individual scripts.
"""

from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent

DATA_PATH = PROJECT_ROOT / "1000RPM_Baseline" / "Combined_Torque_Data.csv"
OUTPUT_DIR = HERE / "results"
N_TEETH = 48

# How much of each torque level's angle sweep goes to each split, for the
# angle-block split (see data.split_by_angle_blocks). Whatever is left
# over goes to the test split.
TRAIN_FRACTION = 0.70
VAL_FRACTION = 0.15

# How many POD modes to keep per channel (Fr, Ft). Chosen to cover this
# much of the signal's variance - see pod_analysis.py for the spectrum
# that justifies this number instead of just guessing it.
VARIANCE_TO_EXPLAIN = 0.9999

# The same second rhythm found for the hand-built harmonic model
# (harmonic_model/model.py): each mode's strength wobbles at this rate
# (and double this rate) per full electrical turn, on top of its own
# natural rotation speed. Re-used here rather than re-discovered, since
# it is a property of the machine, not of which basis is used to
# describe it - pod_analysis.py checks this assumption still holds.
MODULATION_STEP = 24
MODULATION_COUNT = 2

# Where the separate autoencoder+ANN pipeline's saved model lives, used
# only for the optional side-by-side comparison in bakeoff.py.
NEURAL_MODEL_PATH = PROJECT_ROOT / "results_v2" / "model.pt"

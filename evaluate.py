"""Small shared scoring helper used by the bake-off and plotting scripts."""

from sklearn.metrics import r2_score

from . import config


def r2_breakdown(true, pred, n_teeth=config.N_TEETH):
    """Overall, Fr-only, and Ft-only R2 between true and predicted force arrays."""
    return {
        "r2_overall": r2_score(true.ravel(), pred.ravel()),
        "r2_fr": r2_score(true[:, :n_teeth].ravel(), pred[:, :n_teeth].ravel()),
        "r2_ft": r2_score(true[:, n_teeth:].ravel(), pred[:, n_teeth:].ravel()),
    }

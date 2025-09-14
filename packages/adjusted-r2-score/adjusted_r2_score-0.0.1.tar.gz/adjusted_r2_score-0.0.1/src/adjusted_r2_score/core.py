import numpy as np

def adjusted_r2_score(y_true, y_pred, n_features):
    """
    Calculates the adjusted R-squared score.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground truth (correct) target values.
    y_pred : array-like of shape (n_samples,)
        Estimated target values.
    n_features : int
        Number of features used to predict y_pred.

    Returns
    -------
    float
        The adjusted R-squared score.
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length.")

    n_samples = len(y_true)
    if n_samples - n_features - 1 == 0:
        return 0.0

    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    r2 = 1 - (ss_res / ss_tot)
    adj_r2 = 1 - (1 - r2) * (n_samples - 1) / (n_samples - n_features - 1)

    return adj_r2
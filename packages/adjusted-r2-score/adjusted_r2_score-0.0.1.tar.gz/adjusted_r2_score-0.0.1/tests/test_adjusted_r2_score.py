import pytest
import numpy as np
from adjusted_r2_score import adjusted_r2_score
from sklearn.metrics import r2_score

def test_basic_calculation():
    """
    Tests the adjusted R-squared score against a known value.
    This example uses scikit-learn's r2_score to verify the intermediate R² calculation.
    """
    y_true = [3, -0.5, 2, 7]
    y_pred = [2.5, 0.0, 2, 8]
    n_features = 2
    n_samples = len(y_true)

    # Calculate expected R² from scikit-learn
    r2 = r2_score(y_true, y_pred)
    
    # Calculate expected adjusted R² manually
    expected_adj_r2 = 1 - (1 - r2) * (n_samples - 1) / (n_samples - n_features - 1)
    
    # Calculate with our function
    actual_adj_r2 = adjusted_r2_score(y_true, y_pred, n_features)
    
    # Assert that the values are close enough to account for floating point differences
    assert actual_adj_r2 == pytest.approx(expected_adj_r2)

def test_perfect_prediction():
    """
    Tests if a perfect prediction results in an adjusted R-squared score of 1.
    """
    y_true = [1, 2, 3, 4, 5]
    y_pred = [1, 2, 3, 4, 5]
    n_features = 2
    
    assert adjusted_r2_score(y_true, y_pred, n_features) == pytest.approx(1.0)

def test_edge_case_division_by_zero():
    """
    Tests the edge case where (n_samples - n_features - 1) is zero.
    The function should handle this gracefully and return 0.0.
    """
    y_true = [1, 2, 3]
    y_pred = [1, 2, 4]
    n_features = 2  # This makes n_samples - n_features - 1 = 3 - 2 - 1 = 0
    
    assert adjusted_r2_score(y_true, y_pred, n_features) == 0.0

def test_input_length_mismatch():
    """
    Tests that a ValueError is raised if input arrays have different lengths.
    """
    y_true = [1, 2, 3]
    y_pred = [1, 2]
    n_features = 1
    
    # pytest.raises checks if a specific exception is raised
    with pytest.raises(ValueError, match="y_true and y_pred must have the same length."):
        adjusted_r2_score(y_true, y_pred, n_features)
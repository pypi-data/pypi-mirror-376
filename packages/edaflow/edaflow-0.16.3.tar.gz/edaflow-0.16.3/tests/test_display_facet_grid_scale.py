import pandas as pd
import pytest
from edaflow.display import display_facet_grid, scale_features
import matplotlib.pyplot as plt
import seaborn as sns

def test_display_facet_grid_scatter():
    df = pd.DataFrame({
        'A': ['x', 'x', 'y', 'y'],
        'B': [1, 2, 1, 2],
        'C': [10, 20, 30, 40],
        'D': [5, 6, 7, 8]
    })
    g = display_facet_grid(df, col='A', row='B', kind='scatter', x='C', y='D')
    assert hasattr(g, 'axes')
    plt.close('all')

def test_display_facet_grid_hist():
    df = pd.DataFrame({
        'A': ['x', 'x', 'y', 'y'],
        'B': [1, 2, 1, 2],
        'C': [10, 20, 30, 40]
    })
    g = display_facet_grid(df, col='A', kind='hist', x='C')
    assert hasattr(g, 'axes')
    plt.close('all')

def test_scale_features_standard():
    df = pd.DataFrame({
        'A': [1, 2, 3, 4],
        'B': [10, 20, 30, 40],
        'C': ['x', 'y', 'x', 'y']
    })
    scaled = scale_features(df, columns=['A', 'B'], method='standard')
    assert abs(scaled['A'].mean()) < 1e-8
    assert abs(scaled['B'].mean()) < 1e-8

def test_scale_features_minmax():
    df = pd.DataFrame({
        'A': [1, 2, 3, 4],
        'B': [10, 20, 30, 40]
    })
    scaled = scale_features(df, method='minmax')
    assert scaled['A'].min() == 0
    assert scaled['A'].max() == 1
    assert scaled['B'].min() == 0
    assert scaled['B'].max() == 1

def test_scale_features_robust():
    df = pd.DataFrame({
        'A': [1, 2, 3, 100],
        'B': [10, 20, 30, 40]
    })
    scaled = scale_features(df, method='robust')
    # Robust scaling: median should be 0
    assert abs(scaled['A'].median()) < 1e-8
    assert abs(scaled['B'].median()) < 1e-8

def test_scale_features_invalid_method():
    df = pd.DataFrame({'A': [1, 2, 3]})
    with pytest.raises(ValueError):
        scale_features(df, method='unknown')

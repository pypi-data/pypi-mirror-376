import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import edaflow.display as edisp

def test_display_heatmap_corr():
    df = pd.DataFrame(np.random.rand(10, 4), columns=['A', 'B', 'C', 'D'])
    corr = df.corr()
    fig = edisp.display_heatmap(corr, cmap='coolwarm', annot=True, title='Correlation Matrix')
    assert fig is not None

def test_display_heatmap_custom():
    arr = np.random.rand(5, 5)
    fig = edisp.display_heatmap(arr, cmap='magma', annot=False, title='Custom Matrix')
    assert fig is not None

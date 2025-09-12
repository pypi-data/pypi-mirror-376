import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import edaflow.display as edisp

def sample_violin_df():
    np.random.seed(42)
    df = pd.DataFrame({
        'score': np.random.normal(50, 10, 100),
        'group': np.random.choice(['A', 'B', 'C'], 100)
    })
    return df

def test_display_violinplot_basic():
    df = sample_violin_df()
    fig = edisp.display_violinplot(df, column='score', title='Score Distribution')
    assert fig is not None

def test_display_violinplot_grouped():
    df = sample_violin_df()
    fig = edisp.display_violinplot(df, column='score', group_by='group', title='Score by Group')
    assert fig is not None

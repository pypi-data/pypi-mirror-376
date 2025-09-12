import pandas as pd
import pytest
import matplotlib.pyplot as plt
from edaflow.display import group_rare_categories, export_figure

def test_group_rare_categories_basic():
    df = pd.DataFrame({'cat': ['a', 'a', 'b', 'c', 'c', 'c', 'd']})
    grouped = group_rare_categories(df, 'cat', threshold=0.3)
    # 'a' (2/7), 'b' (1/7), 'd' (1/7) should be 'Other', 'c' (3/7) kept
    assert (grouped == 'Other').sum() == 4
    assert (grouped == 'c').sum() == 3

def test_group_rare_categories_custom_value():
    df = pd.DataFrame({'cat': ['x', 'y', 'y', 'z', 'z', 'z']})
    grouped = group_rare_categories(df, 'cat', threshold=0.4, new_value='RARE')
    # 'x' (1/6) and 'y' (2/6) should be 'RARE', 'z' (3/6) kept
    assert (grouped == 'RARE').sum() == 3
    assert (grouped == 'z').sum() == 3

def test_export_figure_png(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6])
    out_file = tmp_path / "test_export.png"
    export_figure(fig, str(out_file))
    assert out_file.exists()
    plt.close(fig)

def test_export_figure_format(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6])
    out_file = tmp_path / "test_export.pdf"
    export_figure(fig, str(out_file), format="pdf")
    assert out_file.exists()
    plt.close(fig)

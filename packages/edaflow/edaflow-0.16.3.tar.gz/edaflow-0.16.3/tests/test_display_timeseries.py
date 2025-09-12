import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # For headless testing
import edaflow.display as edisp

def sample_timeseries_df():
    dates = pd.date_range('2023-01-01', periods=30)
    sales = np.random.normal(100, 10, size=30)
    df = pd.DataFrame({'date': dates, 'sales': sales})
    return df

def test_display_timeseries():
    df = sample_timeseries_df()
    fig = edisp.display_timeseries(df, x='date', y='sales', title='Sales Over Time')
    assert fig is not None

def test_display_seasonal_decompose():
    df = sample_timeseries_df()
    fig = edisp.display_seasonal_decompose(df, column='sales', freq=7)
    assert fig is not None

def test_display_autocorrelation():
    df = sample_timeseries_df()
    fig = edisp.display_autocorrelation(df, column='sales')
    assert fig is not None

def test_display_lag_plot():
    df = sample_timeseries_df()
    fig = edisp.display_lag_plot(df, column='sales', lag=1)
    assert fig is not None

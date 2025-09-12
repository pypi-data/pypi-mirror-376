import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import edaflow.display as edisp

def sample_anomaly_df():
    dates = pd.date_range('2023-01-01', periods=30)
    sales = np.random.normal(100, 10, size=30)
    sales[5] = 200  # Inject anomaly
    sales[20] = 10  # Inject anomaly
    df = pd.DataFrame({'date': dates, 'sales': sales})
    return df

def test_display_timeseries_anomaly():
    df = sample_anomaly_df()
    fig = edisp.display_timeseries(df, x='date', y='sales', highlight_anomalies=True, title='Sales with Anomalies')
    assert fig is not None

def test_create_lag_features():
    df = sample_anomaly_df()
    df_lag = edisp.create_lag_features(df, column='sales', lags=[1,2], dropna=True)
    assert 'sales_lag1' in df_lag.columns
    assert 'sales_lag2' in df_lag.columns
    assert not df_lag.isnull().any().any()

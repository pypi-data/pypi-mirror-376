import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import edaflow.display as edisp

def sample_forecast_df():
    dates = np.arange(50)
    sales = np.random.normal(100, 10, size=50)
    df = pd.DataFrame({'date': dates, 'sales': sales})
    df.set_index('date', inplace=True)
    return df

def test_display_arima():
    df = sample_forecast_df()
    fig = edisp.display_arima(df, column='sales', order=(1,1,1), forecast_steps=10, title='ARIMA Forecast')
    assert fig is not None

def test_display_exponential_smoothing():
    df = sample_forecast_df()
    fig = edisp.display_exponential_smoothing(df, column='sales', trend='add', seasonal='add', seasonal_periods=12, forecast_steps=10, title='Exp Smoothing Forecast')
    assert fig is not None

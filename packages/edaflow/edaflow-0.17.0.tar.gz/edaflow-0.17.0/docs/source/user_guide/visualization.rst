**Advanced Time Series Topics**
------------------------------
Take your time series analysis further with these advanced techniques:

**1. Forecasting**
------------------
.. code-block:: python

	# Simple forecasting with statsmodels or scikit-learn
	from statsmodels.tsa.holtwinters import ExponentialSmoothing
	model = ExponentialSmoothing(df['sales'], trend='add', seasonal='add', seasonal_periods=12)
	fit = model.fit()
	df['sales_forecast'] = fit.forecast(steps=12)
	eda.display_timeseries(df, x='date', y=['sales', 'sales_forecast'])

**2. Autocorrelation & Lag Analysis**
-------------------------------------
.. code-block:: python

	from pandas.plotting import autocorrelation_plot, lag_plot
	autocorrelation_plot(df['sales'])
	lag_plot(df['sales'], lag=1)

**3. Feature Engineering for Time Series**
------------------------------------------
.. code-block:: python

	df['month'] = pd.to_datetime(df['date']).dt.month
	df['year'] = pd.to_datetime(df['date']).dt.year
	df['sales_lag1'] = df['sales'].shift(1)

**4. Integrating Time Series Models**
-------------------------------------
.. code-block:: python

	# Example: ARIMA model
	from statsmodels.tsa.arima.model import ARIMA
	arima = ARIMA(df['sales'], order=(1,1,1))
	arima_fit = arima.fit()
	df['arima_forecast'] = arima_fit.forecast(steps=12)

**Tips for Advanced Time Series:**
- Always check autocorrelation before modeling
- Use lag features to improve predictive models
- Compare multiple forecasting models for best results
- Visualize actual vs. forecasted values for validation
**Time Series Analysis & Visualization**
----------------------------------------
edaflow supports time series data exploration and visualization. Here are some practical examples:

.. code-block:: python

	# Line plot for time series trends
	eda.display_timeseries(df, x='date', y='sales')

	# Seasonal decomposition (if available)
	eda.display_seasonal_decompose(df, column='sales', freq=12)

	# Rolling mean and window statistics
	df['sales_rolling'] = df['sales'].rolling(window=7).mean()
	eda.display_timeseries(df, x='date', y='sales_rolling')

	# Highlight anomalies
	eda.display_timeseries(df, x='date', y='sales', highlight_anomalies=True)

**Tips for Time Series:**
- Always plot your time series to check for trends, seasonality, and anomalies
- Use rolling statistics to smooth out short-term fluctuations
- Decompose series to analyze trend and seasonality components
- Highlight anomalies for outlier detection and business insights

Visualization Guide
===================

edaflow provides a rich set of visualization tools to help you understand your data, identify patterns, and communicate insights effectively. This guide covers:

- Distribution analysis (boxplots, histograms)
- Correlation and relationship analysis
- Advanced scatter matrix and pair plots
- Interactive visualizations with Plotly

**Getting Started**
-------------------
To visualize your data, simply use edaflow's built-in functions:

.. code-block:: python

	import edaflow as eda
	eda.display_boxplot(df, column='age')
	eda.display_histogram(df, column='income')

**Correlation Analysis**
------------------------
Explore relationships between variables:

.. code-block:: python

	eda.display_correlation_matrix(df)
	eda.display_scatter_matrix(df, columns=['age', 'income', 'score'])

**Advanced & Interactive Plots**
--------------------------------
For publication-ready and interactive dashboards:

.. code-block:: python

	eda.display_interactive_boxplot(df, column='score')
	eda.display_interactive_scatter(df, x='age', y='income')

**More Visualization Examples**
-------------------------------
Violin Plot for Distribution and Density:

.. code-block:: python

	eda.display_violinplot(df, column='income', group_by='region')

Heatmap for Feature Relationships:

.. code-block:: python

	eda.display_heatmap(df.corr(), cmap='viridis')

Time Series Visualization:

.. code-block:: python

	eda.display_timeseries(df, x='date', y='sales')

Multi-Feature Scatter Plot:

.. code-block:: python

	eda.display_scatter(df, x='age', y='income', color='score', size='spending')

**Best Practices**
------------------
- Always visualize distributions before modeling
- Use correlation plots to detect multicollinearity
- Leverage interactive plots for presentations and reports
- Try different plot types to uncover hidden patterns

.. _external_library_requirements:

External Library Requirements for Advanced Features
==================================================

Some advanced edaflow features require additional Python libraries. Please ensure these are installed for full functionality:

- **matplotlib**: Required for all core plotting functions (boxplot, histogram, timeseries, heatmap, etc.)
- **seaborn**: Required for advanced visualizations (facet grid, violinplot, heatmap, scatter matrix)
- **scikit-learn**: Required for feature scaling (`scale_features`), machine learning utilities
- **statsmodels**: Required for time series models (ARIMA, Exponential Smoothing, seasonal decomposition)
- **pandas**: Required for all data manipulation and plotting

Feature Dependency Table:
------------------------

+--------------------------+--------------------------+
| Feature                  | Required Libraries       |
+==========================+==========================+
| display_timeseries       | matplotlib, pandas       |
| display_seasonal_decompose | statsmodels, matplotlib |
| display_arima            | statsmodels, matplotlib  |
| display_exponential_smoothing | statsmodels, matplotlib |
| display_facet_grid       | seaborn, matplotlib      |
| display_violinplot       | seaborn, matplotlib      |
| display_heatmap          | seaborn, matplotlib      |
| scale_features           | scikit-learn, pandas     |
| group_rare_categories    | pandas                   |
| export_figure            | matplotlib               |
+--------------------------+--------------------------+

To install all recommended libraries:

.. code-block:: bash

   pip install matplotlib seaborn scikit-learn statsmodels pandas

If you encounter import errors, check that these packages are installed in your environment.

.. note::
   Some features (e.g., PDF/SVG export) may require a working Tkinter/tcl installation for matplotlib. For headless environments, set the backend to 'Agg' using:

   .. code-block:: python

      import matplotlib
      matplotlib.use('Agg')

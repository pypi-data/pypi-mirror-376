Basic EDA Workflow
==================

This example demonstrates a complete exploratory data analysis (EDA) workflow using edaflow. Follow these steps to analyze your dataset:

**1. Load Data**
----------------
.. code-block:: python

	import pandas as pd
	import edaflow as eda
	df = pd.read_csv('your_data.csv')

**2. Assess Data Quality**
--------------------------
.. code-block:: python

	eda.check_null_columns(df)
	eda.display_column_types(df)

**3. Visualize Distributions**
------------------------------
.. code-block:: python

	eda.display_boxplot(df, column='age')
	eda.display_histogram(df, column='income')

**4. Handle Missing Values & Outliers**
---------------------------------------
.. code-block:: python

	df = eda.impute_numerical_median(df, column='income')
	df = eda.handle_outliers_median(df, column='score')

**5. Explore Relationships**
----------------------------
.. code-block:: python

	eda.display_correlation_matrix(df)
	eda.display_scatter_matrix(df, columns=['age', 'income', 'score'])

**6. Summarize Insights**
-------------------------
.. code-block:: python

	eda.summarize_eda_insights(df)

**7. Analyze Categorical Features**
-----------------------------------
.. code-block:: python

	eda.analyze_categorical_columns(df, columns=['gender', 'region'])
	eda.display_barplot(df, column='region')

**8. Feature Engineering**
--------------------------
.. code-block:: python

	df['income_per_age'] = df['income'] / df['age']
	eda.display_scatter(df, x='income_per_age', y='score')

**9. Generate Summary Report**
------------------------------
.. code-block:: python

	eda.create_model_report(df)

This workflow helps you quickly assess, clean, and understand your data before modeling. For more advanced analysis, see the Advanced Visualization and Data Cleaning Pipeline examples.

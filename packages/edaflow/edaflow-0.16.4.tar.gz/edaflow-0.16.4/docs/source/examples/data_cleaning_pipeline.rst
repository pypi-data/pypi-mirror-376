Data Cleaning Pipeline
======================

This example demonstrates a robust data cleaning workflow using edaflow functions.

**1. Identify Missing Data**
----------------------------
.. code-block:: python

	import edaflow as eda
	missing_report = eda.check_null_columns(df)

**2. Impute Missing Values**
----------------------------
.. code-block:: python

	df = eda.impute_numerical_median(df, column='income')
	df = eda.impute_categorical_mode(df, column='category')

**3. Convert Data Types**
-------------------------
.. code-block:: python

	df = eda.convert_to_numeric(df, columns=['score', 'income'])

**4. Handle Outliers**
----------------------
.. code-block:: python

	df = eda.handle_outliers_median(df, column='score')

**5. Validate Data Quality**
----------------------------
.. code-block:: python

	eda.display_column_types(df)
	eda.validate_ml_data(df)

**6. Remove Duplicates**
------------------------
.. code-block:: python

	df = df.drop_duplicates()

**7. Handle Rare Categories**
-----------------------------
.. code-block:: python

	df['region'] = df['region'].replace(df['region'].value_counts()[df['region'].value_counts() < 10].index, 'Other')

**8. Feature Scaling**
----------------------
.. code-block:: python

	from sklearn.preprocessing import StandardScaler
	scaler = StandardScaler()
	df['income_scaled'] = scaler.fit_transform(df[['income']])

**Best Practices:**
- Always check for missing and invalid values before modeling
- Use appropriate imputation strategies for each data type
- Validate data after cleaning to ensure readiness for analysis
- Remove duplicates to avoid bias
- Group rare categories to improve model stability
- Scale features for algorithms sensitive to magnitude

Refer to the ML Workflow guide for next steps after cleaning.

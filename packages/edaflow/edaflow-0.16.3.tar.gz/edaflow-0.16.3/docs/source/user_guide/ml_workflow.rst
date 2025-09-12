Machine Learning Workflow with edaflow
=====================================

This guide consolidates all steps for a complete ML workflow using edaflow, from experiment setup to model deployment.

**Step 1: Setup ML Experiment**
------------------------------
.. code-block:: python

   experiment = ml.setup_ml_experiment(df, 'target')  # DataFrame style
   # OR
   experiment = ml.setup_ml_experiment(X=X, y=y, val_size=0.15)  # sklearn style

**Step 2: Compare Multiple Models**
-----------------------------------
.. code-block:: python

   models = {
       'RandomForest': RandomForestClassifier(),
       'LogisticRegression': LogisticRegression()
   }
   results = ml.compare_models(models, **experiment)

**Step 3: Optimize Hyperparameters**
------------------------------------
.. code-block:: python

   model_name = 'LogisticRegression'  # or 'RandomForest' or 'GradientBoosting'

   if model_name == 'RandomForest':
       param_distributions = {
           'n_estimators': [100, 200, 300],
           'max_depth': [5, 10, 15, None],
           'min_samples_split': [2, 5, 10]
       }
       model = RandomForestClassifier()
       method = 'grid'
   elif model_name == 'GradientBoosting':
       param_distributions = {
           'n_estimators': (50, 200),
           'learning_rate': (0.01, 0.3),
           'max_depth': (3, 8)
       }
       from sklearn.ensemble import GradientBoostingClassifier
       model = GradientBoostingClassifier()
       method = 'bayesian'
   elif model_name == 'LogisticRegression':
       param_distributions = {
           'C': [0.01, 0.1, 1, 10, 100],
           'penalty': ['l1', 'l2', 'elasticnet', 'none'],
           'solver': ['lbfgs', 'liblinear', 'saga']
       }
       model = LogisticRegression(max_iter=1000)
       method = 'grid'
   else:
       raise ValueError(f"Unknown model_name: {model_name}")

   results = ml.optimize_hyperparameters(
       model,
       param_distributions=param_distributions,
       **experiment
   )

**Step 4: Rank and Select Best Model**
--------------------------------------
.. code-block:: python

   best_model_name = ml.rank_models(results, 'accuracy', return_format='list')[0]['model_name']
   ranked_df = ml.rank_models(results, 'accuracy')
   best_model_traditional = ranked_df.iloc[0]['model']

**Step 5: Save Model Artifacts**
-------------------------------
.. code-block:: python

   ml.save_model_artifacts(
       model=results['best_model'],
       model_name=best_model_name,
       experiment_config=experiment,
       performance_metrics=results['cv_results']
   )

**Step 6: Visualize Learning Curves**
-------------------------------------
.. code-block:: python

   ml.plot_learning_curves(results['best_model'], **experiment)

**Tips:**
- All steps above are copy-paste safe and work for RandomForest, LogisticRegression, and GradientBoosting.
- For more advanced workflows, see the User Guide and API Reference.

# Classification Example with edaflow
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import edaflow.ml as ml

# Load data
df = pd.read_csv('your_classification_data.csv')

# Setup experiment
experiment = ml.setup_ml_experiment(df, 'target')

# Compare models
models = {
    'RandomForest': RandomForestClassifier(),
    'LogisticRegression': LogisticRegression()
}
results = ml.compare_models(models, **experiment)

# Optimize hyperparameters for best model
model = RandomForestClassifier()
param_distributions = {'n_estimators': [100, 200, 300]}
opt_results = ml.optimize_hyperparameters(model, param_distributions=param_distributions, **experiment)

# Save artifacts
ml.save_model_artifacts(model=opt_results['best_model'], model_name='optimized_rf', experiment_config=experiment, performance_metrics=opt_results['cv_results'])

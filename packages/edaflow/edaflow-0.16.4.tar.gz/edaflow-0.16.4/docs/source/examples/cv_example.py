# Computer Vision Example with edaflow
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import edaflow.ml as ml

# Load image classification data
df = pd.read_csv('your_image_data.csv')

# EDA for computer vision
df_quality = edaflow.image_quality_assessment(df, image_column='image_path')
edaflow.visualize_image_samples(df, image_column='image_path', class_column='label')

# Setup experiment
experiment = ml.setup_ml_experiment(df, 'label')

# Compare models
models = {
    'RandomForest': RandomForestClassifier()
}
results = ml.compare_models(models, **experiment)

Best Practices for edaflow
=========================

- Always verify your data quality before starting ML workflows
- Use `setup_ml_experiment` for reproducible train/val/test splits
- Compare multiple models before optimizing hyperparameters
- Use copy-paste-safe param_distributions blocks for supported models
- Save model artifacts and document your workflow for reproducibility
- Refer to the User Guide and API Reference for troubleshooting and advanced usage

**Best Practices for New Features**
-----------------------------------
- Use `display_facet_grid` for multi-category visual analysis
- Apply `scale_features` before ML modeling for better results
- Use `group_rare_categories` to simplify categorical variables
- Export figures with `export_figure` for reproducible reporting
- Always check external library requirements before using advanced features

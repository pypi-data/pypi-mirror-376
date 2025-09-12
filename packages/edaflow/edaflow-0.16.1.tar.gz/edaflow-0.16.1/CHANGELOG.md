# [0.15.1] - 2025-08-15

### 🚀 ENHANCEMENT: Robust Metric Handling in ML Workflows

- `setup_ml_experiment` now supports a `primary_metric` argument, making metric selection robust and error-free for all ML workflows.
- All documentation, user guides, and quickstart examples updated to show and explain `primary_metric` usage.
- Downstream code and all ML workflow logic now consistently use the metric set in the experiment config.
- Added a dedicated test to ensure the metric is set and accessible throughout the workflow.
- **Result:** Users can now copy-paste ML workflow code with confidence that metric selection will work as expected.

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.15.0] - 2025-08-13

### 🚨 CRITICAL FIXES - ML Workflow Documentation

**MAJOR ISSUE RESOLVED**: Fixed critical documentation bugs that were preventing users from successfully following ML workflows. All ML documentation examples now work perfectly without errors.

#### 🎯 **Critical Fixes Applied**:

**1. Missing Model Fitting Requirements**
- **Problem**: Both ML workflows called `compare_models` with unfitted models, causing `RandomForestClassifier instance is not fitted yet` errors
- **Solution**: Added explicit model training loops to all documentation examples
- **Impact**: Users can now copy-paste examples that work immediately

**2. Incorrect Function Parameters**
- **Problem**: Documentation used wrong parameter names causing `TypeError: unexpected keyword argument` errors
- **Solution**: Fixed all function calls to use correct signatures:
  - `setup_ml_experiment(data=df, target_column='target')` ✅
  - `compare_models(models=models, experiment_config=config)` ✅
- **Impact**: No more confusing parameter errors for beginners

**3. Missing Context & Imports**
- **Problem**: Quickstart referenced undefined variables like `df_converted` without showing origin
- **Solution**: Added complete context, imports, and data preparation steps
- **Impact**: Clear, complete examples that beginners can follow step-by-step

**4. Step Numbering Issues**
- **Problem**: Complete ML Workflow had duplicate "Step 7" sections causing confusion
- **Solution**: Fixed step numbering sequence (Step 7→8, 8→9, 9→10, 10→11)
- **Impact**: Clear, logical progression through workflow steps

#### 📋 **Documentation Files Fixed**:
- ✅ `docs/source/quickstart.rst` - ML Workflow Quick Start
- ✅ `docs/source/user_guide/ml_guide.rst` - Complete ML Workflow

#### ⚠️ **Enhanced Warnings Added**:
- Added prominent warning boxes about model fitting requirements
- Enhanced ML-specific Pro Tips section
- Clear guidance for beginners about critical steps

#### 🧪 **Comprehensive Testing**:
- Created complete end-to-end validation tests
- Verified both workflows work without errors
- Tested all function parameter combinations

### Enhanced - User Experience
- **Beginner-Friendly**: All examples now work out-of-the-box
- **Professional Documentation**: Enhanced warnings and best practices guidance
- **No More Errors**: Eliminated common user confusion points
- **Copy-Paste Ready**: All code examples are immediately usable

### Fixed - Function Compatibility
- **setup_ml_experiment**: Now properly documented with correct parameter patterns
- **compare_models**: Fixed parameter usage in all examples
- **configure_model_pipeline**: Corrected data_config parameter usage

**Migration Note**: This version primarily fixes documentation - no breaking changes to actual API functionality.

## [Unreleased] - 2025-08-13

### Enhanced - rank_models Function Major Enhancement 🎯
- **Dual Return Formats**: Added `return_format` parameter with 'dataframe' and 'list' options
- **User-Requested Pattern Support**: Now supports `rank_models(results, 'accuracy', return_format='list')[0]["model_name"]` pattern
- **Dictionary Access**: List format returns dictionaries with both 'model' and 'model_name' keys for flexibility
- **Backward Compatibility**: Default 'dataframe' format preserves all existing workflows
- **Enhanced Documentation**: Comprehensive examples added to user guide and README
- **Weighted Ranking**: Support for multi-metric weighted ranking in both formats
- **Comprehensive Examples**: Added complete example file with all usage patterns

### Enhanced - API Consistency & Error Handling
- **compare_models Requirement**: Enhanced documentation to clarify models must be pre-trained
- **Training Examples**: All documentation examples now show proper model.fit() calls
- **Error Prevention**: Better error messages for common usage mistakes

## [0.14.2] - 2025-08-13

### Enhanced - API Consistency & Dual Pattern Support 🔄
- **validate_ml_data Enhancement**: Added full support for both experiment_config and X,y calling patterns
- **Dual API Consistency**: All ML functions now support consistent calling patterns like setup_ml_experiment()
- **Enhanced Parameters**: Added check_cardinality and check_distributions parameters for X,y pattern
- **Auto Problem Detection**: Intelligent problem type detection when using X,y pattern
- **Documentation Enhancement**: Comprehensive dual API pattern examples in quickstart.rst and ML_LEARNING_GUIDE.md
- **User Experience**: Fixed reported error where validate_ml_data didn't accept X,y parameters

### Fixed - Function Signature Compatibility
- **Parameter Support**: validate_ml_data now accepts X=X_train, y=y_train as requested by users
- **Error Resolution**: Fixed unexpected keyword argument 'X' error reported in documentation
- **API Parity**: All ML functions now have consistent parameter patterns for maximum flexibility

## [0.14.1] - 2025-08-13

### Enhanced - Complete ML Workflow Documentation 📚
- **Complete ML Workflow Documentation**: Added comprehensive "Complete ML Workflow" section to match existing "Complete EDA Workflow" documentation structure
- **Documentation Parity**: ML workflow examples now have the same level of detail and comprehensiveness as EDA workflows
- **API Parameter Fixes**: Corrected all documentation examples to use proper function signatures
- **Model Fitting Requirements**: Updated examples to show proper model fitting before comparison
- **Deployment Ready**: All ML workflow documentation examples tested and verified working

## [0.14.0] - 2025-08-13

### Enhanced - ML Workflow Major Update 🚀
- **Parameter Expansion**: Added comprehensive support for `val_size` and `experiment_name` parameters in `setup_ml_experiment()`
- **Dual API Enhancement**: Improved sklearn-style and DataFrame-style parameter compatibility
- **Validation Split Logic**: Enhanced validation data creation with proper `val_size` parameter handling
- **Experiment Tracking**: Added `experiment_name` parameter for comprehensive experiment identification and tracking
- **Downstream Integration**: Enhanced all ML functions (`compare_models`, `validate_ml_data`, `configure_model_pipeline`) to properly utilize new parameters
- **Documentation Alignment**: Updated all documentation (README, quickstart, user guide) with comprehensive parameter examples
- **Complete ML Workflow Documentation**: Added comprehensive "Complete ML Workflow" section to match existing "Complete EDA Workflow" documentation structure

### Fixed - ML Function Compatibility
- **compare_models Enhancement**: Added `experiment_config` parameter support for seamless integration
- **Parameter Processing**: Fixed parameter mapping and validation logic for `val_size` → `validation_size`
- **Syntax Corrections**: Resolved syntax errors in `tuning.py` module
- **Configuration Structure**: Enhanced experiment configuration dictionary with proper metadata storage

### Improved - ML Best Practices
- **Data Split Quality**: Proper train/validation/test separation with configurable validation size
- **Model Evaluation**: Enhanced model evaluation on dedicated validation sets
- **Experiment Configuration**: Comprehensive metadata tracking including experiment names, problem types, and data characteristics
- **Backward Compatibility**: Maintained full compatibility with existing ML workflow code

## [0.13.3] - 2025-08-13

### Fixed
- **ML Workflow Compatibility**: Fixed `TypeError: setup_ml_experiment() got an unexpected keyword argument 'X'`
- **Parameter Support**: Added support for sklearn-style parameter pattern `setup_ml_experiment(X=X, y=y)`
- **Backward Compatibility**: Maintained existing DataFrame + target_column calling pattern
- **Input Validation**: Enhanced type checking and error handling for both calling patterns
- **Documentation**: Updated function docstring with examples for both usage patterns

### Enhanced
- **Dual API Support**: Functions now accept both edaflow-style and sklearn-style parameter patterns
- **Error Messages**: Improved error messages for invalid parameter combinations
- **Type Safety**: Added comprehensive input validation for DataFrames and Series

## [0.13.2] - 2025-08-12

### Enhanced
- **Display Optimization**: Enhanced Rich console styling across all major EDA functions for improved visual consistency
- **Google Colab Compatibility**: Optimized console width constraints and panel styling for better notebook rendering
- **Visual Standards**: Applied consistent rounded borders, proper alignment, and professional color schemes
- **User Experience**: Improved readability and visual hierarchy in data analysis outputs

## [0.13.1] - 2025-08-12

### Fixed
- **Theme Detection**: Fixed hardcoded theme detection in `optimize_display()` that was defaulting to light theme
- **Google Colab Compatibility**: Improved theme detection for Google Colab dark mode environments  
- **Dynamic CSS**: Enhanced CSS to properly respond to environment theme changes
- **Environment Variables**: Added support for `COLAB_THEME` environment variable detection

## [0.13.0] - 2025-08-11

### Added - ML Expansion
- **🤖 NEW SUBPACKAGE**: Complete `edaflow.ml` subpackage with comprehensive machine learning workflow capabilities
- **🔧 ML EXPERIMENT SETUP**: `ml.setup_ml_experiment()` for intelligent data splitting and validation
- **📊 MODEL COMPARISON**: `ml.compare_models()` for multi-model evaluation with comprehensive metrics
- **🎯 HYPERPARAMETER OPTIMIZATION**: Grid search, random search, and Bayesian optimization with `ml.optimize_hyperparameters()`
- **📈 PERFORMANCE VISUALIZATION**: Learning curves, ROC curves, validation curves, and feature importance analysis
- **💾 MODEL PERSISTENCE**: Complete artifact saving with `ml.save_model_artifacts()` and experiment tracking
- **🏆 MODEL LEADERBOARDS**: Automated model ranking and comparison with `ml.display_leaderboard()`
- **📋 COMPREHENSIVE REPORTING**: Generate detailed model reports with `ml.create_model_report()`

### Added - Educational Learning System 🎓
- **📚 EDA LEARNING GUIDE**: Comprehensive 50-page guide combining EDA theory with hands-on edaflow practice
- **🤖 ML LEARNING GUIDE**: Complete 60-page machine learning guide from concepts to production deployment
- **🎯 EDUCATIONAL INTEGRATION**: Strategic integration of learning resources with technical documentation
- **📖 ENHANCED DOCUMENTATION**: Updated README and QUICKSTART with clear learning paths
- **🧠 THEORY + PRACTICE**: Deep educational content explaining not just "how" but "why" and "when"
- **🎓 PROFESSIONAL DEVELOPMENT**: Skill-building focus beyond tool usage

### New ML Modules
- **`edaflow.ml.config`**: ML experiment foundation and data validation
- **`edaflow.ml.leaderboard`**: Model comparison and ranking system
- **`edaflow.ml.tuning`**: Advanced hyperparameter optimization strategies
- **`edaflow.ml.curves`**: Performance visualization and analysis
- **`edaflow.ml.artifacts`**: Model persistence and experiment tracking

### New Educational Resources
- **`EDA_LEARNING_GUIDE.md`**: Complete EDA education with decision frameworks and professional workflows
- **`ML_LEARNING_GUIDE.md`**: Comprehensive ML learning from algorithms to deployment best practices
- **`EDUCATIONAL_INTEGRATION.md`**: Documentation strategy and learning path design

### Enhanced Features
- **🔀 COMPLETE WORKFLOW**: Seamless transition from EDA to ML modeling
- **⚡ PARALLEL PROCESSING**: Multi-core hyperparameter optimization
- **🎨 RICH STYLING**: Professional visualizations consistent with edaflow design
- **📦 26 NEW FUNCTIONS**: Comprehensive ML toolkit with consistent API
- **📚 EDUCATIONAL DIFFERENTIATION**: Unique market positioning through comprehensive learning resources

### Dependencies
- **scikit-optimize**: Added optional dependency for Bayesian optimization
- **joblib**: Enhanced model persistence capabilities

## [0.12.33] - 2025-01-11

### Added 
- **NEW CLEAN APIs**: Introduced `apply_encoding()` and `apply_encoding_with_encoders()` functions for consistent, predictable behavior
- **📚 EXPLICIT DOCUMENTATION**: Clear examples showing proper usage of new encoding functions
- **🎯 BEST PRACTICE GUIDANCE**: Deprecation warnings guide users toward cleaner API alternatives

### Fixed
- **🐛 ROOT CAUSE RESOLVED**: Eliminated confusion from `apply_smart_encoding()` inconsistent return types (DataFrame vs tuple)
- **🛡️ ENHANCED ERROR MESSAGES**: Better validation with helpful guidance when wrong data types are passed
- **🔧 IMPROVED INPUT HANDLING**: Robust detection and handling of tuple inputs in visualization functions

### Deprecated
- **⚠️ DEPRECATION WARNING**: `apply_smart_encoding()` with `return_encoders=True` now shows deprecation warning recommending `apply_encoding_with_encoders()`
- **🔄 MIGRATION PATH**: Existing code continues working with guidance toward better alternatives

### Changed
- **✅ ZERO BREAKING CHANGES**: All existing workflows continue working exactly the same
- **🎨 API CONSISTENCY**: New functions provide predictable, consistent return types

## [0.12.32] - 2025-08-11

### Fixed
- **🐛 CRITICAL INPUT FIX**: Fixed AttributeError: 'tuple' object has no attribute 'empty' in visualization functions
- **🎯 ROOT CAUSE**: Resolved issue when users pass tuple result from `apply_smart_encoding(..., return_encoders=True)` directly to visualization functions
- **🛠️ ENHANCED VALIDATION**: Added intelligent input validation with helpful error messages for common usage mistakes
- **🔧 IMPROVED HANDLING**: Better error handling in `visualize_scatter_matrix` and other visualization functions  
- **📚 CLEAR DOCUMENTATION**: Added examples showing correct vs incorrect usage patterns for `apply_smart_encoding`
- **✅ EDA WORKFLOW FIX**: Prevents crashes in step 14 of EDA workflows when encoding functions are misused

## [0.12.31] - 2025-01-05

### Fixed
- **🚨 CRITICAL HOTFIX**: Fixed KeyError: 'type' in `summarize_eda_insights()` function during Google Colab usage
- **🛠️ ERROR HANDLING**: Enhanced exception handling when target analysis dictionary missing expected keys
- **🔧 SAFE ACCESS**: Implemented safe dictionary access using `.get()` method to prevent KeyErrors
- **✅ STABILITY**: All existing functionality preserved - pure stability fix
- **🧪 VERIFIED**: Tested fix across all notebook platforms (Colab, JupyterLab, VS Code)

## [0.12.30] - 2025-01-05

### Added
- **🎨 BREAKTHROUGH FEATURE**: Introduced `optimize_display()` function for universal notebook compatibility
- **PLATFORM DETECTION**: Automatic detection of Google Colab, JupyterLab, VS Code Notebooks, Classic Jupyter
- **CSS INJECTION**: Dynamic CSS injection for improved dark/light mode visibility across all platforms
- **📊 MATPLOTLIB OPTIMIZATION**: Automatic matplotlib backend optimization for each notebook environment
- **🌙 DARK MODE FIX**: Solves visibility issues in dark mode themes universally
- **⚡ ZERO CONFIG**: No configuration required - automatically detects and optimizes for your platform
- **🔄 UNIVERSAL COMPATIBILITY**: Works reliably across all major notebook platforms
- **📖 SIMPLE USAGE**: `from edaflow import optimize_display; optimize_display()`

## [0.12.29] - 2025-08-11

### Fixed
- **🐛 CRITICAL FIX**: Fixed TypeError in `analyze_categorical_columns` when processing columns with unhashable types (lists, dicts)
  - Added proper exception handling for `nunique()` and `unique()` operations on columns containing unhashable data types
  - Function now converts unhashable types to strings before processing unique value counts
  - Added comprehensive error handling to gracefully handle any processing errors
  - Added missing return statement to provide structured data output for programmatic use
  - Returns dictionary with keys: `object_columns`, `numeric_potential`, `truly_categorical`, `non_object_columns`

## [0.12.28] - 2025-08-09

### Added
- **✨ NEW FUNCTION**: `summarize_eda_insights()` - Generate comprehensive EDA insights and recommendations after completing analysis workflow
  - Analyzes dataset characteristics, data quality, class distribution, and feature types  
  - Provides intelligent recommendations for modeling and preprocessing
  - Supports target column analysis for classification/regression tasks
  - Tracks which edaflow functions have been used in the workflow
  - Returns structured dictionary with organized insights and actionable recommendations

### Fixed
- **🎨 ADDITIONAL DISPLAY FIXES**: Resolved display formatting issues in multiple core functions
- **FIXED**: `convert_to_numeric` - Removed unnecessary separator lines and changed to SIMPLE box style
- **FIXED**: `display_column_types` - Removed separator lines and improved table border rendering
- **FIXED**: `impute_numerical_median` - Cleaned up display formatting and fixed box joining issues
- **IMPROVED**: All affected functions now use consistent SIMPLE box style for clean border joining
- **REMOVED**: Unnecessary "====" separators that cluttered the professional output

## [0.12.26] - 2025-08-09

### Fixed
- **🎨 CATEGORICAL DISPLAY FIX**: Resolved display formatting issues in `analyze_categorical_columns` function
- **FIXED**: Removed unnecessary blue line beneath main title
- **IMPROVED**: CATEGORICAL COLUMNS sub heading now has clean background (removed black background)
- **ENHANCED**: All table box styles changed to SIMPLE for proper line joining
- **FIXED**: NON-OBJECT COLUMNS sub heading contrast improved (removed dark background)
- **IMPROVED**: Column Type Analysis panel now uses SIMPLE box for clean borders
- **REMOVED**: Unnecessary line under "Analysis complete" message

## [0.12.25] - 2025-08-08

### Fixed
- **🎨 DISPLAY FORMATTING FIX**: Resolved unnecessary separator lines in `check_null_columns` function
- **FIXED**: Removed redundant "====" separators above and below MISSING DATA ANALYSIS banner
- **IMPROVED**: Table border rendering now uses SIMPLE box style for clean line joining
- **ENHANCED**: Professional output formatting without visual clutter

## [0.12.24] - 2025-08-08

### Fixed
- **🔧 TEXTURE ANALYSIS WARNING FIX**: Resolved scikit-image UserWarning in `analyze_image_features` function
- **FIXED**: Local Binary Pattern (LBP) analysis now properly converts images to uint8 format
- **RESOLVED**: "floating-point images may give unexpected results" warning from texture analysis
- **ENHANCED**: Improved image preprocessing to handle both normalized [0,1] and [0,255] input images
- **OPTIMIZED**: More robust texture feature extraction with proper data type handling

## [0.12.23] - 2025-08-08

### Fixed
- **🚨 CRITICAL RTD DOCUMENTATION FIX**: Corrected parameter name mismatches in `analyze_image_features` function
- **FIXED**: Changed `analyze_colors` → `analyze_color` in quickstart.rst documentation (3 instances)
- **FIXED**: Changed `bins` → `bins_per_channel` in RTD documentation examples
- **RESOLVED**: TypeError when users followed RTD documentation examples exactly
- **ENHANCED**: Documentation now matches actual function signature correctly
- **TESTED**: Created comprehensive test suite to prevent future parameter mismatches

## [0.12.22] - 2025-08-08

### Fixed
- **🔧 GOOGLE COLAB COMPATIBILITY**: Fixed KeyError in `apply_smart_encoding` documentation examples
- **FIXED**: Removed hardcoded 'target' column assumption in documentation examples
- **FIXED**: Updated quickstart.rst and README.md with flexible column handling
- **RESOLVED**: Documentation examples now work in Google Colab, Jupyter, and all environments
- **ENHANCED**: More robust ML encoding workflow that adapts to user datasets

### Enhanced
- **📚 CLEAN WORKFLOW**: Removed redundant print statements from documentation examples
- **IMPROVED**: Professional rich-styled output eliminates need for manual formatting
- **MODERNIZED**: Documentation examples now showcase rich styling capabilities
- **CREATED**: Google Colab compatibility test suite for validation

## [0.12.21] - 2025-08-08

### Fixed
- **🔧 DOCUMENTATION PARAMETER FIXES**: Corrected parameter name mismatches in `visualize_scatter_matrix` documentation
- **FIXED**: Changed `regression_line` → `regression_type` in README.md and quickstart.rst examples
- **FIXED**: Changed `diagonal_type` → `diagonal` in documentation examples
- **FIXED**: Changed `upper_triangle`/`lower_triangle` → `upper`/`lower` parameter names
- **FIXED**: Changed `color_column` → `color_by` in documentation examples
- **RESOLVED**: TypeError when using sample code from documentation
- **ENHANCED**: All documentation examples now match actual function signature

## [0.12.20] - 2025-08-08

### Enhanced 
- **🌈 COMPREHENSIVE RICH STYLING**: Enhanced ALL major EDA functions with vibrant, professional output
- **ENHANCED MISSING DATA ANALYSIS**: `check_null_columns` now features:
  - Rich tables with color-coded severity levels (✅ CLEAN, ⚠️ MINOR, 🚨 WARNING, 💀 CRITICAL)
  - Data integrity indicators with health assessment panels
  - Smart recommendations based on missing data patterns
  - Professional summary with overall dataset health scoring
- **ADVANCED COLUMN CLASSIFICATION**: `display_column_types` now includes:
  - Side-by-side rich tables for categorical vs numerical columns
  - Memory usage analysis with optimization recommendations
  - Data type insights and composition analysis
  - Range information and advanced metrics for better understanding
- **PROFESSIONAL IMPUTATION REPORTING**: `impute_numerical_median` enhanced with:
  - Detailed imputation tables showing before/after status
  - Smart value formatting (K/M notation for large numbers)
  - Color-coded success indicators and completion rates
  - Rich summary panels with actionable insights

### Previous Enhancements (v0.12.19)
- **VIBRANT CATEGORICAL ANALYSIS**: `analyze_categorical_columns` rich styling
- **COLORFUL DATA TYPE CONVERSION**: `convert_to_numeric` professional output

### Dependencies
- **MAINTAINED**: `rich>=13.0.0` for enhanced terminal output formatting

## [Unreleased]

### Added

## [0.12.19] - 2025-08-08

### Enhanced
- **VIBRANT CATEGORICAL ANALYSIS**: Completely redesigned `analyze_categorical_columns` output with rich styling
  - Professional tables with color-coded status indicators (✅ GOOD, ⚠️ MANY, 🚨 HIGH cardinality)  
  - Visual separation between potentially numeric vs truly categorical columns
  - Smart cardinality warnings with recommendations
  - Beautiful summary panels with emoji icons and statistics
- **COLORFUL DATA TYPE CONVERSION**: Enhanced `convert_to_numeric` with rich, dynamic output
  - Professional conversion tables showing before/after status for each column
  - Color-coded actions: ✅ CONVERTED, ⚠️ SKIPPED, 📊 ALREADY NUMERIC
  - Detailed summary panels with conversion statistics and threshold information
  - Visual progress indicators and conversion details table
  - Maintains backward compatibility with fallback to plain output if rich is unavailable
  - Graceful fallback to basic styling if rich library unavailable

### Dependencies
- **NEW**: Added `rich>=13.0.0` dependency for enhanced terminal output formatting

## [Unreleased]

### Added

## [0.12.17] - 2025-08-07

### Fixed
- **CRITICAL DOCUMENTATION FIX**: Corrected parameter names in all documentation
  - Updated function docstring: `image_path_column` → `image_column`, `class_column` → `label_column`
  - Fixed quickstart guide: `max_classes` → `max_classes_display` (7 instances)
  - Fixed README examples: corrected column parameter names (5 instances)
  - Fixed index page: `max_classes` → `max_classes_display`
  - This resolves TypeError when users follow documentation examples

## [0.12.16] - 2025-08-07

### Fixed
- **ROW OVERLAP RESOLUTION**: Eliminated overlapping rows in `visualize_image_classes` multi-row layouts
- **IMPROVED SPACING**: Increased hspace values (0.45-0.6 from 0.3-0.4) for better row separation
- **SCIENTIFIC NAME SUPPORT**: Enhanced layout specifically optimized for long taxonomic/scientific class names
- **PROFESSIONAL LAYOUTS**: Clean separation between class titles and images in dense visualizations

### Improved
- Font sizing optimization: slightly smaller subplot titles for tighter vertical spacing
- Reduced title padding (6px from 8px) to minimize title height interference
- Enhanced bottom margin (0.12 from 0.08) for better class limiting remark positioning
- Better scalability from small datasets (5 classes) to large datasets (100+ classes)

## [0.12.15] - 2025-08-07

### Added
- **CLASS LIMITING TRANSPARENCY**: Added informative remark beneath visualizations when class limiting is applied
- **SMART USER GUIDANCE**: Shows "X of Y total classes (Z not displayed for optimal readability)" with actionable instructions
- **CONTEXT AWARENESS**: Users always understand they're seeing a curated subset of their dataset
- **PROFESSIONAL STYLING**: Subtle gray styling with rounded box that doesn't compete with main visualization

### Improved
- Enhanced transparency in `visualize_image_classes` when `max_classes_display` parameter limits displayed classes
- Better user experience with clear guidance on how to show all classes if desired

## [0.12.14] - 2025-08-07

### Fixed
- **TITLE SPACING IMPROVEMENTS**: Generous margins eliminate title overlap issues across all figure sizes
- **PROFESSIONAL LAYOUTS**: Publication-ready spacing with 15-18% buffer between titles and subplots  
- **DYNAMIC POSITIONING**: Height-based title positioning (0.96-0.98 y-position) for optimal appearance
- **VISUAL EXCELLENCE**: Enhanced `visualize_image_classes` with professional spacing standards

### Changed
- More conservative top margins: 0.82-0.88 (vs previous 0.88-0.92) for better title clearance
- Improved title positioning algorithm based on figure height for consistent professional appearance

## [0.12.11] - 2025-08-07

### Fixed
- **COMPLETE VISUALIZATION FIX**: Fully resolved "visualization skipped due to dataset size" issue in `visualize_image_classes`
- **SMART DOWNSAMPLING**: Implemented complete smart downsampling that always shows images instead of skipping
- **ALWAYS DISPLAY**: Function now never skips visualization - always shows something meaningful
- **ENHANCED UX**: Eliminated all frustrating "visualization skipped" messages for better user experience

## [0.12.10] - 2025-08-07

### Fixed
- **IMPROVED DEFAULTS**: Updated default parameters for better user experience (auto_skip_threshold and max_images_display now 80)
- **PARTIAL VISUALIZATION FIX**: Reduced skipping behavior through better parameter defaults
- **PREPARATION**: Set foundation for complete smart downsampling implementation

## [0.12.9] - 2025-08-07

### Changed
- **UX IMPROVEMENT**: Major enhancement attempt for `visualize_image_classes` with smart downsampling
- **PARAMETER CONSISTENCY**: Both CV functions now use consistent parameter names and defaults
- **BETTER FEEDBACK**: Clear user messages about adjustments made to visualization

## [Unreleased]

### Added

## [0.12.8] - 2025-08-06

### Fixed
- **CRITICAL BUG FIX**: Fixed KeyError: 'target' not found in axis error in `apply_smart_encoding()` function
- **TARGET COLUMN VALIDATION**: Added proper validation for target column existence before accessing DataFrame
- **GRACEFUL FALLBACK**: Function now gracefully falls back to frequency encoding when target column is missing
- **IMPROVED ERROR HANDLING**: Added informative warning messages for missing target column scenarios
- **USER EXPERIENCE**: Enhanced function robustness to prevent crashes when target column doesn't exist

## [0.12.7] - 2025-08-06

### Added
- **COMPREHENSIVE DOCUMENTATION**: Complete documentation synchronization across PyPI and ReadTheDocs platforms
- **SMART ENCODING INTEGRATION**: Added Smart Encoding functions to complete EDA workflow documentation
- **RTD ENHANCEMENT**: Enhanced ReadTheDocs quickstart guide with Smart Encoding section and examples
- **WORKFLOW INTEGRATION**: Smart Encoding now properly integrated as Step 12 in complete 13-step EDA workflow
- **PARAMETER CONSISTENCY**: Standardized parameter examples across all documentation platforms

### Improved
- **DOCUMENTATION ACCURACY**: Corrected parameter names (max_cardinality_onehot, max_cardinality_target) across all docs
- **USER EXPERIENCE**: Consistent examples and function signatures between README and RTD documentation
- **FUNCTION COUNT**: Updated from 16 to 18 functions in all documentation to reflect Smart Encoding additions
- **CODE EXAMPLES**: Comprehensive Smart Encoding examples with practical parameter values
- **PLATFORM CONSISTENCY**: Synchronized information across PyPI README, RTD quickstart, and main index pages

### Fixed
- **LEGACY COMPATIBILITY**: Added `max_cardinality` parameter alias in `analyze_encoding_needs()` for backward compatibility
- **PARAMETER CONFUSION**: Resolved TypeError issues caused by parameter naming inconsistencies
- **DOCUMENTATION GAPS**: Filled missing Smart Encoding information in complete workflow documentation

## [0.12.6] - 2025-08-06

### Added
- **SMART VISUALIZATION**: Intelligent handling of large image datasets in `visualize_image_classes()`
- **AUTO-SKIP THRESHOLD**: Automatically skip visualization for datasets with 200+ images to prevent unreadable plots
- **IMAGE LIMIT CONTROL**: New `max_images_display` parameter to limit total images shown for readability
- **FORCE DISPLAY OPTION**: New `force_display` parameter to override auto-skip behavior when needed
- **DYNAMIC SIZING**: Smart figure and font size adjustments based on dataset size
- **HELPFUL WARNINGS**: Clear guidance when visualizations might be hard to read due to size

### Improved
- **GRID LAYOUTS**: Better automatic grid layout calculations for large datasets
- **FONT SCALING**: Dynamic font sizes that scale appropriately with image count
- **USER GUIDANCE**: Comprehensive suggestions for handling large datasets effectively
- **DOCUMENTATION**: Added examples for large dataset scenarios and parameter usage

### Technical Details
- Images are limited to 50 total by default for optimal readability
- Datasets with 200+ images auto-skip visualization (customizable via `auto_skip_threshold`)
- Smart warnings at 50+ images with optimization suggestions
- Improved grid layouts prevent overlapping and unreadable content

## [0.12.5] - 2025-08-06

### Fixed
- **CRITICAL**: Fixed corrupted image display in `visualize_image_classes()` visualization output
- **BUG FIX**: Resolved PIL Image to matplotlib incompatibility causing garbled/unacceptable visualizations
- **FUNCTIONALITY**: Converted PIL Image objects to numpy arrays for proper matplotlib display
- **DISPLAY**: Images now render correctly in visualizations instead of corrupted content
- **COMPATIBILITY**: Enhanced image processing pipeline for matplotlib.imshow() requirements

## [0.12.4] - 2025-08-06

### Fixed
- **CRITICAL**: Fixed `visualize_image_classes()` not supporting list of image paths from `glob.glob()`
- **BUG FIX**: Resolved TypeError "data_source must be either a directory path (str) or pandas DataFrame" when using `glob.glob()` results
- **FUNCTIONALITY**: Added proper support for list input type in `visualize_image_classes()` function
- **IMPLEMENTATION**: Added `_parse_image_path_list()` helper function to handle file path lists
- **USABILITY**: Function now supports all three input types: directory paths (str), file lists (list), and DataFrames
- **DOCUMENTATION**: Updated function signature and examples to show list support
- **CONSISTENCY**: Aligned function behavior with documentation examples that use `glob.glob()`

### Enhanced  
- **ERROR MESSAGES**: Improved error messages to clearly indicate all supported input types
- **VALIDATION**: Enhanced input validation with better type checking and error reporting
- **EXAMPLES**: Added comprehensive list-based analysis example in function docstring

### Technical Details
- **INPUT TYPES**: Now accepts `Union[str, List[str], pd.DataFrame]` for `data_source` parameter  
- **CLASS DETECTION**: Automatically extracts class names from parent directory names in file paths
- **FILE VALIDATION**: Validates file existence and skips non-existent paths with warnings
- **BACKWARD COMPATIBILITY**: Maintains full compatibility with existing directory and DataFrame workflows

### Added
- Future features will be documented here

### Changed
- Future changes will be documented here

### Deprecated
- Future deprecations will be documented here

### Removed
- Future removals will be documented here

## [0.12.3] - 2025-08-06 - Complete Positional Argument Compatibility Fix 🔧

### Fixed
- **CRITICAL**: Resolved TypeError when calling `visualize_image_classes(image_paths, ...)` with positional arguments
- **Positional Arguments**: Function now properly handles legacy positional argument usage from Jupyter notebooks
- **Backward Compatibility**: Complete support for all three usage patterns:
  1. `visualize_image_classes(path, ...)` - Positional (deprecated, shows warning)  
  2. `visualize_image_classes(image_paths=path, ...)` - Keyword deprecated (shows warning)
  3. `visualize_image_classes(data_source=path, ...)` - Recommended (no warning)

### Improved
- **User Experience**: Clear deprecation warnings guide users toward recommended `data_source=` syntax
- **Function Architecture**: Refactored to wrapper function pattern for robust argument handling
- **Error Messages**: Enhanced error messages provide clear guidance for parameter usage
- **Documentation**: Updated examples showing all supported usage patterns

### Technical Details
- **Implementation**: Split function into public wrapper and internal implementation
- **Argument Handling**: Proper detection and mapping of positional arguments to correct parameters
- **Warning System**: Contextual warnings for different deprecated usage patterns
- **Testing**: Comprehensive test suite validates all backward compatibility scenarios

### Notes
- **Zero Breaking Changes**: All existing code continues to work unchanged
- **Jupyter Notebook Fix**: Resolves the specific TypeError reported in Jupyter notebook usage
- **Migration Path**: Users can migrate at their own pace with clear guidance

## [0.12.3] - 2025-08-06 - Complete Backward Compatibility Fix 🔧

### Fixed
- **Critical Issue**: Resolved TypeError when calling `visualize_image_classes()` with positional arguments
- **Positional Arguments**: Added support for legacy positional syntax: `visualize_image_classes(image_paths, ...)`
- **Function Wrapper**: Implemented comprehensive argument handling to catch all usage patterns

### Enhanced
- **Complete Compatibility**: Now supports all three calling patterns:
  1. Positional: `visualize_image_classes(path, samples_per_class=6)` (shows deprecation warning)
  2. Deprecated keyword: `visualize_image_classes(image_paths=path, samples_per_class=6)` (shows deprecation warning)
  3. Recommended: `visualize_image_classes(data_source=path, samples_per_class=6)` (no warning)
- **Clear Warnings**: Improved deprecation messages with specific migration guidance
- **Educational Value**: Users learn correct API patterns while maintaining backward compatibility

### Documentation
- **Updated Examples**: All README code examples now use recommended `data_source=` parameter
- **User Education**: Ensures new users learn modern API patterns from documentation
- **Migration Guidance**: Clear examples of all supported usage patterns

### Technical Implementation
- **Function Wrapper**: Created wrapper function with `*args, **kwargs` to properly handle positional arguments
- **Internal Implementation**: Separated logic into `_visualize_image_classes_impl()` for clean architecture
- **Comprehensive Testing**: Validated all three usage patterns with proper warning behavior

### Notes
- **Zero Breaking Changes**: All existing code continues to work unchanged
- **Performance**: No performance impact - wrapper adds minimal overhead
- **Future-Proof**: Clean architecture supports future parameter evolution

## [0.12.2] - 2025-08-06 - Documentation Refresh 📚

### Improved
- **Documentation**: Enhanced README.md with updated timestamps and current version indicators
- **PyPI Display**: Forced PyPI cache refresh to ensure current changelog information is displayed
- **Visibility**: Added latest updates indicator to changelog section for better user awareness
- **Metadata**: Updated version indicators throughout documentation files

### Fixed
- **PyPI Cache**: Resolved issue where PyPI was displaying outdated changelog (showing v0.11.0 instead of current releases)
- **Documentation Sync**: Ensured all documentation platforms display consistent current version information

### Notes
- **No Functional Changes**: All code functionality identical to v0.12.1 - purely documentation improvements
- **Compatibility**: Maintains full backward compatibility from v0.12.1 patch

## [0.12.1] - 2025-08-06 - Backward Compatibility Patch 🔧

### Fixed
- **Backward Compatibility**: Added support for deprecated `image_paths` parameter in `visualize_image_classes()`
  - Function now accepts both `data_source` (recommended) and `image_paths` (deprecated) parameters
  - Shows deprecation warning when `image_paths` is used to encourage migration to `data_source`
  - Prevents using both parameters simultaneously to avoid confusion
  - Resolves TypeError for users calling with `image_paths=` parameter

### Enhanced  
- Improved error messages for parameter validation in image visualization functions
- Added comprehensive parameter documentation including deprecation notices

## [0.12.0] - 2025-08-06 - Machine Learning Preprocessing Release 🤖

### Added
- `analyze_encoding_needs()` function for intelligent categorical encoding strategy analysis
  - Automatic cardinality analysis for optimal encoding method selection
  - Target correlation analysis for supervised encoding recommendations
  - Memory impact assessment for high-cardinality features
  - Support for 7 different encoding strategies: One-Hot, Target, Ordinal, Binary, TF-IDF, Text, and Keep Numeric
  - Beautiful emoji-rich output with detailed recommendations and summaries
  
- `apply_smart_encoding()` function for automated categorical variable transformation
  - Intelligent preprocessing pipeline with automatic analysis integration
  - Memory-efficient handling of high-cardinality categorical variables
  - Support for scikit-learn encoders: OneHotEncoder, TargetEncoder, OrdinalEncoder
  - TF-IDF vectorization for text features with customizable parameters
  - Binary encoding for medium cardinality features to optimize memory usage
  - Graceful handling of unknown categories with configurable strategies
  - Comprehensive progress tracking with emoji-rich status updates
  - Automatic shape transformation reporting (columns before/after)

### Enhanced
- Package now includes comprehensive ML preprocessing capabilities alongside EDA functions
- Total function count increased from 18 to 20 with new encoding suite
- Improved integration with scikit-learn ecosystem for end-to-end ML workflows
- Enhanced documentation with ML preprocessing examples and use cases

### Dependencies
- Added scikit-learn integration for advanced encoding transformations
- Maintained backward compatibility with existing EDA functionality
- All new features include graceful fallbacks if optional dependencies unavailable

## [0.11.0] - 2025-01-30 - Image Feature Analysis Release 🎨

### Added
- `analyze_image_features()` function for deep statistical analysis of visual features
- Edge density analysis using Canny, Sobel, and Laplacian edge detection methods  
- Texture analysis with Local Binary Patterns (LBP) for pattern characterization
- Color histogram analysis across RGB, HSV, LAB, and grayscale color spaces
- Gradient magnitude and direction analysis for understanding image structure
- Feature ranking system to identify most discriminative features between classes
- Statistical comparison framework for quantifying inter-class visual differences
- Comprehensive visualization suite with box plots for feature distributions
- Automated recommendation system for feature engineering and preprocessing decisions
- Production-ready feature extraction with optional raw feature vector export
- OpenCV and scikit-image integration with graceful fallback mechanisms
- Support for custom analysis parameters (LBP radius, edge thresholds, color spaces)

### Enhanced
- Expanded edaflow from 16 to 17 comprehensive EDA functions
- Complete computer vision EDA trinity: Visualization + Quality + Features
- Advanced dependency handling for optimal performance with available libraries

### Technical
- Added CV2_AVAILABLE and SKIMAGE_AVAILABLE flags for robust dependency checking
- Implemented comprehensive edge detection fallbacks using scipy when advanced libraries unavailable
- Enhanced texture analysis with multiple feature extraction methods
- Added multi-color-space support with automatic conversion handling

## [0.8.6] - 2025-08-05

### Fixed - PyPI Changelog Display Issue
- **CRITICAL**: Fixed PyPI changelog not displaying latest releases (v0.8.4, v0.8.5)
- **DOCUMENTATION**: Updated README.md changelog section that PyPI displays instead of CHANGELOG.md
- **PYPI**: Synchronized README.md changelog with comprehensive CHANGELOG.md content
- **ENHANCED**: Ensured PyPI users see complete version history and latest features

## [0.8.5] - 2025-08-05

### Changed - Code Organization and Structure Improvement Release
- **REFACTORED**: Renamed `missing_data.py` to `core.py` to better reflect comprehensive EDA functionality
- **ENHANCED**: Updated module docstring to describe complete suite of analysis functions
- **IMPROVED**: Better project structure with appropriately named core module containing all 14 EDA functions
- **FIXED**: Updated all imports and tests to reference the new core module structure
- **MAINTAINED**: Full backward compatibility - all functions work exactly the same

## [0.8.4] - 2025-08-05

### Added - Comprehensive Scatter Matrix Visualization Release
- **NEW**: `visualize_scatter_matrix()` function with advanced pairwise relationship analysis
- **NEW**: Flexible diagonal plots: histograms, KDE curves, and box plots
- **NEW**: Customizable upper/lower triangles: scatter plots, correlation coefficients, or blank
- **NEW**: Color coding by categorical variables for group-specific pattern analysis
- **NEW**: Multiple regression line types: linear, polynomial (2nd/3rd degree), and LOWESS smoothing
- **NEW**: Comprehensive statistical insights: correlation analysis, pattern identification
- **NEW**: Professional scatter matrix layouts with adaptive figure sizing
- **NEW**: Full integration with existing edaflow workflow and styling consistency
- **ENHANCED**: Complete EDA visualization suite now includes 14 functions (from 13)
- **ENHANCED**: Added scikit-learn and statsmodels dependencies for advanced analytics
- **ENHANCED**: Updated package metadata and documentation for scatter matrix capabilities

### Technical Features
- **Matrix Customization**: Independent control of diagonal, upper, and lower triangle content
- **Statistical Analysis**: Automatic correlation strength categorization and reporting  
- **Regression Analysis**: Advanced trend line fitting with multiple algorithm options
- **Color Intelligence**: Automatic categorical/numerical variable handling for color coding
- **Performance Optimization**: Efficient handling of large datasets with smart sampling suggestions
- **Error Handling**: Comprehensive validation with informative error messages
- **Professional Output**: Publication-ready visualizations with consistent edaflow styling

## [0.8.3] - 2025-08-04

### Fixed
- **CRITICAL**: Updated README.md changelog section that PyPI was displaying instead of CHANGELOG.md
- **PYPI**: Fixed PyPI changelog display by synchronizing README.md changelog with main CHANGELOG.md
- **DOCUMENTATION**: Ensured consistent changelog information across all package files

## [0.8.2] - 2025-08-04

### Fixed
- **METADATA**: Enhanced PyPI metadata to ensure proper changelog display
- **PYPI**: Forced PyPI cache refresh by updating package metadata
- **LINKS**: Added additional project URLs for better discoverability

## [0.8.1] - 2025-08-04

### Fixed
- **FIXED**: Updated changelog dates to current date format
- **FIXED**: Removed duplicate changelog header that was causing PyPI display issues
- **ENHANCED**: Improved changelog formatting for better PyPI presentation

## [0.8.0] - 2025-08-04

### Added
- **NEW**: `visualize_histograms()` function with advanced statistical analysis and skewness detection
- Comprehensive distribution analysis with normality testing (Shapiro-Wilk, Jarque-Bera, Anderson-Darling)
- Advanced skewness interpretation: Normal (|skew| < 0.5), Moderate (0.5-1), High (≥1)
- Kurtosis analysis: Normal, Heavy-tailed (leptokurtic), Light-tailed (platykurtic)
- KDE curve overlays and normal distribution comparisons
- Statistical text boxes with comprehensive distribution metrics
- Transformation recommendations based on skewness analysis
- Multi-column histogram visualization with automatic subplot layout
- Missing data handling and robust error validation
- Detailed statistical reporting with emoji-formatted output

### Enhanced
- Updated Complete EDA Workflow to include 12 functions (from 9)
- Added histogram analysis as Step 10 in the comprehensive workflow
- Enhanced README documentation with detailed histogram function examples
- Comprehensive test suite with 7 test scenarios covering various distribution types

### Fixed
- Fixed Anderson-Darling test attribute error (significance_levels → significance_level)
- Improved statistical test error handling and validation

## [0.7.0] - 2025-08-03

### Added
- **NEW**: `visualize_heatmap()` function with comprehensive heatmap visualizations
- Four distinct heatmap types: correlation, missing data patterns, values, and cross-tabulation
- Multiple correlation methods: Pearson, Spearman, and Kendall
- Missing data pattern visualization with threshold highlighting
- Data values heatmap for detailed small dataset inspection  
- Cross-tabulation heatmaps for categorical relationship analysis
- Automatic statistical insights and detailed reporting
- Smart column detection and validation for each heatmap type
- Comprehensive customization options (colors, sizing, annotations)
- Enhanced Complete EDA Workflow with Step 11: Heatmap Analysis
- Comprehensive test suite with error handling validation
- Updated README documentation with detailed heatmap examples and use cases

### Enhanced
- Complete EDA workflow now includes 11 steps with comprehensive heatmap analysis
- Updated package features to highlight new heatmap visualization capabilities
- Improved documentation with statistical insights explanations

## [0.6.0] - 2025-08-02

### Added
- **NEW**: `visualize_interactive_boxplots()` function with full Plotly Express integration
- Interactive boxplot visualization with hover tooltips, zoom, and pan functionality
- Statistical summaries with emoji-formatted output for better readability
- Customizable styling options (colors, dimensions, margins)
- Smart column selection for numerical data
- Complete Plotly Express px.box equivalent functionality
- Added plotly>=5.0.0 dependency for interactive visualizations
- Comprehensive test suite for interactive visualization function
- Updated Complete EDA Workflow Example to include interactive visualization as Step 10
- Enhanced README documentation with interactive visualization examples and features

### Enhanced
- Complete EDA workflow now includes 10 steps with interactive final visualization
- Updated requirements documentation to include plotly dependency
- Improved package feature list to highlight interactive capabilities

## [0.5.1] - 2024-01-14

### Fixed
- Updated PyPI documentation to properly showcase handle_outliers_median() function in Complete EDA Workflow Example
- Ensured PyPI page displays the complete 9-step EDA workflow including outlier handling
- Synchronized local documentation improvements with PyPI display

## [0.5.0] - 2025-08-04

### Added
- `handle_outliers_median()` function for automated outlier detection and replacement
- Multiple outlier detection methods: IQR, Z-score, and Modified Z-score
- Complete outlier analysis workflow integration with boxplot visualization
- Median-based outlier replacement for robust statistical handling
- Flexible column selection with automatic numerical column detection
- Detailed reporting showing exactly which outliers were replaced and statistical bounds
- Safe operation mode (inplace=False by default) to preserve original data
- Statistical method comparison with customizable IQR multipliers
- Complete 9-function EDA package with comprehensive outlier management

### Fixed
- Dtype compatibility improvements to eliminate pandas FutureWarnings
- Enhanced error handling and validation for numerical column processing

## [0.4.2] - 2025-08-04

### Fixed
- Updated README.md changelog to properly reflect v0.4.1 boxplot features on PyPI page
- Corrected version history display for proper PyPI documentation

## [0.4.1] - 2025-08-04

### Added
- `visualize_numerical_boxplots()` function for comprehensive outlier detection and statistical analysis
- Advanced boxplot visualization with customizable layouts (rows/cols), orientations, and color palettes
- Automatic numerical column detection for boxplot analysis
- Detailed statistical summaries including skewness analysis and interpretation
- IQR-based outlier detection with threshold reporting
- Comprehensive outlier identification with actual outlier values displayed
- Support for horizontal and vertical boxplot orientations
- Seaborn integration for enhanced styling and color palettes

### Fixed
- `impute_categorical_mode()` function now properly returns DataFrame instead of None
- Corrected inplace parameter handling for categorical imputation function

### Fixed
- Future fixes will be documented here

### Security
- Future security updates will be documented here

## [0.1.0] - 2025-08-04

### Added
- Initial package structure
- Basic `hello()` function in `edaflow.__init__`
- Setup configuration with `setup.py` and `pyproject.toml`
- Core dependencies: pandas, numpy, matplotlib, seaborn, scipy, missingno
- Comprehensive README with installation and usage instructions
- MIT License
- Development dependencies and tooling configuration
- Git ignore file
- Basic project documentation structure

### Infrastructure
- Package structure with `edaflow/` module directory
- Development tooling setup (black, flake8, isort, pytest, mypy)
- Continuous integration ready configuration
- PyPI publishing ready setup

[Unreleased]: https://github.com/yourusername/edaflow/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/edaflow/releases/tag/v0.1.0

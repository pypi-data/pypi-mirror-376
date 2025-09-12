# cheutils

A package with a set of basic reusable utilities and tools to facilitate quickly getting up and going on any machine learning project.

## Features
- Managing properties files or project configuration, based on jproperties. The application configuration is expected to be available in a properties file named `app-config.properties`, which can be placed anywhere in the project root or any project subfolder.
- Convenience methods such as `get_estimator()` to get a handle on any configured estimator with a specified hyperparameters dictionary, `get_params_grid()` or `get_param_defaults()` relating to obtaining model hyperparameters in the `app-config.properties` file.
- Convenience methods for conducting hyperparameter optimization such as `params_optimization()`, `promising_params_grid()` for obtaining a set of promising hyperparameters using RandomSearchCV and a set of broadly specified or configured hyperparameters in the `app-config.properties`; a combination of `promising_params_grid()` followed by `params_optimization()` constitutes a coarse-to-fine search.
- Convenience methods for accessing the project tree folders - e.g., `get_data_dir()` for accessing the configured data and `get_output_dir()` for the output folders, `load_dataset()` for loading, `save_excel()` and `save_csv()` for savings Excel in the project output folder and CSV respectively; you can also save any plotted figure using `save_current_fig()` (note that this must be called before `plt.show()`.
- Convenience methods to support common programming tasks, such as renaming or tagging file names- e.g., `label(file_name, label='some_label')`) or tagging and date-stamping files (e.g., `datestamp(file_name, fmt='%Y-%m-%d')`).
- A debug or logging, timer, and singleton decorators - for enabling logging and method timing, as well as creating singleton instances.
- Convenience methods available via the `DSWrapper` for managing datasource configuration or properties files - e.g. `ds-config.properties` - offering a set of generic datasource access methods such as `apply_to_datasource()` to persist data to any configured datasource or `read_from_datasource()` to read data from any configured datasources.
- A set of custom `scikit-learn` transformers for preprocessing data such as `PreOrPostDataPrep` which can be added to a data pipeline for pre-process dataset - e.g., handling date conversions, type casting of columns, clipping data, generating special features from rows of text strings, generating calculated features, masking columns, dropping correlated or potential data leakage columns, and generating target variables from other features as needed (separet from target encoding). A `GeohashAugmenter` for generating geohash features from latitude and longitudes; a `FunctionTransformerWrapper` and `SelectiveScaler` for selectively transforming dataframe columns; a `DateFeaturesAugmenter` for generating date-related features for feature engineering, and `FeatureSelector` for feature selection using configured estimators such as `Lasso` or `LinearRegression`
- A set of generic or common utilities for summarizing dataframes and others - e.g., using `summarize()` or to winsorize using `winsorize_it()`
- A set of convenience properties handlers to accessing generic configured properties relating to the project tree, data preparation, or model development and execution such as `ProjectTreeProperties`, `DataPropertiesHandler`, and `ModelProperties`. These handlers offer a convenient feature for reloading properties as needed, thereby refreshing properties without having to re-start the running VM (really only useful in development). However you may access any configured properties in the usual way via the `AppProperties` object.

## Usage
You can install this module as follows:
```commandline
pip install cheutils
```
OPTIONAL: if you want the latest release:
```commandline
pip install --upgrade cheutils
```
## Get started using `cheutils`
The module supports application configuration via a properties file. As such, you can include a project configuration file - the default properties file expected is `app-config.properties`, which you can place anywhere in your project root or any project sub folder. You can also include a special properties file called `ds-config.properties` with the configuration of your data sources; this is also automatically loaded. A sample application properties file may contain entries such as the following:
```properties
##
# Sample application properties file
##
# It is usefull to include at least the following four minimal properties in your project
project.namespace=cheutils
project.root.dir=./
project.data.dir=./data/
project.output.dir=./output/
# properties handlers
project.properties.proj_handler={'name': 'ProjectTreeProperties', 'package': 'cheutils', }
project.properties.data_handler={'name': 'DataPropertiesHandler', 'package': 'cheutils', }
project.properties.model_handler={'name': 'ModelProperties', 'package': 'cheutils', }
# SQLite DB - used for selected caching for efficiency
project.sqlite3.db=cheutils_sqlite.db
project.dataset.list=[X_train.csv, X_test.csv, y_train.csv, y_test.csv]
# estimator configuration: default parameters are those not necessarily included for any tuning or optimization
# but are useful for instantiating instances of the estimator; all others in the estimator params_grid are
# candidates for any optimization. If no default parameters are needed simply ignore or set default_params value to None
project.models.supported={'xgb_boost': {'name': 'XGBRegressor', 'package': 'xgboost', 'default_params': None, }, \
  'random_forest': {'name': 'RandomForestRegressor', 'package': 'sklearn.ensemble', 'default_params': None, }, \
  'lasso': {'name': 'Lasso', 'package': 'sklearn.linear_model'}, 'default_params': {'alpha': 0.10}, }
# selected estimator parameter grid options - these are included in any tuning or model optimization
model.params_grid.xgb_boost={'learning_rate': {'type': float, 'start': 0.0, 'end': 1.0, 'num': 10}, 'subsample': {'type': float, 'start': 0.0, 'end': 1.0, 'num': 10}, 'min_child_weight': {'type': float, 'start': 0.1, 'end': 1.0, 'num': 10}, 'n_estimators': {'type': int, 'start': 10, 'end': 400, 'num': 10}, 'max_depth': {'type': int, 'start': 3, 'end': 17, 'num': 5}, 'colsample_bytree': {'type': float, 'start': 0.0, 'end': 1.0, 'num': 5}, 'gamma': {'type': float, 'start': 0.0, 'end': 1.0, 'num': 5}, 'reg_alpha': {'type': float, 'start': 0.0, 'end': 1.0, 'num': 5}, }
model.params_grid.random_forest={'min_samples_leaf': {'type': int, 'start': 1, 'end': 60, 'num': 5}, 'max_features': {'type': int, 'start': 5, 'end': 1001, 'num': 10}, 'max_depth': {'type': int, 'start': 5, 'end': 31, 'num': 6}, 'n_estimators': {'type': int, 'start': 5, 'end': 201, 'num': 10}, 'min_samples_split': {'type': int, 'start': 2, 'end': 21, 'num': 5}, 'max_leaf_nodes': {'type': int, 'start': 5, 'end': 401, 'num': 10}, }
model.baseline.model_option=lasso
model.active.model_option=xgb_boost
# hyperparameter search algorith options supported: hyperopt with cross-validation and Scikit-Optimize
project.hyperparam.searches=['hyperoptcv', 'skoptimize']
model.active.n_iters=200
model.active.n_trials=10
model.narrow_grid.scaling_factor=0.20
model.narrow_grid.scaling_factors={'start': 0.1, 'end': 1.0, 'steps': 10}
model.find_optimal.grid_resolution=False
model.find_optimal.grid_resolution.with_cv=False
model.grid_resolutions.sample={'start': 1, 'end': 21, 'step': 1}
model.active.grid_resolution=7
model.cross_val.num_folds=3
model.active.n_jobs=-1
model.cross_val.scoring=neg_mean_squared_error
model.active.random_seed=100
model.active.trial_timeout=60
model.hyperopt.algos={'rand.suggest': 0.05, 'tpe.suggest': 0.75, 'anneal.suggest': 0.20, }
# transformers - defined as a dictionary of pipelines containing dictionaries of transformers
# note that each pipeline is mapped to a set of columns, and all transformers in a pipeline act on the set of columns
model.feature.scalers=[{'pipeline_name': 'scaler_pipeline', 'transformers': [{'name': 'scaler_tf', 'module': 'StandardScaler', 'package': 'sklearn.preprocessing', 'params': None, }, ], 'columns': ['col1_label', 'col2_label']}, ]
model.feature.encoders=[{'pipeline_name': 'encoder_pipeline', 'transformers': [{'name': 'encoder_tf', 'module': 'OneHotEncoder', 'package': 'sklearn.preprocessing', 'params': None, }, ], 'columns': ['col1_label', 'col2_label']}, ]
model.feature.binarizers=[{'pipeline_name': 'binarizers_pipeline', 'transformers': [{'name': 'binarizer_tf', 'module': 'Binarizer', 'package': 'sklearn.preprocessing', 'params': {'threshold': 0.5, }, }, ], 'columns': ['col1_label', 'col2_label']}, ]
# transformers - defined as a dictionary of pipelines containing dictionaries of transformers
# note that each pipeline is mapped to a set of columns, and all transformers in a pipeline act on the set of columns
model.target.encoder={'pipeline_name': 'target_enc_pipeline', 'target_encoder': {'name': 'target_enc_tf', 'module': 'SelectiveTargetEncoder', 'package': 'sklearn.preprocessing', 'params': {'target_type': 'auto', 'smooth': 'auto', 'cv': 5, 'shuffle': True, }, }, 'columns': ['col1_label', 'col2_label'], }
# configure feature selection transformers
model.feature.selectors={\
  'selector1': {'module': 'SelectFromModel', 'package': 'sklearn.feature_selection', 'params': {'threshold': 'median', }, }, \
  'selector2': {'module': 'RFE', 'package': 'sklearn.feature_selection', 'params': {'n_features_to_select': 0.25, }, }, \
  }
model.feat_selection.passthrough=True
model.feat_selection.selector=selector1
# use the following once feature selection has been settled - extracted from feature selection to use going forward
# an example situation where this is helpful is during tuning when the feature selection has been settled beforehand.
# It means feature selection does not have to be a pipeline step, as that can introduce errors if cross-validation is as
# different folds may select different feature subsets - we desire a consistent set of features for each fold.
# So, set use_selected=False, run test pipeline notebook to generate list of selected features; then set use_selected=True
# that enables the pipeline to simply take advantage of the selected features (which should be copied and pasted below).
model.feat_selection.use_selected=False
# once feature selection is done the output is copied and pasted below to be optionally used as selected
model.feat_selection.selected=['col1', 'col2', ]
# global winsorize default limits or specify desired property and use accordingly
func.winsorize.limits=[0.05, 0.05]
```
A sample datasource configuration properties file may contain something like the following:
```properties
##
# Sample datasource configuration properties file
##
# datasources supported
project.ds.supported=[{'mysql_local': {'db_driver': 'MySQL ODBC 8.1 ANSI Driver', 'drivername': 'mysql+pyodbc', 'db_server': 'host.domain.com', 'db_port': 3306, 'db_name': 'mysql_db_name', 'username': 'db_username', 'password': 'db_user_passwd', 'direct_conn': 0, 'timeout': 0, 'verbose': True, 'encoding': 'utf8', }, }, ]
# database tables and interactions
db.rel_cols.db_namespace.some_table_name=['some_prim_key', 'name', 'iso_2code', 'iso_3code', 'gps_lat', 'gps_lon', 'is_active']
db.unique_key.db_namespace.some_table_name=['some_prim_key']
db.to_tables.replace.db_namespace=[some_table_name=False, ]
db.to_table.delete.db_namespace.some_table_name=[some_prim_key=120]
```
You import the `cheutils` module as per usual:
```python
from cheutils import AppProperties, get_data_dir

# The following provide access to the properties file, usually expected to be named "app-config.properties" and 
# typically found in the project data folder or anywhere either in the project root or any other subfolder
APP_PROPS = AppProperties() # this automatically search for the app-config.properties file and loads it

# During development, you may find it convenient to reload properties file changes without re-starting the 
# VM - NB: not recommended for production. You can achieve that by adding the following somewhere at the top of your Jupyter notebook, for example.
APP_PROPS.reload() # this automatically notifies and registered properties handlers to be reloaded

# You can access any properties using various methods such as:
data_dir = APP_PROPS.get('project.data.dir')

# You can also retrieve the path to the data folder (see app-config.properties), which is under the project root as follows:
data_dir = get_data_dir()  # also returns the path to the project data folder, which is always interpreted relative to the project root

# You can also retrieve other properties as follows:
datasets = APP_PROPS.get_list('project.dataset.list') # e.g., some.configured.list=[1, 2, 3] or ['1', '2', '3']; see dataset configured in app-config.properties
hyperopt_algos = APP_PROPS.get_dic_properties('model.hyperopt.algos') # e.g., some.configured.dict={'val1': 10, 'val2': 'value'}
sel_transformers = APP_PROPS.get_list_properties('model.selective_column.transformers') # e.g., configured pipelines of transformers in the sample properties file above
find_opt_grid_res = APP_PROPS.get_bol('model.find_optimal.grid_resolution') # e.g., some.configured.bol=True
```
You access the LOGGER instance and use it in a similar way to you will when using a logging module like `loguru` or standard logging
```python
from cheutils import LoguruWrapper

LOGGER = LoguruWrapper().get_logger()
# You may also wish to change the logging context from the default, which is usually set to the configured project namespace property, by calling `set_prefix()` 
# to ensure the log messages are scoped to that context thereafter - which can be helpful when reviewing the generated log file (`app-log.log`) - the default 
# prefix is "app-log". You can set the logger prefix as follows:
LoguruWrapper().set_prefix(prefix='some_namespace')
some_val = 100
LOGGER.info('Some info you wish to log some value: {}', some_val) # or debug() etc.
```

The `cheutils` module currently supports any configured estimator (see, the xgb_boost example in the sample properties file for how to configure any estimator).
You can configure the active or main estimators for your project with an entry in the app-config.properties as below, but you add your own properties as well, 
provided the estimator has been fully configured as in the sample application properties file:
```python
from cheutils import get_estimator, get_params_grid, AppProperties, load_dataset

# You can get a handle to the corresponding estimator in your code as follows:
estimator = get_estimator(model_option='xgb_boost') # the appropriate porperty can be seen in the sample app-config.properties

# You can do the following as well, to get a non-default instance, with appropriately configured hyperparameters:
estimator = get_estimator(**get_params_grid(model_option='xgb_boost'))
# You can fit the estimator as follows per usual:
datasets = AppProperties().get_list('project.dataset.list')
X_train, y_train, X_val, y_val, X_test, y_test = [load_dataset(file_name=file_name, is_csv=True) for file_name in datasets]
estimator.fit(X_train, y_train)
```
Given a default broad estimator hyperparameter configuration (usually in the properties file), you can generate a promising parameter 
grid using RandomSearchCV as in the following line. Note that, the pipeline can either be an sklearn pipeline or an estimator. 
The general idea is that, to avoid worrying about trying to figure out the optimal set of hyperparameter values for a given estimator, you can do that automatically, by 
adopting a two-step coarse-to-fine search, where you configure a broad hyperparameter space or grid based on the estimator's most important or impactful hyperparameters, and the use a random search to find a set of promising hyperparameters that 
you can use to conduct a finer hyperparameter space search using other algorithms such as Bayesian optimization (e.g., hyperopt or Scikit-Optimize, etc.)
```python
from cheutils import promising_params_grid, params_optimization, AppProperties, load_dataset
from sklearn.pipeline import Pipeline
datasets = AppProperties().get_list('project.dataset.list') # AppProperties is a singleton
X_train, y_train, X_val, y_val, X_test, y_test = [load_dataset(file_name=file_name, is_csv=False) for file_name in datasets]
pipeline = Pipeline(steps=['some previously defined pipeline steps'])
promising_grid = promising_params_grid(pipeline, X_train, y_train, grid_resolution=3, prefix='baseline_model') # the prefix is not needed if not part of a model pipeline
# thereafter, you can run hyperparameter optimization or tuning as follows (assuming you enabled cross-validation in your configuration or app-conf.properties - e.g., with an entry such as `model.cross_val.num_folds=3`), 
# if using hyperopt - i.e., 'hyperoptcv' indicates using hyperopt optimization with cross-validation
best_estimator, best_score, best_params, cv_results = params_optimization(pipeline, X_train, y_train, promising_params_grid=promising_grid, with_narrower_grid=True, fine_search='hyperoptcv', prefix='model_prefix')
# if you are running the optimization as part of a Mlflow experiment and logging, you could also pass an optional parameter in the optimization call:
mlflow_exp={'log': True, 'uri': 'http://<mlflow_tracking_server>:<port>', } # ensures mlflow logging is done as well and you should also have the appropriate mlflow server instance running
best_estimator, best_score, best_params, cv_results = params_optimization(pipeline, X_train, y_train, promising_params_grid=promising_grid, with_narrower_grid=True, fine_search='hyperoptcv', prefix='model_prefix', mlflow_exp=mlflow_exp)
```
If you have also configured some datasources (i.e., using the `ds-config.properties`), you can get a handle to the datasource wrapper as follows:
```python
import os
from cheutils import DSWrapper, get_data_dir
ds = DSWrapper() # it is a singleton
# You can then read a large CSV file, leveraging `dask` as follows:
data_df = ds.read_large_csv(path_to_data_file=os.path.join(get_data_dir(), 'some_large_file.csv')) # where the data file is expected to be in the data sub folder of the project tree

# Assuming you previously defined a datasource configuration such as `ds-config.properties` somewhere in the project tree or sub folder, containing:
# You could then simply read from a configured datasource (DB) as below. Note that, the ds_params allows you to prescribe how DSWrapper behaves in 
# the current interaction; the data_file attribute in ds_params MUST be set to None or left unset (i.e., left entirely out), 
# if you wish to read from a configured DB resource - i.e., a datasource other than Excel or CSV file. You should set the attribute to signal to DWrapper to
# read from either an Excel or CSV file, and you should additionally provide another attribute: is_csv=False if reading an Excel file. Note the ds_key matches
# the entry in the sample ds-config.properties. DSWrapper expects the data_file to be in the data sub folder of the project.
ds_params = {'db_key': 'mysql_local', 'ds_namespace': 'test', 'db_table': 'some_table', 'data_file': None}
data_df = ds.read_from_datasource(ds_config=ds_params, chunksize=5000)
```
The `cheutils` module comes with custom transformers for some preprocessing - e.g., some basic data cleaning and formatting, handling date conversions, type casting of columns, clipping data, generating special features, calculating new features, masking columns, dropping correlated and potential leakage columns, and generating target variables if needed. 

You can add a data preprocessing transformer to your pipeline as follows:

```python
from cheutils import DataPrep

date_cols = ['rental_date']
int_cols = ['release_year', 'length', 'NC-17', 'PG', 'PG-13', 'R',
            'trailers', 'deleted_scenes', 'behind_scenes', 'commentaries', 'extra_fees']
correlated_cols = ['rental_rate_2', 'length_2', 'amount_2']
drop_missing = True  # drop rows with missing data
clip_data = None  # no data clipping; but you could clip outliers based on category aggregates with something like clip_data = {'rel_cols': ['col1', 'col2'], 'filterby': 'cat_col', }
exp_tf = DataPrep(date_cols=date_cols,
                  int_cols=int_cols,
                  drop_missing=drop_missing,
                  clip_data=clip_data,
                  correlated_cols=correlated_cols, )
data_prep_pipeline_steps = [('data_prep_step', exp_tf)]  # this can be added to a model pipeline
```
You can also include feature selection by adding the following to the pipeline:

```python
from cheutils import feature_selector, FeatureSelectionInterceptor, DataPipelineInterceptor, get_estimator, AppProperties, ModelProperties, SelectiveScaler

standard_pipeline_steps = ['some previously defined pipeline steps']
model_handler: ModelProperties = AppProperties().get_subscriber('model_handler')
feat_sel_tf = feature_selector(estimator=get_estimator(model_option='xgboost'),
                               random_state=model_handler.get_random_seed())
# add feature selection to pipeline
standard_pipeline_steps.append(('feat_selection_step', feat_sel_tf))
# Alternatively, you may have previously conducted feature selection and simply wish to 
# inject the selected features in the pipeline - in which case, you could simply use the appropriate
# interceptor as follows:
APP_PROPS = AppProperties()
selected_features = APP_PROPS.get_list('model.feat_selection.selected') # the selected features available in app-config.properties
interceptors = [FeatureSelectionInterceptor(selected_features=selected_features)]
feat_sel_tf = DataPipelineInterceptor(interceptors=interceptors, )
standard_pipeline_steps.append(('feat_sel_tf', feat_sel_tf))
# You can also add a configured selective column transformer.
# e.g., if you already have configured a list of column transformers in the `app-config.properties` such as in the sample properties file above,
# you can add it to the pipeline as below. The `SelectiveScaler` uses the configured property to determine 
# the transformer(s), and the corresponding columns affected, to add to the pipeline. 
# Each configured transformer only applies any transformations to the specified columns and others are simply passed through.
scaler_tf = SelectiveScaler()
standard_pipeline_steps.append(('scale_feats_step', scaler_tf))
```
Ultimately, you may create a model pipeline and execute using steps similar to the following:

```python
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.compose import TransformedTargetRegressor
from cheutils import get_estimator, winsorize_it, AppProperties, LoguruWrapper

LOGGER = LoguruWrapper().get_logger()
# assuming any previous necessary steps
standard_pipeline_steps = ['some previosly defined pipeline steps']
# ...
baseline_model = get_estimator(model_option=AppProperties().get('model.baseline.model_option'))
baseline_pipeline_steps = standard_pipeline_steps.copy()
baseline_pipeline_steps.append(('baseline_mdl', baseline_model))
baseline_pipeline = Pipeline(steps=baseline_pipeline_steps, verbose=True)
# you could even wrap the pipeline with an appropriate `scikit-learn` target encoder, for argument's sake
# here the target is winsorized, but you could do other encoding as you wish
baseline_est = TransformedTargetRegressor(regressor=baseline_pipeline, 
                                          func=winsorize_it, 
                                          inverse_func=winsorize_it,
                                          check_inverse=False, )
X_train = None # ignore the None value - assume previously defined and gone through an appropriate train_test_split
y_train = None # ditto what is said on X_train above
baseline_est.fit(X_train, y_train)
y_train_pred = baseline_est.predict(X_train)
mse_score = mean_squared_error(y_train, y_train_pred)
r_squared = r2_score(y_train, y_train_pred)
LOGGER.debug('Training baseline mse = {:.2f}'.format(mse_score))
LOGGER.debug('Training baseline r_squared = {:.2f}'.format(r_squared))
```

## Community

Contributions are welcomed from contributors, all experience levels, anyone looking to collaborate to improve the package or to be helpful. 
We rely on a scikit-learn's [`Development Guide`](https://scikit-learn.org/stable/developers/index.html), which contains lots of best practices and detailed information about contributing code, documentation, tests, and more. 

### Source code
You can check the latest sources with the command:
```commandline
git clone https://github.com/chewitty/cheutils.git
```
### Communication
- Author email: ferdinand.che@gmail.com

### Citation

If you use `cheutils` in a media/research publication, we would appreciate citations to this repository.


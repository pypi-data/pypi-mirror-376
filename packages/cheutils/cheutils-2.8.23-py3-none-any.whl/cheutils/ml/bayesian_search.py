import numpy as np
import mlflow
from mlflow.models import infer_signature
from hyperopt import fmin, space_eval, STATUS_OK, Trials
from sklearn.base import BaseEstimator, clone
from sklearn.metrics import mean_squared_error, roc_auc_score
from sklearn.model_selection import cross_val_score
from sklearn.base import is_classifier
from sklearn.pipeline import Pipeline
from cheutils.common_base import CheutilsBase
from cheutils.loggers import LoguruWrapper
from typing import cast

LOGGER = LoguruWrapper().get_logger()

"""
Based on https://hyperopt.github.io/hyperopt/. A hyperopt implementation that includes using cross validation during optimization
"""
class HyperoptSearchCV(CheutilsBase, BaseEstimator):
    def __init__(self, estimator, max_evals: int=100, algo=None,
                 cv=None, n_jobs: int=-1, params_space: dict= None, trial_timeout: int=60,
                 random_state: int=100, mlflow_exp: dict=None, **kwargs):
        super().__init__()
        self.max_evals = max_evals
        self.cv = cv
        self.n_jobs = n_jobs
        self.trial_timeout = trial_timeout
        self.random_state = random_state
        self.estimator = estimator
        self.best_estimator_ = None
        self.best_params_ = None
        self.best_score_ = float('inf')
        self.cv_results_ = None
        self.scoring_ = kwargs.get('scoring', 'neg_mean_squared_error')
        self.params_space = params_space if params_space is not None else {}
        self.algo = algo
        self.mlflow_exp = mlflow_exp
        self.trial_run = 0
        self.X = None
        self.y = None
        self.signature = None

    def fit(self, X, y=None, **kwargs):
        LOGGER.debug('HyperoptSearchCV: Fitting dataset, shape {}, {}', X.shape, y.shape if y is not None else None)
        self.X = X
        self.y = y
        input_example = self.X.head()
        self.signature = infer_signature(input_example, self.y.head())
        # Perform the optimization
        def optimize_and_fit():
            trials = Trials()
            best_params = fmin(fn=self.__objective, space=self.params_space, algo=self.algo,
                               max_evals=self.max_evals, timeout=self.trial_timeout, trials=trials,
                               rstate=np.random.default_rng(self.random_state))
            best_run = sorted(trials.results, key=lambda x: x['loss'])[0]
            LOGGER.debug('Minimum loss = {}', best_run['loss'])
            self.best_params_ = space_eval(self.params_space, best_params)
            self.best_score_ = best_run['loss']
            LOGGER.debug('Best score = {}', self.best_score_)
            LOGGER.debug('HyperoptSearchCV: Best hyperparameters  = \n{}', self.best_params_)
        if self.mlflow_exp is not None and self.mlflow_exp.get('log'):
            mlflow.config.enable_async_logging(enable=True)
            descr = 'Hyperopt optimization - ' + str(self.estimator)
            with mlflow.start_run(log_system_metrics=True, description=descr) as active_run:
                optimize_and_fit()
                mlflow.set_tag('Best model info', 'Best model by evaluation metric')
                model_uri = 'runs:/{run_id}/model'.format(run_id=active_run.info.run_id)
                LOGGER.debug('Mlflow model URI = {}', model_uri)
                mlflow.log_params(self.best_params_)
                mlflow.log_metric('eval_mse', self.best_score_)
                mlflow.sklearn.log_model(sk_model=self.best_estimator_, artifact_path='best_model',
                                         input_example=input_example, signature=self.signature,
                                         registered_model_name='best_model')
        else:
            optimize_and_fit()
        return self

    def predict(self, X):
        assert X is not None, 'A valid X expected'
        assert self.best_estimator_ is not None, 'Model must be fitted before predict'
        return self.best_estimator_.predict(X)

    def predict_proba(self, X):
        assert X is not None, 'A valid X expected'
        assert self.best_estimator_ is not None, 'Model must be fitted before predict_proba'
        return self.best_estimator_.predict_proba(X)

    def __objective(self, params):
        LOGGER.debug('\nRunning trial ID = {}', self.trial_run)
        LOGGER.debug('Current hyperparams:\n{}', params)
        underlying_model = clone(self.estimator)
        underlying_model = cast(Pipeline, underlying_model)
        underlying_model.set_params(**params)
        def evaluate_obj():
            min_score = self.best_score_
            if self.cv is not None:
                cv_score = cross_val_score(underlying_model, self.X, self.y, scoring=self.scoring_,
                                           cv=self.cv, n_jobs=self.n_jobs, error_score='raise')
                min_score = -np.nanmean(cv_score) if is_classifier(underlying_model) else abs(np.nanmean(cv_score))
                LOGGER.debug('Current cv loss = {}', min_score)
                # refit the model for mlflow registering and logging
                underlying_model.fit(self.X, self.y)
                if min_score < self.best_score_:
                    self.best_score_ = min_score
                    self.cv_results_ = cv_score
                    self.best_estimator_ = underlying_model
            else:
                #no cross-validation
                underlying_model.fit(self.X, self.y)
                y_pred = underlying_model.predict(self.X)
                min_score = -roc_auc_score(self.y, y_pred) if is_classifier(underlying_model) else abs(mean_squared_error(self.y, y_pred))
                LOGGER.debug('Current loss = {}', min_score)
                if min_score < self.best_score_:
                    self.best_score_ = min_score
                    self.best_estimator_ = underlying_model
            return min_score
        if self.mlflow_exp is not None and self.mlflow_exp.get('log'):
            descr = 'Nested run - ' + str(underlying_model)
            with mlflow.start_run(nested=True, description=descr) as active_run:
                model_uri = 'runs:/{run_id}/model'.format(run_id=active_run.info.run_id)
                LOGGER.debug('Mlflow model URI = {}', model_uri)
                input_example = self.X.head()
                min_score = evaluate_obj()
                mlflow.set_tag('Trial model', 'Trial model ' + str(self.trial_run))
                mlflow.log_params(params)
                mlflow.log_metric('eval_mse', min_score)
                mlflow.sklearn.log_model(sk_model=underlying_model, artifact_path='best_model',
                                         input_example=input_example, signature=self.signature,
                                         registered_model_name='trial_model_' + str(self.trial_run))
        else:
            min_score = evaluate_obj()
        self.trial_run = self.trial_run + 1
        return {'loss': min_score, 'status': STATUS_OK, 'model': underlying_model}




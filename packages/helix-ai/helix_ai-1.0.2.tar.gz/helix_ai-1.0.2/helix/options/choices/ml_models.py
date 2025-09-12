from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import (
    ElasticNet,
    Lasso,
    LinearRegression,
    LogisticRegression,
    Ridge,
    RidgeClassifier,
)
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from xgboost import XGBClassifier, XGBRegressor

from helix.machine_learning.models.BRNNs import BRNNClassifier, BRNNRegressor
from helix.machine_learning.models.mlrem import EMLinearRegression
from helix.machine_learning.models.svm import SVC, SVR
from helix.options.enums import ModelNames

# Grid search parameters for each model
LINEAR_MODEL_GRID = {
    "fit_intercept": [True, False],
}

RANDOM_FOREST_GRID = {
    "n_estimators": [10, 50, 100, 200],
    "max_depth": [None, 10, 20, 30],
    "min_samples_split": [2, 5, 10],
}

XGB_GRID = {
    "n_estimators": [10, 50, 100, 200],
    "max_depth": [3, 5, 7, 9],
    "learning_rate": [0.01, 0.1, 0.3],
    "subsample": [0.5, 0.8, 1.0],
}

SVM_GRID = {
    "kernel": ["linear", "poly", "rbf"],
    "C": [0.1, 1.0, 10.0],
    "degree": [2, 3, 4],
}

MLREM_GRID = {
    "alpha": [0.05, 0.1, 0.5],
    "max_beta": [40],
    "weight_threshold": [1e-3, 1e-2],
    "max_iterations": [300],
    "tolerance": [0.001],
}

CLASSIFIERS: dict[ModelNames, type] = {
    ModelNames.LinearModel: LogisticRegression,
    ModelNames.RandomForest: RandomForestClassifier,
    ModelNames.XGBoost: XGBClassifier,
    ModelNames.SVM: SVC,
    ModelNames.Ridge: RidgeClassifier,
    ModelNames.KNearestNeighbours: KNeighborsClassifier,
    ModelNames.MLP: MLPClassifier,
    ModelNames.GNB: GaussianNB,
    ModelNames.BRNN: BRNNClassifier,
}

REGRESSORS: dict[ModelNames, type] = {
    ModelNames.LinearModel: LinearRegression,
    ModelNames.RandomForest: RandomForestRegressor,
    ModelNames.XGBoost: XGBRegressor,
    ModelNames.SVM: SVR,
    ModelNames.MLREM: EMLinearRegression,
    ModelNames.Lasso: Lasso,
    ModelNames.ElasticNet: ElasticNet,
    ModelNames.Ridge: Ridge,
    ModelNames.KNearestNeighbours: KNeighborsRegressor,
    ModelNames.MLP: MLPRegressor,
    ModelNames.BRNN: BRNNRegressor,
}

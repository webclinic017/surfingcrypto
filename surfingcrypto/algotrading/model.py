"""model object"""

import pandas as pd
import copy

from sklearn import linear_model
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from surfingcrypto.algotrading.features import Features


class Model:
    def __init__(self, name: str, f: Features):
        self.name = name
        self.feature = copy.copy(f)
        self.model = self._set_model()
        self.X = self.feature.model_df[self.feature.x_cols_names].copy()
        self.Y = self.feature.model_df["direction"].copy()
        self._fit_model()
        self.estimated = self._estimate()

    def _set_model(self):
        if self.name == "svm":
            return SVC()
        elif self.name == "log_reg":
            return linear_model.LogisticRegression()
        elif self.name == "gauss_nb":
            return GaussianNB()
        elif self.name == "random_forest":
            return RandomForestClassifier(max_depth=10, n_estimators=100)
        elif self.name == "MLP":
            return MLPClassifier(max_iter=500)
        else:
            raise NotImplementedError

    def _fit_model(self):
        self.model.fit(self.X, self.Y)

    def _estimate(self) -> pd.Series:
        return pd.DataFrame(
            self.model.predict(self.X), index=self.X.index, columns=["predicted"]
        )

    def make_tomorrow_prediction(self) -> int:
        return self.model.predict(
            self.feature.get_future_x().to_numpy().reshape(1, -1)
        )[0]

    def __repr__(self) -> str:
        return f"Model(name={self.name})"

    def __str__(self) -> str:
        return f"Model(name={self.name})"

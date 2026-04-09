from sklearn.ensemble import ExtraTreesClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

from .preprocess import add_engineered_features, build_preprocessor


def build_model() -> Pipeline:
    return Pipeline(
        steps=[
            ("feature_engineering", FunctionTransformer(add_engineered_features, validate=False)),
            ("preprocessor", build_preprocessor()),
            (
                "classifier",
                ExtraTreesClassifier(
                    n_estimators=45,
                    max_depth=None,
                    class_weight="balanced",
                    random_state=42,
                    n_jobs=1,
                ),
            ),
        ]
    )

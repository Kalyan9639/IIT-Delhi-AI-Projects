"""
Explainability module for Bangalore Real Estate Intelligence System.
Provides SHAP-based global and local explanation utilities.
"""

import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from .logging_utils import log_error, log_info

warnings.filterwarnings("ignore")


class ExplainabilityAnalyzer:
    """SHAP explainability wrapper for the trained models."""

    def __init__(self):
        self.explainer = None
        self.shap_values = None
        self.feature_names = None
        self.background = None
        self.X_sample = None
        self.expected_value = None

    def create_explainer(self, model, X_background):
        """Create a SHAP explainer for the given model."""
        log_info("create_explainer", "Creating SHAP explainer")

        self.background = X_background.copy()
        try:
            if hasattr(model, "feature_importances_"):
                self.explainer = shap.TreeExplainer(model)
            elif hasattr(model, "coef_"):
                self.explainer = shap.LinearExplainer(model, X_background)
            else:
                self.explainer = shap.Explainer(model.predict, X_background)
        except Exception as exc:
            log_error("create_explainer", f"Error creating explainer: {exc}")
            raise

        return self.explainer

    def calculate_shap_values(self, X, model=None, nsamples=100):
        """Calculate SHAP values for a sample of rows."""
        log_info("calculate_shap_values", "Calculating SHAP values")

        if self.explainer is None:
            raise RuntimeError("Explainer has not been created yet")

        self.X_sample = X.sample(n=min(nsamples, len(X)), random_state=42).copy()
        self.feature_names = self.X_sample.columns.tolist()

        try:
            if hasattr(self.explainer, "shap_values"):
                values = self.explainer.shap_values(self.X_sample)
                self.expected_value = getattr(self.explainer, "expected_value", None)
            else:
                explanation = self.explainer(self.X_sample)
                values = explanation.values
                self.expected_value = getattr(explanation, "base_values", None)

            self.shap_values = self._normalize_values(values)
        except Exception as exc:
            log_error("calculate_shap_values", f"Error calculating SHAP values: {exc}")
            raise

        log_info("calculate_shap_values", f"SHAP values calculated for {len(self.X_sample)} rows")
        return self.shap_values

    def get_global_feature_importance(self):
        """Return mean absolute SHAP importance for each feature."""
        log_info("get_global_feature_importance", "Calculating global feature importance")

        if self.shap_values is None:
            log_error("get_global_feature_importance", "SHAP values not calculated")
            return {}

        importance = np.abs(self.shap_values).mean(axis=0)
        importance_dict = dict(zip(self.feature_names, importance))
        importance_dict = dict(sorted(importance_dict.items(), key=lambda item: item[1], reverse=True))
        return importance_dict

    def get_local_explanation(self, instance_index, X=None):
        """Return feature contributions for one row."""
        log_info("get_local_explanation", f"Getting local explanation for instance {instance_index}")

        if self.shap_values is None:
            log_error("get_local_explanation", "SHAP values not calculated")
            return None

        if instance_index >= len(self.shap_values):
            log_error("get_local_explanation", "Instance index out of range")
            return None

        local_values = self.shap_values[instance_index]
        explanation = dict(zip(self.feature_names, local_values))
        return dict(sorted(explanation.items(), key=lambda item: abs(item[1]), reverse=True))

    def plot_global_feature_importance(self, save_path=None):
        """Plot global feature importance."""
        log_info("plot_global_feature_importance", "Plotting global feature importance")

        if self.shap_values is None:
            log_error("plot_global_feature_importance", "SHAP values not calculated")
            return None

        importance = np.abs(self.shap_values).mean(axis=0)
        importance_df = pd.DataFrame({"feature": self.feature_names, "importance": importance})
        importance_df = importance_df.sort_values("importance", ascending=True)

        fig, ax = plt.subplots(figsize=(10, 8))
        ax.barh(importance_df["feature"], importance_df["importance"], color="#1f77b4")
        ax.set_xlabel("Mean Absolute SHAP Value")
        ax.set_title("Global Feature Importance")
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig

    def plot_shap_summary(self, save_path=None):
        """Plot a SHAP summary plot."""
        log_info("plot_shap_summary", "Plotting SHAP summary")

        if self.shap_values is None:
            log_error("plot_shap_summary", "SHAP values not calculated")
            return None

        shap.summary_plot(self.shap_values, self.X_sample, feature_names=self.feature_names, show=False)
        fig = plt.gcf()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig

    def get_top_features(self, n=10):
        """Return the top N features by SHAP importance."""
        importance = self.get_global_feature_importance()
        return list(importance.keys())[:n]

    def get_feature_insights(self, n=5):
        """Return SHAP statistics for top features."""
        log_info("get_feature_insights", "Generating feature insights")

        if self.shap_values is None:
            log_error("get_feature_insights", "SHAP values not calculated")
            return {}

        importance = self.get_global_feature_importance()
        insights = {}

        for feature in list(importance.keys())[:n]:
            idx = self.feature_names.index(feature)
            feature_shap = self.shap_values[:, idx]
            insights[feature] = {
                "mean_shap": float(np.mean(feature_shap)),
                "std_shap": float(np.std(feature_shap)),
                "positive_impact": float(np.mean(feature_shap[feature_shap > 0])) if np.any(feature_shap > 0) else 0.0,
                "negative_impact": float(np.mean(feature_shap[feature_shap < 0])) if np.any(feature_shap < 0) else 0.0,
                "importance": float(importance[feature]),
            }

        return insights

    def explain_prediction(self, instance_index, X, y=None):
        """Generate a compact local explanation."""
        log_info("explain_prediction", f"Generating explanation for instance {instance_index}")

        local_exp = self.get_local_explanation(instance_index, X)
        if local_exp is None:
            return None

        top_positive = {k: v for k, v in local_exp.items() if v > 0}
        top_negative = {k: v for k, v in local_exp.items() if v < 0}

        explanation = {
            "instance_index": instance_index,
            "top_positive_contributors": dict(list(top_positive.items())[:5]),
            "top_negative_contributors": dict(list(top_negative.items())[:5]),
            "total_features": len(local_exp),
            "feature_names": self.feature_names,
        }

        if y is not None and instance_index < len(y):
            explanation["actual_value"] = float(y.iloc[instance_index])

        return explanation

    def _normalize_values(self, values):
        """Normalize SHAP outputs to a 2D numpy array."""
        if isinstance(values, list):
            values = values[0]
        if hasattr(values, "values"):
            values = values.values
        return np.asarray(values)

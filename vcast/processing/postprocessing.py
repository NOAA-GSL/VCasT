import pandas as pd
import numpy as np
from typing import Tuple, Literal

class StatiscalSignificance:

    def __init__(self,config):

        df1 = pd.read_csv(config.input_model_A,sep="\t")
        df2 = pd.read_csv(config.input_model_B,sep="\t")
        output_file = config.output_file
        metric = config.metric

        df = self.compare_models(df1, df2, metric)

        df.to_csv(output_file, sep='\t', index=False, header=True)

    def pairwise_bootstrap_significance(
        self,
        metric_a: np.ndarray,
        metric_b: np.ndarray,
        n_iterations: int = 10000,
        ci_percentile: float = 95.0
    ) -> Tuple[float, float, Tuple[float, float]]:
        """
        Perform pairwise bootstrap significance test and return observed diff, p-value, and CI.

        Returns:
            Tuple of (observed_diff, p_value, (ci_lower, ci_upper))
        """
        metric_a = np.asarray(metric_a)
        metric_b = np.asarray(metric_b)
        differences = []

        rng = np.random.default_rng()

        for _ in range(n_iterations):
            sample_indices = rng.integers(0, len(metric_a), len(metric_a))
            sample_a = metric_a[sample_indices]
            sample_b = metric_b[sample_indices]
            diff = np.mean(sample_b - sample_a)
            differences.append(diff)

        differences = np.array(differences)
        observed_diff = np.mean(metric_b) - np.mean(metric_a)
        p_value = np.mean(np.abs(differences) >= np.abs(observed_diff))

        lower = np.percentile(differences, (100 - ci_percentile) / 2)
        upper = np.percentile(differences, 100 - (100 - ci_percentile) / 2)

        return observed_diff, p_value, (lower, upper)

    def compare_models(
        self,
        df_model_a: pd.DataFrame,
        df_model_b: pd.DataFrame,
        metric: Literal["rmse", "bias", "fss"] = "rmse",
        n_iterations: int = 10000,
        ci_percentile: float = 95.0
    ) -> pd.DataFrame:
        """
        Compare two models using pairwise bootstrapping by lead time.

        Returns:
            DataFrame with lead time, observed difference, p-value, CI, better model, and significance flag.
        """
        results = []
        for lead in sorted(set(df_model_a["fcst_lead"]).intersection(df_model_b["fcst_lead"])):
            values_a = df_model_a[df_model_a["fcst_lead"] == lead][metric].values
            values_b = df_model_b[df_model_b["fcst_lead"] == lead][metric].values

            if len(values_a) == 0 or len(values_b) == 0:
                continue

            obs_diff, p_val, (ci_low, ci_high) = self.pairwise_bootstrap_significance(
                values_a, values_b, n_iterations=n_iterations, ci_percentile=ci_percentile
            )

            better_model = "Model A" if obs_diff < 0 else "Model B"
            significant = p_val < 0.05

            results.append({
                "fcst_lead": lead,
                "observed_diff": obs_diff,
                "p_value": p_val,
                "ci_lower": ci_low,
                "ci_upper": ci_high,
                "better_model": better_model,
                "significant": significant
            })

        return pd.DataFrame(results)
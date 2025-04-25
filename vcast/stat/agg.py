import numpy as np
import pandas as pd
from scipy.stats import t
import pandas as pd

class Aggregation:

    def __init__(self, config, df = None, stats = None):

        if df is None:
            self.df = self.get_df(config.input_file)
        else:
            self.df = df

        self.lead_cols = config.group_by

        if stats is None:
            self.estimate_cols = config.stats
        else:
            self.estimate_cols = stats 

        self.output_file = config.output_agg_file

        self.ci = False 
        if hasattr(config,"ci"):
            self.ci = config.ci
    
    def get_df(self,input_file):
        return pd.read_csv(input_file,sep="\t")

    def run(
        self,
        ci: float = 0.95
    ) -> pd.DataFrame:
        """
        Compute pooled point estimates and Student's t-based CIs per group (e.g., by lead time) for multiple metrics.
    
        Parameters
        ----------
        daily_df : pd.DataFrame
            DataFrame containing per-run daily estimates for each metric.
            Must include columns in `lead_cols` and `estimate_cols`.
        lead_cols : list[str]
            Column names to group by (e.g., ['fcst_lead']).
        estimate_cols : list[str]
            List of column names with point estimates (e.g., ['rmse', 'bias']).
        ci : float, default=0.95
            Confidence level (e.g. 0.95 for 95% CI).
    
        Returns
        -------
        pd.DataFrame
            One row per unique combination of `lead_cols`, with columns:
              - each column in `lead_cols`
              - for each `col` in `estimate_cols`:
                  - `{col}_mean`
                  - `{col}_bcl`
                  - `{col}_bcu`
        """
        alpha = 1 - ci
        records = []
    
        # Group by the specified lead columns
        for group_vals, grp in self.df.groupby(self.lead_cols):
            # Ensure group_vals is a tuple when multiple keys
            if not isinstance(group_vals, tuple):
                group_vals = (group_vals,)
            row = dict(zip(self.lead_cols, group_vals))
            n = len(grp)
            row["count"] = n

            # Compute mean and t-based CI for each metric column
            for col in self.estimate_cols:
                values = grp[col].to_numpy()
                mean_val = np.mean(values)
                row[f"{col}_mean"] = mean_val

                if self.ci:
                    s = np.std(values, ddof=1) if n > 1 else 0.0
                    t_crit = t.ppf(1 - alpha/2, df=n-1) if n > 1 else np.nan
                    half_width = t_crit * s / np.sqrt(n) if n > 1 else 0.0
                    row[f"{col}_bcl"] = mean_val - half_width
                    row[f"{col}_bcu"] = mean_val + half_width
    
            records.append(row)
    
        self.df = pd.DataFrame(records)
        return self.df

    def save_output(self):
        self.df.to_csv(self.output_file,sep="\t")

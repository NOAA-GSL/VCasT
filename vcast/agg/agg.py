import numpy as np
import pandas as pd
from scipy.stats import t

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

            # Compute mean and t-based CI for each metric column.
            # Bin columns (e.g. thresh_i/oy_i/on_i from PCT data) may not be
            # present for every row in the group -- different dates or
            # variables can carry a different number of probability bins --
            # so missing values show up as NaN. Average over only the rows
            # that actually have that bin instead of letting NaNs collapse
            # the whole column, and size the CI off that same valid count.
            for col in self.estimate_cols:
                values = grp[col].to_numpy(dtype=float)
                valid = values[~np.isnan(values)]
                n_valid = len(valid)
                mean_val = np.mean(valid) if n_valid > 0 else np.nan
                row[f"{col}"] = mean_val

                if self.ci:
                    s = np.std(valid, ddof=1) if n_valid > 1 else 0.0
                    t_crit = t.ppf(1 - alpha/2, df=n_valid-1) if n_valid > 1 else np.nan
                    half_width = t_crit * s / np.sqrt(n_valid) if n_valid > 1 else 0.0
                    row[f"{col}_bcl"] = mean_val - half_width
                    row[f"{col}_bcu"] = mean_val + half_width
    
            records.append(row)
    
        self.df = pd.DataFrame(records)
        return self.df

    def save_output(self):
        self.df.to_csv(self.output_file,sep="\t")

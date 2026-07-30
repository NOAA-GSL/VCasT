import pandas as pd
import matplotlib.pyplot as plt
from .base_plot import BasePlot
import numpy as np


class Roc(BasePlot):
    """ROC diagram derived from aggregated PCT (probability contingency table) counts.

    For each probability bin ``i`` the aggregated file provides ``oy_i`` (obs-yes
    count) and ``on_i`` (obs-no count).  The ROC curve is built by sweeping the
    probability threshold and accumulating counts from the high-probability end::

        PODY(k) = sum(oy_i for i >= k) / sum(oy)
        POFD(k) = sum(on_i for i >= k) / sum(on)

    Counts are additive across cases, so aggregating PCT and re-deriving the rates
    here is the statistically correct way to build a pooled ROC.  (Averaging
    PODY/POFD across cases directly would be wrong.)  This reuses the very same
    aggregated ``agg.data`` that the reliability plot consumes -- no separate PRC
    aggregation is needed.
    """

    def __init__(self, config):
        super().__init__(config)

    def setup_plot(self):
        """Set up the ROC axes (unit square)."""
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.ax.set_title(self.config.plot_title, fontsize=16, fontweight="bold")
        self.ax.set_xlabel("Probability of False Detection (POFD)", fontsize=12)
        self.ax.set_ylabel("Probability of Detection (PODY)", fontsize=12)
        self.ax.set_xlim([0, 1])
        self.ax.set_ylim([0, 1])

        if getattr(self.config, "grid", False):
            self.ax.grid(True, linestyle="--", alpha=0.6)

    def _roc_points(self, row):
        """Compute (POFD, PODY, AUC) for a single aggregated PCT row."""
        oy_cols = self.bin_columns(row.index, "oy_")
        on_cols = self.bin_columns(row.index, "on_")
        if not oy_cols or not on_cols:
            raise Exception(
                "No 'oy_'/'on_' columns found -- ROC needs an aggregated PCT file."
            )

        oy = np.array([row[c] for c in oy_cols], dtype=float)
        on = np.array([row[c] for c in on_cols], dtype=float)

        tot_oy, tot_on = oy.sum(), on.sum()
        if tot_oy == 0 or tot_on == 0:
            raise Exception(
                "Cannot build ROC: zero obs-yes or obs-no total in the PCT counts."
            )

        # Threshold sweep k = 0..n. Bins are ordered low->high forecast probability,
        # so accumulating from index k upward gives "forecast yes when prob >= edge k".
        # k=0 -> always yes -> (1,1); k=n -> never yes -> (0,0).
        n = len(oy)
        pody = np.array([oy[k:].sum() / tot_oy for k in range(n + 1)])
        pofd = np.array([on[k:].sum() / tot_on for k in range(n + 1)])

        # Points run from (1,1) at k=0 to (0,0) at k=n and are monotonically
        # non-increasing in both POFD and PODY, so integrate along the curve
        # (reversed to ascending POFD). Re-sorting would scramble PODY at tied
        # POFD values and corrupt the area. The trapezoid is computed directly
        # to stay compatible across numpy versions (np.trapz was removed in
        # numpy 2.x in favour of np.trapezoid).
        x, y = pofd[::-1], pody[::-1]
        auc = float(np.sum((x[1:] - x[:-1]) * (y[1:] + y[:-1]) / 2.0))
        return pofd, pody, auc

    def add_lines(self):
        """Add one ROC curve per entry in ``vars`` (mirrors the reliability plot)."""
        for i, var_obj in enumerate(self.config.vars):
            var_dict = vars(var_obj)
            for lead, file in var_dict.items():
                data = pd.read_csv(file, sep="\t")

                data = data[data["fcst_lead"] == lead]
                if len(data) == 0:
                    raise Exception(f"No data found for fcst_lead = {lead}")

                if self.config.fcst_var is not None:
                    data = data[data["fcst_var"] == self.config.fcst_var]
                    if len(data) == 0:
                        raise Exception(
                            f"No data found for fcst_var = {self.config.fcst_var}"
                        )

                # Optional grouping, matching the reliability/line-plot behaviour.
                if self.config.unique is not None and self.config.unique in data.columns:
                    unique_vals = np.unique(data[self.config.unique])
                    if i < len(unique_vals):
                        data = data[data[self.config.unique] == unique_vals[i - 1]]
                    else:
                        raise IndexError(
                            f"Index {i} out of bounds for unique values "
                            f"in {self.config.unique}."
                        )

                pofd, pody, auc = self._roc_points(data.iloc[0])

                label = self.config.labels[i]
                if getattr(self.config, "show_auc", True):
                    label = f"{label} (AUC={auc:.3f})"

                self.ax.plot(
                    pofd, pody,
                    color=self.config.line_color[i],
                    marker=self.config.line_marker[i],
                    linestyle=self.config.line_type[i],
                    linewidth=self.config.line_width[i],
                    label=label,
                )

    def add_no_skill_line(self):
        """Diagonal POFD=PODY no-skill reference line."""
        self.ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="No skill")

    def plot(self):
        self.setup_plot()
        self.add_lines()
        self.add_no_skill_line()
        self.finalize_and_save()

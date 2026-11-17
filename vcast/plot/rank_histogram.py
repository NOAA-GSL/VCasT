import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from .base_plot import BasePlot


class RankHistogram(BasePlot):
    """
    Rank histogram (Talagrand diagram) from MET RHIST data read by VCasT.

    Input files are VCasT tables with ``rank_1 ... rank_N`` count columns
    (``line_type: rhist`` with ``stat_vars: ["total", "all_ranks"]``), either the
    per-line output or an aggregated file. For every series the counts of all
    selected rows are summed and normalised to relative frequency, so the plot
    can pool any combination of leads, dates or domains. The dashed line is the
    flat histogram of a perfectly calibrated ensemble (1 / N).

    YAML keys (besides the usual plot_type / vars / output_filename / labels /
    line_color / plot_title / legend_title / grid):
      vars:      list of ``- <name>: <file>``; each entry is one input file.
      unique:    optional list of ``- <column>: <value>``; each item becomes its
                 own series for every vars entry (e.g. one series per vx_mask).
      fcst_var:  optional forecast-variable filter.
      filters:   optional ``{column: [values]}`` row filter applied to every
                 series (e.g. ``fcst_lead: [60000, 120000]``).
      style:     "bar" (grouped bars, default) or "step".
      ylim, yticks, x_label, y_label: optional axis settings.
    """

    def __init__(self, config):
        super().__init__(config)

    # ------------------------------------------------------------------
    @staticmethod
    def _select(data, column, values):
        """Keep rows whose `column` is in `values`; numeric columns are compared
        as numbers so "060000" and 60000 match."""
        if column not in data.columns:
            raise KeyError(f"Column '{column}' not found for filtering.")
        if not isinstance(values, (list, tuple)):
            values = [values]
        if pd.api.types.is_numeric_dtype(data[column]):
            vals = [float(v) for v in values]
            return data[data[column].astype(float).isin(vals)]
        return data[data[column].astype(str).isin([str(v) for v in values])]

    def _filtered(self, file):
        data = pd.read_csv(file, sep="\t")
        fcst_var = getattr(self.config, "fcst_var", None)
        if fcst_var is not None:
            data = self._select(data, "fcst_var", fcst_var)
        filters = getattr(self.config, "filters", None) or {}
        if not isinstance(filters, dict):
            filters = vars(filters)
        for column, values in filters.items():
            data = self._select(data, column, values)
        if len(data) == 0:
            raise Exception(f"No rows left in {file} after fcst_var/filters.")
        return data

    def series_frequencies(self):
        """-> list of (ranks, relative frequency) per series, in plotting order."""
        out = []
        unique = getattr(self.config, "unique", None) or [None]
        for var_obj in self.config.vars:
            for _, file in vars(var_obj).items():
                data = self._filtered(file)
                rank_cols = self.bin_columns(data.columns, "rank_")
                if not rank_cols:
                    raise Exception(f"No 'rank_' columns in {file}; rank_histogram needs RHIST data.")
                for item in unique:
                    sub = data
                    if item is not None:
                        for column, value in vars(item).items():
                            sub = self._select(sub, column, value)
                    counts = sub[rank_cols].to_numpy(dtype=float)
                    counts = np.nansum(counts, axis=0)
                    total = counts.sum()
                    if total <= 0:
                        raise Exception(f"Rank counts sum to zero in {file} for {item}.")
                    ranks = np.array([int(c[len("rank_"):]) for c in rank_cols])
                    out.append((ranks, counts / total))
        return out

    # ------------------------------------------------------------------
    def setup_plot(self):
        figsize = getattr(self.config, "figsize", None) or (10, 8)
        self.fig, self.ax = plt.subplots(figsize=tuple(figsize))
        self.ax.set_title(self.config.plot_title, fontsize=16, fontweight="bold")
        self.ax.set_xlabel(getattr(self.config, "x_label", None) or "Observation rank", fontsize=12)
        self.ax.set_ylabel(getattr(self.config, "y_label", None) or "Relative frequency", fontsize=12)
        if getattr(self.config, "grid", False):
            self.ax.grid(True, axis="y", linestyle="--", alpha=0.6)
            self.ax.set_axisbelow(True)

    def add_bars(self):
        series = self.series_frequencies()
        style = (getattr(self.config, "style", None) or "bar").lower()
        n = len(series)
        width = 0.8 / max(n, 1)
        n_rank = 0
        for k, (ranks, freq) in enumerate(series):
            n_rank = max(n_rank, len(ranks))
            color = self.config.line_color[k]
            label = self.config.labels[k]
            if style == "step":
                self.ax.step(ranks, freq, where="mid", color=color,
                             linewidth=self.config.line_width[k] if hasattr(self.config, "line_width") else 2,
                             label=label)
            else:
                offset = (k - (n - 1) / 2) * width
                self.ax.bar(ranks + offset, freq, width=width, color=color,
                            edgecolor="white", linewidth=0.3, label=label)
        if n_rank:
            self.ax.axhline(1.0 / n_rank, color="gray", linestyle="--", linewidth=1.2,
                            label="Perfectly calibrated")
            ticks = range(1, n_rank + 1)
            self.ax.set_xticks(list(ticks) if n_rank <= 25 else list(ticks)[::2])
            self.ax.set_xlim(0.4, n_rank + 0.6)
        if getattr(self.config, "ylim", None):
            self.ax.set_ylim(self.config.ylim)
        if getattr(self.config, "yticks", None):
            self.ax.set_yticks(self.config.yticks)

    def plot(self):
        self.setup_plot()
        self.add_bars()
        self.finalize_and_save()

import pandas as pd
import matplotlib.pyplot as plt
from .base_plot import BasePlot
import numpy as np

class PerformanceDiagram(BasePlot):
    """Performance diagram (POD vs. success ratio with CSI and frequency-bias lines).

    Each ``vars`` entry is one file and one series. Two input kinds are accepted:

    * CTS-style files with ``pody`` and ``far`` (or ``sr``) columns: one point per
      row, joined in file order (the original behaviour).
    * PCT files (``thresh_i``/``oy_i``/``on_i`` columns, e.g. an aggregated
      ``line_type: pct`` table): the counts of all rows are summed and one point is
      drawn per probability threshold p_k, treating "forecast yes" as
      probability >= p_k::

          hits(k) = sum(oy_i for i >= k),  false alarms(k) = sum(on_i for i >= k)
          POD(k)  = hits(k) / sum(oy)
          SR(k)   = hits(k) / (hits(k) + false alarms(k))

      The lowest edge (p = 0, always yes) is skipped. Set ``annotate: true`` to
      label each point with its probability threshold.
    """

    def __init__(self, config):
        super().__init__(config)

    def _pct_points(self, data):
        """(SR, POD, thresholds) from the summed PCT counts of all rows in `data`."""
        oy_cols = self.bin_columns(data.columns, "oy_")
        on_cols = self.bin_columns(data.columns, "on_")
        th_cols = self.bin_columns(data.columns, "thresh_")
        idx = sorted(set(int(c[3:]) for c in oy_cols) & set(int(c[3:]) for c in on_cols)
                     & set(int(c[7:]) for c in th_cols))
        if not idx:
            raise Exception("No matching 'thresh_'/'oy_'/'on_' columns -- PCT input expected.")
        oy = np.nansum(data[[f"oy_{k}" for k in idx]].to_numpy(dtype=float), axis=0)
        on = np.nansum(data[[f"on_{k}" for k in idx]].to_numpy(dtype=float), axis=0)
        thresh = data[[f"thresh_{k}" for k in idx]].iloc[0].to_numpy(dtype=float)
        if oy.sum() == 0:
            raise Exception("Cannot build performance diagram: no observed events in the PCT counts.")
        sr, pod, th = [], [], []
        for k in range(1, len(idx)):              # skip the p = 0 edge (always "yes")
            hits, fa = oy[k:].sum(), on[k:].sum()
            pod.append(hits / oy.sum())
            sr.append(hits / (hits + fa) if hits + fa > 0 else np.nan)
            th.append(thresh[k])
        return np.array(sr), np.array(pod), np.array(th)

    def setup_plot(self):
        """
        Set up the base grid for the Performance Diagram.
        """

        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.ax.set_title(self.config.plot_title, fontsize=16, fontweight="bold")
        self.ax.set_xlabel("Success Ratio (1 - FAR)", fontsize=12)
        self.ax.set_ylabel("Probability of Detection (POD)", fontsize=12)
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)

        x = np.linspace(0.01, 1, 100)
        y = np.linspace(0.01, 1, 100)
        X, Y = np.meshgrid(x, y)
        CSI_levels = [0.1, 0.25, 0.5, 0.6, 0.75, 1.0]
        CSI = (X * Y) / (X + Y - X * Y)
    
        # Shade CSI regions with different gray levels
        shades = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]  # Shades for CSI levels
        for i, level in enumerate(CSI_levels[:-1]):
            self.ax.contourf(
                X, Y, CSI, levels=[level, CSI_levels[i + 1]], colors=[str(shades[i])], alpha=0.8
            )
    
        # Plot CSI contour lines
        contour = self.ax.contour(X, Y, CSI, levels=CSI_levels, colors="black", linestyles="solid")
        self.ax.clabel(contour, fmt="%.2f", inline=True, fontsize=10, colors="black")
        self.ax.text(1.05, 0.5, "CSI Curves", rotation=270, fontsize=12, va="center", color="black")
    
        # Add frequency bias (FBIAS) lines
        FB_values = [0.1, 0.25, 0.5, 1, 2, 4, 10]
        for FB in FB_values:
            fb_y = np.minimum(1, FB * x)
            self.ax.plot(x, fb_y, linestyle="--", color="black", linewidth=0.8)
    
            # Add value labels for FBIAS lines at the end
            end_x = x[np.where(fb_y < 1)[0][-1]]  # The last valid x-coordinate
            end_y = fb_y[np.where(fb_y < 1)[0][-1]]  # The corresponding y-coordinate
            self.ax.text(
                end_x + 0.02, end_y, f"{FB:.1f}", fontsize=10, color="black", ha="left", va="center"
            )

        self.ax.grid(True, linestyle="--", alpha=0.5)

    def add_lines(self):
        """
        Add lines to the plot. The x-axis is always dates.
        A complete date range is built from self.config.start_date to self.config.end_date 
        using self.config.interval (in hours). Data from the file is merged with this date range;
        if a date is missing, its corresponding y value is np.nan.
        """
        for i, file in enumerate(self.config.vars):
            # Load data (assuming tab-separated values)
            data = pd.read_csv(file, sep="\t")
            
            if self.config.fcst_var is not None:
                data = data[data["fcst_var"] == self.config.fcst_var]
                if len(data) == 0:
                    raise Exception(f"No data found for fcst_var = {self.config.fcst_var}")
    
            # Handle unique grouping if applicable
            if self.config.unique is not None:
                if self.config.unique in data.columns:
                    unique_vals = np.unique(data[self.config.unique])
                    # Use the (i-1)th unique value
                    if i < len(unique_vals):
                        data = data[data[self.config.unique] == unique_vals[i-1]]
                    else:
                        raise IndexError(f"Index {i} out of bounds for unique values in {self.config.unique}.")
    
            if "pody" not in data.columns and self.bin_columns(data.columns, "oy_"):
                sr, pod, th = self._pct_points(data)
                self.ax.plot(
                    sr, pod,
                    color=self.config.line_color[i],
                    marker=self.config.line_marker[i],
                    linestyle=self.config.line_type[i],
                    linewidth=self.config.line_width[i],
                    label=self.config.labels[i]
                )
                if getattr(self.config, "annotate", False):
                    for x, y, t in zip(sr, pod, th):
                        if np.isfinite(x) and np.isfinite(y):
                            self.ax.annotate(f"{t:g}", (x, y), textcoords="offset points", xytext=(4, 3),
                                             fontsize=8, color=self.config.line_color[i])
                continue

            if "sr" not in data.columns:
                data["sr"] = 1 - data["far"]
            
            self.ax.plot(
                data["sr"], data["pody"],
                color=self.config.line_color[i],
                marker=self.config.line_marker[i],
                linestyle=self.config.line_type[i],
                linewidth=self.config.line_width[i],
                label=self.config.labels[i]
            )


    def plot(self):
        self.setup_plot()
        self.add_lines()
        self.finalize_and_save()

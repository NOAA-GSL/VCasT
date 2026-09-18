import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from .base_plot import BasePlot
import math
from matplotlib.colors import to_rgb

def parse_rgb_string(color_str):
    """
    Parse a color string into a normalized RGB tuple in the range [0, 1].

    Accepts:
    - Named colors or hex codes (via matplotlib)
    - RGB tuples or lists in "(r,g,b)" or "[r, g, b]" format
      with values in either [0, 1] or [0, 255]

    Returns:
    - (True, (r, g, b)) if successful
    - (False, None) if parsing fails
    """
    try:
        # Named colors or hex codes
        return True, to_rgb(color_str)
    except ValueError:
        pass

    try:
        # Strip brackets or parentheses and split
        color_str = color_str.strip("()[]")
        parts = [float(x.strip()) for x in color_str.split(",")]
        if len(parts) != 3:
            return False, None
        
        # Normalize if any value is >1 (assume it's 0–255 scale)
        if any(x > 1.0 for x in parts):
            parts = [min(max(x / 255.0, 0), 1) for x in parts]
        else:
            parts = [min(max(x, 0), 1) for x in parts]

        return True, tuple(parts)
    except Exception:
        return False, None

class LinePlot(BasePlot):
    def __init__(self, config):
        super().__init__(config)

    def setup_plot(self):
        """
        Set up the base line plot.
        """
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.ax.set_title(self.config.plot_title, fontsize=16, fontweight="bold")
        self.ax.set_xlabel(self.config.x_label, fontsize=12)
        self.ax.set_ylabel(self.config.y_label, fontsize=12)

        for i, var in enumerate(self.config.vars):
            var_dict = vars(var)  # Convert ConfigObject to a dictionary
            for var, file in var_dict.items():
        
                # Load data (assuming tab-separated values)
                data = pd.read_csv(file, sep="\t")
                is_date = False
                if "date" in data.columns:
                    is_date = True
                break

        if is_date:
            # Set the x-axis to use date formatting (assumes x-axis values are datetime)
            self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
            self.fig.autofmt_xdate()  # Automatically rotate date labels for readability

        if self.config.ylim:
            self.ax.set_ylim(self.config.ylim)

        # Set y-ticks if provided
        if self.config.yticks:
            self.ax.set_yticks(self.config.yticks)

        if self.config.grid:
            self.ax.grid(True, linestyle="--", alpha=0.6)

    def add_lines(self):
        """
        Add lines to the plot. The x-axis is always dates.
        A complete date range is built from self.config.start_date to self.config.end_date 
        using self.config.interval (in hours). Data from the file is merged with this date range;
        if a date is missing, its corresponding y value is np.nan.
        """
        for i, var_obj in enumerate(self.config.vars):
            # Convert ConfigObject to a dictionary
            start_dt = pd.to_datetime(self.config.start_date, format='%Y-%m-%d_%H:%M:%S')
            end_dt = pd.to_datetime(self.config.end_date, format='%Y-%m-%d_%H:%M:%S')

            var_dict = vars(var_obj)
            for var, file in var_dict.items():
                # Load data (assuming tab-separated values)
                data = pd.read_csv(file, sep="\t")
                
                if hasattr(self.config, 'fcst_var'):
                    if self.config.fcst_var is not None:                
                        data = data[data["fcst_var"] == self.config.fcst_var]
                        if len(data) == 0:
                            raise Exception(f"No data found for fcst_var = {self.config.fcst_var}")
        
                # Handle unique grouping if applicable
                unique = False
                if hasattr(self.config, "unique"):
                    if self.config.unique:
                        unique = True 
                
                if not unique:
                        self.__exceute_line(var, data, file, start_dt, end_dt, i)
                else:
                    for j, column_obj in enumerate(self.config.unique):
                        column_dict = vars(column_obj)

                        for column, value in column_dict.items():

                            xdata = data[data[column] == value]
                            
                            self.__exceute_line(var, xdata, file, start_dt, end_dt, i + j)

    def _count_series(self):
        """Return the total number of series that will be drawn.

        This mirrors the index used when calling ``__exceute_line`` so that the
        dodge offsets stay centred: without ``unique`` grouping each ``vars``
        entry is one series; with grouping the series index runs up to
        ``len(vars) + len(unique) - 1``.
        """
        n = len(self.config.vars)
        unique = getattr(self.config, "unique", None)
        if unique:
            n = n + len(unique) - 1
        return n

    def _dodge_offset(self, series_index, x_values):
        """Horizontal offset for one series so overlapping points/CIs separate.

        When the ``dodge`` config option is truthy each series is shifted along
        the x-axis by a small amount, symmetric around the true x position. The
        total spread is ``dodge_width`` (default 0.6) times the typical spacing
        between x points, so it adapts to both date and ``fcst_lead`` x-axes.
        Returns ``0.0`` when dodging is disabled or there is a single series.
        """
        if not getattr(self.config, "dodge", False):
            return 0.0

        n_series = self._count_series()
        if n_series <= 1:
            return 0.0

        xs = np.asarray(x_values, dtype=float)
        xs = np.unique(xs[~np.isnan(xs)])
        if xs.size >= 2:
            dx = float(np.median(np.diff(xs)))
        else:
            dx = 1.0

        width = getattr(self.config, "dodge_width", 0.6) or 0.6
        step = (width * dx) / (n_series - 1)
        return (series_index - (n_series - 1) / 2.0) * step

    def __exceute_line(self, var, data, file, start_dt, end_dt, i):

        # Check that the variable exists in the merged DataFrame.
        if var not in data.columns:
            raise ValueError(f"Variable '{var}' not found in the file {file}.")
                
        y_values = data[var]

        # Build x-values: Always use date
        if "date" in data.columns:
            # Convert the date column using the expected format (adjust format if needed)
            data["date"] = pd.to_datetime(data["date"], format='%Y-%m-%d %H:%M:%S')
            # Create a complete date range using the config settings.
            complete_dates = pd.date_range(
                start=start_dt, 
                end=end_dt, 
                freq=f"{self.config.interval_hours}h"
            )
            complete_df = pd.DataFrame({"date": complete_dates})
            # Merge complete dates with the data (left join: missing dates yield NaN)
            merged = pd.merge(complete_df, data, on="date", how="left")
            # x_values are the complete date column converted to matplotlib's date numbers.
            x_values = mdates.date2num(merged["date"])
        elif "fcst_lead" in data.columns:
            x_values = data["fcst_lead"].astype(int).tolist()
            if sum(x_values) / len(x_values) > 10000:
                x_values = [val / 10000 for val in x_values]
        else:
            raise ValueError(f"'date' column not found in the file {file}.")

        if len(y_values) != len(x_values):
            raise Exception("ERROR: x and y dimensions are different, likely due to date settings.")

        # Optionally set custom x-ticks if provided.
        if self.config.xticks:
            custom_xticks = [x_values[j] for j in self.config.xticks if j < len(x_values)]
            self.ax.set_xticks(custom_xticks)
        # Set x-axis limits if provided.
        if self.config.xlim:
            self.ax.set_xlim(x_values[self.config.xlim[0]], x_values[self.config.xlim[1]])

        # Optionally dodge this series horizontally so overlapping points and
        # confidence intervals from multiple lines are separated. Ticks and
        # limits above keep using the true x positions; only the drawn series
        # (line, markers, CIs and significance markers) are shifted.
        dodge_offset = self._dodge_offset(i, x_values)
        x_dodged = np.asarray(x_values, dtype=float) + dodge_offset

        ylabel = self.config.labels[i]
        is_valid, color = parse_rgb_string(self.config.line_color[i])

        if not is_valid:
            raise Exception(f"{self.config.line_color[i]} is not a valid color.")

        scale = 1
        if hasattr(self.config, "scale"):
            if self.config.scale:
                scale = self.config.scale

        if hasattr(self.config, "hlines"):
            if self.config.hlines:
                           
                for j in self.config.hlines:

                    hline = [j] * len(x_values)

                    self.ax.plot(
                        x_values,
                        hline,
                        color="black",
                        linestyle="-",
                        linewidth=0.5
                    )                    

        if hasattr(self.config, "ci"):
            
            prefix = self.config.ci[i]

            if hasattr(self.config, "ci_fill_between"):

                if self.config.ci_fill_between:

                    self.ax.fill_between(
                        x_dodged,
                        data[f"{prefix}_bcl"] * scale,
                        data[f"{prefix}_bcu"] * scale,
                        color=color,
                        alpha=0.2,  # Transparency of the shaded region
                        label=f"{ylabel} CI"
                    )
            else:
                
                lower = data[f"{prefix}_bcl"] * scale
                upper = data[f"{prefix}_bcu"] * scale
                central = y_values * scale
            
                # Ensure error bars are non-negative
                yerr_lower = (central - lower).clip(lower=0)
                yerr_upper = (upper - central).clip(lower=0)
                yerr = [yerr_lower, yerr_upper]
            
                self.ax.errorbar(
                    x_dodged,
                    central,
                    yerr=yerr,
                    fmt='none',
                    ecolor=color,
                    elinewidth=1.5,
                    capsize=3,
                    alpha=0.6,
                    label=f"{ylabel} CI"
                )

        if hasattr(self.config, "significance"):
            if self.config.significance:
                if "significant" in data.columns:
                    signif = True
                    significant_mask = data["significant"]

                    y_values = list(y_values)

                    y_min = self.ax.get_ylim()[0]
                    y_margin = (self.ax.get_ylim()[1] - y_min) * 0.02  # 2% margin
                    y_marker = y_min - y_margin

                    # Extract significant x-values (dodged to match the series)
                    x_sig = [x for x, is_sig in zip(x_dodged, significant_mask) if is_sig]
                    
                    # Plot dot markers at the bottom for significant points
                    self.ax.scatter(
                        x_sig,
                        [y_marker + 2 * y_margin] * len(x_sig),
                        color=color,
                        marker="o",
                        s=20,
                        label=f"{ylabel} (significant)",
                        zorder=10
                    )

        self.ax.plot(
            x_dodged, y_values * scale,
            color=color,
            linestyle=self.config.line_type[i],
            marker=self.config.line_marker[i],
            linewidth=self.config.line_width[i],
            label=ylabel
            )

        if hasattr(self.config, "average"):
            if self.config.average:
                # Compute the average, ignoring NaN values.
                scaled_values = [(y * scale) for y in y_values if y is not None and not math.isnan(y)]
                avg_value = sum(scaled_values) / len(scaled_values) if scaled_values else float("nan")
                self.ax.axhline(
                    y=avg_value ,
                    color=color,
                    linestyle=self.config.line_type[i],
                    linewidth=self.config.line_width[i],
                    label=f"{ylabel} Average ({avg_value:.2f})"
                )    

    def get_x_values(self, data):
        """
        Determine x-axis values based on 'date' or 'fcst_lead'.
        """
        if "date" in data.columns:
            dates = pd.to_datetime(data["date"])
            return mdates.date2num(dates)
        elif "fcst_lead" in data.columns:
            return pd.to_numeric(data["fcst_lead"], errors="coerce").astype("Int64")
        else:
            raise ValueError("No valid x-axis column found.")

    def plot(self):
        self.setup_plot()
        self.add_lines()
        self.finalize_and_save()

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from .base_plot import BasePlot
import numpy as np

class Reliability(BasePlot):
    def __init__(self, config):
        super().__init__(config)

    def setup_plot(self):
        """
        Set up the base line plot.
        """
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.ax.set_title(self.config.plot_title, fontsize=16, fontweight="bold")
        self.ax.set_ylabel("Obs. Relative Frequency", fontsize=12)
        self.ax.set_xlabel("Forecast Probability", fontsize=12)

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

        self.ax.set_ylim([0,1])

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

            var_dict = vars(var_obj)
            for var, file in var_dict.items():
                # Load data (assuming tab-separated values)
                data = pd.read_csv(file, sep="\t")
                
                data = data[(data["fcst_lead"] == var)]

                if len(data) == 0:
                    raise Exception(f"No data found for fcst_lead = {var}")
            
                if self.config.fcst_var is not None:
                    data = data[data["fcst_var"] == self.config.fcst_var]
                    if len(data) == 0:
                        raise Exception(f"No data found for fcst_var = {self.config.fcst_var}")
        
                # Handle unique grouping if applicable
                if self.config.unique is not None:
                    if self.config.unique in data.columns:
                        unique_vals = np.unique(data[self.config.unique])
                        # Use the (i-1)th unique value (or adjust as needed)
                        if i < len(unique_vals):
                            data = data[data[self.config.unique] == unique_vals[i-1]]
                        else:
                            raise IndexError(f"Index {i} out of bounds for unique values in {self.config.unique}.")

                tcolumns = [f"thresh_{i}" for i in range(2, 12)]
                probs = data[tcolumns].iloc[0].tolist()

                ycolumns = [f"oy_{i}" for i in range(2, 12)]
                oy = np.array(data[ycolumns].iloc[0].tolist())

                ncolumns = [f"on_{i}" for i in range(2, 12)]
                on = np.array(data[ncolumns].iloc[0].tolist())

                ob_freq = oy / (oy + on)

                self.ax.set_xlim([0,1])
                
                self.ax.plot(
                    probs, ob_freq,
                    color=self.config.line_color[i],
                    marker=self.config.line_marker[i],
                    linestyle=self.config.line_type[i],
                    linewidth=self.config.line_width[i],
                    label=self.config.labels[i]
                )

    def add_perfect_line(self):
        """
        Plot the perfect reliability line (diagonal) from (0,0) to (1,1).
        """
        self.ax.plot(
            [0, 1], [0, 1],
            linestyle="--",
            color="gray",
            label="Perfect Reliability"
        )

    def plot(self):
        self.setup_plot()
        self.add_lines()
        self.add_perfect_line()
        self.finalize_and_save()

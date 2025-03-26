import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from .base_plot import BasePlot
import numpy as np

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

                if self.config.unique is None:
                    self.__exceute_line(var, data, file, start_dt, end_dt, i)

                else:
                    for j, column_obj in enumerate(self.config.unique):
                        column_dict = vars(column_obj)

                        for column, value in column_dict.items():

                            xdata = data[data[column] == value]
                            
                            self.__exceute_line(var, xdata, file, start_dt, end_dt, i + j)

    def __exceute_line(self, var, data, file, start_dt, end_dt, i):

        # Check that the variable exists in the merged DataFrame.
        if var not in data.columns:
            raise ValueError(f"Variable '{var}' not found in the file {file}.")
                
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
            if np.mean(x_values) > 10000:
                x_values = [val / 10000 for val in x_values]
        else:
            raise ValueError(f"'date' column not found in the file {file}.")

        # Extract y-values from the merged DataFrame.
        y_values = data[var]

        # Optionally set custom x-ticks if provided.
        if self.config.xticks:
            custom_xticks = [x_values[j] for j in self.config.xticks if j < len(x_values)]
            self.ax.set_xticks(custom_xticks)
        # Set x-axis limits if provided.
        if self.config.xlim:
            self.ax.set_xlim(x_values[self.config.xlim[0]], x_values[self.config.xlim[1]])                
        self.ax.plot(
            x_values, y_values * self.config.scale,
            color=self.config.line_color[i],
            marker=self.config.line_marker[i],
            linestyle=self.config.line_type[i],
            linewidth=self.config.line_width[i],
            label=self.config.labels[i]
        )
        # If self.config.average is True, calculate the overall average and add a horizontal line.
        if getattr(self.config, "average", False):
            # Compute the average, ignoring NaN values.
            avg_value = np.nanmean(y_values * self.config.scale)
            self.ax.axhline(
                y=avg_value ,
                color=self.config.line_color[i],
                linestyle=self.config.line_type[i],
                linewidth=self.config.line_width[i],
                label=f"{self.config.labels[i]} Average ({avg_value:.2f})"
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

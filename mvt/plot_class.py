import yaml
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

class Plot:
    def __init__(self, config_file):
        """
        Initialize the Plot class with a YAML configuration file.

        Parameters:
        - config_file (str): Path to the YAML configuration file.
        """
        with open(config_file, 'r') as file:
            self.config = yaml.safe_load(file)

        self.plot_type = self.config.get("plot_type", "performance_diagram")
        self.title = self.config.get("plot_title", "Default Plot")
        self.legend_title = self.config.get("legend_title", "Legend")
        self.output_file = self.config.get("output_filename", "output.png")
        self.input_files = self.config.get("input_files", [])
        self.labels = self.config.get("labels", [])
        self.colors = self.config.get("line_color", [])
        self.markers = self.config.get("line_marker", [])
        self.line_styles = self.config.get("line_type", [])
        self.line_widths = self.config.get("line_width", [])
        self.var_name = self.config.get("var_name", "RMSE")
        self.date_col = "DATE"
        self.y_label = self.config.get("y_label", "Value")
        # self.y_range = self.config.get("y_range", None)

    def setup_performance_diagram(self):
        """
        Set up the base grid for the Performance Diagram.
        """
        x = np.linspace(0.01, 1, 100)
        y = np.linspace(0.01, 1, 100)
        X, Y = np.meshgrid(x, y)
        CSI_levels = [0.1, 0.25, 0.5, 0.6, 0.75, 1.0]
        CSI = (X * Y) / (X + Y - X * Y)

        self.fig, self.ax = plt.subplots(figsize=(10, 8))

        # Plot CSI contours
        contour = self.ax.contour(X, Y, CSI, levels=CSI_levels, colors="gray", linestyles="solid")
        self.ax.clabel(contour, fmt="%.2f", inline=True, fontsize=10, colors="black")
        self.ax.text(1.05, 0.5, "CSI Curves", rotation=270, fontsize=12, va="center", color="gray")

        # Add frequency bias lines
        FB_values = [0.1, 0.25, 0.5, 1, 2, 4, 10]
        for FB in FB_values:
            fb_y = np.minimum(1, FB * x)
            self.ax.plot(x, fb_y, linestyle="--", color="black", linewidth=0.8)
            if fb_y[-1] < 1:
                self.ax.text(1.01, fb_y[-1], f"{FB:.1f}", fontsize=9, va="center", color="black")

        self.ax.set_xlabel("Success Ratio (1 - FAR)", fontsize=12)
        self.ax.set_ylabel("Probability of Detection (POD)", fontsize=12)
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.grid(True, linestyle="--", alpha=0.5)

    def add_to_performance_diagram(self):
        """
        Add data from files to the Performance Diagram.
        """
        for file, label, color, marker, line_style, line_width in zip(
            self.input_files, self.labels, self.colors, self.markers, self.line_styles, self.line_widths
        ):
            df = pd.read_csv(file)
            df = df.dropna(subset=['POD', 'SR', 'CSI', 'FBIAS'])
            self.ax.plot(
                df['SR'], df['POD'], label=label, color=color, marker=marker,
                linestyle=line_style, linewidth=line_width, alpha=0.8
            )

    def setup_time_series_plot(self):
        """
        Set up the time series plot area.
        """
        plt.figure(figsize=(12, 6))
        plt.title(self.title, fontsize=14)
        plt.xlabel("Date and Time", fontsize=12)
        plt.ylabel(self.y_label, fontsize=12)
        plt.grid(True, linestyle="--", alpha=0.6)

        # if self.y_range:
        #     plt.ylim(self.y_range)

    def add_to_time_series_plot(self):
        """
        Add data from files to the Time Series Plot.
        """
        for file, label, color, marker, line_style, line_width in zip(
            self.input_files, self.labels, self.colors, self.markers, self.line_styles, self.line_widths
        ):
            df = pd.read_csv(file)
            df[self.date_col] = pd.to_datetime(df[self.date_col])

            plt.plot(
                df[self.date_col],
                df[self.var_name],
                linestyle=line_style,
                color=color,
                marker=marker,
                label=label,
                linewidth=line_width,
                alpha=0.8
            )

            mean_value = np.mean(df[self.var_name])
            plt.axhline(
                y=mean_value,
                linestyle="--",
                color=color,
                label=f"{label} Mean ({mean_value:.2f})"
            )

    def finalize_and_save_plot(self):
        """
        Finalize and save the plot.
        """
        plt.legend(title=self.legend_title, fontsize='medium', shadow=True)
        plt.gcf().autofmt_xdate()
        plt.savefig(self.output_file, bbox_inches='tight')
        plt.close()
        print(f"Plot saved to {self.output_file}")

    def plot(self):
        """
        Generate the plot based on the configuration.
        """
        if self.plot_type == "performance_diagram":
            self.setup_performance_diagram()
            self.add_to_performance_diagram()
        elif self.plot_type == "time_series":
            self.setup_time_series_plot()
            self.add_to_time_series_plot()
        else:
            print("Invalid plot type. Please specify 'performance_diagram' or 'time_series'.")
            return

        self.finalize_and_save_plot()

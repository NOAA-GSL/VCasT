import matplotlib.pyplot as plt
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class BasePlot:
    def __init__(self, config_file):
        """
        Base class for all plots. Handles configuration loading and validation.
        """
        self.config = config_file
        self.fig, self.ax = None, None  # Initialize figure and axis

    @staticmethod
    def bin_columns(columns, prefix):
        """Return the ``<prefix>N`` columns present in ``columns``, in ascending
        numeric bin order. Used to discover how many probability bins a PCT-style
        aggregated file has, instead of assuming a fixed count."""
        cols = [c for c in columns
                if c.startswith(prefix) and c[len(prefix):].isdigit()]
        return sorted(cols, key=lambda c: int(c[len(prefix):]))

    def finalize_and_save(self):
        """
        Save the plot to a file.
        """

        # Draw a legend unless the config disables it with `legend: false`.
        if getattr(self.config, "legend", True):
            if getattr(self.config, "legend_style", False):
                self.ax.legend(
                    title=self.config.legend_title,
                    fontsize='medium',
                    shadow=True,
                    loc='center left',
                    bbox_to_anchor=(1, 0.5)
                )
            else:
                self.ax.legend(title=self.config.legend_title, fontsize='medium', shadow=True)


        plt.savefig(self.config.output_filename, bbox_inches='tight')
        plt.close()
        logging.info(f"Plot saved to {self.config.output_filename}")


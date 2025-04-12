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

    def finalize_and_save(self):
        """
        Save the plot to a file.
        """

        if hasattr(self.config, "legend_style"):
            if self.config.legend_style:
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


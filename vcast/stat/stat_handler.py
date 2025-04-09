import pandas as pd
import glob
import vcast.stat.constants as cn
from vcast.stat import AVAILABLE_LINE_TYPES
import numpy as np
import logging

class ReadStat:
    def __init__(self, config):
        """
        Initialize the class with the configuration file.
        """

        # Configure the logging system
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        self.config = config

    def run_all(self):
        
        config = self.config

        logging.info("Initializing ReadStat with config: %s", config)
        if config.line_type.lower() not in AVAILABLE_LINE_TYPES:
            logging.error("Line type %s not recognized.", config.line_type)
            raise Exception(f"Line type {config.line_type} not recognized.")
        
        sfiles = sorted(glob.glob(f'{config.input_stat_folder}/*.stat'))
        logging.info("Found %d stat files in %s.", len(sfiles), config.input_stat_folder)

        # Loop through all .stat files
        for i, file in enumerate(sfiles):
            logging.debug("Processing file %d: %s", i+1, file)
            df = self.process_file(file, config.line_type)  # Process each file

            if i == 0:
                # Initialize an empty DataFrame with correct headers
                df_combined = pd.DataFrame(columns=df.columns)
                logging.debug("Initialized combined DataFrame with columns: %s", df.columns.tolist())

            # Only concatenate if df is not empty
            if not df.empty:
                df_combined = pd.concat([df_combined, df], ignore_index=True)
                logging.debug("Concatenated file %s; combined DataFrame shape is now %s.", file, df_combined.shape)
            else:
                logging.warning("File %s produced an empty DataFrame; skipping.", file)

        if df_combined.empty:
            logging.error("All files produced empty DataFrames after filtering by line type.")
            raise ValueError("The DataFrame is empty after the line type filter.")

        df = df_combined
        logging.info("Combined DataFrame shape after processing files: %s", df.shape)
        
        df = self.filter_by_date(df, config.date_column, config.start_date, config.end_date)
        logging.info("DataFrame shape after date filtering: %s", df.shape)
        
        df = df.sort_values(by=config.date_column)
        logging.debug("DataFrame sorted by %s.", config.date_column)

        if config.string_filters:  # Check if self.string_filters is not empty
            df = self.filter_by_string(df, config.string_filters)
            logging.info("DataFrame shape after applying string filters: %s", df.shape)

        if config.thresholds:  # Check if self.thresholds is not empty
            df = self.filter_by_threshold(df, config.thresholds)
            logging.info("DataFrame shape after applying threshold filters: %s", df.shape)

        if config.columns_to_keep:  # Check if self.columns_to_keep is not empty
            df = self.filter_by_columns(df, config.columns_to_keep)
            logging.info("DataFrame shape after filtering by columns: %s", df.shape)

        # Call only if reformat_file is True
        if config.reformat_file:
            logging.info("Reformat file flag is True; saving reformatted file to %s.", config.output_reformat_file)
            self.save_dataframe(df, config.output_reformat_file)

        df = df.rename(columns={config.date_column: "date"})
        logging.debug("Renamed column %s to 'date'.", config.date_column)

        add_columns = config.stat_vars
        if hasattr(self, 'column_specific'):
            if "all_thresh" in config.stat_vars:
                add_columns = [var for var in config.stat_vars if var != "all_thresh"]
                add_columns = np.unique(self.column_specific + add_columns)
                logging.debug("Unique stat vars after combining column_specific: %s", add_columns)

        for i in add_columns:
            if i not in df.columns:
                logging.warning("Stat var '%s' is not available in the DataFrame.", i)

        new_columns = [col.lower() for col in add_columns if col.lower() in df.columns]
        logging.debug("Final list of stat var columns to use: %s", new_columns)

        # Convert the selected columns to numeric, coercing errors to NaN
        df[new_columns] = df[new_columns].apply(pd.to_numeric, errors="coerce")
        logging.info("Converted selected stat var columns to numeric.")

        scol = []
        for column, values in config.string_filters.items():
            scol += [column]

        columns = ['date'] + scol + new_columns
        logging.debug("Final DataFrame columns selected: %s", columns)

        df = df[columns]
        logging.info("DataFrame shape after final column selection: %s", df.shape)

        if config.output_file:
            logging.info("Saving output file to %s.", config.output_plot_file)
            self.save_dataframe(df, config.output_plot_file)
    
        if config.aggregate:
            self.run_aggregation(df, add_columns)


    def run_aggregation(self, df, add_columns = None):
            
            if not isinstance(df, pd.DataFrame):
                df = pd.read_csv(df, sep="\t")
            
            logging.info("DataFrame shape after aggregation: %s", df.shape)

            df = self.aggregation(df, self.config.group_by)

            if add_columns is not None:
                if self.config.line_type.lower() == "ecnt" and "ratio" in add_columns:
                    df['ratio'] = df['spread_plus_oerr'] / df['rmse']
                    logging.debug("Calculated 'ratio' as spread_plus_oerr / rmse.")

            logging.info("Saving aggregated file to %s.", self.config.output_agg_file)
            self.save_dataframe(df, self.config.output_agg_file)

    def all_columns(self, line_type, line_type_columns=cn.LINE_TYPE_COLUMNS):
        # Get the additional columns based on line type, or an empty list if not found
        line_type_columns = line_type_columns.get(line_type.lower(), [])
        full_cols = cn.FULL_HEADER + line_type_columns
        logging.debug("all_columns() for line_type '%s': %s", line_type, full_cols)
        return full_cols

    def process_file(self, file_path, line_type):
        """
        Reads a file line by line, skips the first line, 
        checks if a line matches the given line_type, 
        and adds it to a Pandas DataFrame.
        """
        logging.info("Processing file: %s", file_path)
        matching_rows = []
        # Get column headers dynamically
        headers = self.all_columns(line_type)
        fheaders = headers

        with open(file_path, "r") as file:
            next(file)  # Skip the first line (header row)
            for line in file:
                row_data = line.split()  # Split the line into columns
                # Check if the line contains the specific line type
                if row_data[headers.index("line_type")].lower() == line_type.lower():
                    if line_type.lower() in ['pct', 'pstd']:
                        fheaders = self.update_headers(headers, row_data, line_type.lower())
                        logging.debug("Updated headers for %s: %s", line_type, fheaders)
                    if len(row_data) != len(fheaders):
                        headers = self.all_columns(line_type, cn.LINE_TYPE_COLUMNS_OLD)
                        fheaders = headers
                        logging.debug("Re-adjusted headers using old columns for file: %s", file_path)
                    if len(row_data) == len(fheaders):
                        row_dict = dict(zip(fheaders, row_data[:len(fheaders)]))
                        matching_rows.append(row_dict)
                    else:
                        logging.warning("Skipping line in %s due to mismatched column count.", file_path)
        df = pd.DataFrame(matching_rows, columns=fheaders)
        logging.info("Processed file %s; resulting DataFrame shape: %s", file_path, df.shape)
        return df

    def update_headers(self, headers, row_data, line_type):
        number_of_thresholds = int(row_data[len(cn.FULL_HEADER) + 1])
        logging.debug("Number of thresholds found: %d", number_of_thresholds)
        hh = []
        if line_type == 'pct':
            self.column_specific = [item for i in range(1, number_of_thresholds) 
                                    for item in (f"thresh_{i}", f"oy_{i}", f"on_{i}")] + ["thresh_n"]
            hh = headers + self.column_specific
        elif line_type == 'pstd':
            self.column_specific = [f"thresh_{i}" for i in range(1, number_of_thresholds + 1)]
            hh = headers + self.column_specific
        logging.debug("Updated headers: %s", hh)
        return hh

    def filter_by_date(self, df, date_column, start_date, end_date):
        """
        Filters the DataFrame based on a date range.
        Converts date strings to datetime format before filtering.
        Raises an exception if the resulting DataFrame is empty.
        """
        logging.info("Filtering DataFrame by date range %s to %s on column '%s'.", start_date, end_date, date_column)
        try:
            if date_column not in df.columns:
                raise KeyError(f"Column '{date_column}' not found in DataFrame. Cannot filter by date.")
    
            df = df.copy()
            df[date_column] = pd.to_datetime(df[date_column], format="%Y%m%d_%H%M%S", errors="coerce")
            if df[date_column].isna().all():
                logging.error("Date conversion failed; all values are NaT: %s", df[date_column])
                raise ValueError(f"All values in column '{date_column}' could not be converted to datetime format.")
    
            start_date = pd.to_datetime(start_date, format="%Y-%m-%d_%H:%M:%S")
            end_date = pd.to_datetime(end_date, format="%Y-%m-%d_%H:%M:%S")
            df_filtered = df[(df[date_column] >= start_date) & (df[date_column] <= end_date)]
    
            if df_filtered.empty:
                logging.error("Date filtering resulted in an empty DataFrame.")
                raise ValueError("The DataFrame is empty after applying the date filter.")
    
            logging.info("Date filtering successful; resulting shape: %s", df_filtered.shape)
            return df_filtered
    
        except Exception as e:
            logging.exception("Error in filter_by_date:")
            raise RuntimeError(f"Error in `filter_by_date`: {str(e)}")
    
    def filter_by_threshold(self, df, thresholds):
        """
        Filters the DataFrame based on threshold values for multiple columns.
        Converts numeric columns to float before filtering to prevent errors.
        Raises an exception if the resulting DataFrame is empty.
        """
        logging.info("Filtering DataFrame by thresholds: %s", thresholds)
        try:
            df_filtered = df.copy()
            for column, (min_val, max_val) in thresholds.items():
                if column in df_filtered.columns:
                    df_filtered.loc[:, column] = df_filtered[column].astype(float)
                    df_filtered = df_filtered[(df_filtered[column] >= min_val) & (df_filtered[column] <= max_val)]
                    logging.debug("After filtering column '%s', shape: %s", column, df_filtered.shape)
                else:
                    logging.warning("Column '%s' not found in DataFrame, skipping threshold filter.", column)
    
            if df_filtered.empty:
                logging.error("Threshold filtering resulted in an empty DataFrame.")
                raise ValueError("The DataFrame is empty after applying threshold filters.")
    
            logging.info("Threshold filtering successful; resulting shape: %s", df_filtered.shape)
            return df_filtered
    
        except Exception as e:
            logging.exception("Error in filter_by_threshold:")
            raise RuntimeError(f"Error in `filter_by_threshold`: {str(e)}")

    def filter_by_string(self, df, string_filters):
        """
        Filters the DataFrame based on allowed string values for multiple columns.
        Raises an exception if the resulting DataFrame is empty.
        """
        logging.info("Filtering DataFrame using string filters: %s", string_filters)
        try:
            df_filtered = df.copy()
            for column, allowed_values in string_filters.items():
                if column in df_filtered.columns:
                    df_filtered = df_filtered[df_filtered[column].isin(allowed_values)]
                    logging.debug("After filtering column '%s', shape: %s", column, df_filtered.shape)
                else:
                    logging.warning("Column '%s' not found in DataFrame, skipping string filter.", column)
    
            if df_filtered.empty:
                logging.error("String filtering resulted in an empty DataFrame.")
                raise ValueError("The DataFrame is empty after applying the string filter.")
    
            logging.info("String filtering successful; resulting shape: %s", df_filtered.shape)
            return df_filtered
    
        except Exception as e:
            logging.exception("Error in filter_by_string:")
            raise RuntimeError(f"Error in `filter_by_string`: {str(e)}")

    def filter_by_columns(self, df, columns_to_keep):
        """
        Keeps only the specified columns in the DataFrame.
        Raises an exception if the resulting DataFrame is empty.
        """
        logging.info("Filtering DataFrame to keep columns: %s", columns_to_keep)
        try:
            if not columns_to_keep:
                logging.debug("No columns specified to keep; returning original DataFrame.")
                return df
    
            existing_columns = [col for col in columns_to_keep if col in df.columns]
            if not existing_columns:
                logging.error("None of the specified columns exist in the DataFrame.")
                raise ValueError("None of the specified columns exist in the DataFrame.")
    
            df_filtered = df[existing_columns]
            if df_filtered.empty:
                logging.error("Filtering by columns resulted in an empty DataFrame.")
                raise ValueError("The DataFrame is empty after applying the column filter.")
    
            logging.info("Column filtering successful; resulting shape: %s", df_filtered.shape)
            return df_filtered
    
        except Exception as e:
            logging.exception("Error in filter_by_columns:")
            raise RuntimeError(f"Error in `filter_by_columns`: {str(e)}")

    def aggregation(self, df, group_by_columns):
        """
        Aggregates the given DataFrame by the specified group_by_columns while keeping 
        the 'date' column if all values in the group are the same.
        
        Parameters:
          - df (pd.DataFrame): Input DataFrame containing the data.
          - group_by_columns (list): List of column names to group by.
        
        Returns:
          - pd.DataFrame: Aggregated DataFrame.
        """
        logging.info("Aggregating DataFrame using group_by columns: %s", group_by_columns)
        # Define aggregation functions for numeric columns
        aggregation_functions = {col: 'mean' for col in df.select_dtypes(include=['number']).columns}
        aggregated_df = df.groupby(group_by_columns, as_index=False).agg(aggregation_functions)
        logging.info("Aggregation complete; resulting shape: %s", aggregated_df.shape)
        return aggregated_df
    
    def save_dataframe(self, df, output_file):
        """
        Saves the DataFrame to a CSV file if reformat_file is set to True.
        Raises an error if the DataFrame is empty.
        """
        try:
            if df.empty:
                logging.error("Attempted to save an empty DataFrame.")
                raise ValueError("Cannot save an empty DataFrame.")
    
            df.to_csv(output_file, sep="\t", index=False, header=True)
            logging.info("DataFrame saved successfully to %s.", output_file)
    
        except Exception as e:
            logging.exception("Error in save_dataframe:")
            raise RuntimeError(f"Error in `save_dataframe`: {str(e)}")

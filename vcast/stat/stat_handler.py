import pandas as pd
import glob
import vcast.stat.constants as cn
from vcast.stat import AVAILABLE_LINE_TYPES

class ReadStat:
    def __init__(self, config):
        """
        Initialize the class with the configuration file.
        """

        if config.line_type.lower() not in AVAILABLE_LINE_TYPES:
            raise Exception(f"Line type not {config.line_type} not recognized.")
        
        sfiles = sorted(glob.glob(f'{config.input_stat_folder}/*.stat'))

        # Initialize an empty DataFrame with correct headers
        df_combined = pd.DataFrame(columns=self.all_columns(config.line_type))

        # Loop through all .stat files
        for file in sfiles:
            df = self.process_file(file, config.line_type)  # Process each file
           
            # Only concatenate if df is not empty
            if not df.empty:
                df_combined = pd.concat([df_combined, df], ignore_index=True)

        if df_combined.empty:
            raise ValueError("The DataFrame is empty after the line type filter.")
        
        df = df_combined

        df = self.filter_by_date(df, config.date_column, config.start_date, config.end_date)

        df = df.sort_values(by=config.date_column)

        if config.string_filters:  # Check if self.string_filters is not empty
            df = self.filter_by_string(df, config.string_filters)

        if config.thresholds:  # Check if self.thresholds is not empty
            df = self.filter_by_threshold(df, config.thresholds)        

        if config.columns_to_keep:  # Check if self.columns_to_keep is not empty
            df = self.filter_by_columns(df, config.columns_to_keep)

        # Call only if reformat_file is True
        if config.reformat_file:
            self.save_dataframe(df, config.output_reformat_file)

        df = df.rename(columns={config.date_column: "date"})

        #self.validate_stat_vars(df, self.stat_vars)

        new_columns = [col.lower() for col in config.stat_vars if col.lower() in df.columns]
        # Convert the selected columns to numeric, coercing errors to NaN
        df[new_columns] = df[new_columns].apply(pd.to_numeric, errors="coerce")

        scol = []
        for column, values in config.string_filters.items():
            scol += [column]

        columns = ['date'] + scol + new_columns

        df = df[columns]

        if config.output_file:
            self.save_dataframe(df, config.output_plot_file)

        if config.aggregate:
            df = self.aggregation(df, config.group_by)
            self.save_dataframe(df, config.output_agg_file)
        
    def all_columns(self, line_type):
        # Get the additional columns based on line type, or an empty list if not found
        line_type_columns = cn.LINE_TYPE_COLUMNS.get(line_type.lower(), [])
    
        return cn.FULL_HEADER + line_type_columns

    def process_file(self,file_path, line_type):
        """
        Reads a file line by line, skips the first line, 
        checks if a line matches the given line_type, 
        and adds it to a Pandas DataFrame.
        """
        # Get column headers dynamically
        headers = self.all_columns(line_type)
        
        # Create an empty DataFrame with these columns
        df = pd.DataFrame(columns=headers)        


        matching_rows = []

        # Open the file and read line by line
        with open(file_path, "r") as file:
            next(file)  # Skip the first line (header row)
            
            for line in file:
                # Split the line into columns (handling multiple spaces)
                row_data = line.split()
               
                # Ensure the line has enough columns before proceeding
                if len(row_data) == len(headers):
                    # Check if the line contains the specific line type
                    if row_data[headers.index("line_type")].lower() == line_type.lower():
                        # Convert to dictionary mapping headers to row values
                        row_dict = dict(zip(headers, row_data[:len(headers)]))
                        matching_rows.append(row_dict)

        # Convert list of dictionaries to DataFrame in one go
        df = pd.DataFrame(matching_rows, columns=headers)

        return df  # Return the filtered DataFrame


    def filter_by_date(self, df, date_column, start_date, end_date):
        """
        Filters the DataFrame based on a date range.
        Converts date strings to datetime format before filtering.
        Raises an exception if the resulting DataFrame is empty.
        """
        try:
            # Ensure the date column exists before filtering
            if date_column not in df.columns:
                raise KeyError(f"Column '{date_column}' not found in DataFrame. Cannot filter by date.")
    
            # Convert the date column to datetime format
            df = df.copy()  # Ensure modification doesn't affect original DataFrame
            df[date_column] = pd.to_datetime(df[date_column], format="%Y%m%d_%H%M%S", errors="coerce")
    
            # Check for NaT (invalid dates after conversion)
            if df[date_column].isna().all():
                print(df[date_column])
                raise ValueError(f"All values in column '{date_column}' could not be converted to datetime format.")
    
            # Convert start and end dates from YAML to datetime
            start_date = pd.to_datetime(start_date, format="%Y-%m-%d_%H:%M:%S")
            end_date = pd.to_datetime(end_date, format="%Y-%m-%d_%H:%M:%S")
    
            # Apply date filtering
            df_filtered = df[(df[date_column] >= start_date) & (df[date_column] <= end_date)]
    
            # Raise an error if filtering results in an empty DataFrame
            if df_filtered.empty:
                raise ValueError("The DataFrame is empty after applying the date filter.")
    
            return df_filtered
    
        except Exception as e:
            raise RuntimeError(f"Error in `filter_by_date`: {str(e)}")
    
    
    def filter_by_threshold(self, df, thresholds):
        """
        Filters the DataFrame based on threshold values for multiple columns.
        Converts numeric columns to float before filtering to prevent errors.
        Raises an exception if the resulting DataFrame is empty.
        """
        try:
            df_filtered = df.copy()  # Ensure we are working on a separate DataFrame
    
            # Apply threshold filtering for multiple columns (min-max range)
            for column, (min_val, max_val) in thresholds.items():
                if column in df_filtered.columns:
                    # Convert column to float before filtering (using .loc to avoid SettingWithCopyWarning)
                    df_filtered.loc[:, column] = df_filtered[column].astype(float)
    
                    # Apply filtering condition
                    df_filtered = df_filtered[(df_filtered[column] >= min_val) & (df_filtered[column] <= max_val)]
                else:
                    print(f"Warning: Column '{column}' not found in DataFrame, skipping threshold filter.")
    
            # Raise an error if filtering results in an empty DataFrame
            if df_filtered.empty:
                raise ValueError("The DataFrame is empty after applying threshold filters.")
    
            return df_filtered
    
        except Exception as e:
            raise RuntimeError(f"Error in `filter_by_threshold`: {str(e)}")

    def filter_by_string(self, df, string_filters):
        """
        Filters the DataFrame based on allowed string values for multiple columns.
        Raises an exception if the resulting DataFrame is empty.
        """
        try:
            df_filtered = df.copy()  # Work on a copy to avoid modifying original data

            for column, allowed_values in string_filters.items():
                if column in df_filtered.columns:
                    # Filter only rows where column values are in the allowed list
                    df_filtered = df_filtered[df_filtered[column].isin(allowed_values)]
                else:
                    print(f"Warning: Column '{column}' not found in DataFrame, skipping string filter.")
    
            # Raise an error if filtering results in an empty DataFrame
            if df_filtered.empty:
                raise ValueError("The DataFrame is empty after applying the string filter.")
    
            return df_filtered
    
        except Exception as e:
            raise RuntimeError(f"Error in `filter_by_string`: {str(e)}")

    def filter_by_columns(self, df, columns_to_keep):
        """
        Keeps only the specified columns in the DataFrame.
        Raises an exception if the resulting DataFrame is empty.
        """
        try:

            # If columns_to_keep is empty, return the full DataFrame
            if not columns_to_keep:
                return df
    
            # Filter only existing columns
            existing_columns = [col for col in columns_to_keep if col in df.columns]
    
            if not existing_columns:
                raise ValueError("None of the specified columns exist in the DataFrame.")
    
            df_filtered = df[existing_columns]
    
            # Raise an error if filtering results in an empty DataFrame
            if df_filtered.empty:
                raise ValueError("The DataFrame is empty after applying the column filter.")
    
            return df_filtered
    
        except Exception as e:
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
    
        # Define aggregation functions for numeric columns
        aggregation_functions = {col: 'mean' for col in df.select_dtypes(include=['number']).columns}
    
        # Perform the aggregation
        aggregated_df = df.groupby(group_by_columns, as_index=False).agg(aggregation_functions)
    
        return aggregated_df

    
    def save_dataframe(self, df, output_file):
        """
        Saves the DataFrame to a CSV file if reformat_file is set to True.
        Raises an error if the DataFrame is empty.
        """
        try:
            if df.empty:
                raise ValueError("Cannot save an empty DataFrame.")
    
            df.to_csv(output_file, sep="\t", index=False, header=True)
            print(f"DataFrame saved successfully to {output_file}.")

        except Exception as e:
            raise RuntimeError(f"Error in `save_dataframe`: {str(e)}")
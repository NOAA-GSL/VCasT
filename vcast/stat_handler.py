import yaml
import pandas as pd
import glob
import vcast.constants as cn
import numpy as np
from vcast.stat_handler import *


class ReadStat:
    def __init__(self, config_file):
        """
        Initialize the class with the configuration file.
        """
        self.available_line_types = [
            "fho", "ctc", "cts", "cnt", "mctc", "mpr", "sl1l2", "sal1l2", 
            "vl1l2", "vcnt", "pct", "pstd", "pjc", "prc", "eclv", "sl1l2", 
            "sal1l2", "vl1l2", "val1l2", "vcnt", "mpr", "seeps_mpr", "seeps"
        ]

        self.config = self.read_config_file(config_file)
        self.input_stat_folder = self.config['input_stat_folder']
        self.line_type = self.config['line_type']
        self.date_column = self.config["date_column"]
        self.start_date = self.config["start_date"]
        self.end_date = self.config["end_date"]
        self.thresholds = self.config.get("thresholds", {})  # Min-Max filter for numerical columns
        self.string_filters = self.config.get("string_filters", {})  # Allowed values for string columns
        self.columns_to_keep = self.config.get("columns_to_keep", [])  # Columns to keep (empty means keep all)
        self.reformat_file = self.config.get("reformat_file", False)  # Default to False if not found
        self.output_reformat_file = self.config['output_reformat_file']
        self.stat_vars = self.config.get("stat_vars", [])  # Columns to keep (empty means keep all)
        self.output_file = self.config.get("output_file", False)  # Default to False if not found
        self.output_plot_file = self.config['output_plot_file']
        self.aggregate = self.config.get("aggregate", False)  # Default to False if not found
        self.group_by = self.config.get("group_by", [])   # Default to False if not found
        self.output_agg_file = self.config['output_agg_file']

        if self.line_type.lower() not in self.available_line_types:
            raise Exception(f"Line type not {self.line_type} not recognized.")
        
        sfiles = sorted(glob.glob(f'{self.input_stat_folder}/*.stat'))

        # Initialize an empty DataFrame with correct headers
        df_combined = pd.DataFrame(columns=self.all_columns(self.line_type))

        # Loop through all .stat files
        for file in sfiles:
            df = self.process_file(file, self.line_type)  # Process each file
           
            # Only concatenate if df is not empty
            if not df.empty:
                df_combined = pd.concat([df_combined, df], ignore_index=True)

        if df_combined.empty:
            raise ValueError("The DataFrame is empty after the line type filter.")
        
        df = df_combined

        df = self.filter_by_date(df, self.date_column, self.start_date, self.end_date)

        df = df.sort_values(by=self.date_column)

        if self.string_filters:  # Check if self.string_filters is not empty
            df = self.filter_by_string(df, self.string_filters)

        if self.thresholds:  # Check if self.thresholds is not empty
            df = self.filter_by_threshold(df, self.thresholds)        

        if self.columns_to_keep:  # Check if self.columns_to_keep is not empty
            df = self.filter_by_columns(df, self.columns_to_keep)

        # Call only if reformat_file is True
        if self.reformat_file:
            self.save_dataframe(df, self.output_reformat_file)

        df = df.rename(columns={self.date_column: "date"})

        #self.validate_stat_vars(df, self.stat_vars)

        new_columns = [col.lower() for col in self.stat_vars if col.lower() in df.columns]
        # Convert the selected columns to numeric, coercing errors to NaN
        df[new_columns] = df[new_columns].apply(pd.to_numeric, errors="coerce")

        scol = []
        for column, values in self.string_filters.items():
            scol += [column]

        columns = ['date'] + scol + new_columns

        df = df[columns]

        if self.output_file:
            self.save_dataframe(df, self.output_plot_file)

        if self.aggregate:
            df = self.aggregation(df, self.group_by)
            self.save_dataframe(df, self.output_agg_file)

    @staticmethod
    def read_config_file(config_file):
        """
        Read the configuration file and return the parsed config as a dictionary.
        """
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
        
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

    def validate_stat_vars(self, df, stat_vars):
        """
        Validates if all required columns exist in the DataFrame for each statistic in stat_vars.
        
        Args:
            df: Pandas DataFrame
            stat_vars: List of statistics from YAML file (e.g., ['rmse', 'ff'])
    
        Returns:
            Dictionary with validation results (True if all required fields exist, False otherwise).
        """
        try:
            validation_results = {}
    
            for stat in stat_vars:
                            # If the statistic itself is already a column, it's valid
                if stat in df.columns:
                    validation_results[stat] = True
                    print(df[stat])
                    continue  # Skip checking required fields
                
                required_fields = []
    
                # Check if the stat exists in STATISTIC_TO_FIELDS1
                if stat in cn.STATISTIC_TO_FIELDS1:
                    required_fields.extend(cn.STATISTIC_TO_FIELDS1[stat])
    
                # Check if the stat exists in STATISTIC_TO_FIELDS2
                if stat in cn.STATISTIC_TO_FIELDS2:
                    required_fields.extend(cn.STATISTIC_TO_FIELDS2[stat])
    
                # Remove duplicates (in case the stat appears in both dictionaries)
                required_fields = list(set(required_fields))
    
                # Check if all required fields exist in the DataFrame
                if required_fields:
                    missing_fields = [field for field in required_fields if field not in df.columns]
                    validation_results[stat] = len(missing_fields) == 0  # True if all fields exist
    
                    if missing_fields:
                        print(f"Warning: Missing columns for '{stat}': {missing_fields}")
                    else:
                        df = calculate_stats(stat,df)
                        print(df[stat])
    
                else:
                    print(f"Warning: Statistic '{stat}' not found in STATISTIC_TO_FIELDS1 or STATISTIC_TO_FIELDS2.")
                    validation_results[stat] = False
    
            return validation_results
    
        except Exception as e:
            raise RuntimeError(f"Error in `validate_stat_vars`: {str(e)}")


def calculate_stats(stat, df):
    """
    Calculates various contingency table statistics based on the provided statistic name.
    
    Args:
        stat (str): The name of the statistic to calculate.
        df (pd.DataFrame): The DataFrame containing contingency table values.

    Returns:
        pd.DataFrame: Updated DataFrame with the computed statistic.
    """
    # Ensure contingency table values are integers
    contingency_vars = ['fy_oy', 'fy_on', 'fn_oy', 'fn_on']

    print(df[contingency_vars])
    for var in contingency_vars:
        if var in df.columns:
            df[var] = df[var].astype(int)

    if stat == "baser":
        # Base Rate: How often the event actually occurs
        df["baser"] = df["fy_oy"] / (df["fy_oy"] + df["fn_oy"])

    elif stat == "acc":
        # Accuracy: Proportion of correct forecasts
        df["acc"] = (df["fy_oy"] + df["fn_on"]) / (df["fy_oy"] + df["fn_on"] + df["fy_on"] + df["fn_oy"])

    elif stat == "fbias":
        # Frequency Bias: How often an event is forecasted compared to how often it occurs
        df["fbias"] = (df["fy_oy"] + df["fy_on"]) / (df["fy_oy"] + df["fn_oy"])

    elif stat == "fmean":
        # Forecast Mean: Average of forecasted "yes" events
        df["fmean"] = (df["fy_oy"] + df["fy_on"]) / 2

    elif stat == "pody":
        # Probability of Detection (PODY): Sensitivity or recall
        df["pody"] = df["fy_oy"] / (df["fy_oy"] + df["fn_oy"])

    elif stat == "pofd":
        # Probability of False Detection (POFD): False alarm ratio among negatives
        df["pofd"] = df["fy_on"] / (df["fy_on"] + df["fn_on"])

    elif stat == "podn":
        # Probability of Detecting "No" (PODN): Correctly forecasting no events
        df["podn"] = df["fn_on"] / (df["fn_on"] + df["fy_on"])

    elif stat == "far":
        # False Alarm Ratio (FAR): How often a "yes" forecast is incorrect
        df["far"] = df["fy_on"] / (df["fy_oy"] + df["fy_on"])

    elif stat == "csi":
        # Critical Success Index (CSI): Accuracy when ignoring "no-no" cases
        df["csi"] = df["fy_oy"] / (df["fy_oy"] + df["fy_on"] + df["fn_oy"])

    elif stat == "gss":
        # Gilbert Skill Score (GSS): Measures forecast skill compared to random chance
        df["gss"] = ((df["fy_oy"] * df["fn_on"]) - (df["fy_on"] * df["fn_oy"])) / (
                    (df["fy_oy"] + df["fn_oy"]) * (df["fy_oy"] + df["fy_on"]) +
                    (df["fn_on"] + df["fy_on"]) * (df["fn_on"] + df["fn_oy"])
        )

    elif stat == "hk":
        # Hanssen-Kuipers Score (HK): True Skill Statistic
        df["hk"] = (df["fy_oy"] / (df["fy_oy"] + df["fn_oy"])) - (df["fy_on"] / (df["fy_on"] + df["fn_on"]))

    elif stat == "hss":
        # Heidke Skill Score (HSS): Measures skill relative to random chance
        df["hss"] = 2 * ((df["fy_oy"] * df["fn_on"]) - (df["fy_on"] * df["fn_oy"])) / (
                    (df["fy_oy"] * df["fn_on"]) + (df["fy_on"] * df["fn_oy"]) +
                    (df["fy_oy"] * df["fy_on"]) + (df["fn_oy"] * df["fn_on"])
        )

    elif stat == "odds":
        # Odds Ratio: The ratio of correctly forecasted events vs. false alarms
        df["odds"] = (df["fy_oy"] * df["fn_on"]) / (df["fy_on"] * df["fn_oy"])

    elif stat == "lodds":
        # Log Odds Ratio: Log transformation of the odds ratio
        df["lodds"] = np.log(df["odds"])

    elif stat == "baggs":
        # Bias-Adjusted Gilbert Skill Score (BAGGS)
        df["baggs"] = df["fy_oy"] / (df["fy_oy"] + df["fn_oy"] + df["fy_on"])

    elif stat == "eclv":
        # Economic Cost/Loss Value (ECLV): Measures financial impact
        df["eclv"] = (df["fy_oy"] - df["fy_on"]) / (df["fy_oy"] + df["fn_oy"] + df["fy_on"] + df["fn_on"])

    else:
        raise Exception(f"Stat name '{stat}' not recognized.")

    return df



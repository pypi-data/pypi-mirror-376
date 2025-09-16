import pandas as pd
import numpy as np
import time
import sys
import os
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from seshatdatasetanalysis.utils import download_data, fetch_urls, weighted_mean, get_max
from seshatdatasetanalysis.mappings import value_mapping, social_complexity_mapping, miltech_mapping, ideology_mapping


class Template():
    def __init__(self, 
                 categories = list(['sc']),
                 polity_url = "https://seshat-db.com/api/core/polities/",
                 file_path = None,
                 save_excel = False
                 ):
        self.template = pd.DataFrame()
        self.categories = categories
        self.polity_url = polity_url
        self.save_excel = save_excel

        self.debug = pd.DataFrame(columns=["polity", "variable", "label", "issue"])
        if self.save_excel:
            self.full_dataset = pd.DataFrame(columns=["NGA", "PolityID", "PolityName", "Section", "Subsection","value_from", "value_to", "year_from", "year_to", "is_disputed", "is_uncertain"])

        if (polity_url is not None ) and (file_path is None):
            self.initialize_dataset(polity_url)
        elif (file_path is not None):
            self.load_dataset(file_path)
        else:
            print("Please provide either a polity_url or a file_path")
            sys.exit()
        
    def __len__(self):
        return len(self.template)

    def __getitem__(self, idx):
        return self.template.iloc[idx]
    
    # ---------------------- HELPER FUNCTIONS ---------------------- #
    def compare_dicts(self, dict1, dict2):
        """Compare whether two dictionaries are the same entry by entry."""
        differences = {}
        
        # Get all keys from both dictionaries
        all_keys = set(dict1.keys()).union(set(dict2.keys()))
        
        for key in all_keys:
            value1 = dict1.get(key, None)
            value2 = dict2.get(key, None)
            
            if value1 != value2:
                if pd.isnull(value1) and pd.isnull(value2):
                    continue
                differences[key] = (value1, value2)
        
        return differences

    def compare_rows(self, row1, row2):
        """Compare whether two rows are the same entry by entry. Returns a dictionary of differences."""
        differences = self.compare_dicts(dict(row1), dict(row2))
        return differences

    def is_same(self, row1, row2):
        """Check if two rows are the same entry by entry. Returns a boolean."""
        return self.compare_rows(row1, row2) == {}

    def check_for_nans(self,d):
        """Check if a variable dictionary contains NaN values."""

        if not isinstance(d, dict):
            if np.isnan(d):
                return False
            else:
                print(d)
            return False
        
        def contains_nan(values):
            # Check if the values are numeric and contain NaNs
            if isinstance(values, (list, np.ndarray)):
                return any(isinstance(v, (int, float)) and np.isnan(v) for v in values)
            return False
        
        ts = d.get('t', [])
        if contains_nan(ts):
            return True
        
        vals = d.get('value', [])
        for val_row in vals:
            for (x, y) in val_row:
                if (isinstance(x, (int, float)) and np.isnan(x)) or (isinstance(y, (int, float)) and np.isnan(y)):
                    return True
        
        years = d.get('polity_years', [])
        if contains_nan(years):
            return True
        
        return False

    def check_nan_polities(self, pol, df, variable_name):
        """Check if a polity has all NaN values for a given variable."""
        pol_df = df.loc[df.polity_id == pol]
        if pol_df.empty:
            return True
        if pol_df[variable_name].isnull().all():
            return True
        return False

    def get_values(self, val_from, val_to):
        """Clean up the values for a range variable."""
        if (val_from is None) and (val_to is None):
            return None
        elif (val_from is not None) and (val_to is None):
            val_to = val_from
        elif (val_from is None) and (val_to is not None):
            val_from = val_to
        return (val_from, val_to)

    def add_empty_col(self, variable_name):
        self.template[variable_name] = np.nan
        self.template[variable_name] = self.template[variable_name].astype('object')

    # ---------------------- BUILDING FUNCTIONS ---------------------- #

    def initialize_dataset(self, url):
        """
        Initializes the dataset by downloading polity data from the given URL and populating a template DataFrame.
        Args:
            url (str): The URL from which to download the polity data.
        Returns:
            None
        This function performs the following steps:
        1. Sets up an empty template DataFrame with columns ["NGA", "PolityID", "PolityName"].
        2. Specifies the data type for the "PolityID" column as integer.
        3. Downloads the polity data from the provided URL.
        4. Iterates over all unique polity IDs in the downloaded data.
        5. For each polity ID, creates a temporary DataFrame with relevant data.
        6. Adds the temporary DataFrame to the template.
        7. Resets the index of the template DataFrame.
        """

        # set up empty template
        self.template = pd.DataFrame(columns = ["NGA", "PolityID", "PolityName"])
        # specify the columns data types
        self.template['PolityID'] = self.template['PolityID'].astype('int')
        # download the polity data
        df = download_data(url)

        polityIDs = df.id.unique()
        # iterate over all polities
        for polID in polityIDs:
            pol_df = df.loc[df.id == polID, ['home_nga_name', 'id', 'name','start_year','end_year']]
            # create a temporary dataframe with all data for current polity
            pol_df_new = pd.DataFrame(dict({"NGA" : pol_df.home_nga_name.values[0], 
                                            "PolityID": pol_df.id.values[0], 
                                            "PolityName": pol_df.name.values[0],
                                            "StartYear": pol_df.start_year.values[0],
                                            "EndYear": pol_df.end_year.values[0]}), index = [0])
            # add the temporary dataframe to the template
            self.template = pd.concat([self.template, pol_df_new])
        self.template.reset_index(drop=True, inplace=True)

    def download_all_categories(self):
        """
        Downloads datasets for all categories in the attribute self.categories.
        This method iterates over all categories, fetches URLs for each category,
        and then adds the datasets from the fetched URLs to the instance.
        Returns:
            None
        """

        urls = {}
        for category in self.categories:
            urls.update(fetch_urls(category))
        for key in urls.keys():
            self.add_dataset_from_url(key,urls[key])
    
    def add_dataset_from_url(self, key, url):
        """
        Adds a dataset to the template from a given URL.
        This method checks if the dataset identified by the given key is already present in the template's dataframe.
        If the dataset is not present, it downloads the data from the specified URL, measures the download time,
        and adds the dataset to the template.
        Parameters:
        key (str): The key to identify the dataset in the dataframe.
        url (str): The URL from which to download the dataset.
        Returns:
        None
        """

        # check if the dataset is already in the dataframe
        if key in self.template.columns:
            print(f"Dataset {key} already in dataframe")
            return
        
        # download the data
        tic = time.time()
        df = download_data(url)
        toc = time.time()
        print(f"Downloaded {key} dataset with {len(df)} rows in {toc-tic} seconds")
        if len(df) == 0:
            print(f"Empty dataset for {key}")
            return
        self.add_to_template(df, key)


    def add_to_template(self, df, key):
        """
        Adds data from a given DataFrame to the template based on a specified key.
        This function processes the input DataFrame `df` and adds its data to the template.
        It checks for the presence of specific columns and handles the addition of data
        for each polity in the template. If a polity is not found in the DataFrame, it
        attempts to download the data from a specified URL. The function also performs
        tests after adding the data to ensure consistency.
        Args:
            df (pandas.DataFrame): The DataFrame containing the data to be added.
            key (str): The key used to identify the dataset and construct the URL for downloading missing data.
        Returns:
            None
        """

        variable_name = df.name.unique()[0].lower()
        row_variable_name = variable_name
        if (variable_name not in df.columns) and (variable_name + "_from" not in df.columns):
            row_variable_name = 'coded_value'
        range_var = False
        col_name = key.split('/')[-1]
        if variable_name + "_from" in df.columns:
            range_var = True
        elif ('religion' in variable_name) and ('polity' in variable_name):
            col_name = col_name.replace('polity-', '')
            row_variable_name = variable_name.replace('polity_', '')
        
        self.add_empty_col(col_name)
        polities = self.template.PolityName.unique()
        df.columns = df.columns.str.lower()
        
        if self.save_excel:
            new_df = pd.DataFrame(columns=["NGA", "PolityID", "PolityName", "Section", "Subsection","value_from", "value_to", "year_from", "year_to", "is_disputed", "is_uncertain"])
        
        for pol in polities:
            if pol not in df.polity_name.values:
                # pol_old_name = self.template.loc[self.template.PolityName == pol, 'PolityOldName'].values[0]
                pol_df = download_data("https://seshat-db.com/api/"+f"{key}/?polity__new_name__icontains={pol}",size = None)
                if pol_df.empty:
                    continue
                else:
                    print(f"Found {pol} in {key} dataset")
            else:
                pol_df = df.loc[df.polity_name == pol]
            
            self.add_polity(pol_df, range_var, variable_name, col_name)
        
            if self.save_excel and len(pol_df) > 0:
                if range_var:
                    new_df = pd.DataFrame({
                        "NGA": self.template.loc[self.template.PolityID == pol_df.polity_id.iloc[0],'NGA'].values[0],
                        "PolityID": pol_df['polity_id'],
                        "PolityName": pol_df['polity_name'],
                        "Section": key.split('/')[0],
                        "Subsection": key.split('/')[1],
                        "value_from": pol_df[row_variable_name + '_from'],
                        "value_to": pol_df[row_variable_name + '_to'],
                        "year_from": pol_df['year_from'],
                        "year_to": pol_df['year_to'],
                        "is_disputed": pol_df['is_disputed'],
                        "is_uncertain": pol_df['is_uncertain']
                    })
                else:
                    new_df = pd.DataFrame({
                        "NGA": self.template.loc[self.template.PolityID == pol_df.polity_id.iloc[0],'NGA'].values[0],
                        "PolityID": pol_df['polity_id'],
                        "PolityName": pol_df['polity_name'],
                        "Section": key.split('/')[0],
                        "Subsection": key.split('/')[1],
                        "value_from": pol_df[row_variable_name],
                        "value_to": np.nan,
                        "year_from": pol_df['year_from'],
                        "year_to": pol_df['year_to'],
                        "is_disputed": pol_df['is_disputed'],
                        "is_uncertain": pol_df['is_uncertain']
                    })
                self.full_dataset = pd.concat([self.full_dataset, new_df], ignore_index=True)
        self.perform_tests(df, row_variable_name, range_var, col_name)
        print(f"Added {key} dataset to template")

    def add_polity(self, pol_df, range_var, variable_name, col_name):
        """
        Adds polity data to the template.
        This function processes a DataFrame containing polity data, checks for duplicates, handles disputed and uncertain entries, 
        and appends the processed data to the template. It ensures that the data is in chronological order and handles various 
        cases where year data might be missing or overlapping.
        Parameters:
        pol_df (pd.DataFrame): DataFrame containing polity data with columns such as 'polity_id', 'year_from', 'year_to', 
                               'is_disputed', 'is_uncertain', and the variable of interest.
        range_var (bool): Indicates whether the variable of interest is a range variable.
        variable_name (str): The name of the variable to be processed.
        col_name (str): The name of the column in the template where the processed data will be stored.
        Returns:
        None
        Raises:
        SystemExit: If there is an unexpected overlap in year data or other critical issues.
        """
        
        # create a dataframe with only the data for the current polity and sort it by year
        # this allows to assume entries are dealth with in chronological order
        pol = pol_df.polity_id.values[0]

        pol_df = pol_df.sort_values(by = 'year_from')
        pol_df = pol_df.reset_index(drop=True)

        polity_years = [self.template.loc[self.template.PolityID == pol, 'StartYear'].values[0], self.template.loc[self.template.PolityID == pol, 'EndYear'].values[0]]
        
        # reset variable dict variables
        times = [[]]
        values = [[]]
        
        for ind,row in pol_df.iterrows():
            # reset variables
            disp = False
            unc = False
            row_variable_name = variable_name
            if 'polity_religion' in variable_name:
                row_variable_name = variable_name.replace('polity_', '')
            if (row_variable_name not in row) and (row_variable_name + "_from" not in row):
                row_variable_name = 'coded_value'

            t = []
            value = []
            # check if the polity has multiple rows
            if ind > 0:
                if range_var:
                    relevant_columns = ['polity_id','year_from', 'year_to', 'is_disputed', 'is_uncertain', row_variable_name+'_from', row_variable_name +'_to']
                else:
                    relevant_columns = ['polity_id','year_from', 'year_to', 'is_disputed', 'is_uncertain', row_variable_name]
               
                # if the row is a duplicate of the previous row, skip it
                if pol_df.loc[:ind-1, relevant_columns].apply(lambda x: self.is_same(x, pol_df.loc[ind,relevant_columns]), axis=1).any():
                    print("Duplicate rows found")
                    continue
                elif pol_df.loc[ind,'is_disputed']:
                    # check if the disputed row has the same year as a previous row
                    if pol_df.loc[:ind-1,'year_from'].apply(lambda x: x == pol_df.loc[ind,'year_from']).any():
                        disp = True
                    # check if the disputed row doesn't have a year, this is here because NaN != NaN so need to check separately
                    elif pol_df.loc[:ind-1,'year_from'].isna().any() and pol_df.loc[ind,'year_from'].isna():
                        disp = True
                elif pol_df.loc[ind,'is_uncertain']:
                    if pol_df.loc[:ind-1,'year_from'].apply(lambda x: x == pol_df.loc[ind,'year_from']).any():
                        unc = True
                    elif pol_df.loc[:ind-1,'year_from'].isna().any() and pd.isna(pol_df.loc[ind,'year_from']):
                        unc = True

            if ind < len(pol_df)-1:
                # in the case of the year to being the same as the year from of the next row, subtract one year to the year from to remove overlap
                if (pol_df.loc[ind,'year_from'] is not None):
                    if (pol_df.loc[ind,'year_to'] == pol_df.loc[ind+1,'year_from']) and (pol_df.loc[ind,'year_from'] != pol_df.loc[ind+1,'year_from']):
                        if row.year_to == row.year_from:
                            sys.exit(7)
                        row.year_to = row.year_to - 1
                    
            # check if polity has no year data and in that case use the polity start and end year
            if (row.year_from is None or pd.isna(row.year_from)) and (row.year_to is None or pd.isna(row.year_to)):
                # if the variable is a range variable, check if the range is defined
                if range_var:

                    val_from = row[row_variable_name + "_from"]
                    val_to = row[row_variable_name + "_to"]
                    # if no range variables are defined skip the row
                    val = self.get_values(val_from, val_to)
                    if val is None:
                        continue
                elif isinstance(row[row_variable_name], str) and row_variable_name.startswith('religion'):
                    v = row[row_variable_name].lower()
                    val = (v,v)
                else:
                    v = value_mapping.get(row[row_variable_name], -1)
                    if (v is None) or pd.isna(v):
                        continue
                    elif v == -1:
                        debug_row = pd.DataFrame({"polity": pol, "variable": variable_name, "label": 'template', "issue": f"value {row[row_variable_name]} is not in mapping"}, index = [0])
                        self.debug = pd.concat([self.debug, debug_row])
                        continue

                    val = (value_mapping[row[row_variable_name]], value_mapping[row[row_variable_name]])

                # append the values and times to the lists
                value.append(val)
                value.append(val)
                t.append(self.template.loc[self.template.PolityID == pol, 'StartYear'].values[0])
                t.append(self.template.loc[self.template.PolityID == pol, 'EndYear'].values[0])
                
            # check if only one year is defined, either because the year_from and year_to are the same or one of them is None
            elif (row.year_from == row.year_to) or ((row.year_from is None) and (row.year_to is not None)) or ((row.year_from is not None) and (row.year_to is None)):
                # if variable is a range variable, check if the range is defined
                if range_var:
                    val_from = row[row_variable_name + "_from"]
                    val_to = row[row_variable_name + "_to"]
                    # if no range variables are defined skip the row
                    val = self.get_values(val_from, val_to)
                    if val is None:
                        continue
                elif isinstance(row[row_variable_name], str) and row_variable_name.startswith('religion'):
                    v = row[row_variable_name].lower()
                    val = (v,v)
                else:
                    v = value_mapping.get(row[row_variable_name], -1)
                    if (v is None) or pd.isna(v):
                        continue
                    elif v == -1:
                        debug_row = pd.DataFrame({"polity": pol, "variable": variable_name, "label": 'template', "issue": f"value {row[row_variable_name]} is not in mapping"}, index = [0])
                        self.debug = pd.concat([self.debug, debug_row])
                        continue
                    val = (v, v)

                value.append(val)
                year = row.year_from if row.year_from is not None else row.year_to
                
                if year < self.template.loc[self.template.PolityID == pol, 'StartYear'].values[0]:
                    print("Error: The year is outside the polity's start and end year")
                    debug_row = pd.DataFrame({"polity": pol, "variable": variable_name, "label": 'template', "issue": f"year {year} outside polity years"}, index = [0])
                    self.debug = pd.concat([self.debug, debug_row])
                    continue
                elif year > self.template.loc[self.template.PolityID == pol, 'EndYear'].values[0]:
                    print("Error: The year is outside the polity's start and end year")
                    debug_row = pd.DataFrame({"polity": pol, "variable": variable_name, "label": 'template', "issue": f"year {year} outside polity years"}, index = [0])
                    self.debug = pd.concat([self.debug, debug_row])
                    continue
                    
                t.append(year)

            # check if both years are defined
            elif (row.year_from != row.year_to) and pd.notna(row.year_from) and pd.notna(row.year_to):
                
                if range_var:
                    val_from = row[row_variable_name + "_from"]
                    val_to = row[row_variable_name + "_to"]
                    # if no range variables are defined skip the row
                    val = self.get_values(val_from, val_to)
                    if val is None:
                        continue
                elif isinstance(row[row_variable_name], str) and row_variable_name.startswith('religion'):
                    v = row[row_variable_name].lower()
                    val = (v,v)
                else:
                    
                    # check if row[variable_name] is a finite number
                    if isinstance(row[row_variable_name], (int, float)) and pd.notna(row[row_variable_name]):
                        v = row[row_variable_name]
                    else:
                        v = value_mapping.get(row[row_variable_name], -1)
                        if (v is None) or pd.isna(v):
                            continue
                        elif v == -1:
                            debug_row = pd.DataFrame({"polity": pol, "variable": variable_name, "label": 'template', "issue": f"value {row[row_variable_name]} is not in mapping"}, index = [0])
                            self.debug = pd.concat([self.debug, debug_row])
                            continue
                    val = (v, v)

                value.append(val)
                value.append(val)
                t_from = row.year_from
                t_to = row.year_to

                if isinstance(t_from, (str)):
                    t_from = t_from.replace('CE', '').replace('BCE','')
                    t_from = int(t_from)
                if isinstance(t_to, (str)):
                    t_to = t_to.replace('CE', '').replace('BCE','')
                    t_to = int(t_to)

                if t_from<self.template.loc[self.template.PolityID == pol, 'StartYear'].values[0]:
                    print("Error: The year is outside the polity's start and end year")
                    debug_row = pd.DataFrame({"polity": pol, "variable": variable_name, "label": "template", "issue": f"year {t_from} outside polity years"}, index = [0])
                    self.debug = pd.concat([self.debug, debug_row])
                    continue
                elif t_to > self.template.loc[self.template.PolityID == pol, 'EndYear'].values[0]:
                    print("Error: The year is outside the polity's start and end year")
                    debug_row = pd.DataFrame({"polity": pol, "variable": variable_name, "label": "template", "issue": f"{t_to} outside polity years"}, index = [0])
                    self.debug = pd.concat([self.debug, debug_row])
                    continue
                    
                t.append(t_from)
                t.append(t_to)
            else:
                print('new')
                sys.exit(1) 
                
            if disp or unc:

                new_vals = []
                new_t = []
                for val_row,time_row in zip(values,times):
                    # find the closest year to t
                    for ti in t:
                        time_diff = np.abs(np.array(time_row)-np.array(ti))
                        ind = np.argmin(time_diff)
                        new_t_row = time_row.copy()
                        new_t_row[ind] = ti
                        new_t.append(new_t_row)
                        new_row = val_row.copy()
                        new_row[ind] = val
                        new_vals.append(new_row)
                #  append new timeline to the value entry of the dictionary
                values = values + new_vals
                times = times + new_t
            else:
                if len(values[0]) == 0:
                    values = list([value])
                else:
                    for val_row in range(len(values)):
                        values[val_row] = values[val_row] + value
                if len(times[0]) == 0:
                    times = list([t])
                else:
                    for time_row in range(len(times)):
                        times[time_row] = list(times[time_row]) + t

        variable_dict = {"t": times, "value": values, "polity_years": polity_years}

        for dict_row,t_row in zip(variable_dict['value'],variable_dict['t']):
            if len(t_row) != len(dict_row):
                # add to debug dataframe
                debug_row = pd.DataFrame({"polity": pol, "variable": variable_name, "label": "template", "issue": "mismatched lengths"}, index = [0])
                self.debug = pd.concat([self.debug, debug_row])
                return "Error: The length of the time and value arrays are not the same"
    
        if len(variable_dict['t'][0]) == 0:
            return "Error: No data for polity"
            
        self.template.loc[self.template.PolityID == pol, col_name] = [variable_dict]

    def perform_tests(self, df, variable_name, range_var, col_name):
        if self.template[col_name].apply(lambda x: self.check_for_nans(x)).any():
            print("Error: NaNs found in the data")
            sys.exit(4)
        if range_var:
            var_name = variable_name + "_from"
        else:
            var_name = variable_name
        if (self.template['PolityID'].apply(lambda x: self.check_nan_polities(x, df, var_name)) > self.template[col_name].isna()).all():
            print("Nans in template that are not in the template")
            sys.exit(5)
        elif (self.template['PolityID'].apply(lambda x: self.check_nan_polities(x, df, var_name)) < self.template[col_name].isna()).all():
            print("Extra entries in the template")
            sys.exit(6)

        return "Passed tests"
    
    # ---------------------- SAMPLING FUNCTIONS ---------------------- #

    def sample_dict(self, variable_dict, t, error, interpolation = 'zero', sampling = 'uniform'):
        """
        Samples values from a given dictionary of timelines based on the provided time(s) and error margin.
        Parameters:
        variable_dict (dict): A dictionary containing 't', 'value', and 'polity_years' keys.
                              't' is a list of time points, 'value' is a list of value ranges corresponding to the time points,
                              and 'polity_years' is a list of years defining the polity period.
        t (int, float, list, np.ndarray): The time or list of times at which to sample the values.
        error (int, float): The error margin to extend the polity years.
        Returns:
        list or float: The sampled value(s) at the given time(s). If the time is out of bounds, returns "Out of bounds".
                       If the input time is not a number, returns "Error: The year is not a number".
                       If the input dictionary is None or invalid, returns None.
        """

        if variable_dict is None or pd.isna(variable_dict):
            return None
        if len(variable_dict['t'][0]) == 0:
            return None
        if len(variable_dict['value'][0]) == 0:
            return None
        if len(variable_dict['polity_years']) == 0:
            return None
        
        n_timelines = len(variable_dict['value'])
        s = random.randint(0, n_timelines-1)
        times = variable_dict['t'][s]
        values = variable_dict['value'][s]
        polity_years = variable_dict['polity_years']
        error = abs(error)
        polity_years = [min(polity_years) - error, max(polity_years) + error]

        if polity_years[0] not in times:
            times = [polity_years[0]] + times
            values = [values[0]] + values

        if polity_years[1] not in times:
            times = times + [polity_years[1]]
            values = values + [values[-1]]

        times = np.array(times)
        random_number = random.random()
        if interpolation == 'zero':
            pass
        elif (interpolation == 'linear') or (interpolation == 'smooth'):
            # create a smoothing effect on the data with a smoothing window of 50 years
            import scipy.interpolate as spi
            x = np.array(times)
            if sampling == 'uniform':
                y = np.array([v[0] + random_number*(v[1]-v[0]) for v in values])
            elif sampling == 'mean':
                y = np.array([np.mean([v[0],v[1]]) for v in values])
            smooth_window = 50
            if interpolation == 'linear':
                smoothing = np.ones(smooth_window)
                smoothing = smoothing / smoothing.sum()
            elif interpolation == 'smooth':
                smoothing = np.exp(-np.linspace(-3, 3, smooth_window)**2)
                smoothing /= smoothing.sum()
            x_new = np.arange(min(x), max(x), smooth_window // 5)
            y_new = spi.interp1d(x, y)(x_new)
            y_new = np.pad(y_new, smooth_window, mode='edge')
            y_new = np.convolve(y_new, smoothing, mode='same')[smooth_window:-smooth_window]
            
        if isinstance(t, (list, np.ndarray)):
            vals = [None] * len(t)
            for i, time in enumerate(t):
                if time < polity_years[0] or time > polity_years[1]:
                    print(f"Error: The year {time} is outside the polity years {polity_years}")
                    vals[i] = "Out of bounds"
                    continue
                if interpolation == 'zero':
                    time_selection = times[times<=time]
                    ind = np.argmin(np.abs(np.array(time_selection) - time))
                    if isinstance(values[ind][0], str):
                        vals[i] = values[ind][0]
                        continue
                    if sampling == 'uniform':
                        val = values[ind][0] + random_number * (values[ind][1] - values[ind][0])
                    elif sampling == 'mean':
                        val = np.mean(values[ind])
                    vals[i] = val
                elif (interpolation == 'linear') or (interpolation == 'smooth'):
                    if isinstance(values[ind][0], str):
                        print(f"Error: String column must use 'zero' interpolation")
                        vals[i] = np.nan
                        continue
                    vals[i] = y_new[np.argmin(np.abs(x_new - time))]
            return vals
        elif isinstance(t, (int, float, np.int64, np.int32, np.float64, np.float32)):
            if t < polity_years[0] or t > polity_years[1]:
                print(f"Error: The year {t} is outside the polity years {polity_years}")
                return "Out of bounds"
            # find the closest year to t
            if interpolation == 'zero':
                times = times[times<=t]
                ind = np.argmin(np.abs(np.array(times) - t))
                # sample the values
                val = values[ind][0] + random.random() * (values[ind][1] - values[ind][0])
            elif (interpolation == 'linear') or (interpolation == 'smooth'):
                val = y_new[np.argmin(np.abs(x_new - t))]
            return val
        else:
            print("Error: The year is not a number")
            return "Error: The year is not a number"
        
    # ---------------------- DEBUG FUNCTIONS ---------------------- #

    def is_in_range(self, variable_dict, t, value):
        if variable_dict is None and pd.notna(value):
            return False
        elif variable_dict is None and pd.isna(value):
            return True
        
        if len(variable_dict['t'][0]) == 0:
            return np.nan
        if len(variable_dict['value'][0]) == 0:
            return np.nan
        if len(variable_dict['polity_years']) == 0:
            return np.nan

        times = variable_dict['t'][0]
        values = self.reduce_to_largest_ranges(variable_dict['value'])
        polity_years = variable_dict['polity_years']

        if polity_years[0] not in times:
            times = [polity_years[0]] + times
            values = [values[0]] + values

        if polity_years[1] not in times:
            times = times + [polity_years[1]]
            values = values + [values[-1]]

        if t < polity_years[0] or t > polity_years[1]:
            print(f"Error: The year {t} is outside the polity years {polity_years}")
            return "Out of bounds"
        # find the closest year to t
        times = np.array(times)[times<=t]
        ind = np.argmin(np.abs(times - t))
        # sample the values
        val = values[ind]
        if min(val) <= value <= max(val):
            return True
        else:
            return False

    def reduce_to_largest_ranges(self, values):
        # Initialize a list to store the (min, max) tuples
        result = []
        
        # Get the length of the inner lists (assuming all inner lists have the same length)
        num_points = len(values[0])
        
        # Iterate through the indices of the inner lists
        for i in range(num_points):
            # Initialize min and max values for the current index
            min_value = float('inf')
            max_value = float('-inf')
            
            # Iterate through the outer list
            for inner_list in values:
                # Get the tuple at the current index
                x1, x2 = inner_list[i]
                
                # Update min and max values
                min_value = min(min_value, x1)
                max_value = max(max_value, x2)
            
            # Append the (min, max) tuple to the result list
            result.append((min_value, max_value))
        
        # Return the result list
        return result

    # ---------------------- SAVING FUNCTIONS ---------------------- #
    def save_dataset(self, file_path):
        self.template.to_csv(file_path, index = False)
        print(f"Saved template to {file_path}")
    # ---------------------- LOADING FUNCTIONS ---------------------- #
    def load_dataset(self, file_path):
        self.template = pd.read_csv(file_path)
        print(f"Loaded template from {file_path}")


# ---------------------- TESTING ---------------------- #
if __name__ == "__main__":
    # Test the Template class
    template = Template(categories = ['sc','wf','rt','ec','rel'], save_excel=False)
    template.download_all_categories()
    template.save_dataset("template.csv")
    

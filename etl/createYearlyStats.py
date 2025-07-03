# prompt: Iterate over all sub directories x of directory json, and the sub directories of x called y and the sub directories of y called year. Within the directories year create a new json file, called "all.json" which contains the data of the json files found in the respective directory year.

import os
import json
import pandas as pd
base_dir = "json"

# Create all JSON Files
measures = ["hurs", "tas", "tasmin", "tasmax", "pr"]

if os.path.isdir(base_dir):
    for x in os.listdir(base_dir):
        x_dir = os.path.join(base_dir, x)
        if os.path.isdir(x_dir):  # Add this check
            for y in os.listdir(x_dir):
                y_dir = os.path.join(x_dir, y)
                if os.path.isdir(y_dir):
                    for year in os.listdir(y_dir):
                        year_dir = os.path.join(y_dir, year)
                        if os.path.isdir(year_dir):
                            all_data = {}  # Initialize all_data as a dictionary
                            for filename in os.listdir(year_dir):
                                if filename.endswith("all.json"):
                                    filepath = os.path.join(year_dir, filename)
                                    print(filepath)
                                    with open(filepath, 'r') as f:
                                        try:
                                            data = json.load(f)
                                            df = pd.DataFrame(data)
                                            stats = {}
                                            stats['Heizperiode'] = len(df[df['tas'] < 15])
                                            stats['Eistage'] = len(df[df['tasmax'] < 0])
                                            stats['Frosttage'] = len(df[df['tasmin'] < 0])
                                            stats['Hitzetage'] = len(df[df['tasmax'] >= 30])
                                            stats['Niederschlagtage'] = len(df[df['pr'] >= 0.1])
                                            stats['Tropennacht'] = len(df[df['tasmin'] >= 20])
                                            stats['Vegetationsperiode'] = len(df[df['tas'] > 5])
                                            num_rows = len(df)
                                            halfway_index = num_rows // 2

                                            #  Filter the first half of the DataFrame and find rows where 'tasmin' is less than 0
                                            frost_in_first_half = df.iloc[:halfway_index][
                                                df.iloc[:halfway_index]['tasmin'] < 0]
                                            frost_in_second_half = df.iloc[halfway_index:][
                                                df.iloc[halfway_index:]['tasmin'] < 0]
                                            # Get the index of the last row in the filtered DataFrame
                                            if not frost_in_first_half.empty:
                                                last_frost_index = frost_in_first_half.index[-1]
                                            else:
                                                last_frost_index = 0
                                            # Get the index of the last row in the filtered DataFrame
                                            if not frost_in_first_half.empty:
                                                first_frost_index = frost_in_second_half.index[0]
                                            else:
                                                first_frost_index = 365
                                            stats['LetzterFrostFrühjahr'] = int(last_frost_index)
                                            stats['ErsterFrostHerbst'] = int(first_frost_index)
                                            stats['FrostFreiePeriode'] = int(first_frost_index - last_frost_index)
                                        except json.JSONDecodeError:
                                            print(f"Error decoding JSON in file: {filepath}")
                                        except Exception as e:  # Catch other potential errors
                                            print(f"An error occurred while processing file {filepath}: {e}")
                            output_filepath = os.path.join(year_dir, "stats.json")
                            with open(output_filepath, 'w') as outfile:
                                json.dump(stats, outfile, indent=2)  # Dump the dictionary
                                print(f"Created {output_filepath}")
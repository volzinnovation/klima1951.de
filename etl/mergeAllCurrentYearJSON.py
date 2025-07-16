# prompt: Iterate over all sub directories x of directory json, and the sub directories of x called y and the sub directories of y called year. Within the directories year create a new json file, called "all.json" which contains the data of the json files found in the respective directory year.

import os
import json

base_dir = "json"

# Create all JSON Files
measures = ["hurs","tas", "tasmin", "tasmax","pr"]

import datetime
year = str(datetime.datetime.now().year)

if os.path.isdir(base_dir):
  for x in os.listdir(base_dir):
    x_dir = os.path.join(base_dir, x)
    if os.path.isdir(x_dir): # Add this check
      for y in os.listdir(x_dir):
        y_dir = os.path.join(x_dir, y)
        if os.path.isdir(y_dir):
          #for year in os.listdir(y_dir):
          year_dir = os.path.join(y_dir, year)
          if os.path.isdir(year_dir):
              all_data = {} # Initialize all_data as a dictionary
              for filename in os.listdir(year_dir):
                if filename.endswith(".json"):
                  filepath = os.path.join(year_dir, filename)
                  print(filepath)
                  with open(filepath, 'r') as f:
                    try:
                      data = json.load(f)
                      if not all_data:  # If all_data is empty, append all data
                        all_data = data
                      else: # Otherwise, append only keys not called "time"
                        for key, value in data.items():
                            if key != "time":
                                all_data[key] = value
                    except json.JSONDecodeError:
                      print(f"Error decoding JSON in file: {filepath}")
                    except Exception as e: # Catch other potential errors
                      print(f"An error occurred while processing file {filepath}: {e}")


              output_filepath = os.path.join(year_dir, "all.json")
              with open(output_filepath, 'w') as outfile:
                json.dump(all_data, outfile, indent=2) # Dump the dictionary
                print(f"Created {output_filepath}")
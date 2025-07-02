# prompt: Iterate over all sub directories x of directory json, and the sub directories of x called y and the sub directories of y called year. Within the directories year create a new json file, called "all.json" which contains the data of the json files found in the respective directory year.

import os
import json
import pandas as pd

base_dir = "json"

if os.path.isdir(base_dir):
  for x in os.listdir(base_dir):
    x_dir = os.path.join(base_dir, x)
    if os.path.isdir(x_dir): # Add this check
      for y in os.listdir(x_dir):
        y_dir = os.path.join(x_dir, y)
        if os.path.isdir(y_dir):
          # Filter for items that are directories and look like years, then sort numerically
          year_dirs = sorted([item for item in os.listdir(y_dir) if os.path.isdir(os.path.join(y_dir, item)) and item.isdigit()], key=lambda item: int(item))
          # Create an empty DataFrame to store the results
          df_stats = pd.DataFrame(columns=[
              'Jahr',
              "Heizperiode",
              "Eistage",
              "Frosttage",
              "Hitzetage",
              "Tropennacht",
              "Vegetationsperiode",
              "LetzterFrostFruehjahr",
              "ErsterFrostHerbst",
              "FrostFreiePeriode"])
          for year in year_dirs:
            year_dir = os.path.join(y_dir, year)
            if os.path.isdir(year_dir):
              for filename in os.listdir(year_dir):
                if filename.endswith("stats.json"):
                  filepath = os.path.join(year_dir, filename)
                  with open(filepath, 'r') as f:
                    try:
                      data = json.load(f)
                      # Append the data to the DataFrame
                      new_row = {
                          'Jahr': int(year),  # Use the directory name as the year
                          "Heizperiode": data.get("Heizperiode"),
                          "Eistage": data.get("Eistage"),
                          "Frosttage": data.get("Frosttage"),
                          "Hitzetage": data.get("Hitzetage"),
                          "Tropennacht": data.get("Tropennacht"),
                          "Vegetationsperiode": data.get("Vegetationsperiode"),
                          "LetzterFrostFruehjahr": data.get("LetzterFrostFrühjahr"), # Note the key difference
                          "ErsterFrostHerbst": data.get("ErsterFrostHerbst"),
                          "FrostFreiePeriode": data.get("FrostFreiePeriode")
                      }
                      # Use pd.concat for appending a new row
                      df_stats = pd.concat([df_stats, pd.DataFrame([new_row])], ignore_index=True)
                    except json.JSONDecodeError:
                      print(f"Error decoding JSON in file: {filepath}")
                    except Exception as e: # Catch other potential errors
                      print(f"An error occurred while processing file {filepath}: {e}")


          output_filepath = os.path.join(y_dir, "stats.csv")
          df_stats.to_csv(output_filepath, index=False)
          print(f"Created {output_filepath}")
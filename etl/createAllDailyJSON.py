# -*- coding: utf-8 -*-
"""Text write many little json files out of one nc file
for each raster one json file with the time series is created


"""
import math
import xarray as xr
import os
from itertools import product
from tqdm import tqdm
import pandas as pd
import json
import re
# Config
output_base = 'json'
var_name="tas"
precision=100
# Load cities.json
# Read the JSON file into a dictionary
with open("../misc/cities.json", "r") as f:
    cities_dict = json.load(f)

# Convert the list of city dictionaries to a DataFrame
# Assuming the structure is {'cities': [{}, {}, ...]}
if 'cities' in cities_dict and isinstance(cities_dict['cities'], list):
    df = pd.DataFrame(cities_dict['cities'])
else:
    # Handle cases where the JSON structure might be different
    # For example, if the top level keys are city names and values are city details
    # In that case, orient='index' might be appropriate
    try:
        df = pd.DataFrame.from_dict(cities_dict, orient="index")
    except ValueError:
         print("Could not automatically determine the correct orientation for the DataFrame.")
         print("Please check the structure of your 'cities.json' file and adjust the code accordingly.")
         df = pd.DataFrame() # Create an empty DataFrame or handle the error as appropriate

# Create all JSON Files
measures = ["hurs","tas", "tasmin", "tasmax","pr"]
for var_name in measures :
# Iterate per metric
  print(var_name)
  for year in range(1951, 2025): #1968?
    # Iterate per year
    print(year)
    input_file = f'hyras/{var_name}_hyras_1_{year}_v6-0_de.nc'
    print(input_file)

    ds = xr.open_dataset(input_file)
    # 3. Holen Sie sich die Koordinatenwerte für die Iteration.
    y_coords = ds.y.values
    x_coords = ds.x.values
    total_files = len(y_coords) * len(x_coords)
    first_timestep = ds[var_name].isel(time=0)
    valid_points = first_timestep.stack(spatial=('y', 'x')).dropna(dim='spatial')
    valid_coords = valid_points.spatial.values
    total_files = len(valid_coords)
    for index, row in df.iterrows():
      city_name = row['city']
      target_lon = row['longitude']/precision
      target_lat = row['latitude']/precision
      # print(city_name)
      # Find nearest grid point
      # Calculate the squared difference between the grid coordinates and the target coordinates
      # This avoids the need for square roots and is sufficient for finding the minimum distance
      lat_diff = (ds['lat'] - target_lat)**2
      lon_diff = (ds['lon'] - target_lon)**2

      # Calculate the total squared distance
      total_diff = lat_diff + lon_diff

      # Find the index of the minimum total difference
      min_index = total_diff.argmin(...)

      # Select the data at the minimum index
      ds1 = ds.isel(y=min_index['y'], x=min_index['x'])
      # Find the closest data point in ds using sel with method='nearest'
      #ds1 = ds.sel(lat=target_lat/100.0, lon=target_lon/100.0, method='nearest')
      # ds1 = ds.sel(x=x_val, y=y_val)
      d = {}
      d["time"] = ds1['time'].values.tolist()
      d[var_name] = ds1[var_name].values.tolist()
      # print(math.isnan(d[var_name][0]))
      if(not math.isnan(d[var_name][0])) :
        #print(type(time))
        #print(type(values))
        lat_int = int(ds1['lat'].values*precision)
        lon_int = int(ds1['lon'].values*precision)
        output_dir = f'{output_base}/{lon_int}/{lat_int}/{year}'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f'{var_name}.json')
        print(output_path)
        if not os.path.exists(output_path):
          with open(output_path, "w") as f:
            json.dump(d, f, indent=2)
        else:
          print(f"\nOutput file {output_path} already exists")
        print(f"Saved timeseries data for {city_name} to {output_path}")
        #break
      else:
        print(f"No data found for {city_name}")
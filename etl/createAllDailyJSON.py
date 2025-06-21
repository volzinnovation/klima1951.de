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
# Create all JSON Files
measures = ["tas", "tasmin", "tasmax","pr","hurs"]
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
    for y_val, x_val in tqdm(valid_coords, total=total_files):
      ds1 = ds.sel(x=x_val, y=y_val)
      d = {}
      d["time"] = ds1['time'].values.tolist()
      d[var_name] = ds1[var_name].values.tolist()
      #print(math.isnan(d[var_name][0]))
      if(not math.isnan(d[var_name][0])) :
        #print(type(time))
        #print(type(values))
        lat_int = int(ds1['lat'].values*precision)
        lon_int = int(ds1['lon'].values*precision)
        output_dir = f'{output_base}/{lon_int}/{lat_int}/{year}'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f'{var_name}.json')
        if not os.path.exists(output_path):
          with open(output_path, "w") as f:
            json.dump(d, f, indent=2)
        #else:
        #  print(f"\nOutput file {output_path} already exists")
        #print(f"Saved timeseries data for x={int(x_val)}, y={int(y_val)} to {output_path}")
        #break
      #else:
        # print(f"No data found for x={int(x_val)}, y={int(y_val)}")
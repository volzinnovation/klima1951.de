# -*- coding: utf-8 -*-
"""Processes .nc files and creates a JSON time series for each city.

This script reads HYRAS climate data in NetCDF format, and for a list of
cities, it finds the nearest data point and extracts the time series for
various climate measures. The output is a set of JSON files organized by
location and year.

Refactored by Cascade on 2025-07-17.
"""
import argparse
import datetime
import json
import math
import os
import pandas as pd
import xarray as xr

PRECISION = 100
MEASURES = ["hurs", "tas", "tasmin", "tasmax", "pr"]
OUTPUT_BASE = 'json'

def process_file(var_name, year, cities_df, overwrite=False):
    """Processes a single NetCDF file for a given measure and year."""
    input_file = f'hyras/{var_name}_hyras_1_{year}_v6-0_de.nc'
    print(f"Processing {input_file}...")

    if not os.path.exists(input_file):
        print(f"File not found: {input_file}. Skipping.")
        return

    try:
        ds = xr.open_dataset(input_file)
    except Exception as e:
        print(f"Could not open {input_file}: {e}. Skipping.")
        return

    for _, row in cities_df.iterrows():
        city_name = row['city']
        target_lon = row['longitude'] / PRECISION
        target_lat = row['latitude'] / PRECISION

        # Find nearest grid point by calculating squared distance
        lat_diff = (ds['lat'] - target_lat)**2
        lon_diff = (ds['lon'] - target_lon)**2
        total_diff = lat_diff + lon_diff
        min_index = total_diff.argmin(...)

        # Select data at the nearest point
        ds1 = ds.isel(y=min_index['y'], x=min_index['x'])

        # Skip if data is all NaN
        if math.isnan(ds1[var_name].values[0]):
            print(f"No data found for {city_name} in {year} for {var_name}.")
            continue

        # Prepare data for JSON output
        data = {
            "time": ds1['time'].values.tolist(),
            var_name: ds1[var_name].values.tolist()
        }

        output_dir = f'{OUTPUT_BASE}/{row['longitude']}/{row['latitude']}/{year}'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f'{var_name}.json')

        if not os.path.exists(output_path) or overwrite:
            try:
                with open(output_path, "w") as f:
                    json.dump(data, f, indent=2)
                # print(f"Saved data for {city_name} to {output_path}")
            except IOError as e:
                print(f"Error writing to {output_path}: {e}")
        # else:
            # print(f"File {output_path} already exists. Skipping.")

def main():
    parser = argparse.ArgumentParser(description='Create daily JSON files from HYRAS NetCDF data.')
    parser.add_argument(
        '--years', 
        type=str, 
        default='current', 
        help="Specify years to process. 'all' for 1951-2024, 'current' for the current year, or a specific year (e.g., '2023')."
    )
    parser.add_argument(
        '--overwrite', 
        action='store_true', 
        help='Overwrite existing JSON files.'
    )
    args = parser.parse_args()

    # Load cities data
    try:
        with open("../misc/cities.json", "r") as f:
            cities_dict = json.load(f)
        cities_df = pd.DataFrame(cities_dict['cities'])
    except (FileNotFoundError, KeyError, TypeError) as e:
        print(f"Error loading or parsing '../misc/cities.json': {e}")
        return

    # Determine which years to process
    if args.years == 'all':
        years_to_process = range(1951, 2025)
    elif args.years == 'current':
        years_to_process = [datetime.datetime.now().year]
    else:
        try:
            years_to_process = [int(args.years)]
        except ValueError:
            print("Invalid year format. Please provide a single year, 'all', or 'current'.")
            return

    print(f"Processing years: {list(years_to_process)}")
    for year in years_to_process:
        print(f"--- Processing year {year} ---")
        for measure in MEASURES:
            process_file(measure, year, cities_df, args.overwrite)

if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""Merges all yearly 'all.json' files into a single 'all-years.json' for each location.

This script iterates through the directory structure (json/{lon}/{lat}) and combines
the 'all.json' files from each year's subdirectory into a single, comprehensive
file for that location, containing the complete time series.

Refactored by Cascade on 2025-07-17.
"""
import argparse
import json
import os

BASE_DIR = "json"
OUTPUT_FILENAME = "all-years.json"

def merge_data_for_place(place_dir, overwrite=False):
    """Merges all yearly data for a single location."""
    output_filepath = os.path.join(place_dir, OUTPUT_FILENAME)
    if os.path.exists(output_filepath) and not overwrite:
        # print(f"Skipping {place_dir}, {OUTPUT_FILENAME} already exists.")
        return

    # Get and sort year directories numerically
    try:
        year_dirs = [d for d in os.listdir(place_dir) if os.path.isdir(os.path.join(place_dir, d)) and d.isdigit()]
        year_dirs.sort(key=int)
    except FileNotFoundError:
        print(f"Directory not found: {place_dir}")
        return

    if not year_dirs:
        return

    all_combined_data = {}

    for year in year_dirs:
        year_dir_path = os.path.join(place_dir, year)
        all_json_filepath = os.path.join(year_dir_path, "all.json")

        if os.path.exists(all_json_filepath):
            # print(f"Processing: {all_json_filepath}")
            try:
                with open(all_json_filepath, 'r') as f:
                    data = json.load(f)
                
                for key, value in data.items():
                    if key not in all_combined_data:
                        all_combined_data[key] = []
                    all_combined_data[key].extend(value)
            except json.JSONDecodeError:
                print(f"Error decoding JSON in file: {all_json_filepath}")
            except Exception as e:
                print(f"An error occurred while processing {all_json_filepath}: {e}")

    if all_combined_data:
        try:
            with open(output_filepath, 'w') as outfile:
                json.dump(all_combined_data, outfile, indent=2)
            print(f"Created combined file: {output_filepath}")
        except IOError as e:
            print(f"Error writing to {output_filepath}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Merge all yearly 'all.json' files into a single 'all-years.json' for each location.")
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing all-years.json files.'
    )
    args = parser.parse_args()

    if not os.path.isdir(BASE_DIR):
        print(f"Base directory '{BASE_DIR}' not found.")
        return

    print(f"Starting merge process...")

    for lon_dir in os.listdir(BASE_DIR):
        lon_path = os.path.join(BASE_DIR, lon_dir)
        if not os.path.isdir(lon_path):
            continue
        
        for lat_dir in os.listdir(lon_path):
            lat_path = os.path.join(lon_path, lat_dir)
            if not os.path.isdir(lat_path):
                continue
            
            merge_data_for_place(lat_path, args.overwrite)

if __name__ == '__main__':
    main()

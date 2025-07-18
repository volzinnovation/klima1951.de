# -*- coding: utf-8 -*-
"""Merges individual measure JSON files into a single all.json for each year and location.

This script iterates through the directory structure created by create_daily_json.py
(json/{lon}/{lat}/{year}) and combines the individual JSON files (e.g., tas.json,
pr.json) into a single 'all.json' file for the specified year(s).

Refactored by Cascade on 2025-07-17.
"""
import argparse
import datetime
import json
import os

BASE_DIR = "json"

def merge_json_in_dir(directory):
    """
    Merges all individual measure .json files in a directory into a single all.json.
    """
    all_data = {}
    json_files = [f for f in os.listdir(directory) if f.endswith('.json') and f != 'all.json']

    if not json_files:
        return

    for filename in sorted(json_files):
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            if not all_data:  # First file
                all_data = data
            else:
                for key, value in data.items():
                    if key != "time":
                        all_data[key] = value
        except json.JSONDecodeError:
            print(f"Error decoding JSON in file: {filepath}")
        except Exception as e:
            print(f"An error occurred while processing file {filepath}: {e}")

    if all_data:
        output_filepath = os.path.join(directory, "all.json")
        try:
            with open(output_filepath, 'w') as outfile:
                json.dump(all_data, outfile, indent=2)
            print(f"Created {output_filepath}")
        except IOError as e:
            print(f"Error writing to {output_filepath}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Merge individual measure JSON files into a single all.json for each year and location.')
    parser.add_argument(
        '--years',
        type=str,
        default='current',
        help="Specify years to process. 'all' to process all year directories found, 'current' for the current year, or a specific year (e.g., '2023')."
    )
    args = parser.parse_args()

    if not os.path.isdir(BASE_DIR):
        print(f"Base directory '{BASE_DIR}' not found.")
        return

    print(f"Starting merge process for years: {args.years}")

    for lon_dir in os.listdir(BASE_DIR):
        lon_path = os.path.join(BASE_DIR, lon_dir)
        if not os.path.isdir(lon_path):
            continue
        
        for lat_dir in os.listdir(lon_path):
            lat_path = os.path.join(lon_path, lat_dir)
            if not os.path.isdir(lat_path):
                continue

            years_in_dir = [d for d in os.listdir(lat_path) if os.path.isdir(os.path.join(lat_path, d))]
            
            years_to_process = []
            if args.years == 'all':
                years_to_process = years_in_dir
            elif args.years == 'current':
                current_year_str = str(datetime.datetime.now().year)
                if current_year_str in years_in_dir:
                    years_to_process = [current_year_str]
            else:
                if args.years in years_in_dir:
                    years_to_process = [args.years]

            if not years_to_process:
                continue

            for year in years_to_process:
                year_dir_path = os.path.join(lat_path, year)
                # print(f"Processing {year_dir_path}...")
                merge_json_in_dir(year_dir_path)

if __name__ == '__main__':
    main()

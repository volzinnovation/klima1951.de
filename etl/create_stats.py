# -*- coding: utf-8 -*-
"""Calculates and compiles yearly climate statistics for each location.

This script reads the 'all.json' file for each specified year within a location's
directory, calculates various climate statistics (e.g., frost days, heat days),
and compiles them into a single 'stats.csv' file for that location.

Refactored by Cascade on 2025-07-17.
"""
import argparse
import datetime
import json
import os
import pandas as pd

BASE_DIR = "json"

def calculate_stats_from_df(df):
    """Calculates a dictionary of statistics from a DataFrame of climate data."""
    stats = {}
    stats['Heizperiode'] = len(df[df['tas'] < 15])
    stats['Eistage'] = len(df[df['tasmax'] < 0])
    stats['Frosttage'] = len(df[df['tasmin'] < 0])
    stats['Hitzetage'] = len(df[df['tasmax'] >= 30])
    stats['Niederschlagtage'] = len(df[df['pr'] >= 0.1])
    stats['Tropennacht'] = len(df[df['tasmin'] >= 20])
    stats['Vegetationsperiode'] = len(df[df['tas'] > 5])

    # Note: Splitting the year in half to find last/first frost is a simplification.
    halfway_index = len(df) // 2
    frost_in_first_half = df.iloc[:halfway_index][df.iloc[:halfway_index]['tasmin'] < 0]
    frost_in_second_half = df.iloc[halfway_index:][df.iloc[halfway_index:]['tasmin'] < 0]

    last_frost_index = frost_in_first_half.index[-1] if not frost_in_first_half.empty else 0
    first_frost_index = frost_in_second_half.index[0] if not frost_in_second_half.empty else len(df)

    stats['LetzterFrostFruehjahr'] = int(last_frost_index)
    stats['ErsterFrostHerbst'] = int(first_frost_index)
    stats['FrostFreiePeriode'] = int(first_frost_index - last_frost_index)
    
    return stats

def process_location(place_dir, years_to_process, overwrite=False):
    """Processes all specified years for a single location and creates a stats.csv."""
    output_filepath = os.path.join(place_dir, "stats.csv")
    if os.path.exists(output_filepath) and not overwrite:
        # print(f"Skipping {place_dir}, stats.csv already exists.")
        return

    stats_columns = [
        'Jahr', 'Heizperiode', 'Eistage', 'Frosttage', 'Hitzetage',
        'Tropennacht', 'Niederschlagtage', 'Vegetationsperiode',
        'LetzterFrostFruehjahr', 'ErsterFrostHerbst', 'FrostFreiePeriode'
    ]
    all_stats_df = pd.DataFrame(columns=stats_columns)
    
    for year in sorted(years_to_process, key=int):
        all_json_path = os.path.join(place_dir, str(year), "all.json")
        if not os.path.exists(all_json_path):
            continue

        try:
            with open(all_json_path, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            yearly_stats = calculate_stats_from_df(df)
            yearly_stats['Jahr'] = int(year)
            
            new_row = pd.DataFrame([yearly_stats])
            all_stats_df = pd.concat([all_stats_df, new_row], ignore_index=True)

        except (json.JSONDecodeError, pd.errors.EmptyDataError) as e:
            print(f"Error processing {all_json_path}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred with {all_json_path}: {e}")

    if not all_stats_df.empty:
        try:
            all_stats_df.to_csv(output_filepath, index=False)
            print(f"Created {output_filepath}")
        except IOError as e:
            print(f"Error writing to {output_filepath}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Calculate and compile yearly climate statistics.')
    parser.add_argument(
        '--years',
        type=str,
        default='full',
        help="'all' for all available years, 'full' for all full years'current' for the current year, or a specific year (e.g., '2023')."
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing stats.csv files.'
    )
    args = parser.parse_args()

    if not os.path.isdir(BASE_DIR):
        print(f"Base directory '{BASE_DIR}' not found.")
        return

    print(f"Starting statistics calculation for years: {args.years}")

    for lon_dir in os.listdir(BASE_DIR):
        lon_path = os.path.join(BASE_DIR, lon_dir)
        if not os.path.isdir(lon_path): continue

        for lat_dir in os.listdir(lon_path):
            lat_path = os.path.join(lon_path, lat_dir)
            if not os.path.isdir(lat_path): continue

            available_years = sorted([d for d in os.listdir(lat_path) if os.path.isdir(os.path.join(lat_path, d)) and d.isdigit()])
            
            years_to_process = []
            if args.years == 'all':
                years_to_process = available_years
            elif args.years == 'full':
                years_to_process = available_years[:-1]
                #print(f"Processing full years: {years_to_process}")
            elif args.years == 'current':
                current_year_str = str(datetime.datetime.now().year)
                if current_year_str in available_years:
                    years_to_process = [current_year_str]
            else:
                if args.years in available_years:
                    years_to_process = [args.years]

            if years_to_process:
                process_location(lat_path, years_to_process, args.overwrite)

if __name__ == '__main__':
    main()

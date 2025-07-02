import os
import json

base_dir = "json"

if os.path.isdir(base_dir):
    for x in os.listdir(base_dir):
        x_dir = os.path.join(base_dir, x)
        if os.path.isdir(x_dir):
            for y in os.listdir(x_dir):
                y_dir = os.path.join(x_dir, y)
                if os.path.isdir(y_dir):
                    # Get and sort year directories numerically
                    year_dirs = [d for d in os.listdir(y_dir) if os.path.isdir(os.path.join(y_dir, d)) and d.isdigit()]
                    year_dirs.sort(key=int)

                    output_filepath = os.path.join(y_dir, "all1951-2024.json")
                    all_combined_data = {}

                    for year in year_dirs:
                        year_dir = os.path.join(y_dir, year)
                        all_json_filepath = os.path.join(year_dir, "all.json")

                        if os.path.exists(all_json_filepath):
                            print(f"Processing: {all_json_filepath}")
                            with open(all_json_filepath, 'r') as f:
                                try:
                                    data = json.load(f)
                                    for key, value in data.items():
                                        if key not in all_combined_data:
                                            all_combined_data[key] = []
                                        all_combined_data[key].extend(value)
                                except json.JSONDecodeError:
                                    print(f"Error decoding JSON in file: {all_json_filepath}")
                                except Exception as e:
                                    print(f"An error occurred while processing file {all_json_filepath}: {e}")

                    # Write the combined data to a new all.json file
                    if all_combined_data:
                       with open(output_filepath, 'w') as outfile:
                          json.dump(all_combined_data, outfile, indent=2)
                       print(f"Created combined {output_filepath}")
                    else:
                       print("No data found to combine.")
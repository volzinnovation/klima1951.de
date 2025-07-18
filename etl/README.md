**ETL Pipeline for HYRAS Climate Data**

This directory contains a series of Python scripts that form an ETL (Extract, Transform, Load) pipeline to download, process, and analyze HYRAS climate data from the German Weather Service (DWD).

## The Refactored Pipeline

The scripts have been refactored to be modular, efficient, and configurable through command-line arguments. The pipeline is designed to be run in sequence.

### Prerequisites

-   Python 3.x
-   A `cities.json` file in the `../misc/` directory with the locations to process.
-   Required Python packages: `requests`, `xarray`, `pandas`, `beautifulsoup4`, `netcdf4`

    You can install these using pip:
    ```bash
    pip install requests xarray pandas beautifulsoup4 netcdf4
    ```

### Execution Order

The scripts are intended to be run in the following order. Each script builds upon the output of the previous one.

#### Step 1: Download Climate Data

Use `download_data.py` to fetch the raw `.nc` (NetCDF) files from the DWD server. The data will be saved in a `hyras/` directory.

-   **To download data for a specific year (e.g., 2023):**
    ```bash
    python download_data.py --year 2023
    ```
-   **To download data only for the current year:**
    ```bash
    python download_data.py --year current
    ```
-   **To download all available years (default behavior):**
    ```bash
    python download_data.py --year all
    ```

#### Step 2: Create Daily JSON Files

Use `create_daily_json.py` to process the `.nc` files. For each city and year, it extracts the time series data and saves it as a small JSON file.

-   **To process a specific year:**
    ```bash
    python create_daily_json.py --years 2023
    ```
-   **To process the current year (default):**
    ```bash
    python create_daily_json.py --years current
    ```
-   **To process all years:**
    ```bash
    python create_daily_json.py --years all
    ```
-   **To overwrite existing files (optional):**
    ```bash
    python create_daily_json.py --years all --overwrite
    ```

#### Step 3: Merge Yearly JSON Files

Use `merge_yearly_json.py` to combine the individual JSON files (e.g., `tas.json`, `pr.json`) for each location into a single `all.json` file for that year.

-   **To merge a specific year:**
    ```bash
    python merge_yearly_json.py --years 2023
    ```
-   **To merge the current year (default):**
    ```bash
    python merge_yearly_json.py --years current
    ```
-   **To merge all available years:**
    ```bash
    python merge_yearly_json.py --years all
    ```

#### Step 4: Aggregate All Data for Each Place

Use `merge_place_data.py` to combine all the yearly `all.json` files into a single, comprehensive `all-years.json` file for each location.

-   **To run a full rebuild of the aggregated files:**
    ```bash
    python merge_place_data.py
    ```
-   **To overwrite existing `all-years.json` files (optional):**
    ```bash
    python merge_place_data.py --overwrite
    ```

#### Step 5: Create Statistics

Finally, use `create_stats.py` to calculate yearly statistics from the `all.json` files and compile them into a `stats.csv` for each location.

-   **To calculate for a specific year:**
    ```bash
    python create_stats.py --years 2023
    ```
-   **To calculate for all years:**
    ```bash
    python create_stats.py --years all
    ```
-   **To calculate for all past years (default):**
    ```bash
    python create_stats.py --years full
    ```
-   **To overwrite existing `stats.csv` files (optional):**
    ```bash
    python create_stats.py --years all --overwrite
    ```
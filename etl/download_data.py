#
# Downloads HYRAS v6.1 nc files from the opendata.dwd.de site
# Vibe Coded by Raphael Volz on 2025-06-16 with help of Gemini on Colab
# Refactored by Cascade on 2025-07-17
#
import requests
import argparse
import datetime
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_PATTERN = "v6-1_de.nc"
REQUEST_TIMEOUT = (10, 120)


def build_session():
  retry = Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
  )
  session = requests.Session()
  session.mount("https://", HTTPAdapter(max_retries=retry))
  session.mount("http://", HTTPAdapter(max_retries=retry))
  return session

# path ="../../data/hyras/"

def download(session, url, year_filter):
  """
  Downloads files from a given URL based on a year filter.

  Args:
    url (str): The URL of the directory to download from.
    year_filter (str): 'all', 'current', or a specific year.
  """
  # Determine the file pattern based on the year filter
  if year_filter == 'current':
    year = str(datetime.datetime.now().year)
    file_pattern = f"{year}_{BASE_PATTERN}"
  elif year_filter.isdigit():
    file_pattern = f"{year_filter}_{BASE_PATTERN}"
  else: # 'all'
    file_pattern = BASE_PATTERN

  print(f"Searching for files ending with '{file_pattern}' in {url}")

  # Fetch the content of the directory listing page
  response = session.get(url, timeout=REQUEST_TIMEOUT)
  response.raise_for_status() # Raise an exception for bad status codes

  # Parse the HTML content
  soup = BeautifulSoup(response.text, 'html.parser')

  # Find all links on the page and filter for the desired files
  links = soup.find_all('a')
  nc_files = [link.get('href') for link in links if link.get('href') and link.get('href').endswith(file_pattern)]

  if not nc_files:
    print(f"No files found matching the pattern '{file_pattern}'.")
    return

  # Download each .nc file
  for filename in nc_files:
    file_url = url + filename
    print(f"Downloading {filename}...")
    try:
      file_response = session.get(file_url, stream=True, timeout=REQUEST_TIMEOUT)
      file_response.raise_for_status()

      with open(filename, 'wb') as f:
        for chunk in file_response.iter_content(chunk_size=8192):
          f.write(chunk)
      print(f"Downloaded {filename}")
    except requests.exceptions.RequestException as e:
      print(f"Failed to download {filename}: {e}")

def main():
  parser = argparse.ArgumentParser(description='Download HYRAS climate data from DWD OpenData server.')
  parser.add_argument('--year', type=str, default='all', 
                      help="'all' to download all years, 'current' for the current year, or a specific year (e.g., '2023').")
  args = parser.parse_args()

  urls = [
          "https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/hyras_de/air_temperature_min/",
          "https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/hyras_de/air_temperature_mean/",
          "https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/hyras_de/air_temperature_max/",
          "https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/hyras_de/precipitation/",
          "https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/hyras_de/humidity/",
  ]

  session = build_session()
  for url in urls:
    download(session, url, args.year)

if __name__ == '__main__':
  main()

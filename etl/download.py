#
# Downloads all v6.0 nc files from the opendata.dwd.de site
# Vibe Coded by Raphael Volz on 2025-06-16 with help of Gemini on Colab
#
pattern = "v6-0_de.nc"
# path ="../../data/hyras/"
import requests
import re
from bs4 import BeautifulSoup

def download(url):
  # Fetch the content of the directory listing page
  response = requests.get(url)
  response.raise_for_status() # Raise an exception for bad status codes
  # Parse the HTML content
  soup = BeautifulSoup(response.text, 'html.parser')
  # Find all links on the page
  links = soup.find_all('a')
  # Filter for links ending with .nc
  nc_files = [link.get('href') for link in links if link.get('href') and link.get('href').endswith(pattern)]
  # Download each .nc file
  for filename in nc_files:
    file_url = url + filename
    print(f"Downloading {filename}...")
    file_response = requests.get(file_url, stream=True)
    file_response.raise_for_status()

    with open(filename, 'wb') as f:
      for chunk in file_response.iter_content(chunk_size=8192):
        f.write(chunk)
    # print(f"Downloaded {filename}")

urls = [
        "https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/hyras_de/air_temperature_min/",
        "https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/hyras_de/air_temperature_mean/"]
#        "https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/hyras_de/air_temperature_max/",
#        "https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/hyras_de/precipitation/",
#        "https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/hyras_de/humidity/",]

for url in urls:
  download(url)
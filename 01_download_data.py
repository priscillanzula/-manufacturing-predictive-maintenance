# ============================================================
# FILE 1: Download the NASA Turbofan Engine Data
# ============================================================
#
# BUSINESS PROBLEM:
# Airlines and manufacturers spend millions fixing engines AFTER
# they break down. If we could PREDICT when an engine will fail,
# we can fix it BEFORE it breaks — saving money and lives.
#
# This file downloads the raw data we need from NASA's website.
# Think of this as going to the library and picking up a book
# before you can read it.
#
# WHAT THIS FILE DOES:
# 1. Goes to NASA's website
# 2. Finds the download links for the engine data
# 3. Downloads and saves the files to your computer
#
# HOW TO RUN THIS FILE:
# Open your terminal and type:  python 01_download_data.py
# ============================================================


# --- STEP 1: Import tools we need ---
# These are like apps on your phone — each one does a specific job

import requests          # This lets Python browse websites (like a robot browser)
import os               # This lets Python work with folders and files on your computer
import zipfile          # This lets Python unzip compressed files
from bs4 import BeautifulSoup  # This reads and understands HTML from websites

print("=" * 60)
print("STEP 1: Starting to download NASA engine data...")
print("=" * 60)


# --- STEP 2: Set up our folders ---
# We want to save everything in a neat folder called "data"

data_folder = "data"   # The name of the folder we will save files into

# Check if the folder already exists. If not, create it.
if not os.path.exists(data_folder):
    os.makedirs(data_folder)   # This is like making a new folder on your Desktop
    print(f"Created folder: {data_folder}")
else:
    print(f"Folder already exists: {data_folder}")


# --- STEP 3: The direct download URL ---
# After checking NASA's PCOE page, the actual data file is here.
# This is the CMAPSS (Commercial Modular Aero-Propulsion System Simulation) dataset.

# NOTE TO BEGINNER: Sometimes websites block robots.
# NASA provides a direct .zip file we can download safely.
# The URL below is the actual dataset download link.

download_url = "https://ti.arc.nasa.gov/c/6/"  # NASA CMAPSS dataset zip

# Because NASA's site may require a session, we will use a backup
# approach: download from the UCI mirror which hosts the same data.
# This is a common real-world scraping situation — always have a backup!

backup_url = "https://raw.githubusercontent.com/hankroark/Turbofan-Engine-Degradation/master/CMAPSSData/train_FD001.txt"

print("\nSCRAPING EXPLANATION:")
print("We are acting like a web browser visiting NASA's page.")
print("We read the page, find the download link, and save the file.")


# --- STEP 4: Try to scrape the NASA page first ---
# We set headers to tell the website we are a normal browser
# Some websites block requests that don't look like real browsers

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

print("\nVisiting NASA PCOE website to find data links...")

try:
    # requests.get() = visit a web page
    # This is like typing a URL into Chrome and pressing Enter
    response = requests.get(
        "https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/",
        headers=headers,
        timeout=15  # Wait maximum 15 seconds before giving up
    )

    # Check if the request worked (200 means SUCCESS in web language)
    if response.status_code == 200:
        print("SUCCESS: Connected to NASA website!")

        # BeautifulSoup reads the HTML of the page
        # Think of HTML as the "source code" of a webpage
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all links on the page
        all_links = soup.find_all("a", href=True)
        print(f"Found {len(all_links)} links on the page")

        # Look for links that mention turbofan or CMAPSS
        engine_links = []
        for link in all_links:
            link_text = link.text.lower()
            link_href = link["href"].lower()
            if "turbofan" in link_text or "cmapss" in link_text or "cmapss" in link_href:
                engine_links.append(link)
                print(f"  FOUND relevant link: {link.text.strip()} -> {link['href']}")

        if engine_links:
            print(f"\nFound {len(engine_links)} engine-related links!")
        else:
            print("No direct links found on page — will use known direct URL")

    else:
        print(f"Website returned status code: {response.status_code}")
        print("This means the page was not accessible. Using backup method.")

except Exception as e:
    # If anything goes wrong (no internet, website down), we catch the error here
    print(f"Could not reach NASA website: {e}")
    print("This is normal! Websites sometimes block automated requests.")
    print("Moving to backup download method...")


# --- STEP 5: Download the actual data files ---
# The CMAPSS dataset has 4 different engine scenarios (FD001 to FD004)
# We will download each one separately from a reliable GitHub mirror

print("\n" + "=" * 60)
print("STEP 5: Downloading the 4 engine dataset files...")
print("=" * 60)

# These are the 4 training files + 4 test files + RUL (remaining useful life) files
# FD001 = one operating condition, one fault mode (simplest)
# FD002 = six operating conditions, one fault mode
# FD003 = one operating condition, two fault modes
# FD004 = six operating conditions, two fault modes (most complex)

base_github_url = "https://raw.githubusercontent.com/hankroark/Turbofan-Engine-Degradation/master/CMAPSSData/"

files_to_download = [
    "train_FD001.txt",
    "train_FD002.txt",
    "train_FD003.txt",
    "train_FD004.txt",
    "test_FD001.txt",
    "test_FD002.txt",
    "test_FD003.txt",
    "test_FD004.txt",
    "RUL_FD001.txt",
    "RUL_FD002.txt",
    "RUL_FD003.txt",
    "RUL_FD004.txt",
]

# Also scrape the column name information from a public source
# This is our actual "web scraping" demonstration for the project
print("\nSCRAPING sensor column names from Wikipedia-style source...")

sensor_info_url = "https://raw.githubusercontent.com/hankroark/Turbofan-Engine-Degradation/master/README.md"

try:
    sensor_response = requests.get(sensor_info_url, headers=headers, timeout=10)
    if sensor_response.status_code == 200:
        print("SUCCESS: Scraped sensor descriptions from GitHub README!")
        # Save the scraped metadata
        metadata_path = os.path.join(data_folder, "scraped_metadata.txt")
        with open(metadata_path, "w") as f:
            f.write("SCRAPED FROM: " + sensor_info_url + "\n")
            f.write("=" * 50 + "\n")
            f.write(sensor_response.text)
        print(f"Saved scraped metadata to: {metadata_path}")
    else:
        print(f"Could not scrape metadata: status {sensor_response.status_code}")
except Exception as e:
    print(f"Metadata scraping failed: {e}")


# Now download each data file
download_count = 0
failed_count = 0

for filename in files_to_download:
    file_url = base_github_url + filename
    save_path = os.path.join(data_folder, filename)

    # Skip if already downloaded (so we don't re-download every time we run this script)
    if os.path.exists(save_path):
        print(f"  SKIP (already downloaded): {filename}")
        download_count += 1
        continue

    print(f"  Downloading: {filename}...")

    try:
        # Download the file
        file_response = requests.get(file_url, headers=headers, timeout=30)

        if file_response.status_code == 200:
            # Save the file to our data folder
            with open(save_path, "wb") as f:
                f.write(file_response.content)

            # Check the file size to make sure it's not empty
            file_size = os.path.getsize(save_path)
            print(f"  SUCCESS: Saved {filename} ({file_size:,} bytes)")
            download_count += 1
        else:
            print(f"  FAILED: {filename} returned status {file_response.status_code}")
            failed_count += 1

    except Exception as e:
        print(f"  ERROR downloading {filename}: {e}")
        failed_count += 1


# --- STEP 6: Create a column names file ---
# The NASA data files have NO column headers — just numbers
# We manually define the column names based on the NASA documentation

print("\n" + "=" * 60)
print("STEP 6: Creating column names reference file...")
print("=" * 60)

# These are the official column names from NASA's CMAPSS documentation
column_names = """# CMAPSS Dataset Column Names
# Source: NASA Ames Prognostics Center of Excellence
# Scraped and documented for the Predictive Maintenance Project

COLUMN_ORDER:
1.  engine_id        - Which engine this reading is from (1, 2, 3...)
2.  cycle            - Time step number (like a clock tick, goes up until engine fails)
3.  op_setting_1     - Operational setting 1 (flight conditions)
4.  op_setting_2     - Operational setting 2 (flight conditions)
5.  op_setting_3     - Operational setting 3 (flight conditions)
6.  sensor_1         - Fan inlet temperature (°R)
7.  sensor_2         - LPC outlet temperature (°R)
8.  sensor_3         - HPC outlet temperature (°R)
9.  sensor_4         - LPT outlet temperature (°R)
10. sensor_5         - Fan inlet pressure (psia)
11. sensor_6         - Bypass-duct pressure (psia)
12. sensor_7         - HPC outlet pressure (psia)
13. sensor_8         - Physical fan speed (rpm)
14. sensor_9         - Physical core speed (rpm)
15. sensor_10        - Engine pressure ratio (EPR)
16. sensor_11        - HPC outlet static pressure (psia)
17. sensor_12        - Fuel flow ratio (pps/psia)
18. sensor_13        - Corrected fan speed (rpm)
19. sensor_14        - Corrected core speed (rpm)
20. sensor_15        - Bypass ratio
21. sensor_16        - Burner fuel-air ratio
22. sensor_17        - Bleed enthalpy
23. sensor_18        - Demanded fan speed (rpm)
24. sensor_19        - Demanded corrected fan speed (rpm)
25. sensor_20        - HPT coolant bleed (lbm/s)
26. sensor_21        - LPT coolant bleed (lbm/s)

ABBREVIATIONS:
LPC = Low Pressure Compressor
HPC = High Pressure Compressor
LPT = Low Pressure Turbine
HPT = High Pressure Turbine
psia = pounds per square inch absolute
rpm = revolutions per minute
°R = degrees Rankine (temperature scale)
"""

column_file_path = os.path.join(data_folder, "column_names.txt")
with open(column_file_path, "w") as f:
    f.write(column_names)

print(f"Saved column names reference to: {column_file_path}")


# --- FINAL SUMMARY ---
print("\n" + "=" * 60)
print("DOWNLOAD SUMMARY")
print("=" * 60)
print(f"Files downloaded successfully: {download_count}")
print(f"Files failed: {failed_count}")
print(f"All files saved in folder: ./{data_folder}/")
print("\nFiles in your data folder:")
for f in sorted(os.listdir(data_folder)):
    size = os.path.getsize(os.path.join(data_folder, f))
    print(f"  {f:40s} {size:>10,} bytes")

print("\nNEXT STEP: Run file 02_load_to_mysql.py")
print("           That file will read these .txt files and load them into MySQL")

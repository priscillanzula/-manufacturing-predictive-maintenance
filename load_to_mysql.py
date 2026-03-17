
# import necessary libraries
import mysql.connector   # Lets Python talk to MySQL
import pandas as pd      # Pandas = Python's best tool for reading tables/spreadsheets
import os                # For reading files from folders
import sys               # For stopping the program cleanly if something goes wrong


# Business problem:
# Airlines and engine manufacturers collect large volumes of sensor data from engines.
# Storing and organizing this data efficiently is critical to enable analysis, modeling, and predictive maintenance.
# This file sets up a structured MySQL database to hold the raw engine sensor data, test labels, and metadata for downstream analysis.

# Objective of this file:
# Connect to MySQL database
# Create tables: engines, sensor_readings, rul_labels
# Load CMAPSS dataset (training + test + RUL labels)
# Verify data integrity


#  Set up  database connection details
# The default username is usually "root"

# Where MySQL is running (localhost = your own computer)
DB_HOST = "localhost"
DB_USER = "root"        # MySQL username
DB_PASSWORD = "Kn@24068."  # MySQL password
DB_NAME = "turbofan_db"  # The name of the database to create

print(f"Database settings:")
print(f"  Host:     {DB_HOST}")
print(f"  User:     {DB_USER}")
print(f"  Database: {DB_NAME}")


# Connect to MySQL and create the database
# First we connect WITHOUT specifying a database (because it doesn't exist yet)

print("\nConnecting to MySQL...")

try:
    # Open a connection to MySQL
    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD
    )

    # A cursor is like a pen — we use it to write commands to MySQL
    cursor = connection.cursor()

    print("SUCCESS: Connected to MySQL!")

    # Create the database if it doesn't already exist
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    print(f"Database '{DB_NAME}' is ready.")

    # Now switch to using that database
    cursor.execute(f"USE {DB_NAME}")
    print(f"Now using database: {DB_NAME}")

except mysql.connector.Error as e:
    # If connection fails, show a helpful message
    print(f"\nERROR: Could not connect to MySQL!")
    print(f"Error details: {e}")
    print("\nTROUBLESHOOTING:")
    print("1. Is MySQL running? (Check your system tray or run: mysql.server start)")
    print("2. Is your password correct? Edit DB_PASSWORD at the top of this file.")
    print("3. Did you install mysql-connector-python? Run: pip install mysql-connector-python")
    sys.exit(1)  # Stop the program


# Create the tables
# We need 3 main tables:
# 1. engines      - one row per engine (like a list of all aircraft engines)
# 2. sensor_readings - the actual sensor data recorded over time
# 3. rul_labels   - the "answer" — how many cycles left each engine had at end of test


# SQL commands to create tables

# TABLE 1: engines
# Stores basic info about each engine and which dataset it came from
create_engines_table = """
CREATE TABLE IF NOT EXISTS engines (
    engine_id    INT,             -- The engine number (1, 2, 3...)
    dataset      VARCHAR(10),     -- Which file it came from (FD001, FD002, etc.)
    max_cycle    INT,             -- How many cycles until the engine failed
    PRIMARY KEY (engine_id, dataset)  -- Together these two columns = unique identifier
)
"""

# TABLE 2: sensor_readings
# This is the BIG table — one row for every sensor reading ever recorded
# With FD001 alone this will be ~20,000 rows
create_sensor_readings_table = """
CREATE TABLE IF NOT EXISTS sensor_readings (
    id           INT AUTO_INCREMENT PRIMARY KEY,  -- A unique number for each row
    engine_id    INT,            -- Which engine
    dataset      VARCHAR(10),    -- Which dataset file
    cycle        INT,            -- What time step (cycle number)
    op_setting_1 FLOAT,          -- Operational setting 1
    op_setting_2 FLOAT,          -- Operational setting 2
    op_setting_3 FLOAT,          -- Operational setting 3
    sensor_1     FLOAT,          -- Fan inlet temperature
    sensor_2     FLOAT,          -- LPC outlet temperature
    sensor_3     FLOAT,          -- HPC outlet temperature
    sensor_4     FLOAT,          -- LPT outlet temperature
    sensor_5     FLOAT,          -- Fan inlet pressure
    sensor_6     FLOAT,          -- Bypass-duct pressure
    sensor_7     FLOAT,          -- HPC outlet pressure
    sensor_8     FLOAT,          -- Physical fan speed
    sensor_9     FLOAT,          -- Physical core speed
    sensor_10    FLOAT,          -- Engine pressure ratio
    sensor_11    FLOAT,          -- HPC outlet static pressure
    sensor_12    FLOAT,          -- Fuel flow ratio
    sensor_13    FLOAT,          -- Corrected fan speed
    sensor_14    FLOAT,          -- Corrected core speed
    sensor_15    FLOAT,          -- Bypass ratio
    sensor_16    FLOAT,          -- Burner fuel-air ratio
    sensor_17    FLOAT,          -- Bleed enthalpy
    sensor_18    FLOAT,          -- Demanded fan speed
    sensor_19    FLOAT,          -- Demanded corrected fan speed
    sensor_20    FLOAT,          -- HPT coolant bleed
    sensor_21    FLOAT           -- LPT coolant bleed
)
"""

# TABLE 3: rul_labels
# RUL = Remaining Useful Life
# For the TEST data, NASA tells us how many cycles were left when we stopped recording
create_rul_table = """
CREATE TABLE IF NOT EXISTS rul_labels (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    engine_id    INT,            -- Which test engine
    dataset      VARCHAR(10),    -- Which dataset
    true_rul     INT             -- How many cycles it ACTUALLY had left (the answer)
)
"""

# Run all three CREATE TABLE commands
tables_sql = [
    ("engines", create_engines_table),
    ("sensor_readings", create_sensor_readings_table),
    ("rul_labels", create_rul_table),
]

for table_name, sql_command in tables_sql:
    cursor.execute(sql_command)
    print(f"  Table created (or already existed): {table_name}")

# Save these changes
connection.commit()
print("All tables are ready!")


# Define column names
# The .txt files have no column headers, just space-separated numbers
# We define the headers based on NASA documentation

column_names = [
    "engine_id", "cycle",
    "op_setting_1", "op_setting_2", "op_setting_3",
    "sensor_1", "sensor_2", "sensor_3", "sensor_4", "sensor_5",
    "sensor_6", "sensor_7", "sensor_8", "sensor_9", "sensor_10",
    "sensor_11", "sensor_12", "sensor_13", "sensor_14", "sensor_15",
    "sensor_16", "sensor_17", "sensor_18", "sensor_19", "sensor_20",
    "sensor_21"
]

print(f"\nColumn names assigned: {len(column_names)} columns")


# Load each training file into MySQL
# We have 4 training files: FD001, FD002, FD003, FD004


datasets = ["FD001", "FD002", "FD003", "FD004"]
data_folder = "data"

total_rows_inserted = 0

for dataset_name in datasets:
    filename = f"train_{dataset_name}.txt"
    filepath = os.path.join(data_folder, filename)

    # Check if file exists
    if not os.path.exists(filepath):
        print(f"  SKIP: {filename} not found. Run 01_download_data.py first.")
        continue

    print(f"\nLoading {filename}...")

    # Read the file with pandas
    # sep="\s+" means "columns are separated by spaces"
    # header=None means the file has no header row
    data = pd.read_csv(
        filepath,
        sep=r"\s+",        # split by whitespace (spaces)
        header=None,       # no header row in the file
        names=column_names  # use OUR column names
    )

    # Drop any completely empty columns (some files have trailing spaces)
    data = data.dropna(axis=1, how="all")

    print(f"  Read {len(data):,} rows and {len(data.columns)} columns")

    # First, load unique engines into the engines table
    # Find the maximum cycle for each engine (= when it failed)
    engine_summary = data.groupby("engine_id")["cycle"].max().reset_index()
    engine_summary.columns = ["engine_id", "max_cycle"]

    for row in engine_summary.itertuples():
        insert_engine_sql = """
            INSERT IGNORE INTO engines (engine_id, dataset, max_cycle)
            VALUES (%s, %s, %s)
        """
        cursor.execute(insert_engine_sql, (row.engine_id,
                       dataset_name, row.max_cycle))

    connection.commit()
    print(f"  Loaded {len(engine_summary)} engines into 'engines' table")

    # Now load all sensor readings
    # We insert in batches of 500 rows to avoid memory issues
    batch_size = 500
    rows_loaded = 0

    # Prepare the SQL INSERT statement
    # %s means "fill in this value later"
    insert_sql = """
        INSERT INTO sensor_readings (
            engine_id, dataset, cycle,
            op_setting_1, op_setting_2, op_setting_3,
            sensor_1, sensor_2, sensor_3, sensor_4, sensor_5,
            sensor_6, sensor_7, sensor_8, sensor_9, sensor_10,
            sensor_11, sensor_12, sensor_13, sensor_14, sensor_15,
            sensor_16, sensor_17, sensor_18, sensor_19, sensor_20, sensor_21
        ) VALUES (
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
    """

    # Go through the data in batches
    batch = []

    for row in data.itertuples(index=False):
        # Build one row of values to insert
        values = (
            row.engine_id, dataset_name, row.cycle,
            row.op_setting_1, row.op_setting_2, row.op_setting_3,
            row.sensor_1, row.sensor_2, row.sensor_3, row.sensor_4, row.sensor_5,
            row.sensor_6, row.sensor_7, row.sensor_8, row.sensor_9, row.sensor_10,
            row.sensor_11, row.sensor_12, row.sensor_13, row.sensor_14, row.sensor_15,
            row.sensor_16, row.sensor_17, row.sensor_18, row.sensor_19, row.sensor_20,
            row.sensor_21
        )
        batch.append(values)

        # When we have 500 rows ready, insert them all at once
        if len(batch) >= batch_size:
            cursor.executemany(insert_sql, batch)
            connection.commit()
            rows_loaded += len(batch)
            batch = []  # Clear the batch

    # Insert any remaining rows (the last batch may be smaller than 500)
    if batch:
        cursor.executemany(insert_sql, batch)
        connection.commit()
        rows_loaded += len(batch)

    print(
        f"  Loaded {rows_loaded:,} sensor readings into 'sensor_readings' table")
    total_rows_inserted += rows_loaded


# Load RUL labels for test data
for dataset_name in datasets:
    filename = f"RUL_{dataset_name}.txt"
    filepath = os.path.join(data_folder, filename)

    if not os.path.exists(filepath):
        print(f"  SKIP: {filename} not found.")
        continue

    # RUL files have just ONE column — one number per engine
    rul_data = pd.read_csv(filepath, header=None, names=["true_rul"])

    print(f"Loading {filename}: {len(rul_data)} engines")

    # Each row corresponds to engine 1, 2, 3... in order
    rul_data["engine_id"] = rul_data.index + 1  # engine IDs start at 1
    rul_data["dataset"] = dataset_name

    for row in rul_data.itertuples(index=False):
        cursor.execute(
            "INSERT INTO rul_labels (engine_id, dataset, true_rul) VALUES (%s, %s, %s)",
            (row.engine_id, row.dataset, row.true_rul)
        )

    connection.commit()
    print(f"  Loaded {len(rul_data)} RUL labels for {dataset_name}")


# Verify the data was loaded correctly

# Quick check — how many rows are in each table?
cursor.execute("SELECT COUNT(*) FROM engines")
engine_count = cursor.fetchone()[0]
print(f"  engines table:          {engine_count:>10,} rows")

cursor.execute("SELECT COUNT(*) FROM sensor_readings")
sensor_count = cursor.fetchone()[0]
print(f"  sensor_readings table:  {sensor_count:>10,} rows")

cursor.execute("SELECT COUNT(*) FROM rul_labels")
rul_count = cursor.fetchone()[0]
print(f"  rul_labels table:       {rul_count:>10,} rows")

# Also verify the breakdown by dataset
print("\n  Breakdown by dataset:")
cursor.execute("""
    SELECT dataset,
           COUNT(DISTINCT engine_id) AS number_of_engines,
           COUNT(*) AS total_sensor_readings,
           MIN(cycle) AS min_cycle,
           MAX(cycle) AS max_cycle
    FROM sensor_readings
    GROUP BY dataset
    ORDER BY dataset
""")

rows = cursor.fetchall()
print(f"  {'Dataset':<10} {'Engines':>10} {'Readings':>15} {'Min Cycle':>12} {'Max Cycle':>12}")
print("  " + "-" * 62)
for row in rows:
    print(f"  {row[0]:<10} {row[1]:>10} {row[2]:>15,} {row[3]:>12} {row[4]:>12}")


# Close the connection
cursor.close()
connection.close()
print("\nDatabase connection closed.")


# Summary
print(f"Total sensor readings loaded: {total_rows_inserted:,}")
print(f"Database name: {DB_NAME}")
print(f"Tables created: engines, sensor_readings, rul_labels")
print("\nNEXT STEP: Run file sql_analysis.sql")
print("           Open it in MySQL Workbench to run all the SQL analysis queries")

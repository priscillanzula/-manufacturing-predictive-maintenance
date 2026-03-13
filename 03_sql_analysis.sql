-- ============================================================
-- FILE 3: SQL Analysis - turbofan_db
-- ============================================================
--
-- WHAT IS THIS FILE?
-- This is a SQL script. You run it inside MySQL Workbench.
-- It contains all the smart questions we ask our database.
--
-- BUSINESS QUESTIONS WE ARE ANSWERING:
-- 1. Which engines wore out the fastest?
-- 2. Which sensors changed the most as engines aged?
-- 3. Can we categorise engines by how long they last?
-- 4. Which engines need immediate attention RIGHT NOW?
--
-- HOW TO USE THIS FILE:
-- 1. Open MySQL Workbench
-- 2. Connect to your localhost database
-- 3. Open this file (File > Open SQL Script)
-- 4. Run each section one at a time using the play button
--
-- SQL SKILL SHOWCASE:
-- This file uses: SELECT, WHERE, GROUP BY, ORDER BY,
-- JOINs, Window Functions (RANK, ROW_NUMBER, LAG),
-- CTEs (Common Table Expressions), CASE statements,
-- Aggregate functions (AVG, MAX, MIN, STDDEV),
-- Views, and a Stored Procedure
-- ============================================================


-- Always start by making sure we are using the right database
USE turbofan_db;


-- ============================================================
-- SECTION 1: Basic Exploration
-- "Let's look at what we have"
-- ============================================================

-- How many engines do we have in total?
SELECT
    dataset,
    COUNT(DISTINCT engine_id) AS total_engines,
    MIN(max_cycle)            AS shortest_life,   -- Engine that failed fastest
    MAX(max_cycle)            AS longest_life,     -- Engine that lasted longest
    ROUND(AVG(max_cycle), 1)  AS average_life      -- Typical engine life
FROM engines
GROUP BY dataset
ORDER BY dataset;

-- WHAT THIS TELLS US:
-- If average life for FD001 is 206 cycles, that's our baseline.
-- Engines below that average are our "concern group."


-- How many sensor readings do we have total?
SELECT
    dataset,
    COUNT(*) AS total_readings
FROM sensor_readings
GROUP BY dataset;

-- This confirms our data loaded correctly.
-- FD001 should have roughly 20,000 rows.


-- ============================================================
-- SECTION 2: Engine Lifetime Analysis
-- "How long do engines typically last?"
-- ============================================================

-- Get the lifetime of every engine in FD001
-- (We focus on FD001 first — it's the simplest dataset)
SELECT
    engine_id,
    max_cycle AS total_life_in_cycles,
    -- Categorise each engine into a health bucket
    CASE
        WHEN max_cycle < 150 THEN 'Short Life (Under 150)'
        WHEN max_cycle < 250 THEN 'Normal Life (150-250)'
        ELSE                      'Long Life (Over 250)'
    END AS life_category
FROM engines
WHERE dataset = 'FD001'
ORDER BY max_cycle ASC;

-- INSIGHT: Engines with short lives may have been
-- manufactured differently or operated in harder conditions.


-- Count how many engines fall into each life category
SELECT
    CASE
        WHEN max_cycle < 150 THEN 'Short Life (Under 150)'
        WHEN max_cycle < 250 THEN 'Normal Life (150-250)'
        ELSE                      'Long Life (Over 250)'
    END AS life_category,
    COUNT(*) AS number_of_engines,
    ROUND(AVG(max_cycle), 1) AS avg_life_in_category
FROM engines
WHERE dataset = 'FD001'
GROUP BY life_category
ORDER BY avg_life_in_category;


-- ============================================================
-- SECTION 3: Window Functions
-- "Compare each engine to the average"
-- ============================================================
-- A Window Function looks at a GROUP of rows while still
-- keeping each individual row. It's like saying:
-- "Show me each student AND the class average on the same row."

-- Rank engines by how long they lasted (longest first)
SELECT
    engine_id,
    max_cycle,
    -- RANK() assigns a position: 1st, 2nd, 3rd place...
    RANK() OVER (ORDER BY max_cycle DESC) AS rank_by_longevity,
    -- Calculate how far this engine is from the average
    ROUND(max_cycle - AVG(max_cycle) OVER (), 1) AS difference_from_average,
    -- What percentile is this engine in? (100 = lasted longest)
    ROUND(
        100.0 * RANK() OVER (ORDER BY max_cycle ASC) / COUNT(*) OVER (),
        1
    ) AS percentile
FROM engines
WHERE dataset = 'FD001'
ORDER BY rank_by_longevity;

-- WHY THIS MATTERS:
-- If an engine is in the bottom 10th percentile,
-- it failed much sooner than expected — that's a red flag.


-- ============================================================
-- SECTION 4: Sensor Trend Analysis Using LAG()
-- "How are sensors changing over time for one engine?"
-- ============================================================
-- LAG() is a window function that lets you look at the
-- PREVIOUS row's value. This is perfect for time series data.
-- It answers: "What was the sensor value one cycle ago?"

-- Look at how sensor_2 (temperature) changes cycle by cycle for engine 1
SELECT
    engine_id,
    cycle,
    sensor_2,                                   -- Current reading
    LAG(sensor_2) OVER (
        PARTITION BY engine_id                  -- Reset for each engine
        ORDER BY cycle                          -- Go in time order
    ) AS previous_cycle_sensor_2,              -- Reading from last cycle
    ROUND(
        sensor_2 - LAG(sensor_2) OVER (
            PARTITION BY engine_id ORDER BY cycle
        ),
        4
    ) AS change_from_last_cycle                -- How much it changed
FROM sensor_readings
WHERE dataset = 'FD001'
  AND engine_id = 1
ORDER BY cycle;

-- INSIGHT: If sensor_2 is steadily increasing over time,
-- that could mean the engine is getting hotter as it degrades.


-- ============================================================
-- SECTION 5: CTE (Common Table Expression)
-- "Break a complex query into readable steps"
-- ============================================================
-- A CTE is like a temporary named table you create inside a query.
-- Instead of writing one huge confusing query, you write small
-- readable steps. It's like solving a math problem step by step.

-- BUSINESS QUESTION: For each engine, what are the average sensor
-- readings in the FIRST 50 cycles vs the LAST 50 cycles?
-- This shows us how much each sensor degrades over the engine's life.

WITH
-- Step 1: Get readings from the early life of each engine
early_life AS (
    SELECT
        engine_id,
        AVG(sensor_2)  AS avg_sensor_2_early,
        AVG(sensor_7)  AS avg_sensor_7_early,
        AVG(sensor_11) AS avg_sensor_11_early,
        AVG(sensor_12) AS avg_sensor_12_early
    FROM sensor_readings
    WHERE dataset = 'FD001'
      AND cycle <= 50   -- First 50 cycles = early life
    GROUP BY engine_id
),

-- Step 2: Get readings from the late life of each engine
late_life AS (
    SELECT
        sr.engine_id,
        AVG(sr.sensor_2)  AS avg_sensor_2_late,
        AVG(sr.sensor_7)  AS avg_sensor_7_late,
        AVG(sr.sensor_11) AS avg_sensor_11_late,
        AVG(sr.sensor_12) AS avg_sensor_12_late
    FROM sensor_readings sr
    -- Join with engines table to know each engine's total life
    JOIN engines e ON sr.engine_id = e.engine_id AND sr.dataset = e.dataset
    WHERE sr.dataset = 'FD001'
      AND sr.cycle >= (e.max_cycle - 50)  -- Last 50 cycles = end of life
    GROUP BY sr.engine_id
),

-- Step 3: Get the engine lifespan info
engine_info AS (
    SELECT engine_id, max_cycle
    FROM engines
    WHERE dataset = 'FD001'
)

-- Final step: Combine everything and calculate the CHANGE
SELECT
    ei.engine_id,
    ei.max_cycle                                     AS total_life,
    -- Sensor 2 (temperature) change
    ROUND(el.avg_sensor_2_early, 2)                  AS sensor_2_early,
    ROUND(ll.avg_sensor_2_late, 2)                   AS sensor_2_late,
    ROUND(ll.avg_sensor_2_late - el.avg_sensor_2_early, 2) AS sensor_2_change,
    -- Sensor 11 (pressure) change
    ROUND(el.avg_sensor_11_early, 2)                 AS sensor_11_early,
    ROUND(ll.avg_sensor_11_late, 2)                  AS sensor_11_late,
    ROUND(ll.avg_sensor_11_late - el.avg_sensor_11_early, 2) AS sensor_11_change
FROM engine_info ei
JOIN early_life el ON ei.engine_id = el.engine_id
JOIN late_life  ll ON ei.engine_id = ll.engine_id
ORDER BY sensor_2_change DESC;

-- INSIGHT: Engines where sensor_2 increased the most (positive change)
-- had more heat buildup as they aged — a sign of internal wear.


-- ============================================================
-- SECTION 6: Calculate RUL (Remaining Useful Life) for Training Data
-- ============================================================
-- For the TRAINING data, we know the full engine history.
-- We can calculate how many cycles each engine had LEFT
-- at every single reading. This is what our ML model will learn to predict.
--
-- FORMULA: RUL at cycle X = max_cycle - cycle_X
-- Example: Engine lasted 206 cycles. At cycle 100, RUL = 206 - 100 = 106

SELECT
    sr.engine_id,
    sr.cycle,
    e.max_cycle                           AS total_engine_life,
    (e.max_cycle - sr.cycle)              AS remaining_useful_life,   -- RUL
    sr.sensor_2,
    sr.sensor_7,
    sr.sensor_11,
    sr.sensor_12,
    -- Flag cycles where less than 30 cycles remain (DANGER ZONE)
    CASE
        WHEN (e.max_cycle - sr.cycle) < 30 THEN 'DANGER'
        WHEN (e.max_cycle - sr.cycle) < 80 THEN 'WARNING'
        ELSE 'NORMAL'
    END AS health_status
FROM sensor_readings sr
JOIN engines e
    ON sr.engine_id = e.engine_id
    AND sr.dataset = e.dataset
WHERE sr.dataset = 'FD001'
  AND sr.engine_id IN (1, 2, 3)    -- Look at first 3 engines as example
ORDER BY sr.engine_id, sr.cycle;


-- ============================================================
-- SECTION 7: Create a VIEW
-- "Save a useful query so we can use it easily later"
-- ============================================================
-- A VIEW is like a saved query. You give it a name and then
-- you can use it like it's a table. Great for queries you use often.

-- Drop the view if it already exists (so we can recreate it fresh)
DROP VIEW IF EXISTS v_engine_health;

-- Create the view: gives us a clean table of RUL for all FD001 data
CREATE VIEW v_engine_health AS
SELECT
    sr.engine_id,
    sr.dataset,
    sr.cycle,
    e.max_cycle,
    (e.max_cycle - sr.cycle)     AS remaining_useful_life,
    CASE
        WHEN (e.max_cycle - sr.cycle) < 30 THEN 'DANGER'
        WHEN (e.max_cycle - sr.cycle) < 80 THEN 'WARNING'
        ELSE 'NORMAL'
    END AS health_status,
    sr.sensor_2,
    sr.sensor_7,
    sr.sensor_11,
    sr.sensor_12
FROM sensor_readings sr
JOIN engines e
    ON sr.engine_id = e.engine_id
    AND sr.dataset = e.dataset;

-- Now we can use this view easily:
-- (This is much simpler than rewriting the full query every time!)
SELECT * FROM v_engine_health
WHERE dataset = 'FD001'
  AND health_status = 'DANGER'
LIMIT 20;


-- ============================================================
-- SECTION 8: Stored Procedure
-- "A mini program inside MySQL"
-- ============================================================
-- A Stored Procedure is like saving a function inside MySQL.
-- You call it by name and it runs. This is useful for operations
-- you repeat often, like generating a maintenance alert report.

-- First, drop if it already exists
DROP PROCEDURE IF EXISTS GetMaintenanceAlerts;

-- Change the statement separator temporarily
-- (needed because the procedure body contains semicolons)
DELIMITER //

CREATE PROCEDURE GetMaintenanceAlerts(
    IN target_dataset VARCHAR(10),    -- Input: which dataset to check
    IN danger_threshold INT           -- Input: cycles left = danger
)
BEGIN
    -- This procedure finds all engines currently in the DANGER zone
    -- and returns a maintenance alert report

    SELECT
        sr.engine_id,
        sr.dataset,
        sr.cycle                             AS current_cycle,
        e.max_cycle                          AS failure_cycle,
        (e.max_cycle - sr.cycle)             AS cycles_remaining,
        'IMMEDIATE MAINTENANCE REQUIRED'     AS alert_message,
        NOW()                                AS report_generated_at
    FROM sensor_readings sr
    JOIN engines e
        ON sr.engine_id = e.engine_id
        AND sr.dataset = e.dataset
    WHERE sr.dataset = target_dataset
      AND (e.max_cycle - sr.cycle) <= danger_threshold
      -- Get only the MOST RECENT reading per engine (not all history)
      AND sr.cycle = e.max_cycle
    ORDER BY cycles_remaining ASC;

END //

DELIMITER ;

-- Run the stored procedure:
-- "Give me all FD001 engines with 30 or fewer cycles left"
CALL GetMaintenanceAlerts('FD001', 30);


-- ============================================================
-- SECTION 9: Final Summary Statistics (for the report)
-- ============================================================

-- Overall health dashboard
SELECT
    dataset,
    COUNT(DISTINCT engine_id)              AS total_engines,
    ROUND(AVG(max_cycle), 0)               AS avg_engine_life,
    MIN(max_cycle)                         AS shortest_life,
    MAX(max_cycle)                         AS longest_life,
    ROUND(STDDEV(max_cycle), 1)            AS life_variability
FROM engines
GROUP BY dataset;

-- Which sensors have the highest variation? (These are most useful for prediction)
SELECT
    'sensor_2'                             AS sensor_name,
    ROUND(AVG(sensor_2), 4)                AS average_value,
    ROUND(STDDEV(sensor_2), 4)             AS std_deviation,
    ROUND(MIN(sensor_2), 4)                AS min_value,
    ROUND(MAX(sensor_2), 4)                AS max_value
FROM sensor_readings WHERE dataset = 'FD001'
UNION ALL
SELECT 'sensor_7',  ROUND(AVG(sensor_7), 4),  ROUND(STDDEV(sensor_7), 4),  ROUND(MIN(sensor_7), 4),  ROUND(MAX(sensor_7), 4) FROM sensor_readings WHERE dataset = 'FD001'
UNION ALL
SELECT 'sensor_11', ROUND(AVG(sensor_11), 4), ROUND(STDDEV(sensor_11), 4), ROUND(MIN(sensor_11), 4), ROUND(MAX(sensor_11), 4) FROM sensor_readings WHERE dataset = 'FD001'
UNION ALL
SELECT 'sensor_12', ROUND(AVG(sensor_12), 4), ROUND(STDDEV(sensor_12), 4), ROUND(MIN(sensor_12), 4), ROUND(MAX(sensor_12), 4) FROM sensor_readings WHERE dataset = 'FD001'
UNION ALL
SELECT 'sensor_15', ROUND(AVG(sensor_15), 4), ROUND(STDDEV(sensor_15), 4), ROUND(MIN(sensor_15), 4), ROUND(MAX(sensor_15), 4) FROM sensor_readings WHERE dataset = 'FD001'
ORDER BY std_deviation DESC;

-- RECOMMENDATION:
-- Sensors with high standard deviation (high variability) are the MOST
-- useful for prediction. A sensor that always reads the same value
-- tells us nothing. A sensor that changes a lot as the engine wears
-- gives us valuable information to work with.

-- ============================================================
-- END OF SQL ANALYSIS FILE
-- ============================================================

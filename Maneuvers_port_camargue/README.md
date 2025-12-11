# Maneuvers Analysis Project

## Description
This folder contains a pipeline of Jupyter notebooks and Python scripts to analyze **maneuvers** (jibes and tacks).  
The workflow mirrors the straight-run project: it identifies time intervals of interest, enriches them with rider/equipment metadata, merges data from multiple sources (including Senseboard logs), and generates rider-specific reports for each maneuver.

Execution is automated via **`runner.ipynb`**, which runs all notebooks in a predefined order.

---

## Project Structure

### Main Pipeline (run by `runner.ipynb`)
1. **`MainCOG.ipynb`**  
   - Detects the maneuver intervals to analyze (e.g., jibe and tack windows).  
   - Produces `summary.json` with, for each maneuver: start/end time, maneuver type, and auxiliary details.

2. **`merge_all.ipynb`**  
   - Produces `all_data.csv`.  
   - Merges maneuver intervals with the summary.

3. **`addsenseboarddata.ipynb`**  
   - Produces `all_data_enriched.csv`.  
   - Adds Senseboard log data (including loadcell information) aligned to each maneuver interval.

4. **`Report_Gian_Jibe.ipynb`**  
   - Generates KPIs and visualizations for Gian’s jibes.

5. **`Report_Gian_Tack.ipynb`**  
   - Generates KPIs and visualizations for Gian’s tacks.

6. **`Report_Karl_Jibe.ipynb`**  
   - Generates KPIs and visualizations for Karl’s jibes.

7. **`Report_Karl_Tack.ipynb`**  
   - Generates KPIs and visualizations for Karl’s tacks.

---

### Other Files
- `cog_analysis.py`, `report_fct.py`: Utility functions used across notebooks.  
- `Report_with_eval.py`: Reporting/evaluation helpers for maneuver reports.  
- `summary.json`: Intermediate summary of detected maneuver intervals.  
- `all_data.csv`, `all_data_enriched.csv`: Consolidated datasets used for reporting.  
- `__pycache__/`, `old/`: Cache and archived materials.

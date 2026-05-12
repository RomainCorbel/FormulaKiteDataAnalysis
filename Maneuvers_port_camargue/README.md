# Maneuvers — Port Camargue

Analysis of jibes and tacks from the Port Camargue testing campaign (June 8 and 11, 2025).

Riders: **Gian Stragiotti** and **Karl Maeder**.

---

## Pipeline

Notebooks are run in order via **`runner.ipynb`**.

1. **`MainCOG.ipynb`**
   - Detects maneuver windows (jibes and tacks) from COG and SOG signals.
   - Classification: jibe (TWA > 90°), tack (TWA < 90°).
   - Validates each maneuver with an entry speed threshold and COG inversion check.
   - Output: `summary.json` — one entry per maneuver with start/end time, type, and auxiliary details.

2. **`merge_all.ipynb`**
   - Clips raw CSV files to each maneuver window.
   - Output: `all_data.csv`.

3. **`addsenseboarddata.ipynb`**
   - Time-aligns SenseBoard load cell logs to the merged dataset.
   - Output: `all_data_enriched.csv`.

4. **`Report_Gian_Jibe.ipynb`**
   - KPIs and visualizations for Gian's jibes: SOG loss, recovery time, heel dynamics, line loading.

5. **`Report_Gian_Tack.ipynb`**
   - Same report for Gian's tacks.

6. **`Report_Karl_Jibe.ipynb`**
   - Same report for Karl's jibes.

7. **`Report_Karl_Tack.ipynb`**
   - Same report for Karl's tacks.

---

## Python Utility Scripts

- **`cog_analysis.py`** — maneuver detection (COG change detection, SOG minima, classification).
- **`report_fct.py`** — data loading, statistics, time-series plots.
- **`Report_with_eval.py`** — evaluation helpers and multi-subplot comparison functions.

---

## Intermediate Files

- `summary.json` — detected maneuver intervals
- `all_data.csv` — merged row-level dataset

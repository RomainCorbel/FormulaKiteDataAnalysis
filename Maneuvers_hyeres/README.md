# Maneuvers — Hyères

Analysis of jibes and tacks from the Hyères testing campaign (November 30, 2025).

Rider: **Gian Stragiotti** only (limited maneuver data available for this campaign).

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

3. **`Report_Gian_Jibe.ipynb`**
   - KPIs and visualizations for Gian's jibes: SOG loss, recovery time, heel dynamics, line loading.

4. **`Report_Gian_Tack.ipynb`**
   - Same report for Gian's tacks.

---

## Python Utility Scripts

- **`cog_analysis.py`** — maneuver detection (COG change detection, SOG minima, classification).
- **`report_fct.py`** — data loading, statistics, time-series plots.
- **`Report_with_eval.py`** — evaluation helpers and multi-subplot comparison functions.

---

## Intermediate Files

- `summary.json` — detected maneuver intervals
- `all_data.csv` — merged row-level dataset

---

## Differences from Port Camargue

- Only Gian's maneuvers are analyzed (no Karl reports).
- No SenseBoard load cell data — `addsenseboarddata.ipynb` is not present.
- Only 3 runs recorded for this session.

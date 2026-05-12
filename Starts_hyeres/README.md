# Starts — Hyères

Analysis of race starts from the Hyères testing campaign (November 30, 2025).

10 race starts recorded. This folder has no equivalent at Port Camargue.

---

## Pipeline

Notebooks are run via **`runner.ipynb`**, which executes `Start_analysis.ipynb`.

1. **`Start_analysis.ipynb`**
   - Loads start intervals from `summary.json`.
   - For each start, computes:
     - `polar_ratio_%` — actual SOG as a percentage of the polar reference speed at the same TWA/TWS
     - Time to reach 98% of maximum SOG
     - Acceleration slope at mid-speed
     - SOG range (min to max)
   - Plots:
     - Full trajectory colored by SOG, with wind direction indicator
     - Time-series of SOG, heel, trim, and line tensions with LOWESS smoothing

The polar reference comes from `../Data_Sailnjord/lowess_postprocessed.csv`.

---

## Python Utility Script

- **`start_analysis.py`** — all analysis and plotting functions used by the notebook.

---

## Intermediate Files

- `summary.json` — start interval timestamps and auxiliary details
- `html/` — exported HTML and PDF reports from previous runs

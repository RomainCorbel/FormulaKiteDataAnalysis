# Straight Runs — Port Camargue

Analysis of straight-line sailing intervals (upwind and downwind) from the Port Camargue testing campaign (June 6–10, 2025).

Riders: **Gian Stragiotti** and **Karl Maeder**, sailing simultaneously with a SenseBoard instrumented board.

---

## Pipeline

Notebooks are run in order via **`runner.ipynb`**.

1. **`MainCOG.ipynb`**
   - Detects stable upwind and downwind intervals from raw telemetry using COG (Course Over Ground) change detection.
   - Output: `summary.json` — one entry per interval with start/end timestamps, average SOG, average TWA, stability score.

2. **`AddInfoToSummary.ipynb`**
   - Reads interview files and attaches rider/equipment metadata to each interval.
   - Adds: `total_weight`, `mast_brand` (0=Levi, 1=Chubanga), `master_leeward` role.
   - Output: `summary_enriched.json`.

3. **`merge_all.ipynb`**
   - Clips raw CSV files to each interval window.
   - Computes cumulative directional gains (forward, lateral, VMG).
   - Re-sorts line tensions: `Line_C2` = max, `Line_L2` = mid, `Line_R2` = min.
   - Output: `all_data.csv`.

4. **`addsenseboarddata.ipynb`**
   - Time-aligns SenseBoard load cell logs to the merged dataset.
   - Output: `all_data_enriched.csv`.

5. **`analysis.ipynb`**
   - Statistical analysis of navigation and line data (excluding load cells).
   - Covers: correlation matrix, ANOVA, OLS regression, t-tests (Gian vs Karl, master vs slave).

6. **`analysis_senseboard.ipynb`**
   - Same statistical framework applied to SenseBoard load cell data.

7. **`MainReport.ipynb`**
   - Comparative report across all runs.
   - Per-run KPIs: SOG, VMG, heel, line tensions, directional gains, winner determination.

8. **`Senseboard_Report.ipynb`**
   - Visualizations focused on load cell measurements.

9. **`weight_ttest.ipynb`**
   - T-tests on the effect of rider total weight on SOG.

10. **`mast_ttest.ipynb`**
    - T-tests on the effect of mast type (Levi vs Chubanga) on SOG.

---

## Python Utility Scripts

- **`cog_analysis.py`** — interval detection, COG change detection, trajectory plotting.
- **`report_fct.py`** — run loading, statistics computation, directional gain, comparison plots.
- **`analysis.py`** — correlation, ANOVA, OLS regression, t-test wrappers.

---

## Intermediate Files

- `summary.json` — detected intervals (output of step 1)
- `summary_enriched.json` — intervals with equipment metadata (output of step 2)
- `all_data.csv` — merged row-level dataset (output of step 3)
- `all_data_enriched.csv` — dataset with SenseBoard data added (output of step 4)

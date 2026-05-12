# Straight Runs : Hyères

Analysis of straight-line sailing intervals (upwind and downwind) from the Hyères testing campaign (November 25, 2025).

Riders: **Gian Stragiotti** and **Max Maeder**.

---

## Pipeline

Notebooks are run in order via **`runner.ipynb`**.

1. **`MainCOG.ipynb`**
   - Detects stable upwind and downwind intervals from raw telemetry using COG (Course Over Ground) change detection.
   - Output: `summary.json` : one entry per interval with start/end timestamps, average SOG, average TWA, stability score.

2. **`AddInfoToSummary.ipynb`**
   - Reads interview files and attaches rider/equipment metadata to each interval.
   - Adds: `total_weight`, `mast_brand` (0=Levi, 1=Chubanga), `master_leeward` role.
   - Output: `summary_enriched.json`.

3. **`merge_all.ipynb`**
   - Clips raw CSV files to each interval window.
   - Computes cumulative directional gains (forward, lateral, VMG).
   - Re-sorts line tensions: `Line_C2` = max, `Line_L2` = mid, `Line_R2` = min.
   - Output: `all_data.csv`.

4. **`analysis.ipynb`**
   - Statistical analysis of navigation and line data.
   - Covers: correlation matrix, ANOVA, OLS regression, t-tests (Gian vs Max, master vs slave).

5. **`MainReport.ipynb`**
   - Comparative report across all runs.
   - Per-run KPIs: SOG, VMG, heel, line tensions, directional gains, winner determination.

6. **`LeviVSChub.ipynb`**
   - Paired comparison of mast types (Levi vs Chubanga) across matched intervals.
   - Uses OLS regression controlling for rider and role to isolate the mast effect.

7. **`mast_ttest.ipynb`**
   - T-tests on the effect of mast type on SOG.

---

## Python Utility Scripts

- **`cog_analysis.py`** : interval detection, COG change detection, trajectory plotting.
- **`report_fct.py`** : run loading, statistics computation, directional gain, comparison plots.
- **`analysis.py`** : correlation, ANOVA, OLS regression, t-test wrappers.
- **`leviVSchub.py`** : paired interval builder, mast-type grouping, OLS and ANOVA for mast effect.

---

## Intermediate Files

- `summary.json` : detected intervals (output of step 1)
- `summary_enriched.json` : intervals with equipment metadata (output of step 2)
- `all_data.csv` : merged row-level dataset (output of step 3)

---

## Differences from Port Camargue

- No SenseBoard load cell data available for this campaign : `addsenseboarddata.ipynb` is not present.
- Includes `LeviVSChub.ipynb` for dedicated mast comparison analysis.

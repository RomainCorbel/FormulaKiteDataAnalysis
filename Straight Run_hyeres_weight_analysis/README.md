# Straight Runs : Hyères Weight Analysis

This folder is a specialization of the Hyères straight run pipeline focused on the effect of **rider total weight** on performance (SOG).

It reuses the same interval detection and data merging steps, then applies multiple weight-based filters to compare performance across different weight subsets.

---

## Pipeline

Notebooks are run in order via **`runner.ipynb`**.

1. **`MainCOG.ipynb`**
   - Detects stable upwind/downwind intervals from raw telemetry.
   - Output: `summary.json`.

2. **`AddInfoToSummary.ipynb`**
   - Enriches intervals with rider/equipment metadata (total weight, mast brand, role).
   - Output: `summary_enriched.json`.

3. **`merge_all.ipynb`**
   - Clips data to intervals, computes directional gains, re-sorts line tensions.
   - Output: `all_data.csv`.

4. **`analysis.ipynb`**
   - General statistical analysis of the dataset.

### Weight Impact Notebooks

Each of the following notebooks applies a different weight filter and tests whether SOG differs significantly between groups:

- **`weight_impact.ipynb`** : baseline analysis across all weight combinations
- **`weight_impact_below120.ipynb`** : subset restricted to riders below 120 kg
- **`weight_impact_below120_above105.ipynb`** : subset between 105 and 120 kg
- **`weight_impact_with_instantaneous.ipynb`** : includes instantaneous SOG in the analysis

---

## Python Utility Scripts

- **`cog_analysis.py`** : interval detection and trajectory plotting.
- **`report_fct.py`** : run loading, statistics, directional gain, comparison plots.
- **`analysis.py`** : correlation, ANOVA, OLS regression, t-test wrappers.
- **`weight_impact.py`** : core functions for paired interval building, weight-group aggregation, OLS and ANOVA on weight effect.

---

## Intermediate Files

- `summary.json` : detected intervals
- `summary_enriched.json` : intervals with metadata
- `all_data.csv` : merged row-level dataset

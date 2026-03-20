# Straight runs analysis

## Description
The workflow includes identifying and preparing time intervals of interest (straight runs upwind and downwind), enriching them with additional data, merging data from multiple sources (including Senseboard logs and interviews), running statistical analyses, and generating reports.  

The execution pipeline is automated via **`runner.ipynb`**, which runs all notebooks in a predefined order.

---

## Project Structure

### Main Pipeline
The notebooks are executed in the following order via `runner.ipynb`:

1. **`MainCOG.ipynb`**  
   - Identifies the study intervals ("straight lines") to analyze.  
   - Produces `summary.json` containing, for each run:  
     - Upwind and downwind intervals  
     - Start and end time  
     - Additional information.  

2. **`AddInfoToSummary.ipynb`**  
   - Creates `summary_enriched.json`.  
   - Adds additional information such as:  
     - `mast_brand`  
     - `master_leeward`  
     - `total_weight`  
   - Data is retrieved from the interview files.  

3. **`merge_all.ipynb`**  
   - Produces `all_data.csv`.  
   - Merges the study intervals with enriched summary information.  

4. **`addsenseboarddata.ipynb`**  
   - Produces `all_data_enriched.csv`.  
   - Adds Senseboard log data to the dataset.  

5. **`analysis.ipynb`**  
   - First statistical analysis of the dataset, excluding Senseboard loadcell data.  

6. **`analysis_senseboard.ipynb`**  
   - Statistical analysis focusing only on Senseboard data, using loadcell information.  

7. **`MainReport.ipynb`**  
   - Generates a comprehensive report.  
   - Compares KPI metrics for each straight run between riders.  

8. **`Senseboard_Report.ipynb`**  
   - Generates visualizations from Senseboard data.  

9. **`weight_ttest.ipynb`**  
   - Performs statistical t-tests on the effect of rider weight on performance.  

10. **`mast_ttest.ipynb`**  
    - Performs statistical t-tests on the effect of the foil (Chubanga vs Levi) on performance.  

---

### Other Files
- `analysis.py`, `cog_analysis.py`, `report_fct.py`: Python utility scripts.  
- `summary.json`, `summary_enriched.json`: Intermediate files containing run information.  
- `all_data.csv`, `all_data_enriched.csv`: Consolidated datasets used for analysis.  

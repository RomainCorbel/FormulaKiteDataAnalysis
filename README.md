# Formula Kite Data Analysis  

This repository contains the datasets and analyses from the **Formula Kite testing campaign** held in **Port Camargue (France), June 6–11, 2025**.  
The project focuses on two main aspects of performance:  
- Straight runs (upwind & downwind speed testing)  
- Maneuvers (tacks & gybes)  

The datasets are not stored directly in this GitHub repository because of their large file sizes, which would make the repository heavy and inefficient to clone or update. All raw and pre-processed data are hosted externally on Marco’s drive and must be copied directly into the FormulaKiteDataAnalysis/ folder in order for the analysis scripts and notebooks
---

## Repository Structure  

For both Maneuvers and Straight lines, the data structure always includes:  
- **CSV files** (`Gian.csv`, `Karl.csv`, `SenseBoard.csv`) containing Vakaros measurements for each run  
- **SenseBoard logs** (`SenseBoard_log_modified_… .xlsx`) with data of the senseboard (especially load cells) covering the entire session (by day and not by run) 
- **Interview files** (`Interview … .xlsx`) providing complementary information such as total weight, equipment setup, and other contextual details  

```
FormulaKiteDataAnalysis/
├── README.md
├── Data_Sailnjord/              # processed datasets ready for Python analysis
│   ├── Maneuvers/
│   │   ├── 08_06/
│   │   │   ├── Gian/ ── 08_06_Run{1..5}/ (SenseBoard.csv)
│   │   │   ├── Karl/ ── 08_06_Run{1..6}/ (Karl Maeder.csv)
│   │   │   ├── senseboard_log/ (SenseBoard_log_modified_250608.xlsx)
│   │   │   └── Interview and equipment/ (Interview Karl 250608.xlsx | Interview SenseBoard 250608.xlsx)
│   │   └── 11_06/
│   │       ├── Gian/ ── 11_06_Run{1..5}/ (Gian Stragiotti.csv | SenseBoard.csv)
│   │       ├── Karl/ ── 11_06_Run{1..6}/ (Karl Maeder.csv)
│   │       ├── senseboard_log/ (…250611….xlsx)
│   │       └── Interview and equipment/ (…250611….xlsx)
│   │
│   └── Straight_lines/
│       ├── 06_06/ ── Interview and equipment + senseboard_log + 06_06_Run{1..8}/ (Gian|Karl|SenseBoard.csv)
│       ├── 07_06/ ── Interview and equipment + senseboard_log + 07_06_Run{1..10}/ (Gian|Karl|SenseBoard.csv)
│       ├── 09_06/ ── Interview and equipment + senseboard_log + 09_06_Run{1..11}/ (Karl|SenseBoard.csv)
│       └── 10_06/ ── Interview and equipment + senseboard_log + 10_06_Run{1..10}/ (Gian|Karl|SenseBoard.csv)
│
├── Maneuvers/
│   ├── analysis notebooks & scripts (addsenseboarddata.ipynb, MainCOG.ipynb,
│   │   Report_*_*.ipynb, cog_analysis.py, report_fct.py, Report_with_eval.py…)
│   ├── aggregated data (all_data*.csv, summary*.json)
│   ├── old/ (legacy notebooks)
│   └── __pycache__/
│
├── Straight Run/
│   ├── analysis notebooks (MainReport.ipynb, analysis*.ipynb, *ttest.ipynb…)
│   ├── scripts (analysis.py, cog_analysis.py, report_fct.py, merge_all.ipynb…)
│   ├── aggregated data (all_data*.csv, summary*.json)
│   ├── archives/ (rendered reports, html/pdf, older versions)
│   └── __pycache__/
│
├── Test Kite Port Camargue/     # pre-Python processed materials
│   ├── campaign documents (equipment lists, protocols, pilot logs)
│   ├── Raw data/ organized by Day1..Day6
│   │   ├── SenseBoard bin/ (raw .bin files)
│   │   ├── SenseBoard post-processing/ (scripts + _imu_log_*.csv, test_forces_*.csv)
│   │   ├── Vakaros csv/ (raw exports)
│   │   ├── Vakaros post-processing/ (Cells Renamed/*, Lines/*.xlsx)
│   │   └── Wind and Marks/ (wind & marks logs *.csv)
│   └── Detrending filter/ (scripts + correction spreadsheets)
│
└── __pycache__/
```

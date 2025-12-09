# Formula Kite Data Analysis  

This repository contains the analyses from the **Formula Kite testing campaign** held in **Port Camargue (France), June 6–11, 2025**. Note that the datasets are not stored directly in this GitHub repository because of their large file sizes, which would make the repository heavy and inefficient to clone or update. All raw and pre-processed data are hosted externally on Marco’s drive and the pre-processed folder: Data_Sailnjord must be copied directly into the FormulaKiteDataAnalysis/ folder to run the analysis scripts and notebooks.

The project focuses on two main aspects of performance:  
- Straight runs (upwind & downwind speed testing)  
- Maneuvers (tacks & gybes)  
---

## Repository Structure  

For both Maneuvers and Straight lines, the data structure always includes:  
- **CSV files** (`Gian.csv`, `Karl.csv`, `SenseBoard.csv`) containing Vakaros measurements for each run  
- **SenseBoard logs** (`SenseBoard_log_modified_… .xlsx`) with data of the senseboard (especially load cells) covering the entire session (by day and not by run) 
- **Interview files** (`Interview … .xlsx`) providing complementary information such as total weight, equipment setup, and other contextual details  

```
FormulaKiteDataAnalysis/
├── README.md
│
├── Data_Sailnjord/                         # processed datasets ready for Python analysis
│   └── Port Camargue June 2025/
│       │
│       ├── Maneuvers/
│       │   ├── 08_06_2025/
│       │   │   ├── Gian/
│       │   │   │   └── 08_06_2025_Run{1..5}/ (SenseBoard.csv)
│       │   │   ├── Karl/
│       │   │   │   └── 08_06_2025_Run{1..6}/ (Karl Maeder.csv)
│       │   │   ├── senseboard_log/
│       │   │   │   └── SenseBoard_log_modified_250608.xlsx
│       │   │   └── Interview and equipment/
│       │   │       ├── Interview Karl 250608.xlsx
│       │   │       └── Interview SenseBoard 250608.xlsx
│       │   │
│       │   └── 11_06_2025/
│       │       ├── Gian/
│       │       │   └── 11_06_2025_Run{1..5}/ (Gian Stragiotti.csv | SenseBoard.csv)
│       │       ├── Karl/
│       │       │   └── 11_06_2025_Run{1..6}/ (Karl Maeder.csv)
│       │       ├── senseboard_log/
│       │       │   └── …250611….xlsx
│       │       └── Interview and equipment/
│       │           └── …250611….xlsx
│       │
│       └── Straight_lines/
│           ├── 06_06_2025/
│           │   ├── Interview and equipment/
│           │   ├── senseboard_log/
│           │   └── 06_06_2025_Run{1..8}/ (Gian.csv | Karl.csv | SenseBoard.csv)
│           │
│           ├── 07_06_2025/
│           │   ├── Interview and equipment/
│           │   ├── senseboard_log/
│           │   └── 07_06_2025_Run{1..10}/ (Gian.csv | Karl.csv | SenseBoard.csv)
│           │
│           ├── 09_06_2025/
│           │   ├── Interview and equipment/
│           │   ├── senseboard_log/
│           │   └── 09_06_2025_Run{1..11}/ (Karl.csv | SenseBoard.csv)
│           │
│           └── 10_06_2025/
│               ├── Interview and equipment/
│               ├── senseboard_log/
│               └── 10_06_2025_Run{1..10}/ (Gian.csv | Karl.csv | SenseBoard.csv)
│
├── Maneuvers/                              # Python analysis workspace (maneuvers)
│   ├── analysis notebooks & scripts
│   │   ├── addsenseboarddata.ipynb
│   │   ├── MainCOG.ipynb
│   │   ├── Report_*_*.ipynb
│   │   ├── cog_analysis.py
│   │   ├── report_fct.py
│   │   └── Report_with_eval.py
│   ├── aggregated data/
│   │   ├── all_data*.csv
│   │   └── summary*.json
│   ├── old/                               # legacy notebooks
│   └── __pycache__/
│
├── Straight Run/                          # Python analysis workspace (straight runs)
│   ├── analysis notebooks
│   │   ├── MainReport.ipynb
│   │   ├── analysis*.ipynb
│   │   └── *ttest.ipynb
│   ├── scripts
│   │   ├── analysis.py
│   │   ├── cog_analysis.py
│   │   ├── report_fct.py
│   │   └── merge_all.ipynb
│   ├── aggregated data/
│   │   ├── all_data*.csv
│   │   └── summary*.json
│   ├── archives/               
│   └── __pycache__/
│
│
└── __pycache__/
```

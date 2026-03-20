import json
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf

def load_summary_intervals(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def intervals_to_dataframe(summary):
    rows = []

    for run_block in summary:
        run_name = run_block["run"]
        day = "_".join(run_name.split("_")[:3])

        for interval in run_block["intervals"]:
            b = "boat1"

            rows.append({
                "run": run_name,
                "day": day,
                "start_time": interval["start_time"],
                "end_time": interval["end_time"],
                "duration": interval["duration"],
                "leg_type": interval["leg_type"],

                "boat": 1,
                "name": interval[f"{b}_name"],
                "mast": interval[f"{b}_mast_brand"],
                "total_weight": interval[f"{b}_total_weight"],
                "master_leeward": interval[f"{b}_master_leeward"],

                "avg_SOG": interval[f"avg_SOG_{b}"],
                "SOG_var": interval[f"SOG_variation_{b}"],
                "avg_TWS": interval[f"avg TWS {b}"],
                "avg_TWA": interval[f"avg TWA {b}"],
                "SOG_ref": interval[f"{b}_SOG_ref"],
                "pol_ratio": interval[f"{b}_pol_ratio"],

                "stability": interval["stability_score"],
            })

    return pd.DataFrame(rows)
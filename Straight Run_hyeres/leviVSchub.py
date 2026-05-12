import json
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from leviVSchub import *
def load_summary_intervals(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def intervals_to_dataframe(summary):
    rows = []

    for run_block in summary:
        run_name = run_block["run"]
        day = "_".join(run_name.split("_")[:3])

        for interval in run_block["intervals"]:
            for boat_idx in (1, 2):
                b = f"boat{boat_idx}"

                rows.append({
                    "run": run_name,
                    "day": day,
                    "start_time": interval["start_time"],
                    "end_time": interval["end_time"],
                    "duration": interval["duration"],
                    "leg_type": interval["leg_type"],

                    "boat": boat_idx,
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

def build_paired_intervals(df_intervals: pd.DataFrame) -> pd.DataFrame:
    key_cols = ["run", "start_time", "end_time", "leg_type"]

    b1 = df_intervals[df_intervals["boat"] == 1].drop(columns=["boat"]).copy()
    b2 = df_intervals[df_intervals["boat"] == 2].drop(columns=["boat"]).copy()

    b1 = b1.rename(columns={c: f"boat1_{c}" for c in b1.columns if c not in key_cols})
    b2 = b2.rename(columns={c: f"boat2_{c}" for c in b2.columns if c not in key_cols})

    paired = pd.merge(b1, b2, on=key_cols, how="inner")

    paired["d_pol_ratio"] = paired["boat2_pol_ratio"] - paired["boat1_pol_ratio"]
    paired["d_avg_SOG"] = paired["boat2_avg_SOG"] - paired["boat1_avg_SOG"]

    paired["d_avg_SOG_mast"] = np.where(
        paired["boat1_mast"] == "Levi",
        paired["boat1_avg_SOG"] - paired["boat2_avg_SOG"],
        paired["boat2_avg_SOG"] - paired["boat1_avg_SOG"],
    )

    paired["d_weight_mast"] = np.where(
        paired["boat1_mast"] == "Levi",
        paired["boat1_total_weight"] - paired["boat2_total_weight"],
        paired["boat2_total_weight"] - paired["boat1_total_weight"],
    )
    paired["levi_rider"] = np.where(
        paired["boat1_mast"] == "Levi",
        paired["boat1_name"],
        paired["boat2_name"],
    )

    return paired

from scipy.stats import ttest_ind

def mean_by_mast(df, label):
    g = (
        df.groupby("mast")
          .agg(
              mean_SOG=("avg_SOG", "mean"),
              mean_TWS=("avg_TWS", "mean"),
              mean_TWA=("avg_TWA", "mean"),
              mean_weight=("total_weight", "mean"),
              n=("avg_SOG", "count"),
          )
    )
    diff = g.loc["Levi", "mean_SOG"] - g.loc["Chub", "mean_SOG"]
    sog_levi = df.loc[df["mast"] == "Levi", "avg_SOG"]
    sog_chub = df.loc[df["mast"] == "Chub", "avg_SOG"]

    tstat, pval = ttest_ind(
        sog_levi,
        sog_chub,
        equal_var=False,
        nan_policy="omit",
    )

    if diff > 0:
        conclusion = "Levi is faster on average in the raw data."
    elif diff < 0:
        conclusion = "Chub is faster on average in the raw data."
    else:
        conclusion = "Both masts have the same average speed in the raw data."

    print("=" * 70)
    print(label)
    print(
        f"Average conditions — "
        f"TWS: {g.loc['Levi','mean_TWS']:.3f}/{g.loc['Chub','mean_TWS']:.3f} kn, "
        f"TWA: {g.loc['Levi','mean_TWA']:.3f}/{g.loc['Chub','mean_TWA']:.3f}°, "
        f"Weight: {g.loc['Levi','mean_weight']:.3f}/{g.loc['Chub','mean_weight']:.3f} kg "
        f"(Levi / Chub)."
    )
    print(
        f"Mean SOG difference (Levi − Chub): {diff:.3f} kn. {conclusion}"
    )
    print(
        f"According to the Welch t-test on avg_SOG: t = {tstat:.2f}, p = {pval:.3f}"
    )
    alpha = 0.05
    if pval < alpha:
            significance = (
                f"The difference in mean SOG is statistically significant "
                f"(p = {pval:.3f} < {alpha})."
            )
    else:
            significance = (
                f"The difference in mean SOG is not statistically significant "
                f"(p = {pval:.3f} ≥ {alpha})."
            )
    print(significance)



def analyze_mast_effect(df_paired: pd.DataFrame) -> dict:
    df = df_paired.copy()
    df["d_avg_SOG_mast"] = np.where(
        df["boat1_mast"] == "Levi",
        df["boat1_avg_SOG"] - df["boat2_avg_SOG"],
        df["boat2_avg_SOG"] - df["boat1_avg_SOG"],
    )

    # Weight difference (Levi − Chub)
    df["d_weight_mast"] = np.where(
        df["boat1_mast"] == "Levi",
        df["boat1_total_weight"] - df["boat2_total_weight"],
        df["boat2_total_weight"] - df["boat1_total_weight"],
    )

    # --------------------------------------------------------
    # OLS model on paired differences
    # --------------------------------------------------------

    model_sog = smf.ols(
        """
        d_avg_SOG_mast ~ 1
            + C(leg_type)
            + C(boat1_master_leeward)
            + C(levi_rider)
        """,
        data=df,
    ).fit(cov_type="HC3")

    return {
        "sog_model": model_sog,
    }


def analyze_mast_effect_by_leg(df_paired: pd.DataFrame, label: str):
    df = df_paired.copy()
    model = smf.ols(
        """
        d_avg_SOG_mast ~ 1
            + C(boat1_master_leeward)
            + C(levi_rider)
        """,   
        data=df,
    ).fit(cov_type="HC3")

    print("=" * 70)
    print(f"Paired OLS — {label}")
    print(f"N paired intervals: {len(df)}")
    print(model.summary())
    print()

    return model
import statsmodels.formula.api as smf
import statsmodels.api as sm

def compute_anova_mast(df):
    formula = (
        "d_avg_SOG_mast ~ "
        "C(leg_type) + "
        "C(boat1_master_leeward) + "
        "d_weight_mast"
    )
    
    model = smf.ols(formula, data=df).fit(cov_type="HC3")
    anova = sm.stats.anova_lm(model, typ=2)
    
    # Effect size: partial eta squared
    anova["partial_eta_sq"] = anova["sum_sq"] / (
        anova["sum_sq"] + model.ssr
    )
    
    return model, anova.sort_values("F", ascending=False)


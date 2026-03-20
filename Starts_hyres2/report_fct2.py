import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# LOADERS
# ============================================================
def filter_interval(df, start, end):
    return df[(df["SecondsSince1970"] >= start) & (df["SecondsSince1970"] <= end)].reset_index(drop=True)

def interval(df, start, end):
    return df[(df.SecondsSince1970 >= start) & (df.SecondsSince1970 <= end)]

def load_run(df_all, run):
    df = df_all[df_all.run == run]

    boats = df.boat_name.unique()
    b1, b2 = boats[0], boats[1]

    df1 = df[df.boat_name == b1]
    df2 = df[df.boat_name == b2]

    # # master comes from CSV
    # if df1.boat_role.mode().iloc[0] != "master":
    #     df1, df2 = df2, df1
    #     b1, b2 = b2, b1

    return {
        "names": (b1, b2),
        "intervals": {
            i: (
                df1[df1.interval_id == i],
                df2[df2.interval_id == i]
            )
            for i in df.interval_id.unique()
        }
    }



# ============================================================
# CORE MATH
# ============================================================

def circ_mean(a):
    r = np.deg2rad(a.dropna())
    return np.rad2deg(np.arctan2(np.sin(r).mean(), np.cos(r).mean())) % 360

def vec(angle):
    r = np.deg2rad(angle)
    return np.array([np.sin(r), np.cos(r)])

def to_m(lat, lon, rlat, rlon):
    dx = (lon - rlon) * 111319.9 * np.cos(np.deg2rad(rlat))
    dy = (lat - rlat) * 111319.9
    return np.array([dx, dy])

'''def gain(df1, df2):
    cog = circ_mean(df1.COG)
    twd = circ_mean(df1.TWD)

    fwd = vec(cog)
    lat = np.array([-fwd[1], fwd[0]])
    vmg = vec(twd)

    rlat, rlon = df2.Lat.iloc[0], df2.Lon.iloc[0]

    p1s = to_m(df1.Lat.iloc[0], df1.Lon.iloc[0], rlat, rlon)
    p1e = to_m(df1.Lat.iloc[-1], df1.Lon.iloc[-1], rlat, rlon)
    p2s = to_m(df2.Lat.iloc[0], df2.Lon.iloc[0], rlat, rlon)
    p2e = to_m(df2.Lat.iloc[-1], df2.Lon.iloc[-1], rlat, rlon)

    prog = (p1e - p2e) - (p1s - p2s)

    return prog @ lat, prog @ fwd, prog @ vmg'''
def gain(df1, df2):
    # --- directions moyennes ---
    cog = circ_mean(df1.COG)
    twd = circ_mean(df1.TWD)

    fwd = vec(cog)
    lat = np.array([-fwd[1], fwd[0]])
    vmg = vec(twd)

    # --- déterminer le sens "vers le vent" ---
    wind_sign = np.sign(np.dot(vmg, lat)) or 1
    lat = wind_sign * lat   # lat pointe maintenant TOUJOURS vers le vent

    # --- positions relatives ---
    rlat, rlon = df2.Lat.iloc[0], df2.Lon.iloc[0]

    p1s = to_m(df1.Lat.iloc[0],  df1.Lon.iloc[0],  rlat, rlon)
    p1e = to_m(df1.Lat.iloc[-1], df1.Lon.iloc[-1], rlat, rlon)
    p2s = to_m(df2.Lat.iloc[0],  df2.Lon.iloc[0],  rlat, rlon)
    p2e = to_m(df2.Lat.iloc[-1], df2.Lon.iloc[-1], rlat, rlon)

    initial_rel = p1s - p2s
    final_rel   = p1e - p2e
    progress    = final_rel - initial_rel

    # --- durée ---
    duration_min = (df1.SecondsSince1970.iloc[-1]
                    - df1.SecondsSince1970.iloc[0]) / 60
    if duration_min <= 0:
        return np.nan, np.nan, np.nan

    # --- gains par minute ---
    lat_gain = (progress @ lat) / duration_min
    fwd_gain = (progress @ fwd) / duration_min
    vmg_gain = (progress @ vmg) / duration_min

    return lat_gain, fwd_gain, vmg_gain

'''
# ============================================================
# PLOTS
# ============================================================

def plot_top5_grid(top, df_all, colors=None):
    """
    3x5 grid:
      Row 0: TWS vs t
      Row 1: TWD vs t
      Row 2: track Lon vs Lat
    Each column has a fixed color. Ranked boat = solid, opponent = dashed (same color).
    """
    if colors is None:
        # 5 couleurs fixes (change-les comme tu veux)
        colors = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"]

    ncols = 5
    fig, axs = plt.subplots(3, ncols, figsize=(3.2*ncols, 6.2), constrained_layout=True)

    # axs shape safety (si ncols == 1)
    if ncols == 1:
        axs = np.array(axs).reshape(3, 1)

    for col in range(ncols):
        r = top.iloc[col]
        color = colors[col % len(colors)]

        run = r.Run.split(" (")[0]
        interval_id = int(r.Run.split("interval ")[1][:-1])

        data = load_run(df_all, run)
        df1, df2 = data["intervals"][interval_id]

        # identifier le "ranked boat" (celui de la ligne top)
        ranked_name = r.rider_name
        if df1.boat_name.mode().iloc[0] == ranked_name:
            d_rank, d_opp = df1, df2
        else:
            d_rank, d_opp = df2, df1

        # temps relatif
        t0 = min(d_rank.SecondsSince1970.iloc[0], d_opp.SecondsSince1970.iloc[0])
        tr = d_rank.SecondsSince1970 - t0
        to = d_opp.SecondsSince1970 - t0
        t_start = d_rank.ISODateTimeUTC.iloc[0]
        t_end   = d_rank.ISODateTimeUTC.iloc[-1]

        # ---- Row 1: TWS ----
        ax = axs[0, col]
        ax.plot(tr, d_rank.TWS, color=color, lw=1.5)
        ax.set_title(
            f"#{int(r['rank'])} | {run}\n{r.rider_name} | {r.role}",
            fontsize=8
        )
        ax.set_ylabel("TWS" if col == 0 else "")
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=7)

        # ---- Row 2: TWD ----
        ax = axs[1, col]
        twd_rad = np.deg2rad(d_rank.TWD)
        twd_unwrap_rad = np.unwrap(twd_rad)
        twd_unwrap_deg = np.rad2deg(twd_unwrap_rad)
        ax.plot(tr, twd_unwrap_deg, color=color, lw=1.5)
        ax.set_ylabel("TWD" if col == 0 else "")
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=7)

        # ---- Row 3: Track Lon/Lat ----
        ax = axs[2, col]

        # trajectoire
        ax.plot(d_rank.Lon, d_rank.Lat, color=color, lw=1.5)

        # point de départ
        ax.scatter(d_rank.Lon.iloc[0], d_rank.Lat.iloc[0],
                color=color, s=20, marker="o")

        ax.set_aspect("equal", adjustable="datalim")
        ax.set_ylabel("Lat/Lon" if col == 0 else "")
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=7)

    # petite légende globale (simple)
    fig.suptitle("Top 5", fontsize=10)
    plt.show()

from statsmodels.nonparametric.smoothers_lowess import lowess
def plot_top5_overlaid_metrics(top, df_all, smooth_frac, colors=None):
    """
    1x5 plot:
    VMG | Heel | Trim | Central | Feet load

    LOWESS smoothing with per-metric frac parameter.
    No border data loss.
    """

    if colors is None:
        colors = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"]

    metrics = [
        ("VMG", "VMG"),
        ("Heel_Lwd", "Heel"),
        ("Trim", "Trim"),
        ("central", "Central"),
        ("feet_load", "Feet load"),
    ]

    fig, axs = plt.subplots(1, 5, figsize=(16, 3.5), constrained_layout=True)

    for idx, r in top.iterrows():
        color = colors[idx % len(colors)]

        run = r.Run.split(" (")[0]
        interval_id = int(r.Run.split("interval ")[1][:-1])

        data = load_run(df_all, run)
        df1, df2 = data["intervals"][interval_id]

        # ranked boat
        if df1.boat_name.mode().iloc[0] == r.rider_name:
            d = df1.copy()
        else:
            d = df2.copy()

        if len(d) < 10:
            continue

        # --- time (relative) ---
        t = (d.SecondsSince1970 - d.SecondsSince1970.iloc[0]).values

        for ax, (colname, label) in zip(axs, metrics):

            if colname not in d.columns or colname not in smooth_frac:
                continue

            y = d[colname].values
            mask = ~np.isnan(y)

            if mask.sum() < 10:
                continue

            frac = smooth_frac[colname]

            y_fit = lowess(
                y[mask],
                t[mask],
                frac=frac,
                return_sorted=False
            )

            ax.plot(
                t[mask],
                y_fit,
                color=color,
                lw=1.5
            )

            ax.set_title(
                f"{label}\n(frac={frac:.2f})",
                fontsize=9
            )
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=7)

    axs[0].set_ylabel("Value", fontsize=8)
    fig.suptitle("Top 5 – Overlaid metrics (LOWESS smoothing)", fontsize=10)
    plt.show()

from matplotlib.collections import LineCollection

def plot_rank_detailed(top, df_all, smooth_frac):
    """
    For EACH row in `top`:
      - One figure with 2x5 subplots
      - Row 1: Lat/Lon track colored by metric
      - Row 2: metric vs time (raw transparent + smoothed solid)
    """

    metrics = [
        ("VMG", "VMG"),
        ("Heel_Lwd", "Heel"),
        ("Trim", "Trim"),
        ("central", "Central"),
        ("feet_load", "Feet load"),
    ]

    cmaps = ["viridis", "plasma", "coolwarm", "cividis", "magma"]

    for _, r in top.iterrows():

        run = r.Run.split(" (")[0]
        interval_id = int(r.Run.split("interval ")[1][:-1])

        data = load_run(df_all, run)
        df1, df2 = data["intervals"][interval_id]

        # ranked boat only
        if df1.boat_name.mode().iloc[0] == r.rider_name:
            d = df1.copy()
        else:
            d = df2.copy()

        if len(d) < 20:
            continue

        # time
        t = d.SecondsSince1970.values
        t = t - t[0]

        fig, axs = plt.subplots(
            2, 5,
            figsize=(18, 7),
            constrained_layout=True
        )

        fig.suptitle(
            f"Rank #{int(r['rank'])} – {r['rider_name']}\n{run} (interval {interval_id})",
            fontsize=11
        )

        # ======================================================
        # ROW 1 — TRACKS COLORED BY METRIC
        # ======================================================
        lon = d.Lon.values
        lat = d.Lat.values
        points = np.array([lon, lat]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        for col, ((colname, label), cmap) in enumerate(zip(metrics, cmaps)):
            ax = axs[0, col]

            if colname not in d.columns:
                ax.axis("off")
                continue
            y = d[colname].values
            mask = ~np.isnan(y)

            # smooth values ALONG the track (same logic as time plots)
            frac = smooth_frac.get(colname, 0.3)

            y_smooth = np.full_like(y, np.nan, dtype=float)
            if mask.sum() >= 10:
                y_smooth[mask] = lowess(
                    y[mask],
                    t[mask],
                    frac=frac,
                    return_sorted=False
                )

            # LineCollection needs N-1 values (per segment)
            values = y_smooth[:-1]

            vmin, vmax = np.nanpercentile(values, [5, 95])

            lc = LineCollection(
                segments,
                cmap=cmap,
                array=values,
                linewidth=6,
                norm=plt.Normalize(vmin=vmin, vmax=vmax)
            )
            ax.add_collection(lc)
            ax.scatter(lon[0], lat[0], s=25, color="black", zorder=3)

            ax.set_aspect("equal", adjustable="datalim")
            ax.set_title(label, fontsize=9)
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=7)

            plt.colorbar(lc, ax=ax, fraction=0.046, pad=0.04)

        # ======================================================
        # ROW 2 — TIME SERIES (RAW + SMOOTH)
        # ======================================================
        for col, (colname, label) in enumerate(metrics):
            ax = axs[1, col]

            if colname not in d.columns or colname not in smooth_frac:
                ax.axis("off")
                continue

            y = d[colname].values
            mask = ~np.isnan(y)

            if mask.sum() < 10:
                ax.axis("off")
                continue

            # raw
            ax.plot(
                t[mask],
                y[mask],
                color="gray",
                alpha=0.25,
                lw=1
            )

            # smooth
            frac = smooth_frac[colname]
            y_smooth = lowess(
                y[mask],
                t[mask],
                frac=frac,
                return_sorted=False
            )

            ax.plot(
                t[mask],
                y_smooth,
                lw=2
            )

            ax.set_title(f"{label} vs time", fontsize=9)
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=7)

            if col == 0:
                ax.set_ylabel("Value", fontsize=8)

        plt.show()'''


# ============================================================
# PLOTS
# ============================================================
from statsmodels.nonparametric.smoothers_lowess import lowess

def lowess_smooth(y, t, frac):
    y_smooth = lowess(
        y,
        t,
        frac=frac,
        return_sorted=False
    )
    return y_smooth

def plot_top5_grid(top, df_all, colors=None):
    """
    3x5 grid:
      Row 0: TWS vs t
      Row 1: TWD vs t
      Row 2: track Lon vs Lat
    Each column has a fixed color. Ranked boat = solid, opponent = dashed (same color).
    """
    if colors is None:
        # 5 couleurs fixes (change-les comme tu veux)
        colors = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"]

    ncols = 5
    fig, axs = plt.subplots(3, ncols, figsize=(3.2*ncols, 6.2), constrained_layout=True)

    # axs shape safety (si ncols == 1)
    if ncols == 1:
        axs = np.array(axs).reshape(3, 1)

    for col in range(ncols):
        r = top.iloc[col]
        color = colors[col % len(colors)]

        run = r.Run.split(" (")[0]
        interval_id = int(r.Run.split("interval ")[1][:-1])

        data = load_run(df_all, run)
        df1, df2 = data["intervals"][interval_id]

        # identifier le "ranked boat" (celui de la ligne top)
        ranked_name = r.rider_name
        if df1.boat_name.mode().iloc[0] == ranked_name:
            d_rank, d_opp = df1, df2
        else:
            d_rank, d_opp = df2, df1

        # temps relatif
        t0 = min(d_rank.SecondsSince1970.iloc[0], d_opp.SecondsSince1970.iloc[0])
        tr = d_rank.SecondsSince1970 - t0
        to = d_opp.SecondsSince1970 - t0
        t_start = d_rank.ISODateTimeUTC.iloc[0]
        t_end   = d_rank.ISODateTimeUTC.iloc[-1]

        # ---- Row 1: TWS ----
        ax = axs[0, col]
        ax.plot(tr, d_rank.TWS, color=color, lw=1.5)
        ax.set_title(
            f"#{int(r['rank'])} | {run}\n{r.rider_name} | {r.role}",
            fontsize=8
        )
        ax.set_ylabel("TWS" if col == 0 else "")
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=7)

        # ---- Row 2: TWD ----
        ax = axs[1, col]
        twd_rad = np.deg2rad(d_rank.TWD)
        twd_unwrap_rad = np.unwrap(twd_rad)
        twd_unwrap_deg = np.rad2deg(twd_unwrap_rad)
        ax.plot(tr, twd_unwrap_deg, color=color, lw=1.5)
        ax.set_ylabel("TWD" if col == 0 else "")
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=7)

        # ---- Row 3: Track Lon/Lat ----
        ax = axs[2, col]

        # trajectoire
        ax.plot(d_rank.Lon, d_rank.Lat, color=color, lw=1.5)

        # point de départ
        ax.scatter(d_rank.Lon.iloc[0], d_rank.Lat.iloc[0],
                color=color, s=20, marker="o")

        ax.set_aspect("equal", adjustable="datalim")
        ax.set_ylabel("Lat/Lon" if col == 0 else "")
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=7)

    # petite légende globale (simple)
    fig.suptitle("Top 5", fontsize=10)
    plt.show()

from statsmodels.nonparametric.smoothers_lowess import lowess
def plot_top5_overlaid_metrics(top, df_all, smooth_frac, colors=None):
    """
    1x5 plot:
    VMG | Heel | Trim | Central | Feet load

    LOWESS smoothing with per-metric frac parameter.
    No border data loss.
    """

    if colors is None:
        colors = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"]

    metrics = [
        ("VMG", "VMG"),
        ("Heel_Lwd", "Heel"),
        ("Trim", "Trim"),
        ("central", "Central"),
    ]

    fig, axs = plt.subplots(1, 4, figsize=(16, 3.5), constrained_layout=True)

    for idx, r in top.iterrows():
        color = colors[idx % len(colors)]

        run = r.Run.split(" (")[0]
        interval_id = int(r.Run.split("interval ")[1][:-1])

        data = load_run(df_all, run)
        df1, df2 = data["intervals"][interval_id]

        # ranked boat
        if df1.boat_name.mode().iloc[0] == r.rider_name:
            d = df1.copy()
        else:
            d = df2.copy()

        if len(d) < 10:
            continue

        # --- time (relative) ---
        t = (d.SecondsSince1970 - d.SecondsSince1970.iloc[0]).values

        for ax, (colname, label) in zip(axs, metrics):

            if colname not in d.columns or colname not in smooth_frac:
                continue

            y = d[colname].values
            frac = smooth_frac[colname]

            y_smooth = lowess_smooth(y, t, frac)

            mask = ~np.isnan(y_smooth)
            ax.plot(t[mask], y_smooth[mask], color=color, lw=1.5)

            ax.set_title(
                f"{label}",
                fontsize=9
            )
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=7)

    axs[0].set_ylabel("Value", fontsize=8)
    fig.suptitle("Top 5 – Overlaid metrics (LOWESS smoothing)", fontsize=10)
    plt.show()

from matplotlib.collections import LineCollection

def plot_rank_detailed(top, df_all, smooth_frac):
    """
    For EACH row in `top`:
      - One figure with 2x5 subplots
      - Row 1: Lat/Lon track colored by metric
      - Row 2: metric vs time (raw transparent + smoothed solid)
    """

    metrics = [
        ("VMG", "VMG"),
        ("Heel_Lwd", "Heel"),
        ("Trim", "Trim"),
        ("central", "Central"),
    ]

    cmaps = ["viridis", "plasma", "coolwarm", "cividis", "magma"]

    for _, r in top.iterrows():

        run = r.Run.split(" (")[0]
        interval_id = int(r.Run.split("interval ")[1][:-1])

        data = load_run(df_all, run)
        df1, df2 = data["intervals"][interval_id]

        # ranked boat only
        if df1.boat_name.mode().iloc[0] == r.rider_name:
            d = df1.copy()
        else:
            d = df2.copy()

        if len(d) < 20:
            continue

        # time
        t = d.SecondsSince1970.values
        t = t - t[0]

        fig, axs = plt.subplots(
            2, 4,
            figsize=(18, 7),
            constrained_layout=True
        )

        fig.suptitle(
            f"Rank #{int(r['rank'])} – {r['rider_name']}\n{run}",
            fontsize=11
        )

        # ======================================================
        # ROW 1 — TRACKS COLORED BY METRIC
        # ======================================================
        lon = d.Lon.values
        lat = d.Lat.values
        points = np.array([lon, lat]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        for col, ((colname, label), cmap) in enumerate(zip(metrics, cmaps)):
            ax = axs[0, col]

            if colname not in d.columns:
                ax.axis("off")
                continue
            y = d[colname].values
            mask = ~np.isnan(y)

            # smooth values ALONG the track (same logic as time plots)
            frac = smooth_frac[colname]
            y_smooth = lowess_smooth(y, t, frac)
            values = y_smooth[:-1]

            vmin, vmax = np.nanpercentile(values, [5, 95])

            lc = LineCollection(
                segments,
                cmap=cmap,
                array=values,
                linewidth=6,
                norm=plt.Normalize(vmin=vmin, vmax=vmax)
            )
            ax.add_collection(lc)
            ax.scatter(lon[0], lat[0], s=25, color="black", zorder=3)

            ax.set_aspect("equal", adjustable="datalim")
            ax.set_title(label, fontsize=9)
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=7)

            plt.colorbar(lc, ax=ax, fraction=0.046, pad=0.04)

        # ======================================================
        # ROW 2 — TIME SERIES (RAW + SMOOTH)
        # ======================================================
        for col, (colname, label) in enumerate(metrics):
            ax = axs[1, col]

            if colname not in d.columns or colname not in smooth_frac:
                ax.axis("off")
                continue

            y = d[colname].values

            # raw
            mask = ~np.isnan(y)
            ax.plot(t[mask], y[mask], color="gray", alpha=0.25, lw=1)

            # smooth
            frac = smooth_frac[colname]
            y_smooth = lowess_smooth(y, t, frac)

            mask = ~np.isnan(y_smooth)
            ax.plot(t[mask], y_smooth[mask], lw=2)


            ax.set_title(f"{label} vs time", fontsize=9)
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=7)

            if col == 0:
                ax.set_ylabel("Value", fontsize=8)

        plt.show()

# ============================================================
# PIPELINE
# ============================================================
def run_all(df_all, summary, TOP_N=5, onlyUpwind=False, onlyDownwind=False, rider_name=None,smooth_frac=None):
    rows = []

    for run in summary:
        data = load_run(df_all, run)
        n1, n2 = data["names"]

        for i, (df1, df2) in data["intervals"].items():

            # ==================================
            # INTERVAL FILTER
            # ==================================
            leg_type = df1.leg_type.mode().iloc[0]
            if onlyUpwind and leg_type != "upwind":
                continue
            if onlyDownwind and leg_type != "downwind":
                continue    
            lat_gain_12, fwd_gain_12, vmg_gain_12 = gain(df1, df2)
            for df_boat, sign in [(df1, +1), (df2, -1)]:
                boat_name = df_boat.boat_name.mode().iloc[0]
                if rider_name is not None and boat_name != rider_name:
                    continue
                rows.append({
                    "Run": f"{run} (interval {i})",
                    "rider_name": df_boat.boat_name.mode().iloc[0],
                    "role": df_boat.boat_role.mode().iloc[0],
                    
                    "pol_ratio": df_boat.pol_ratio.mean(),

                    "TWS": df_boat.TWS.mean(),
                    "avg_vmg": df_boat.VMG.mean(),
                    "avg_sog": df_boat.SOG.mean(),
                    "avg_cog": circ_mean(df_boat.COG),
                    "cog_std": df_boat.COG.std(),
                    "avg_rot": df_boat.ROT.mean(),
                    "heel": df_boat.Heel_Lwd.mean(),
                    "trim": df_boat.Trim.mean(),

                    "central": df_boat.central.mean(),
                    "lateral": df_boat.lateral.mean(),

                    "foil_brand": df_boat.mast_brand.mode().iloc[0],

                    "gain_per_min_vmg": sign * vmg_gain_12,
                    "gain_per_min_forward": sign * fwd_gain_12,
                    "gain_per_min_lateral": sign * lat_gain_12,
                })



    df = pd.DataFrame(rows)

    # ==================================
    # SORT + RANK (ONLY pol_ratio)
    # ==================================
    df = df.sort_values("pol_ratio", ascending=False).reset_index(drop=True)
    df.insert(0, "rank", np.arange(1, len(df) + 1))

    top = df.head(TOP_N)

    display(top)
    top5 = top.head(5)
    plot_top5_grid(top5, df_all)

    plot_top5_overlaid_metrics(top5, df_all, smooth_frac=smooth_frac)

    plot_rank_detailed(
        top5,
        df_all,
        smooth_frac=smooth_frac
    ) 

    return top

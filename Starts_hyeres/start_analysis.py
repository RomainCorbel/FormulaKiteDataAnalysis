from time import time

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def extract_boat_name(file_path: str) -> str:
    """
    Extract boat name from CSV file name (without extension)
    """
    return os.path.splitext(os.path.basename(file_path))[0]


import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec

def plot_full_trajectories(
    boat1_df,
    boat1_name="boat1",
    run_folder=None
):
    colors = {boat1_name: 'green'}

    plt.figure(figsize=(15, 8))

    # Trajectoires des bateaux
    # plt.scatter(boat1_df['Lon'], boat1_df['Lat'], c=colors[boat1_name], marker='x', s=10, label=f'Trajectory {boat1_name}')

    # 2. Add a point at the beginning
    beginning_lon = boat1_df['Lon'].iloc[0]
    beginning_lat = boat1_df['Lat'].iloc[0]
    plt.scatter(beginning_lon, beginning_lat, 
                color='red', marker='o', s=100, edgecolors='black', zorder=5,
                label='Initial Position')
    # 3. Plot the t=0s point with a X marker
    # start_lon = boat1_df['Lon'][boat1_df['RelativeTime'] == 0].iloc[0]
    # start_lat = boat1_df['Lat'][boat1_df['RelativeTime'] == 0].iloc[0]
    idx_start = (boat1_df['RelativeTime'] - 0).abs().idxmin() # Better because sometimes there is no exact 0s point
    start_lon = boat1_df.loc[idx_start, 'Lon']
    start_lat = boat1_df.loc[idx_start, 'Lat']
    plt.scatter(start_lon, start_lat, 
                color='red', marker='X', s=100, edgecolors='black', zorder=5,
                label='Race starting Point')
    # 4. Wind direction
    # Direction du vent (TWD moyen)
    twd_rad = np.deg2rad(boat1_df.TWD.mean())
    plt.annotate('', 
                xy=(0.15, 0.8),             # Pointe vers le bas de la zone de texte
                xycoords='axes fraction', 
                xytext=(0.15 + 0.1*np.sin(twd_rad), 0.75 + 0.1*np.cos(twd_rad)), 
                arrowprops=dict(arrowstyle='->', color='blue', lw=2)) # Style '->' pointe vers xy
    
    plt.text(0.15, 0.85, f"Wind direction: {np.rad2deg(twd_rad):.1f}°", color='blue', transform=plt.gca().transAxes, 
            fontsize=8, fontweight='bold', ha='center')

    # 5. Color traj by SOG
    sc = plt.scatter(boat1_df['Lon'], boat1_df['Lat'], 
                     c=boat1_df['SOG_smoothed'], # Couleur basée sur la vitesse lissée
                     cmap='jet',                 # Palette du bleu (lent) au rouge (rapide)
                     s=15,                       # Taille des points
                     edgecolors='none', 
                     alpha=0.8)
    
    # Ajout de la barre de légende pour les couleurs
    cbar = plt.colorbar(sc)
    cbar.set_label('Speed Over Ground (kts)')

    
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Start Analysis - Trajectory' + (f' - {run_folder}'))
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def load_boat_data(boat1_path: str) -> tuple[pd.DataFrame, pd.DataFrame, str, str]:
    """
    Load boat data from CSV files and extract boat names.
    Returns dataframes and corresponding boat names.
    """
    boat1_df = pd.read_csv(boat1_path)

    boat1_name = extract_boat_name(boat1_path)

    return boat1_df, boat1_name

def compute_polar_ratio(boat1_df: pd.DataFrame, polar_path: str):

    from scipy.interpolate import RegularGridInterpolator

    # --- Charger la polaire ---
    sog_ref_df = pd.read_csv(polar_path, index_col=0)

    sog_ref_df.index = pd.to_numeric(sog_ref_df.index)
    sog_ref_df.columns = pd.to_numeric(sog_ref_df.columns)

    tws_vals = sog_ref_df.index.values
    twa_vals = sog_ref_df.columns.values
    Z = sog_ref_df.values

    interp = RegularGridInterpolator(
        (tws_vals, twa_vals),
        Z,
        bounds_error=False,
        fill_value=None
    )

    # --- Moyennes sur tout le run ---
    avg_twa = abs(boat1_df['TWA'].mean())
    avg_tws = boat1_df['TWS'].mean()
    avg_sog = boat1_df['SOG'].mean()
    avg_twd = boat1_df['TWD'].mean()
    print(f"Avg TWA: {avg_twa:.2f}°, Avg TWS: {avg_tws:.2f} kts, Avg TWD: {avg_twd:.2f}° `\n")
    # --- Clamp TWS dans la polaire ---
    tws_clamped = np.clip(avg_tws, tws_vals.min(), tws_vals.max())

    # --- Interpolation ---
    sog_ref = interp([[tws_clamped, avg_twa]])[0]

    # --- Ratio ---
    polar_ratio = avg_sog / sog_ref * 100 if sog_ref else np.nan

    return {
        "avg_TWA": avg_twa,
        "avg_TWS": avg_tws,
        "avg_SOG": avg_sog,
        "SOG_ref": float(sog_ref),
        "polar_ratio_%": polar_ratio
    }
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def start_analysis(boat1_df: pd.DataFrame, boat1_name: str = "boat1", run_folder: str = None):
    """
    Plot raw and smoothed SOG and compute performance metrics.
    """
    sog_raw = boat1_df['SOG']
    sog_smooth = boat1_df['SOG_smoothed']
    relative_time = boat1_df['RelativeTime']
    # --- 2. METRIC CALCULATIONS ---
    polar = compute_polar_ratio(boat1_df, polar_path)
    sog_ref_val = polar['SOG_ref']
    sog_min, sog_max = sog_smooth.min(), sog_smooth.max()
    
    metric1 = sog_ref_val - sog_max  # Delta Max vs Polar
    metric3 = sog_max - sog_min     # Total Gain
    
    # Time to 98% of Max
    mask_95 = sog_smooth >= 0.98 * sog_max
    metric4 = relative_time[mask_95].iloc[0]
    
    # Mid-SOG and Instant Slope logic
    mid_slope_value = sog_min + (metric3 / 2)
    idx_mid = np.argmin(np.abs(sog_smooth.values - mid_slope_value))
    t_mid = relative_time.iloc[idx_mid]
    v_mid = sog_smooth.iloc[idx_mid]
    
    dt_local = relative_time.iloc[idx_mid + 1] - relative_time.iloc[idx_mid - 1]
    dv_local = sog_smooth.iloc[idx_mid + 1] - sog_smooth.iloc[idx_mid - 1]
    instant_slope = dv_local / dt_local

    # --- 3. PLOTTING ---
    plt.figure(figsize=(15, 8))
    
    # Base Curves
    plt.plot(relative_time, sog_raw, color='blue', alpha=0.3, label='Raw SOG')
    plt.plot(relative_time, sog_smooth, color='green', linewidth=1.5, label='Smoothed SOG')

    # Helper to avoid repetitive styling
    def add_annotated_line(val, mode='h', color='black', text="", x_text=None, y_text=None, ha='left', va='bottom', bbox_edge='none'):
        if mode == 'h':
            plt.axhline(y=val, color=color, linestyle='--', alpha=0.6)
            plt.text(x_text if x_text is not None else relative_time.min(), val, text, 
                     color=color, va=va, ha=ha, fontdict={'size': 11},
                     bbox=dict(facecolor='white', alpha=0.5, edgecolor=bbox_edge))
        else:
            plt.axvline(x=val, color=color, linestyle='--', alpha=0.6)
            plt.text(val, y_text if y_text is not None else plt.ylim()[0], text, 
                     color=color, va=va, ha=ha, fontdict={'size': 11},
                     bbox=dict(facecolor='white', alpha=0.5, edgecolor=bbox_edge))

    # Horizontal Lines
    add_annotated_line(sog_ref_val, 'h', 'red', f' SOG Ref: {sog_ref_val:.2f} kts ')
    add_annotated_line(sog_max, 'h', 'green', f' Max SOG: {sog_max:.2f} kts ')
    add_annotated_line(sog_min, 'h', 'green', f' Min SOG: {sog_min:.2f} kts ')
    # add_annotated_line(mid_slope_value, 'h', 'orange', f' Mid-SOG: {mid_slope_value:.2f} kts ')

    # Vertical Lines
    add_annotated_line(metric4, 'v', 'purple', f"Time to 98% Max SOG: {metric4:.2f} s", y_text=plt.ylim()[0]+1.4, ha='center', bbox_edge='purple')
    add_annotated_line(0, 'v', 'black', "Start of the Race: 0s", y_text=plt.ylim()[0]+0.5, ha='center')
    
    # Special Mid-SOG Time Line
    # t_mid_sog = relative_time[sog_smooth >= mid_slope_value].iloc[0]
    # add_annotated_line(t_mid_sog, 'v', 'orange', f' Time at Mid-SOG: {t_mid_sog:.2f} s ', ha='center')

    # Tangent Segment & Slope
    t_tangent = np.array([t_mid - 1, t_mid + 1])
    v_tangent = instant_slope * (t_tangent - t_mid) + v_mid
    plt.plot(t_tangent, v_tangent, color='orange', linewidth=2)
    plt.scatter([t_mid], [v_mid], color='orange', s=80, zorder=5)
    plt.text(t_mid+2.5, v_mid, f' Slope: {instant_slope:.4f} kts/s ', color='orange', va='bottom', ha='center',
             bbox=dict(facecolor='white', alpha=0.5, edgecolor='orange'), fontdict={'size': 11})

    # Vertical Comparison Bars (Right Side)
    x_max = relative_time.max()
    # Total Change Bar
    plt.vlines(x=x_max * 0.9, ymin=sog_min, ymax=sog_max, colors='darkgreen', linewidth=3)
    plt.text(x_max * 0.9 + 0.5, (sog_min + sog_max) / 2, f' SOG max - SOG min: {metric3:.2f} kts ', 
             color='darkgreen', va='center', ha='left', rotation=90, weight='bold', size=10,
             bbox=dict(facecolor='white', alpha=0.7, edgecolor='darkgreen'))
    
    # Polar Delta Bar
    plt.vlines(x=x_max * 0.8, ymin=sog_ref_val, ymax=sog_max, colors='red', linewidth=3)
    plt.text(x_max * 0.8 + 3, (sog_ref_val + sog_max) / 2 + 0.7, f' SOG ref - SOG max: {metric1:+.2f} kts ', 
             color='red', va='center', ha='right', weight='bold', size=10,
             bbox=dict(facecolor='white', alpha=0.7, edgecolor='red', boxstyle='round,pad=0.3'))

    # Final Polish
    print(f"--- Metrics ---\nSOG_ref_polar - SOG Max: {metric1:.2f} knots\nSlope: {instant_slope:.4f} knots/s\n"
          f"SOG max - SOG min: {metric3:.2f} knots\nTime for 98%: {metric4:.2f} seconds")

    plt.xlabel('Time (seconds from start)')
    plt.ylabel('SOG (knots)')
    plt.title('Start Analysis - SOG - ' + run_folder)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def estimate_sampling_frequency(df: pd.DataFrame) -> float:
    """
    Estimate sampling frequency (Hz) from SecondsSince1970 using median dt.
    """
    dt = df['SecondsSince1970'].diff().dropna()
    median_dt = dt.median()
    if median_dt <= 0:
        return np.nan
    return 1.0 / median_dt

polar_path = "../Data_Sailnjord/lowess_postprocessed.csv" 



from matplotlib.collections import LineCollection
from statsmodels.nonparametric.smoothers_lowess import lowess
def lowess_smooth(y, t, frac):
    if len(y) < 5: return y
    return lowess(y, t, frac=frac, return_sorted=False)
DEFAULT_SMOOTH_FRAC = {"SOG": 0.2, "VMG": 0.2, "ROT": 0.1, "COG": 0.1, "Heel_Lwd": 0.2, "Trim": 0.2}
TOP_COLORS = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"]

def plot_details(boat1_df: pd.DataFrame, boat1_name: str = "boat1", run_folder: str = None, metrics_to_show: list = None, smooth_frac: dict = DEFAULT_SMOOTH_FRAC):
    cmaps = ["viridis", "plasma", "coolwarm"]
    d = boat1_df.copy()
    t_relative = d['RelativeTime'].values
    fig, axs = plt.subplots(2, len(metrics_to_show), figsize=(18, 7), constrained_layout=True)
    fig.suptitle(f"Start Analysis - Details - {run_folder}", 
                    fontsize=15, color='#2c3e50')

    lon, lat = d.Lon.values, d.Lat.values
    points = np.array([lon, lat]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    for col, ((colname, label), cmap) in enumerate(zip(metrics_to_show, cmaps)):
        # --- ROW 1 : TRACK COLORÉE ---
        ax_track = axs[0, col]
        y = d[colname].values
        y = d[colname].ffill().bfill().values
        y_smooth = lowess_smooth(y, t_relative, smooth_frac.get(colname, 0.2))
        
        norm = plt.Normalize(np.nanpercentile(y_smooth, 5), np.nanpercentile(y_smooth, 95))
        lc = LineCollection(segments, cmap=cmap, norm=norm, array=y_smooth[:-1], linewidth=5)
        ax_track.add_collection(lc)
        
        # Repères visuels sur la trace
        ax_track.scatter(lon[0], lat[0], color='black', marker='o', s=40, zorder=5) # Start
        
        ax_track.set_aspect("equal", adjustable="datalim")
        ax_track.set_title(f"{label} on track")
        plt.colorbar(lc, ax=ax_track, fraction=0.046, pad=0.04)

        # --- ROW 2 : TIME SERIES ---
        ax_time = axs[1, col]
        ax_time.plot(t_relative, y, color='gray', alpha=0.8, lw=1) 
        ax_time.plot(t_relative, y_smooth, color=TOP_COLORS[col % len(TOP_COLORS)], lw=2.5) 
        ax_time.set_title(f"{label} vs Time")
        ax_time.grid(True, alpha=0.2)
        ax_time.set_xlabel("Seconds")
    plt.show()

# def plot_details(boat1_df: pd.DataFrame, boat1_name: str = "boat1", run_folder: str = None, metrics_to_show: list = None):
#     """
#     Plots a grid of track maps and time-series for specific performance metrics.
#     """

#     num_metrics = len(metrics_to_show)
#     # Using 'jet' or 'viridis' for consistent mapping
#     cmap_list = ["viridis", "plasma", "coolwarm", "magma", "inferno"]
    
#     # Time relative to the start of this specific dataframe
#     t = boat1_df['RelativeTime'].values
#     lon = boat1_df['Lon'].values
#     lat = boat1_df['Lat'].values

#     fig, axs = plt.subplots(2, num_metrics, figsize=(4 * num_metrics, 8), constrained_layout=True)
#     fig.suptitle(f"Detailed Analysis: {boat1_name} - {run_folder}", fontsize=16, fontweight='bold')

#     for col, colname in enumerate(metrics_to_show):
#         if colname not in boat1_df.columns:
#             print(f"Warning: {colname} not found in DataFrame.")
#             continue

#         data_values = boat1_df[colname].values
#         current_cmap = cmap_list[col % len(cmap_list)]

#         # --- ROW 1: TRACK MAP (Color coded by metric) ---
#         ax_track = axs[0, col]
#         sc = ax_track.scatter(lon, lat, c=data_values, cmap=current_cmap, s=10, alpha=0.7)
        
#         # Add a start marker (black dot)
#         ax_track.scatter(lon[0], lat[0], color='black', marker='o', s=50, zorder=5, label='Start')
        
#         ax_track.set_aspect("equal", adjustable="datalim")
#         ax_track.set_title(f"{colname} on Track", fontweight='bold')
#         ax_track.set_xlabel("Lon")
#         ax_track.set_ylabel("Lat")
#         plt.colorbar(sc, ax=ax_track, shrink=0.6)

#         # --- ROW 2: TIME SERIES ---
#         ax_time = axs[1, col]
#         ax_time.plot(t, data_values, color='gray', alpha=0.4, lw=1, label='Raw')
        
#         # Simple moving average for the "smooth" line (since lowess is external)
#         smoothed_values = boat1_df[colname].rolling(window=10, center=True, min_periods=1).mean()
#         ax_time.plot(t, smoothed_values, color='tab:blue', lw=2, label='Smooth')
        
#         ax_time.set_title(f"{colname} vs Time", fontweight='bold')
#         ax_time.set_xlabel("Seconds from Start")
#         ax_time.set_ylabel(colname)
#         ax_time.grid(True, alpha=0.3)
#         if col == 0: ax_time.legend()

#     plt.show()

def analyze_session(boat1_path: str, smoothing_window_sec: float = 0, min_duration_sec: float = 20.0, sog_derivative_threshold: float = 0.2, run_folder: str = None) -> list[dict]:
    """
    Perform a full analysis of a sailing session given CSV paths for boat1 and boat2.
    Returns a list of the top N longest intervals with avg TWA per boat.
    """
    # Load data
    boat1_df, boat1_name = load_boat_data(boat1_path)

    # --- PATCH : On coupe le DF ici pour tout le reste du script ---
    t_start_abs = boat1_df['SecondsSince1970'].min()
    cut_time = t_start_abs + 60 
    boat1_df = boat1_df[boat1_df['SecondsSince1970'] >= cut_time].copy()
    absolute_start_of_slice = boat1_df['SecondsSince1970'].min()
    reference_zero = absolute_start_of_slice + 15 
    relative_time = boat1_df['SecondsSince1970'] - reference_zero
    boat1_df['RelativeTime'] = relative_time
    # --- Estimate sampling frequencies ---
    freq1 = estimate_sampling_frequency(boat1_df)

    window_boat1 = int(smoothing_window_sec * freq1)

    boat1_df['SOG_smoothed'] = boat1_df['SOG'].rolling(
        window=window_boat1,
        center=True,
        min_periods=1
    ).mean()
    
    plot_full_trajectories(boat1_df, boat1_name, run_folder)
    # print(f"Sampling frequency {boat1_name}: {freq1:.2f} Hz")

    start_analysis(boat1_df, boat1_name, run_folder=run_folder)

    # metrics_to_show = ['F_back', 'F_front', 'central', 'Heel_Abs','Trim']        # trim for Pitch, not super sure about that
    metrics_to_show = [("central", "central"), ("Heel_Lwd", "Heel"), ("Trim", "Trim")]
    # metrics_to_show = [("F_back", "F_back"), ("F_front", "F_front"), ("central", "central"), ("Heel_Abs", "Heel_Abs"), ("Trim", "Trim")] # Board metrics are not in the data... so no F bacj, no F front,
    plot_details(boat1_df, boat1_name, run_folder=run_folder, metrics_to_show=metrics_to_show)
    return
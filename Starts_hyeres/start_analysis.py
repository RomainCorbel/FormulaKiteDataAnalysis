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

    plt.figure(figsize=(10, 8))

    # Trajectoires des bateaux
    plt.scatter(boat1_df['Lon'], boat1_df['Lat'], c=colors[boat1_name], marker='x', s=10, label=f'Trajectory {boat1_name}')
    # 2. Add a point at the beginning
    # We take the first available point in the dataframe
    start_lon = boat1_df['Lon'].iloc[0]
    start_lat = boat1_df['Lat'].iloc[0]
    
    plt.scatter(start_lon, start_lat, 
                color='red', marker='o', s=100, edgecolors='black', zorder=5,
                label='Start Point')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Trajectories' + (f' - {run_folder}'))
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
    print(f"Avg TWA: {avg_twa:.2f}°, Avg TWS: {avg_tws:.2f} kts")
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
    # --- 1. DATA PREPARATION ---
    absolute_start_of_slice = boat1_df['SecondsSince1970'].min()
    reference_zero = absolute_start_of_slice + 15 
    relative_time = boat1_df['SecondsSince1970'] - reference_zero
    
    sog_raw = boat1_df['SOG']
    sog_smooth = boat1_df['SOG_smoothed']
    
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
    add_annotated_line(mid_slope_value, 'h', 'orange', f' Mid-SOG: {mid_slope_value:.2f} kts ')

    # Vertical Lines
    add_annotated_line(metric4, 'v', 'purple', f"Time to 98% Max SOG: {metric4:.2f} s", y_text=plt.ylim()[0]+1.4, ha='center', bbox_edge='purple')
    add_annotated_line(0, 'v', 'black', "Start of the Race: 0s", y_text=plt.ylim()[0]+0.5, ha='center')
    
    # Special Mid-SOG Time Line
    t_mid_sog = relative_time[sog_smooth >= mid_slope_value].iloc[0]
    add_annotated_line(t_mid_sog, 'v', 'orange', f' Time at Mid-SOG: {t_mid_sog:.2f} s ', ha='center')

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
    plt.title('Start Analysis - ' + run_folder)
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

def analyze_session(boat1_path: str, smoothing_window_sec: float = 0, min_duration_sec: float = 20.0, sog_derivative_threshold: float = 0.2, run_folder: str = None) -> list[dict]:
    """
    Perform a full analysis of a sailing session given CSV paths for boat1 and boat2.
    Returns a list of the top N longest intervals with avg TWA per boat.
    """
    # Load data
    boat1_df, boat1_name = load_boat_data(boat1_path)

    # --- PATCH : On coupe le DF ici pour tout le reste du script ---
    t_start_abs = boat1_df['SecondsSince1970'].min()
    # On définit le point de référence à T0 + 75s, mais on garde 15s avant
    # Donc on commence à T0 + 60s
    cut_time = t_start_abs + 60 
    boat1_df = boat1_df[boat1_df['SecondsSince1970'] >= cut_time].copy()
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

    return
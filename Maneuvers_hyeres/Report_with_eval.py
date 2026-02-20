import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from geopy.distance import geodesic
from IPython.display import display
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from geopy.distance import geodesic
from IPython.display import display
from matplotlib.collections import LineCollection
from statsmodels.nonparametric.smoothers_lowess import lowess
# === PARAMETERS ===
FICHIER_CSV = "all_data.csv"
MA_WINDOW = 10  # moving average window size
# === PARAMETERS ===
KNOTS_TO_MS = 0.51444
TOP_COLORS = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"]
DEFAULT_SMOOTH_FRAC = {"SOG": 0.2, "VMG": 0.2, "ROT": 0.1, "COG": 0.1, "Heel_Lwd": 0.2, "Trim": 0.2}
# === LOAD DATA ===
df = pd.read_csv(FICHIER_CSV, low_memory=False)

# -- Plot functions: 

from matplotlib.collections import LineCollection
def lowess_smooth(y, t, frac):
    if len(y) < 5: return y
    return lowess(y, t, frac=frac, return_sorted=False)

def plot_top5_maneuvers_comparison(top_maneuvers):
    """
    Affiche les 5 trajectoires (avec sens et vent) 
    + 3 graphs superposés (SOG, COG, ROT) avec Moving Average/Lowess.
    """
    fig = plt.figure(figsize=(20, 10), constrained_layout=True)
    gs = fig.add_gridspec(2, 5)

    # --- LIGNE 1 : LES 5 TRAJECTOIRES INDIVIDUELLES ---
    for i, res in enumerate(top_maneuvers):
        ax = fig.add_subplot(gs[0, i])
        d = res['maneuver_data']
        color = TOP_COLORS[i]

        # Trajectoire
        ax.plot(d.Lon, d.Lat, color=color, lw=2, label=f"Rank {i+1}")
        
        # Marqueurs début (boule) et fin (triangle/flèche)
        ax.scatter(d.Lon.iloc[0], d.Lat.iloc[0], color='black', marker='o', s=20, label='Start')
    # Direction du vent (TWD moyen)
        twd_rad = np.deg2rad(d.TWD.mean())
        
        # Correction de la flèche :
        # xy est la POINTE de la flèche (le point d'impact du vent)
        # xytext est l'ORIGINE (d'où vient le vent)
        ax.annotate('', 
                    xy=(0.15, 0.8),             # Pointe vers le bas de la zone de texte
                    xycoords='axes fraction', 
                    xytext=(0.15 + 0.1*np.sin(twd_rad), 0.75 + 0.1*np.cos(twd_rad)), 
                    arrowprops=dict(arrowstyle='->', color='blue', lw=2)) # Style '->' pointe vers xy
        
        ax.text(0.15, 0.85, "Wind direction", color='blue', transform=ax.transAxes, 
                fontsize=8, fontweight='bold', ha='center')
        ax.set_title(f"Rank {i+1}\nLoss: {res['loss']:.1f}m", fontsize=10)
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(True, alpha=0.3)

    # --- LIGNE 2 : METRIQUES SUPERPOSEES (SOG, COG, ROT) ---
    # On utilise les 3 dernières colonnes de la grille pour les séries temporelles
    metrics = [("SOG", "SOG (kn)"), ("COG", "COG (°)"), ("ROT", "ROT (°/s)")]
    
    for j, (colname, label) in enumerate(metrics):
        # On étale les 3 graphs sur les 5 colonnes dispo
        ax = fig.add_subplot(gs[1, j+1]) 
        
        for i, res in enumerate(top_maneuvers):
            d = res['maneuver_data']
            t = d.SecondsSince1970 - d.SecondsSince1970.iloc[0]
            y = d[colname].values
            
            # Lissage (frac ajustable selon la métrique)
            y_smooth = lowess_smooth(y, t, frac=0.2 if colname != "ROT" else 0.1)
            
            ax.plot(t, y_smooth, color=TOP_COLORS[i], lw=2, label=f"R{i+1}")
            
        ax.set_title(f"{label}", fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)
        if j == 0: ax.legend(fontsize=8)

    plt.show()

def plot_rank_detailed_maneuver(top_maneuvers, metrics_to_show, smooth_frac):
    """
    Un plot complet par manœuvre avec Interval ID dans le titre et marqueurs de sens.
    """
    cmaps = ["viridis", "plasma", "coolwarm", "magma"]

    for i, res in enumerate(top_maneuvers):
        d = res['maneuver_data']
        t = d.SecondsSince1970 - d.SecondsSince1970.iloc[0]
        interval_id = res.get('ID', 'N/A')
        
        fig, axs = plt.subplots(2, len(metrics_to_show), figsize=(18, 7), constrained_layout=True)
        # Titre principal mis à jour
        fig.suptitle(f"RANK #{i+1} - {res['Run']} (Interval ID: {interval_id}) | Total Loss: {res['loss']:.2f}m", 
                     fontsize=15, fontweight='bold', color='#2c3e50')

        lon, lat = d.Lon.values, d.Lat.values
        points = np.array([lon, lat]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        for col, ((colname, label), cmap) in enumerate(zip(metrics_to_show, cmaps)):
            # --- ROW 1 : TRACK COLORÉE ---
            ax_track = axs[0, col]
            y = d[colname].values
            y = d[colname].ffill().bfill().values
            y_smooth = lowess_smooth(y, t, smooth_frac.get(colname, 0.2))
            
            norm = plt.Normalize(np.nanpercentile(y_smooth, 5), np.nanpercentile(y_smooth, 95))
            lc = LineCollection(segments, cmap="RdYlBu_r" if colname == "Heel_Lwd" else cmap, norm=norm, array=y_smooth[:-1], linewidth=5)
            ax_track.add_collection(lc)
            
            # Repères visuels sur la trace
            ax_track.scatter(lon[0], lat[0], color='black', marker='o', s=40, zorder=5) # Start
            
            ax_track.set_aspect("equal", adjustable="datalim")
            ax_track.set_title(f"{label} on Track")
            plt.colorbar(lc, ax=ax_track, fraction=0.046, pad=0.04)

            # --- ROW 2 : TIME SERIES ---
            ax_time = axs[1, col]
            ax_time.plot(t, y, color='gray', alpha=0.8, lw=1) 
            ax_time.plot(t, y_smooth, color=TOP_COLORS[i % len(TOP_COLORS)], lw=2.5) 
            ax_time.set_title(f"{label} vs Time")
            ax_time.grid(True, alpha=0.2)
            ax_time.set_xlabel("Seconds")

        plt.show()
# === Evaluation Functions ===
def compute_path_distance(latitudes, longitudes):
    points = list(zip(latitudes, longitudes))
    return sum(geodesic(points[i], points[i+1]).meters for i in range(len(points)-1))

def compute_straight_line_distance(lat1, lon1, lat2, lon2):
    return geodesic((lat1, lon1), (lat2, lon2)).meters

def compute_integral(time, speed):
    return np.trapz(speed, time)

def evaluate_maneuver(combined_data):
    maneuver_data = combined_data[combined_data['maneuver_index'] != 0]
    reference_data = combined_data[combined_data['maneuver_index'] == 0]
    times = maneuver_data['SecondsSince1970'].values
    sog = maneuver_data['SOG'].values
    vmg = maneuver_data['VMG'].values
    dt_maneuver = times[-1] - times[0]
    v_avg_vmg_before = reference_data['VMG'].mean() 
    v_avg_sog_before = reference_data['SOG'].mean()
    print(f"Reference VMG before maneuver: {v_avg_vmg_before:.2f} | Reference SOG before maneuver: {v_avg_sog_before:.2f}")

    # Eval 1: Distance lost in terms of VMG
    distance_vmg = compute_integral(times, vmg) * KNOTS_TO_MS
    vmg_loss_meters = (v_avg_vmg_before * dt_maneuver * KNOTS_TO_MS) - distance_vmg
    # Eval 1.2:
    # vmg_loss_meters = v_avg_vmg_before * dt_maneuver * KNOTS_TO_MS - vmg.mean()* dt_maneuver * KNOTS_TO_MS

    # Eval 2: Distance lost in terms of SOG
    distance_sog =compute_integral(times, sog) * KNOTS_TO_MS
    sog_loss_meters = (v_avg_sog_before * dt_maneuver * KNOTS_TO_MS) - distance_sog
    # Eval 2.2:
    # sog_loss_meters = v_avg_sog_before * dt_maneuver * KNOTS_TO_MS - sog.mean()* dt_maneuver * KNOTS_TO_MS
    
    # Eval 3: Ratio
    path_dist = compute_path_distance(maneuver_data['Lat'].values, maneuver_data['Lon'].values)
    A = (maneuver_data['Lat'].iloc[0], maneuver_data['Lon'].iloc[0])
    B = (maneuver_data['Lat'].iloc[-1], maneuver_data['Lon'].iloc[-1])
    ab_dist = compute_straight_line_distance(A[0], A[1], B[0], B[1])
    ratio = path_dist / ab_dist if ab_dist > 0.1 else 1.0

    # Eval 4: Sign of VMG loss
    sign_vmg = np.sign(vmg_loss_meters)
    
    print(f"Integrated distance (VMG): {distance_vmg:.2f} m | Integrated distance (SOG): {distance_sog:.2f} m")
    print(f"Expected distance if reference speed maintained (VMG): {(v_avg_vmg_before * dt_maneuver * KNOTS_TO_MS):.2f} m | Expected distance if reference speed maintained (SOG): {(v_avg_sog_before * dt_maneuver * KNOTS_TO_MS):.2f} m")    
    print(f"Distance lost (VMG): {vmg_loss_meters:.2f} m | Distance lost (SOG): {sog_loss_meters:.2f} m")
    print(f"Ratio Path/AB: {ratio:.3f} | Sign of VMG loss: {sign_vmg} (1=positive, -1=negative, 0=neutral), from VMGbefore-VMGreal={vmg_loss_meters:.2f} m")


    return {
        "vmg_loss_meters": vmg_loss_meters,
        "sog_loss_meters": sog_loss_meters,
        "ratio": ratio,
        "sign_vmg": sign_vmg,
        "maneuver_data": maneuver_data
    }

# def main(df, rider_name, maneuver_type_filter=None):
#     rider_data = df[df['rider_name'] == rider_name]
#     eval_records = []

#     for run_name in rider_data['run'].unique():
#         run_data = rider_data[rider_data['run'] == run_name]

#         for target_index in run_data['target_id'].unique():
#             extended_maneuver_data = run_data[run_data['target_id'] == target_index]
#             maneuver_type = extended_maneuver_data['maneuver_type'].iloc[0]

#             if maneuver_type_filter and maneuver_type != maneuver_type_filter:
#                 continue

#             # Evaluation
#             print(f"\n=== {rider_name} - Run: {run_name} - Maneuver {target_index} ({maneuver_type}) ===")
#             eval_results = evaluate_maneuver(extended_maneuver_data)

#             # Save eval data
#             eval_records.append({
#                 "Run": run_name,
#                 "Maneuver ID": target_index,
#                 "Eval 1 - Distance Lost (VMG)": eval_results['vmg_loss_meters'],
#                 "Eval 2 - Distance Lost (SOG)": eval_results['sog_loss_meters'],
#                 "Eval 3 - Ratio Path/AB": eval_results['ratio'],
#                 "Eval 4 - Sign VMG": eval_results['sign_vmg']
#             })

#             # Console summary
#             print(f"Start: {extended_maneuver_data['start_time'].iloc[0]} | End: {extended_maneuver_data['end_time'].iloc[0]}")
#             print(f"Duration: {extended_maneuver_data['interval_duration'].iloc[0]} sec")
#             print(f"TWS mean: {extended_maneuver_data['TWS'].mean():.2f} kn | TWA mean: {extended_maneuver_data['TWA'].mean():.2f}° | TWD mean: {extended_maneuver_data['TWD'].mean():.2f}°")
#             print(f"[Eval 1] Distance Lost (VMG)   : {eval_results['vmg_loss_meters']:.2f} m")
#             print(f"[Eval 2] Distance Lost (SOG)   : {eval_results['sog_loss_meters']:.2f} m")
#             print(f"[Eval 3] Path / AB Ratio       : {eval_results['ratio']:.3f}")
#             print(f"[Eval 4] Sign VMG              : {eval_results['sign_vmg']}")

#             plot(eval_results, rider_name, run_name, maneuver_type, target_index)

#     eval_df = pd.DataFrame(eval_records)

#     # 1. On peut ajouter une colonne de perte cumulée si tu veux un classement global
#     eval_df['Total Distance Lost (m)'] = eval_df['Eval 1 - Distance Lost (VMG)'] + eval_df['Eval 2 - Distance Lost (SOG)']

#     cols_order = [
#             "Run", 
#             "Maneuver ID", 
#             "Total Distance Lost (m)",  # <--- Placé ici pour être à gauche de Eval 1
#             "Eval 1 - Distance Lost (VMG)", 
#             "Eval 2 - Distance Lost (SOG)", 
#             "Eval 3 - Ratio Path/AB", 
#             "Eval 4 - Sign VMG"
#         ]
        
#         # On applique l'ordre (en vérifiant que toutes les colonnes existent)
#     eval_df = eval_df[cols_order]

#     # 2. Tri personnalisé : ici on trie par la plus petite perte VMG d'abord
#     # Tu peux changer par "Total Distance Lost (m)" ou "Eval 1 - Ratio Path/AB"
#     eval_df_sorted = eval_df.sort_values(
#         by="Total Distance Lost (m)", 
#         ascending=True, 
#         ignore_index=True
#     )
#     display(eval_df_sorted.round(2))

def main(df, rider_name, maneuver_type_filter=None):
    rider_data = df[df['rider_name'] == rider_name]
    eval_records = []

    for run_name in rider_data['run'].unique():
        run_data = rider_data[rider_data['run'] == run_name]
        for target_index in run_data['target_id'].unique():
            extended_data = run_data[run_data['target_id'] == target_index]
            maneuver_type = extended_data['maneuver_type'].iloc[0]
            
            # Si un filtre est défini et qu'il ne correspond pas, on passe à la suivante
            if maneuver_type_filter and maneuver_type != maneuver_type_filter:
                continue
            print(f"\n\n === Evaluating {rider_name} - Run: {run_name} - Maneuver {target_index} ===")
            res = evaluate_maneuver(extended_data)
            
            if res:
                eval_records.append({
                    "Run": run_name,
                    "Maneuver ID": target_index,
                    "rider_name": rider_name,
                    "Eval 1 - Distance Lost (VMG)": res['vmg_loss_meters'],
                    "Eval 2 - Distance Lost (SOG)": res['sog_loss_meters'],
                    "Eval 3 - Ratio Path/AB": res['ratio'],
                    "Eval 4 - Sign VMG": res['sign_vmg'],
                    "maneuver_data": res['maneuver_data']
                })

    eval_df = pd.DataFrame(eval_records)
    eval_df['Total Distance Lost (m)'] = eval_df['Eval 1 - Distance Lost (VMG)'] + eval_df['Eval 2 - Distance Lost (SOG)']
    
    # Tri pour obtenir le Top 5 (moins de perte en premier)
    eval_df_sorted = eval_df.sort_values(by="Total Distance Lost (m)", ascending=True).reset_index(drop=True)

    # Préparation de la liste Top 5 pour les fonctions de plot
    top5_list = []
    for idx, row in eval_df_sorted.head(5).iterrows():
        top5_list.append({
            'maneuver_data': row['maneuver_data'],
            'Run': row['Run'],
            'loss': row['Total Distance Lost (m)'],
            'ID': row['Maneuver ID']
        })
    cols_order = [
        "Run", "Maneuver ID", "Total Distance Lost (m)", 
        "Eval 1 - Distance Lost (VMG)", "Eval 2 - Distance Lost (SOG)", 
        "Eval 3 - Ratio Path/AB", "Eval 4 - Sign VMG", "maneuver_data"
    ]
    
    # Réorganiser le DataFrame selon cet ordre
    eval_df_sorted = eval_df_sorted[cols_order]
    print("\n=== Evaluation Summary (sorted by Total Distance Lost) ===")
    display(eval_df_sorted.drop(columns=['maneuver_data']).round(2))

    # --- PLOTS ---
    if top5_list:
        plot_top5_maneuvers_comparison(top5_list)
        
        metrics_to_show = [("SOG", "SOG"), ("ROT", "ROT"), ("Heel_Lwd", "Heel"), ("VMG", "VMG")]
        plot_rank_detailed_maneuver(top5_list, metrics_to_show, DEFAULT_SMOOTH_FRAC)

    return eval_df_sorted

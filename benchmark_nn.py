import os
import sys
import pandas as pd
import numpy as np
import random
import time
from datetime import datetime

# Import application modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import config
import process_model
from fingerprint_engine import robust_read_csv
from modules.ai_core import mbrl_manager
from modules.pirl_mpc import FirstPrinciplesDigitalTwin, PIRL_MPC_Controller

# --- SCRIPT CONFIGURATION ---
SAMPLE_COUNT = 1000         # Number of historical events to benchmark
ROLLOUT_STEPS = 15          # Minutes to predict into the future
TARGET_TARGET = None        # Will default to model_config.json's primary target
print_details = False       # Print every single batch prediction (True/False)

def run_benchmark():
    global TARGET_TARGET, SAMPLE_COUNT
    print("=" * 70)
    print(" 🚀 HYBRID AI vs PHYSICS (DIGITAL TWIN) OFFLINE BENCHMARK")
    print("=" * 70)

    # 1. LOAD CONFIGURATION
    conf = process_model.load_model_config()
    bindings = conf.get('ai_bindings', {})
    TARGET_TARGET = bindings.get('primary_prediction_target', 'Kiln motor 1 Amps')
    print(f"[+] Active Benchmarking Target: {TARGET_TARGET}")
    print(f"[+] Sample Pool Size: {SAMPLE_COUNT} Batches")
    print(f"[+] Simulation Horizon: {ROLLOUT_STEPS} Minutes")

    # 2. LOAD HISTORICAL DATA
    print("[+] Loading Golden Dataset (fingerprint4.csv)...")
    try:
        df = robust_read_csv(getattr(config, 'HISTORICAL_DATA_CSV_PATH', 'files/data/fingerprint4.csv'))
    except Exception as e:
        print(f"[!] FAILED TO LOAD DATA: {e}")
        return

    if df.empty or len(df) < 200:
        print("[!] Historic Dataset is too small or empty.")
        return
        
    print(f"    -> Successfully loaded {len(df)} rows.")

    # 3. INITIALIZE WORLD MODEL
    print("[+] Waking up the Neural Network Ensembles (Black-Box)...")
    mbrl_manager._initialize_system()
    if mbrl_manager._world_model is None:
        print("[!] Neural Network failed to load. Ensure files/models/ exists.")
        return

    # 4. INITIALIZE PIRL-MPC DIGITAL TWIN
    print("[+] Waking up the PIRL Digital Twin (Grey-Box Physics)...")
    mpc_engine = PIRL_MPC_Controller()
    role_mapping = mpc_engine._get_role_mapping(conf)
    dt_twin = FirstPrinciplesDigitalTwin(conf)
    
    # Specific map for fingerprint4.csv columns to Physics Roles
    benchmark_mapping = {
        'Kiln feed': 'feed', 'Kiln speed': 'speed', 'Kiln motor 1 Amps': 'torque',
        'Petcoke (PC)': 'pc_fuel', 'Petcoke (Kiln)': 'kiln_fuel', 'RDF (Kiln)': 'rdf',
        'ID fan speed': 'draft', 'Kiln BZT1': 'bzt', 'Preheater outlet T': 'exhaust_temp',
        'Kiln hood P': 'pressure', 'O2 (Kiln)': 'o2_excess', 'CO (kiln)': 'co_ppm',
        'Secondary air T1': 'sec_air_temp', 'Coal Mill (ON/OFF)': 'coal_mill_on'
    }
    
    dt_target_role = benchmark_mapping.get(TARGET_TARGET, 'torque')
    print(f"    -> Target '{TARGET_TARGET}' mathematically mapped to Physics property: '{dt_target_role.upper()}'")

    # 5. PREPARE VECTORS
    if TARGET_TARGET not in df.columns:
        print(f"[!] The Target Variable '{TARGET_TARGET}' is not in the CSV columns!")
        keys = list(df.columns)
        if 'BZT' in keys: TARGET_TARGET = 'BZT'
        else:
            print("Cannot benchmark without valid target.")
            return

    valid_indices = df[df[TARGET_TARGET].notna()].index.tolist()
    usable_starts = [i for i in valid_indices if 10 < i < (len(df) - ROLLOUT_STEPS - 1)]

    if len(usable_starts) < SAMPLE_COUNT:
        print(f"[!] Not enough clean contiguous data to sample {SAMPLE_COUNT} batches. Reducing to {len(usable_starts)}.")
        SAMPLE_COUNT = len(usable_starts)

    test_indices = random.sample(usable_starts, SAMPLE_COUNT)
    a_cols = mbrl_manager._env_config['a_cols']

    # --- METRICS TRACKERS ---
    ai_mae_list = []
    dt_mae_list = []
    dt_violations = 0

    start_time = time.time()
    print("\n[+] Benchmarking Side-by-Side in progress (AI vs Physics)...\n")

    # 6. EXECUTE BACKTESTING
    for i, idx in enumerate(test_indices):
        hist_window_df = df.iloc[idx - mbrl_manager.HISTORY_WINDOW : idx].copy()
        future_window_df = df.iloc[idx : idx + ROLLOUT_STEPS].copy()
        
        start_val = hist_window_df.iloc[-1][TARGET_TARGET]
        true_end_val = future_window_df.iloc[-1][TARGET_TARGET]
        operator_controls = hist_window_df.iloc[-1][a_cols].to_dict()
        
        # -------------------------------------------------------------
        # A. NEURAL NETWORK ROLLOUT (BLACK-BOX)
        # -------------------------------------------------------------
        sim_results = mbrl_manager.simulate_what_if(hist_window_df, operator_controls, TARGET_TARGET, steps=ROLLOUT_STEPS)
        ai_rollout = sim_results.get('simulated', [])
        
        if ai_rollout and len(ai_rollout) >= ROLLOUT_STEPS:
            ai_pred_end = ai_rollout[-1]
            ai_mae_list.append(abs(ai_pred_end - true_end_val))

        # -------------------------------------------------------------
        # B. DIGITAL TWIN ROLLOUT (GREY-BOX PHYSICS)
        # -------------------------------------------------------------
        raw_state_dict = hist_window_df.iloc[-1].to_dict()
        dt_state = mpc_engine._extract_state_vector(raw_state_dict, benchmark_mapping, conf)
        
        # Convert operator controls to action vector
        dt_action_raw = [{'var_name': k, 'final_target': v} for k, v in operator_controls.items()]
        dt_action = mpc_engine._extract_action_vector(dt_action_raw, benchmark_mapping)
        for k, v in dt_state.items():
            if k not in dt_action: dt_action[k] = v
            
        pirl_rollout = dt_twin.simulate_rollout(dt_state, dt_action, horizon_mins=ROLLOUT_STEPS)
        
        # Track if the real human operator violated physics
        if not pirl_rollout['stable']:
            dt_violations += 1

        dt_pred_end = pirl_rollout['final_sim_state'].get(dt_target_role, start_val)
        dt_mae_list.append(abs(dt_pred_end - true_end_val))
        
        # -------------------------------------------------------------

        if print_details:
            print(f"[{i+1}/{SAMPLE_COUNT}] True: {true_end_val:.1f} | AI: {ai_pred_end:.1f} | DT: {dt_pred_end:.1f}")
        elif (i+1) % 10 == 0:
            sys.stdout.write(f"\rProcessed {i+1}/{SAMPLE_COUNT} batches... AI Err: {np.mean(ai_mae_list):.2f} | Physics Err: {np.mean(dt_mae_list):.2f}")
            sys.stdout.flush()

    sys.stdout.write("\n")
    
    if len(ai_mae_list) == 0:
        print("[!] No successful predictions parsed!")
        return

    # 7. GENERATE FINAL REPORT
    ai_final_mae = np.mean(ai_mae_list)
    dt_final_mae = np.mean(dt_mae_list)
    
    elapsed = time.time() - start_time
    improvement = ((ai_final_mae - dt_final_mae) / ai_final_mae) * 100.0 if ai_final_mae > 0 else 0
    
    report = f"""
============================================================
 📊 HYBRID ARCHITECTURE PERFORMANCE BENCHMARK
============================================================
 Target Variable           : {TARGET_TARGET} -> {dt_target_role.upper()}
 Sample Count Tested       : {len(ai_mae_list)} Random Batches
 Prediction Horizon        : {ROLLOUT_STEPS} Minutes
 Compute Time              : {elapsed:.2f} seconds
------------------------------------------------------------
 🤖 NEURAL NETWORK (AI) MAE : {ai_final_mae:.2f} units avg deviation
 ⚙️ DIGITAL TWIN (MPC) MAE  : {dt_final_mae:.2f} units avg deviation
------------------------------------------------------------
"""
    if dt_final_mae < ai_final_mae:
        report += f" ✅ THE PHYSICS ENGINE IMPROVED ACCURACY BY {improvement:.1f}%\n"
    else:
        report += f" ⚠️ AI OUTPERFORMED THE PHYSICS ENGINE BY {abs(improvement):.1f}%\n"
        
    report += f" 🚨 Physics Violations Avoided: {dt_violations} out of {SAMPLE_COUNT} batches.\n"
    report += "============================================================\n"
    
    print(report)
    with open('benchmark_report.md', 'w', encoding='utf-8') as f:
        f.write("# Hybrid Controller Benchmarking Report\\n\\n")
        f.write("```text\\n")
        f.write(report)
        f.write("```\\n")
    print(f"[+] Saved professional printed report to benchmark_report.md")

if __name__ == "__main__":
    run_benchmark()

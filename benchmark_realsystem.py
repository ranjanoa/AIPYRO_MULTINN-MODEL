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
TEST_DATA_PATH = "realsystemdata/simulation_test_data.csv"
SAMPLE_COUNT = 200          # Number of historical events to benchmark
ROLLOUT_STEPS = 15          # Minutes to predict into the future
print_details = False       # Print every single batch prediction

def run_realsystem_benchmark():
    print("=" * 70)
    print(" 🌍 REAL SYSTEM DATA VALIDATION (AI vs PHYSICS)")
    print("=" * 70)

    # 1. LOAD CONFIGURATION
    conf = process_model.load_model_config()
    bindings = conf.get('ai_bindings', {})
    target_var = bindings.get('primary_prediction_target', 'Kiln motor 1 Amps')
    
    print(f"[+] Target Variable: {target_var}")
    print(f"[+] Data Source: {TEST_DATA_PATH}")

    # 2. LOAD DATA
    print("[+] Loading Real System Dataset...")
    try:
        df = robust_read_csv(TEST_DATA_PATH)
    except Exception as e:
        print(f"[!] FAILED TO LOAD DATA: {e}")
        return

    if df.empty:
        print("[!] Dataset is empty.")
        return
        
    print(f"    -> Successfully loaded {len(df)} rows.")

    # 3. INITIALIZE AI SYSTEM
    print("[+] Initializing AI System...")
    mbrl_manager._initialize_system()
    if mbrl_manager._world_model is None:
        print("[!] AI Model failed to load.")
        return

    # 4. INITIALIZE PHYSICS TWIN
    print("[+] Initializing Physics Digital Twin...")
    mpc_engine = PIRL_MPC_Controller()
    dt_twin = FirstPrinciplesDigitalTwin(conf)
    
    benchmark_mapping = {
        'Kiln feed': 'feed', 'Kiln speed': 'speed', 'Kiln motor 1 Amps': 'torque',
        'Petcoke (PC)': 'pc_fuel', 'Petcoke (Kiln)': 'kiln_fuel', 'RDF (Kiln)': 'rdf',
        'ID fan speed': 'draft', 'Kiln BZT1': 'bzt', 'Preheater outlet T': 'exhaust_temp',
        'Kiln hood P': 'pressure', 'O2 (Kiln)': 'o2_excess', 'CO (kiln)': 'co_ppm',
        'Secondary air T1': 'sec_air_temp', 'Coal Mill (ON/OFF)': 'coal_mill_on'
    }
    
    dt_target_role = benchmark_mapping.get(target_var, 'torque')

    # 5. PREPARE SAMPLES
    valid_indices = df[df[target_var].notna()].index.tolist()
    usable_starts = [i for i in valid_indices if 30 < i < (len(df) - ROLLOUT_STEPS - 1)]
    
    count = min(SAMPLE_COUNT, len(usable_starts))
    test_indices = random.sample(usable_starts, count)
    a_cols = mbrl_manager._env_config['a_cols']

    # --- METRICS ---
    ai_errors = []
    dt_errors = []

    print(f"\n[+] Processing {count} random batches...")
    
    for i, idx in enumerate(test_indices):
        hist_df = df.iloc[idx - 30 : idx].copy()
        future_df = df.iloc[idx : idx + ROLLOUT_STEPS].copy()
        
        start_val = hist_df.iloc[-1][target_var]
        true_val = future_df.iloc[-1][target_var]
        controls = hist_df.iloc[-1][a_cols].to_dict()
        
        # A. AI Prediction
        sim = mbrl_manager.simulate_what_if(hist_df, controls, target_var, steps=ROLLOUT_STEPS)
        ai_pred = sim.get('simulated', [])[-1] if sim.get('simulated') else start_val
        ai_errors.append(abs(ai_pred - true_val))
        
        # B. Physics Prediction
        raw_state = hist_df.iloc[-1].to_dict()
        dt_state = mpc_engine._extract_state_vector(raw_state, benchmark_mapping, conf)
        dt_action_raw = [{'var_name': k, 'final_target': v} for k, v in controls.items()]
        dt_action = mpc_engine._extract_action_vector(dt_action_raw, benchmark_mapping)
        for k, v in dt_state.items():
            if k not in dt_action: dt_action[k] = v
            
        pirl = dt_twin.simulate_rollout(dt_state, dt_action, horizon_mins=ROLLOUT_STEPS)
        dt_pred = pirl['final_sim_state'].get(dt_target_role, start_val)
        dt_errors.append(abs(dt_pred - true_val))

        if (i+1) % 10 == 0:
            sys.stdout.write(f"\r Progress: {i+1}/{count} | AI MAE: {np.mean(ai_errors):.2f}")
            sys.stdout.flush()

    # 6. REPORT
    print("\n\n" + "="*60)
    print(" 📊 FINAL VALIDATION RESULTS")
    print("="*60)
    print(f" AI Model Mean Absolute Error   : {np.mean(ai_errors):.4f}")
    print(f" Physics Model Mean Absolute Error: {np.mean(dt_errors):.4f}")
    print("="*60)

if __name__ == "__main__":
    run_realsystem_benchmark()

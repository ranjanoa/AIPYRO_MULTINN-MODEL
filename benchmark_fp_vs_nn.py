import os
import sys
import pandas as pd
import numpy as np
import random
import time

# Import application modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import config
import process_model
from fingerprint_engine import robust_read_csv, get_live_fingerprint_action, get_active_strategy
from modules.ai_core import mbrl_manager
from modules.pirl_mpc import FirstPrinciplesDigitalTwin, PIRL_MPC_Controller

def evaluate_kpis(action_vec, rollout, dt_twin):
    state = rollout['final_sim_state']
    feed = action_vec.get('feed', 200.0)
    pc_fuel = action_vec.get('pc_fuel', 0.0)
    kiln_fuel = action_vec.get('kiln_fuel', 0.0)
    rdf = action_vec.get('rdf', 0.0)
    
    clinker_tph = feed / dt_twin.params['feed_to_clinker_ratio']
    
    petcoke_cv = dt_twin.params['petcoke_cv_kcal_kg']
    rdf_cv = dt_twin.params['rdf_cv_kcal_kg']
    
    petcoke_heat_kcal_hr = (pc_fuel + kiln_fuel) * 1000 * petcoke_cv
    rdf_heat_kcal_hr = rdf * 1000 * rdf_cv
    total_heat = petcoke_heat_kcal_hr + rdf_heat_kcal_hr
    
    tsr = (rdf_heat_kcal_hr / max(total_heat, 1)) * 100.0
    shc = (total_heat / max(clinker_tph * 1000, 1)) if clinker_tph > 0 else 9999.0
    
    # Process Engineering Score (Weighted Objective Function)
    score = 0.0
    if not rollout['stable']:
        score -= 2000.0  # Apply penalty for physics violation but keep evaluating
    score += clinker_tph * 10.0              # Reward Production
    score += tsr * 5.0                       # Reward Alternative Fuels
    score -= max(0, shc - 800) * 2.0         # Penalize High Thermal Consumption
    
    # Stability & Quality
    bzt = state.get('bzt', 1400)
    o2 = state.get('o2_excess', 2.0)
    co = state.get('co_ppm', 0)
    
    score -= co * 0.5                        # Penalize CO emissions
    score -= abs(bzt - 1400) * 1.5           # Penalize deviation from optimal BZT
    
    if o2 < 1.0: score -= 500                # Severe penalty for starvation
    elif o2 > 3.0: score -= 200              # Penalty for thermal waste (excess air)
    
    return score, tsr, shc, clinker_tph

def run_benchmark():
    print("============================================================")
    print(" 🚀 BENCHMARK: NEURAL NETWORK vs FINGERPRINT ENGINE")
    print("============================================================")

    # 1. LOAD CONFIGURATION
    conf = process_model.load_model_config()
    print("[+] Loading Golden Dataset...")
    try:
        df = robust_read_csv(getattr(config, 'HISTORICAL_DATA_CSV_PATH', 'files/data/fingerprint4.csv'))
    except Exception as e:
        print(f"[!] FAILED TO LOAD DATA: {e}")
        return

    # 2. WAKE UP ENGINES
    print("[+] Initializing Neural Network Ensembles...")
    mbrl_manager._initialize_system()
    
    print("[+] Initializing PIRL Digital Twin (for evaluation)...")
    mpc_engine = PIRL_MPC_Controller()
    dt_twin = FirstPrinciplesDigitalTwin(conf)
    
    # Mapping for Digital Twin
    benchmark_mapping = {
        'Kiln feed': 'feed', 'Kiln speed': 'speed', 'Kiln motor 1 Amps': 'torque',
        'Petcoke (PC)': 'pc_fuel', 'Petcoke (Kiln)': 'kiln_fuel', 'RDF (Kiln)': 'rdf',
        'ID fan speed': 'draft', 'Kiln BZT1': 'bzt', 'Preheater outlet T': 'exhaust_temp',
        'Kiln hood P': 'pressure', 'O2 (Kiln)': 'o2_excess', 'CO (kiln)': 'co_ppm',
        'Secondary air T1': 'sec_air_temp', 'Coal Mill (ON/OFF)': 'coal_mill_on'
    }

    usable_starts = [i for i in range(20, len(df) - 20) if i % 100 == 0]
    SAMPLE_COUNT = min(50, len(usable_starts))
    test_indices = random.sample(usable_starts, SAMPLE_COUNT)

    print(f"\n[+] Running Physics Simulation on {SAMPLE_COUNT} Historical Scenarios...\n")

    nn_better = 0
    fp_better = 0
    
    metrics = {'fp_score': [], 'fp_tsr': [], 'fp_shc': [], 'fp_tph': [],
               'nn_score': [], 'nn_tsr': [], 'nn_shc': [], 'nn_tph': []}

    for i, idx in enumerate(test_indices):
        hist_window_df = df.iloc[idx - 5 : idx].copy()
        
        # A. Get Fingerprint Actions
        state_dict = hist_window_df.iloc[-1].fillna(0).to_dict()
        strategy_name, frontend_strategy = get_active_strategy(conf)
        try:
            fp_result = get_live_fingerprint_action('AUTO', strategy_name, frontend_strategy, state_dict, 1.0, hist_window_df)
        except TypeError:
            try:
                fp_result = get_live_fingerprint_action(hist_window_df)
            except Exception as e:
                fp_result = None
                
        fp_actions = fp_result.get('actions', []) if fp_result else []
        
        # B. Get Neural Network Actions
        nn_result = mbrl_manager.get_optimal_action(hist_window_df)
        nn_actions = nn_result.get('actions', []) if nn_result else []

        # C. Evaluate Both via Physics Twin
        raw_state_dict = hist_window_df.iloc[-1].fillna(0).to_dict()
        dt_state = mpc_engine._extract_state_vector(raw_state_dict, benchmark_mapping, conf)

        fp_action_vec = mpc_engine._extract_action_vector(fp_actions, benchmark_mapping)
        nn_action_vec = mpc_engine._extract_action_vector(nn_actions, benchmark_mapping)

        for k, v in dt_state.items():
            if k not in fp_action_vec: fp_action_vec[k] = v
            if k not in nn_action_vec: nn_action_vec[k] = v

        fp_rollout = dt_twin.simulate_rollout(dt_state, fp_action_vec, horizon_mins=15)
        nn_rollout = dt_twin.simulate_rollout(dt_state, nn_action_vec, horizon_mins=15)

        fp_score, fp_tsr, fp_shc, fp_tph = evaluate_kpis(fp_action_vec, fp_rollout, dt_twin)
        nn_score, nn_tsr, nn_shc, nn_tph = evaluate_kpis(nn_action_vec, nn_rollout, dt_twin)
        
        if fp_score > -9000:
            metrics['fp_score'].append(fp_score); metrics['fp_tsr'].append(fp_tsr)
            metrics['fp_shc'].append(fp_shc); metrics['fp_tph'].append(fp_tph)
            
        if nn_score > -9000:
            metrics['nn_score'].append(nn_score); metrics['nn_tsr'].append(nn_tsr)
            metrics['nn_shc'].append(nn_shc); metrics['nn_tph'].append(nn_tph)

        if nn_score > fp_score:
            nn_better += 1
        elif fp_score > nn_score:
            fp_better += 1

        sys.stdout.write(f"\rProcessed {i+1}/{SAMPLE_COUNT} scenarios...")
        sys.stdout.flush()

    print("\n")
    
    def safe_mean(lst): return np.mean(lst) if lst else 0.0
    def safe_std(lst): return np.std(lst) if lst and len(lst) > 1 else 0.0

    report = f"""
# 📊 HYBRID AI PERFORMANCE BENCHMARK REPORT

**Sample Count Evaluated:** {SAMPLE_COUNT} Random Scenarios
**Evaluation Engine:** First-Principles Digital Twin
**Scoring Criteria:** Maximize Production & TSR, Minimize SHC, Maintain Safety (O2/CO/BZT)

### 🏆 Head-to-Head Comparison

| Key Performance Indicator | 🔍 Fingerprint (Baseline) | 🤖 Neural Network (AI) | 🚀 AI Improvement |
| :--- | :---: | :---: | :---: |
| **Average Process Score** | {safe_mean(metrics['fp_score']):.1f} (± {safe_std(metrics['fp_score']):.1f}) | **{safe_mean(metrics['nn_score']):.1f}** (± {safe_std(metrics['nn_score']):.1f}) | {((safe_mean(metrics['nn_score']) - safe_mean(metrics['fp_score'])) / max(1, abs(safe_mean(metrics['fp_score']))))*100:.1f}% |
| **Avg Production (Feed)** | {safe_mean(metrics['fp_tph']):.1f} tph (± {safe_std(metrics['fp_tph']):.1f}) | **{safe_mean(metrics['nn_tph']):.1f}** tph (± {safe_std(metrics['nn_tph']):.1f}) | {safe_mean(metrics['nn_tph']) - safe_mean(metrics['fp_tph']):.1f} tph |
| **Avg TSR (Alt Fuels)** | {safe_mean(metrics['fp_tsr']):.1f} % (± {safe_std(metrics['fp_tsr']):.1f}) | **{safe_mean(metrics['nn_tsr']):.1f}** % (± {safe_std(metrics['nn_tsr']):.1f}) | {safe_mean(metrics['nn_tsr']) - safe_mean(metrics['fp_tsr']):.1f} % |
| **Avg SHC (Thermal)** | {safe_mean(metrics['fp_shc']):.1f} kcal/kg (± {safe_std(metrics['fp_shc']):.1f}) | **{safe_mean(metrics['nn_shc']):.1f}** kcal/kg (± {safe_std(metrics['nn_shc']):.1f}) | {safe_mean(metrics['nn_shc']) - safe_mean(metrics['fp_shc']):.1f} kcal/kg |

### 🏁 Final Verdict
* **Neural Network Won:** {nn_better} times
* **Fingerprint Won:** {fp_better} times
"""
    print(report)
    with open('benchmark_fp_vs_nn.md', 'w', encoding='utf-8') as f:
        f.write(report)
    print("[+] Report saved to benchmark_fp_vs_nn.md")

if __name__ == "__main__":
    run_benchmark()

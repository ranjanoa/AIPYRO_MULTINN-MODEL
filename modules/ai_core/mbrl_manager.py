import pandas as pd
import numpy as np
import torch
import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from datetime import datetime
from torch.utils.data import DataLoader, Dataset, TensorDataset

# --- PATH SETUP ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import config
import process_model
from process_model import apply_industrial_nudge

# --- REAL AI MODULE IMPORTS ---
try:
    from .world_model import RobustWorldModel
except ImportError:
    try:
        from world_model import RobustWorldModel
    except ImportError:
        print("⚠️ Warning: Could not import RobustWorldModel. Simulation will fail.")
        RobustWorldModel = None

try:
    from .sac_components import SACAgent, ReplayBuffer
    from .model_based_env import PessimisticVirtualEnv

    SAC_AVAILABLE = True
except ImportError:
    try:
        from sac_components import SACAgent, ReplayBuffer
        from model_based_env import PessimisticVirtualEnv

        SAC_AVAILABLE = True
    except ImportError:
        print("⚠️ Warning: Could not import SACAgent. AI Optimization disabled.")
        SAC_AVAILABLE = False

# --- CONFIGURATION ---
MODELS_DIR = getattr(config, 'MODELS_DIR', "files/models")
WM_PATH = os.path.join(MODELS_DIR, "ensemble_wm")
SAC_PATH = os.path.join(MODELS_DIR, "sac_agent")
HISTORY_WINDOW = 30

# --- GLOBAL STATE ---
_world_model = None
_sac_agent = None
_env_config = None
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ==============================================================================
# MEMORY-EFFICIENT DATASET CLASS
# ==============================================================================
class TimeSeriesDataset(Dataset):
    def __init__(self, norm_s, norm_a, window=5):
        self.s = torch.FloatTensor(norm_s)
        self.a = torch.FloatTensor(norm_a)
        self.w = window
        self.length = len(norm_s) - window

    def __len__(self):
        return max(0, self.length)

    def __getitem__(self, idx):
        s_chunk = self.s[idx: idx + self.w]
        a_chunk = self.a[idx: idx + self.w]
        obs = torch.cat([s_chunk, a_chunk], dim=1).flatten()

        curr_s = self.s[idx + self.w - 1]
        next_s = self.s[idx + self.w]
        delta = (next_s - curr_s) * 100.0

        return obs, delta


# ==============================================================================
# 1. INITIALIZATION & SCALING
# ==============================================================================
def _initialize_system():
    global _world_model, _sac_agent, _env_config
    if _world_model is not None: return

    print("⚡ Initializing AI System (Real Neural Network Mode)...")

    process_model.load_model_config()
    controls = process_model.get_control_variables()
    indicators = process_model.get_indicator_variables()

    # Exclude calculated variables and priority 0 variables from the AI's core mathematical optimization space
    s_cols = sorted([k for k, v in {**controls, **indicators}.items() if not v.get('is_calculated') and v.get('priority', 3) != 0 and 'formula' not in v])
    a_cols = sorted([k for k, v in controls.items() if v.get('is_setpoint') and not v.get('is_calculated') and v.get('priority', 3) != 0 and 'formula' not in v])

    required_cols = list(set(s_cols + a_cols))

    try:
        # --- ROBUST DATA LOADING ---
        from fingerprint_engine import robust_read_csv
        df_full = robust_read_csv(config.HISTORICAL_DATA_CSV_PATH)
        
        if df_full.empty:
            print("⚠️ No data loaded. Creating dummy stats.")
            df_train = pd.DataFrame(columns=required_cols)
        else:
            existing_cols = df_full.columns.tolist()
            valid_cols = [c for c in required_cols if c in existing_cols]
            
            if not valid_cols:
                print("⚠️ No matching columns in Data. Creating dummy stats.")
                df_train = pd.DataFrame(columns=required_cols)
            else:
                df_train = df_full[valid_cols]

        for c in required_cols:
            if c not in df_train.columns:
                df_train[c] = 0.0
            df_train[c] = pd.to_numeric(df_train[c], errors='coerce').fillna(0.0)

        s_min, s_max = df_train[s_cols].min().values, df_train[s_cols].max().values
        a_min, a_max = df_train[a_cols].min().values, df_train[a_cols].max().values

        s_range = s_max - s_min
        s_range[s_range < 1e-6] = 1.0
        a_range = a_max - a_min
        a_range[a_range < 1e-6] = 1.0

        stats = {
            'state': {'min': s_min, 'max': s_max, 'range': s_range},
            'action': {'min': a_min, 'max': a_max, 'range': a_range}
        }
        _env_config = {'stats': stats, 's_cols': s_cols, 'a_cols': a_cols}
        print("✅ Config & Data Loaded Successfully.")

    except Exception as e:
        print(f"❌ Critical Error in Initialization: {e}")
        return

    s_dim = len(s_cols)
    a_dim = len(a_cols)

    # --- LOAD WORLD MODEL ---
    try:
        if RobustWorldModel:
            _world_model = RobustWorldModel(s_dim, a_dim, HISTORY_WINDOW)
            try:
                _world_model.load(WM_PATH)
                print("✅ World Model Weights Loaded.")
            except Exception as load_err:
                print(f"⚠️ Warning: Model Shape Mismatch. Starting FRESH World Model.")
    except Exception as e:
        print(f"❌ Error creating World Model: {e}")
        _world_model = None

    # --- LOAD SAC AGENT ---
    if SAC_AVAILABLE:
        try:
            obs_dim = (s_dim + a_dim) * HISTORY_WINDOW
            _sac_agent = SACAgent(obs_dim, a_dim)
            try:
                _sac_agent.load(SAC_PATH)
                print("✅ SAC Agent Weights Loaded.")
            except Exception as load_err:
                print(f"⚠️ Warning: Model Shape Mismatch. Starting FRESH SAC Agent.")
        except Exception as e:
            pass


def _normalize(values, v_type='state'):
    stats = _env_config['stats'][v_type]
    return (values - stats['min']) / stats['range']


def _denormalize(values, v_type='state'):
    stats = _env_config['stats'][v_type]
    return (values * stats['range']) + stats['min']


# ==============================================================================
# 3. SOFT SENSOR PREDICTION
# ==============================================================================
def predict_soft_sensor_rollout(current_real_df, pred_var_name, steps=60):
    if _world_model is None: _initialize_system()
    if _world_model is None or current_real_df.empty: return []

    # >>> SANITIZATION ADDITION: Catch NaNs to prevent API JSON serialization crashes <<<
    if current_real_df.isna().any().any():
        current_real_df = current_real_df.ffill().fillna(0.0)

    s_cols = _env_config['s_cols']
    a_cols = _env_config['a_cols']

    for c in s_cols + a_cols:
        if c not in current_real_df.columns:
            v_type = 'state' if c in s_cols else 'action'
            stats = _env_config['stats'][v_type]
            try:
                col_idx = (s_cols if c in s_cols else a_cols).index(c)
                neutral = float(stats['min'][col_idx]) + 0.5 * float(stats['range'][col_idx])
            except (IndexError, KeyError, TypeError):
                neutral = 0.0
            current_real_df[c] = neutral

    if len(current_real_df) < HISTORY_WINDOW: return []

    raw_s = current_real_df[s_cols].tail(HISTORY_WINDOW).values
    raw_a = current_real_df[a_cols].tail(HISTORY_WINDOW).values
    norm_s = _normalize(raw_s, 'state')
    norm_a = _normalize(raw_a, 'action')

    obs_buffer = []
    for s, a in zip(norm_s, norm_a):
        obs_buffer.extend(s)
        obs_buffer.extend(a)

    current_norm_state = norm_s[-1]
    held_norm_action = norm_a[-1]

    predictions = []
    
    # CASE 1: Action Variables (Controls like Petcoke, Feed)
    # The World Model doesn't "predict" actions, so we project the AI's intended nudge ramp.
    if pred_var_name in a_cols:
        target_val = current_real_df[pred_var_name].iloc[-1]
        # In a real cycle, we would have the AI target here. 
        # Since this is a generic rollout call, we just show the projected hold.
        # But for the UI, we want to see the "path".
        return [float(target_val)] * steps

    # CASE 2: State Variables (Indicators like O2, Temperature)
    try:
        target_idx = s_cols.index(pred_var_name)
    except ValueError:
        return []

    for _ in range(steps):
        inp_tensor = torch.tensor([obs_buffer], dtype=torch.float32).to(device)
        with torch.no_grad():
            mean_delta, _ = _world_model.predict(inp_tensor)

        delta = mean_delta.cpu().numpy()[0]
        next_norm_state = current_norm_state + delta

        # Early-exit guard: if the state has exploded (NaN/Inf from a bad NN cycle),
        # stop the rollout immediately to prevent blocking the background thread.
        if not np.isfinite(next_norm_state).all():
            break

        val_norm = next_norm_state[target_idx]
        val_real = (val_norm * _env_config['stats']['state']['range'][target_idx]) + \
                   _env_config['stats']['state']['min'][target_idx]

        # Ensure we don't append NaNs into the JSON payload
        if np.isnan(val_real) or np.isinf(val_real):
            val_real = 0.0

        predictions.append(float(val_real))

        step_size = len(current_norm_state) + len(held_norm_action)
        obs_buffer = obs_buffer[step_size:]
        obs_buffer.extend(next_norm_state)
        obs_buffer.extend(held_norm_action)
        current_norm_state = next_norm_state

    return predictions


# ==============================================================================
# 4. DIGITAL SIMULATOR
# ==============================================================================
def simulate_what_if(history_df, manual_controls, target_var, steps=60):
    if _world_model is None: _initialize_system()
    if _world_model is None or history_df.empty:
        return {'baseline': [], 'simulated': []}

    # >>> SANITIZATION ADDITION: Catch NaNs to prevent API JSON serialization crashes <<<
    if history_df.isna().any().any():
        history_df = history_df.ffill().fillna(0.0)

    s_cols = _env_config['s_cols']
    a_cols = _env_config['a_cols']

    for c in s_cols + a_cols:
        if c not in history_df.columns: history_df[c] = 0.0

    if len(history_df) < HISTORY_WINDOW:
        return {'baseline': [], 'simulated': []}

    raw_s = history_df[s_cols].tail(HISTORY_WINDOW).values
    raw_a = history_df[a_cols].tail(HISTORY_WINDOW).values
    norm_s = _normalize(raw_s, 'state')
    norm_a = _normalize(raw_a, 'action')

    init_obs = []
    for s, a in zip(norm_s, norm_a):
        init_obs.extend(s)
        init_obs.extend(a)

    def run_rollout(initial_obs, override_actions=None):
        preds = []
        curr_obs = list(initial_obs)
        current_norm_state = norm_s[-1]

        if override_actions:
            base_action = history_df[a_cols].iloc[-1].to_dict()
            base_action.update(override_actions)
            act_vals = [base_action.get(c, 0.0) for c in a_cols]
            act_vals_arr = np.array([act_vals])
            act_norm = _normalize(act_vals_arr, 'action')[0]
            held_norm_action = act_norm
        else:
            held_norm_action = norm_a[-1]

        try:
            target_idx = s_cols.index(target_var)
        except ValueError:
            # If the target variable isn't in the state space directly (e.g. an Indicator)
            # return a flatline array so the graph doesn't crash on the frontend.
            return [float(history_df[target_var].iloc[-1]) if target_var in history_df.columns else 0.0] * steps

        for _ in range(steps):
            inp = torch.tensor([curr_obs], dtype=torch.float32).to(device)
            with torch.no_grad():
                mean_delta, _ = _world_model.predict(inp)

            delta = mean_delta.cpu().numpy()[0]
            next_norm_state = current_norm_state + delta

            val_norm = next_norm_state[target_idx]
            val_real = (val_norm * _env_config['stats']['state']['range'][target_idx]) + \
                       _env_config['stats']['state']['min'][target_idx]

            # Ensure we don't append NaNs into the JSON payload
            if np.isnan(val_real) or np.isinf(val_real):
                val_real = 0.0

            preds.append(float(val_real))

            step_size = len(current_norm_state) + len(held_norm_action)
            curr_obs = curr_obs[step_size:]
            curr_obs.extend(next_norm_state)
            curr_obs.extend(held_norm_action)
            current_norm_state = next_norm_state

        return preds

    baseline_preds = run_rollout(init_obs, override_actions=None)
    sim_preds = run_rollout(init_obs, override_actions=manual_controls)

    last_time_str = history_df['timestamp'].iloc[-1] if 'timestamp' in history_df else str(datetime.now())
    try:
        last_time = pd.to_datetime(last_time_str)
    except:
        last_time = datetime.now()
    timestamps = [str(last_time + pd.Timedelta(seconds=60 * i)) for i in range(1, steps + 1)]

    unit = ""
    try:
        unit = process_model.get_indicator_variables().get(target_var, {}).get('unit', '')
    except:
        pass

    return {
        "variable": target_var,
        "unit": unit,
        "timestamps": timestamps,
        "baseline": baseline_preds,
        "simulated": sim_preds
    }


# ==============================================================================
# 5. GET OPTIMAL ACTION
# ==============================================================================
def get_optimal_action(current_real_df):
    global _world_model, _sac_agent, _env_config

    # >>> SANITIZATION ADDITION: Catch missing tags to prevent AI crash <<<
    if current_real_df.isna().any().any():
        missing_cols = current_real_df.columns[current_real_df.isna().any()].tolist()
        print(f"⚠️ WARNING: Missing data from OPC UA for tags: {missing_cols}")
        print("Forward-filling to keep AI stable...")
        current_real_df = current_real_df.ffill().fillna(0.0)

    full_config = process_model.load_model_config()
    bindings = full_config.get('ai_bindings', {})

    target_var_name = bindings.get('primary_prediction_target', 'sinteringZoneTemp')
    out_keys = bindings.get('output_keys', {
        "confidence": "sac_confidence_score",
        "prediction": "wm_pred_sinteringZoneTemp",
        "recommendation": "sac_rec_coalMainBurner"
    })

    if _world_model is None: _initialize_system()
    if _env_config is None:
        return {"match_score": "AI-INIT-FAILED", "timestamp": str(datetime.now()), "actions": [], "confidence": 0.0}
    if current_real_df.empty:
        return {"match_score": "WAITING", "timestamp": str(datetime.now()), "actions": []}

    s_cols = _env_config['s_cols']
    a_cols = _env_config['a_cols']
    controls_cfg = process_model.get_control_variables()

    for c in s_cols + a_cols:
        if c not in current_real_df.columns:
            # Use the training data midpoint (min + 0.5*range) as the neutral fill value.
            # Filling with raw 0.0 causes extreme negative normalized values for sensors
            # whose training minimum is non-zero (e.g. motor speed min=1400 RPM → normalized=-17.5),
            # which corrupts the entire SAC observation and causes 0% confidence.
            v_type = 'state' if c in s_cols else 'action'
            stats = _env_config['stats'][v_type]
            try:
                col_idx = (s_cols if c in s_cols else a_cols).index(c)
                neutral = float(stats['min'][col_idx]) + 0.5 * float(stats['range'][col_idx])
            except (IndexError, KeyError, TypeError):
                neutral = 0.0
            current_real_df[c] = neutral

    if len(current_real_df) < HISTORY_WINDOW:
        padding = pd.concat([current_real_df.iloc[[0]]] * (HISTORY_WINDOW - len(current_real_df)), ignore_index=True)
        current_real_df = pd.concat([padding, current_real_df], ignore_index=True)

    latest_vals = current_real_df.iloc[-1]

    raw_s = current_real_df[s_cols].tail(HISTORY_WINDOW).values
    raw_a = current_real_df[a_cols].tail(HISTORY_WINDOW).values
    norm_s = _normalize(raw_s, 'state')
    norm_a = _normalize(raw_a, 'action')
    obs = np.concatenate([norm_s, norm_a], axis=1).flatten()

    # Safety catch for the numpy array to prevent PyTorch crashes
    if np.isnan(obs).any() or np.isinf(obs).any():
        print("⚠️ WARNING: Invalid values (NaN/Inf) detected in observation array! Sanitizing...")
        obs = np.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)

    obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(device)

    strat_name = full_config.get('active_strategy', 'BALANCED')
    strat_cfg = full_config.get('strategies', {}).get(strat_name, {})
    strat_weights = strat_cfg.get('weights', {})
    raw_ai_targets = {}

    if SAC_AVAILABLE and _sac_agent is not None:
        action_norm = _sac_agent.select_action(obs, evaluate=True)
        action_real = _denormalize(action_norm, 'action')
        for i, tag in enumerate(a_cols):
            val = float(action_real[i])
            # Apply real-time Strategy Nudge
            if tag in strat_weights:
                val *= (1.0 + float(strat_weights[tag]))
            raw_ai_targets[tag] = val
    else:
        for tag in a_cols:
            raw_ai_targets[tag] = float(latest_vals.get(tag, 0))

    val_confidence = 0.0
    val_prediction = 0.0

    if _world_model is not None:
        _, variance = _world_model.predict(obs_tensor)
        raw_var = variance.mean().item()
        
        # Shield against Python's silent min/max NaN override
        if np.isnan(raw_var) or np.isinf(raw_var):
            val_confidence = 0.0
        else:
            val_confidence = max(0.0, min(100.0, 100.0 * np.exp(-raw_var * 5.0)))
            
        # PROJECT PRIMARY TARGET
        pred_temps = predict_soft_sensor_rollout(current_real_df, target_var_name, steps=15)
        val_prediction = pred_temps[-1] if pred_temps else 0.0
        if np.isnan(val_prediction) or np.isinf(val_prediction): val_prediction = 0.0

    # --------------------------------------------------------------------------
    # POST-PROCESS: Action Packaging & Safety Clamping
    # --------------------------------------------------------------------------
    ui_actions = []
    final_clamped_targets = {}
    
    for tag in a_cols:
        current_val = float(latest_vals.get(tag, 0.0))
        ultimate_goal = raw_ai_targets.get(tag, current_val)

        def_min = controls_cfg.get(tag, {}).get('default_min', -9999)
        def_max = controls_cfg.get(tag, {}).get('default_max', 9999)
        
        # 5% SAFETY CAP: Limits the AI's goal to within +/- 5% of current
        max_deviation = abs(current_val) * 0.05
        if max_deviation < 0.01:
            max_deviation = abs(def_max - def_min) * 0.01
            
        lo_limit = max(def_min, current_val - max_deviation)
        hi_limit = min(def_max, current_val + max_deviation)
        ultimate_goal = max(lo_limit, min(hi_limit, ultimate_goal))
        
        final_clamped_targets[tag] = ultimate_goal

        # Industrial Nudge Calculation
        gain = abs(float(controls_cfg.get(tag, {}).get('nudge_speed', 0.15)))
        nudged_val = apply_industrial_nudge(current_val, ultimate_goal, gain, def_min, def_max)

        ui_actions.append({
            "var_name": tag,
            "fingerprint_set_point": float(ultimate_goal),
            "nudge_target": float(nudged_val),
            "final_target": float(ultimate_goal),
            "current_setpoint": str(round(current_val, 2)),
            "unit": controls_cfg.get(tag, {}).get('unit', ''),
            "reason": "Optimizing (AI-NN)"
        })

    # 2. GENERATE CALCULATED ACTIONS (derived variables)
    calc_vars_cfg = full_config.get('calculated_variables', {})
    indicators_cfg = process_model.get_indicator_variables()
    current_state_map = latest_vals.to_dict()
    mapped_state = {process_model.get_tag_to_name_map().get(k, k): v for k, v in current_state_map.items()}

    calc_actions = process_model.generate_calculated_actions(
        ui_actions, mapped_state, controls_cfg, indicators_cfg, calc_vars_cfg
    )
    
    calc_names = {c['var_name'] for c in calc_actions}
    ui_actions = [a for a in ui_actions if a.get('var_name') not in calc_names]
    ui_actions.extend(calc_actions)

    # 3. GENERATE FULL ROLLOUTS FOR ALL VARIABLES (FOR THE UI CHART)
    ai_rollouts = {}
    if _world_model is not None:
        # Include Controls AND Indicators in the pre-calculated curves
        ui_vars = list(a_cols) + list(s_cols)
        for v in ui_vars:
            if not v: continue
            if v in a_cols:
                curr = float(latest_vals.get(v, 0))
                # Use the finalized clamped target
                target = final_clamped_targets.get(v, curr)
                ramp = []
                for m in range(30):
                    if m <= 10: ramp.append(curr + (target - curr) * (m / 10))
                    else: ramp.append(target)
                ai_rollouts[v] = ramp
            else:
                rollout = predict_soft_sensor_rollout(current_real_df, v, steps=30)
                if rollout: ai_rollouts[v] = [float(x) for x in rollout]

    soft_sensors = {}
    soft_sensors[out_keys['confidence']] = val_confidence
    soft_sensors[out_keys['prediction']] = val_prediction
    for tag, val in final_clamped_targets.items():
        soft_sensors[f"sac_rec_{tag}"] = val

    return {
        "match_score": "SAC-MBRL",
        "confidence": val_confidence,
        "actions": ui_actions,
        "soft_sensors": soft_sensors,
        "fingerprint_prediction": ai_rollouts,
        "active_strategy": "AI"
    }


# ==============================================================================
# 6. OFFLINE TRAINING LOGIC
# ==============================================================================
def train_world_model(df, epochs=10, batch_size=256):
    print(f"   >>> Training World Model ({epochs} epochs)...")
    s_cols = _env_config['s_cols']
    a_cols = _env_config['a_cols']

    raw_s = df[s_cols].values
    raw_a = df[a_cols].values
    norm_s = _normalize(raw_s, 'state')
    norm_a = _normalize(raw_a, 'action')

    dataset = TimeSeriesDataset(norm_s, norm_a, HISTORY_WINDOW)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)

    print(f"       Dataset size: {len(dataset)} samples. Batch size: {batch_size}")

    for epoch in range(epochs):
        epoch_loss = 0
        batch_count = 0
        for batch_x, batch_y in loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            loss = _world_model.train_step(batch_x, batch_y)
            epoch_loss += loss
            batch_count += 1
            if batch_count % 5000 == 0:
                print(f"       [Epoch {epoch}] Batch {batch_count} - Current Loss: {loss:.6f}")

        avg_loss = epoch_loss / max(1, batch_count)
        if epoch % 5 == 0:
            print(f"       Epoch {epoch}: Loss = {avg_loss:.6f}")

    _world_model.save(WM_PATH)
    print("   ✅ World Model Trained & Saved.")


def train_sac_agent(df, steps=2000):
    print(f"   >>> Training SAC Agent ({steps} steps)...")
    if len(df) > 100000:
        print("       Truncating dataset for SAC Env initialization (Last 100k rows)")
        df_subset = df.iloc[-100000:].reset_index(drop=True)
    else:
        df_subset = df

    # Bundle stats and columns correctly for the environment
    env_params = _env_config['stats'].copy()
    env_params['s_cols'] = _env_config['s_cols']
    env_params['a_cols'] = _env_config['a_cols']

    env = PessimisticVirtualEnv(_world_model, df_subset, env_params, HISTORY_WINDOW)
    s_dim = _world_model.input_dim
    a_dim = len(_env_config['a_cols'])
    buffer = ReplayBuffer(capacity=10000, state_dim=s_dim, action_dim=a_dim)

    print("       Collecting initial experience...")
    state = env.reset()
    for _ in range(500):
        action = env.sample_random_action()
        next_state, reward, done, _ = env.step(action)
        buffer.push(state, action, reward, next_state, done)
        state = next_state if not done else env.reset()

    print("       Optimizing Policy...")
    state = env.reset()
    for i in range(steps):
        action_norm = _sac_agent.select_action(state, evaluate=False)
        next_state, reward, done, _ = env.step(action_norm)
        buffer.push(state, action_norm, reward, next_state, done)

        if buffer.size > 256:
            _sac_agent.update_parameters(buffer, batch_size=64)

        state = next_state if not done else env.reset()
        if i % 500 == 0:
            print(f"       Step {i}: Avg Reward = {reward:.4f}")

    _sac_agent.save(SAC_PATH)
    print("   ✅ SAC Agent Trained & Saved.")


def train_system_offline():
    _initialize_system()
    if _world_model is None:
        print("❌ Cannot train: System failed to initialize.")
        return

    s_cols = _env_config['s_cols']
    a_cols = _env_config['a_cols']
    required_cols = list(set(s_cols + a_cols))

    print("\n" + "=" * 50)
    print("   📊 DATA DIAGNOSTICS & PRE-FLIGHT CHECKS")
    print("=" * 50)

    print(f"🔍 Expected {len(required_cols)} target tags from model_config.json")

    try:
        from fingerprint_engine import robust_read_csv
        df_full = robust_read_csv(config.HISTORICAL_DATA_CSV_PATH)
        existing_cols = df_full.columns.tolist()

        valid_cols = [c for c in required_cols if c in existing_cols]
        missing_cols = [c for c in required_cols if c not in existing_cols]

        print(f"✅ Found {len(valid_cols)} matching columns in the Data headers.")

        # 1. LOG MISSING COLUMNS
        if missing_cols:
            print(f"⚠️  Missing {len(missing_cols)} columns! (These will default to 0.0)")
            print(f"   -> Examples: {missing_cols[:5]}")

        if len(valid_cols) == 0:
            print("❌ CRITICAL: 0 matching columns found. Aborting to prevent purely zero dataset.")
            return

        print("⏳ Loading full dataset...")
        df = df_full[valid_cols]
        print(f"📊 Dataset loaded successfully. Shape: {df.shape}")

        # 2. LOG DATA TYPES (European Comma Check)
        sample_col = valid_cols[0]
        dtype = df[sample_col].dtype
        print(f"🔎 Checking raw data types... Sample column '{sample_col}' is type: {dtype}")

        if dtype == 'object':
            sample_val = df[sample_col].dropna().iloc[0] if not df[sample_col].dropna().empty else "N/A"
            print(f"   ⚠️ WARNING: Data is being read as text/strings. Example value: '{sample_val}'")
            print("   -> If it contains commas (e.g., '1450,5'), pd.to_numeric will turn it into 0.0!")

        # Process the data as before
        for c in required_cols:
            if c not in df.columns:
                df[c] = 0.0
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)

        # 3. LOG FINAL ZERO-VARIANCE CHECK
        print("🔎 Verifying data integrity before training...")
        zero_cols = [c for c in required_cols if df[c].abs().sum() == 0.0]

        if len(zero_cols) == len(required_cols):
            print("❌ CRITICAL: ALL columns are completely 0.0! The model will not learn.")
            print("   -> Check for decimal/comma formatting issues in your CSV.")
            return
        elif len(zero_cols) > 0:
            print(f"⚠️  WARNING: {len(zero_cols)} columns contain ONLY zeros. Examples: {zero_cols[:3]}")

        # 4. OUTLIER AUDIT (New Diagnostics)
        print("\n🚩 --- DATA AUDIT: OUTLIER DETECTION ---")
        suspicious_vars = []
        for c in required_cols:
            c_min = df[c].min()
            c_max = df[c].max()
            c_mean = df[c].mean()
            c_median = df[c].median()

            # Logic: If max is more than 100x the median (and median > 1), it's likely a spike
            if c_median > 1.0 and c_max > (c_median * 100):
                suspicious_vars.append(f"  - {c}: Spike Detected (Max: {c_max:.1f} vs Median: {c_median:.1f})")
            
            # Logic: If an indicator that should be positive (O2, Temp, etc) is negative
            if c_min < -0.1 and ('O2' in c or 'Temp' in c or 'production' in c):
                suspicious_vars.append(f"  - {c}: Negative Value (Min: {c_min:.1f})")

        if suspicious_vars:
            print("⚠️ CAUTION: The following variables have extreme ranges that will degrade AI performance:")
            for msg in suspicious_vars:
                print(msg)
            print("🛠️ ACTION: Applying 'Industrial Clamping' to neutralize outliers...")
            
            # --- DATA CLAMPING STEP ---
            all_cfg = {**process_model.get_control_variables(), **process_model.get_indicator_variables()}
            for c in required_cols:
                if c in all_cfg:
                    lo = all_cfg[c].get('default_min', -999999)
                    hi = all_cfg[c].get('default_max', 999999)
                    # If config says 0-100, but data is 4,000,000, clip it to 100
                    df[c] = df[c].clip(lower=lo, upper=hi)
            print("✅ Data Clamped to configuration ranges.")
        else:
            print("✅ No extreme outliers detected in the active feature set.")

    except Exception as e:
        print(f"❌ CRITICAL Error reading CSV during diagnostics: {e}")
        return

    print("=" * 50 + "\n")

    # 1. TRAIN WORLD MODEL
    train_world_model(df, epochs=10)

    # 2. TRAIN SAC AGENT
    if SAC_AVAILABLE:
        train_sac_agent(df, steps=50000)
    else:
        print("⚠️ SAC Agent module missing. Skipping policy training.")
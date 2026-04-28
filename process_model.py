import json
import os
import config
import pandas as pd
import numpy as np
import re

# ==============================================================================
# 1. CONFIGURATION MANAGEMENT
# ==============================================================================
def load_model_config():
    """Loads the central configuration for variables and limits."""
    try:
        if os.path.exists(config.MODEL_CONFIG_PATH):
            with open(config.MODEL_CONFIG_PATH, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Config Load Error: {e}")

    return {"model_name": "Default", "control_variables": {}, "indicator_variables": {}}

def save_model_config(new_config):
    """Saves updated configuration to disk."""
    try:
        with open(config.MODEL_CONFIG_PATH, 'w') as f:
            json.dump(new_config, f, indent=2)
        return True, "Saved"
    except Exception as e:
        return False, str(e)

def apply_industrial_nudge(current, target, gain, def_min, def_max):
    """
    Applies a fractional gain nudge with a 1% span-based safety floor.
    Standard Industrial calculation for setpoint ramping.
    """
    gap = target - current
    span = abs(def_max - def_min)
    
    # Safety Floor: 1.0% of Span (or 0.1 for unit-less/default placeholders)
    # Reducing from 5% to 1% to allow for finer control adjustments
    min_push = max(0.001, (min(span, 10000) * 0.01)) if span > 0.001 else 0.1
    
    if abs(gap) > 0.001:
        # Move is the LARGER of (gap * gain) or (1% of span floor)
        move_request = max(abs(gap * gain), min_push)
        # But never move further than the remaining gap itself
        return current + np.sign(gap) * min(move_request, abs(gap))
    else:
        return target

def apply_signal_filters(df):
    """
    Applies Rolling Median (Despiking) and Exponential Moving Average (EMA) (Smoothing)
    to historical and real-time data exactly as configured in model_config.json.
    """
    if df.empty: return df
    conf = load_model_config()
    
    # Check all variables for filtering config
    all_vars = {**conf.get('control_variables', {}), **conf.get('indicator_variables', {})}
    
    for friendly_name, cfg in all_vars.items():
        filter_cfg = cfg.get('filtering', {})
        if not filter_cfg.get('enabled', False):
            continue
            
        tag_name = cfg.get('tag_name', friendly_name)
        if tag_name not in df.columns:
            continue
            
        # 1. Rolling Median (Outlier/Spike Rejection)
        median_window = int(filter_cfg.get('median_window', 1))
        if median_window > 1:
            df[tag_name] = df[tag_name].rolling(window=median_window, min_periods=1).median()
            
        # 2. Exponential Moving Average (High Frequency Noise Smoothing)
        ema_alpha = float(filter_cfg.get('ema_alpha', 1.0))
        if ema_alpha < 1.0:
            df[tag_name] = df[tag_name].ewm(alpha=ema_alpha, adjust=False).mean()
            
    return df

# ==============================================================================
# 2. VARIABLE HELPERS
# ==============================================================================
def get_control_variables():
    conf = load_model_config()
    controls = conf.get('control_variables', {}).copy()
    calc = conf.get('calculated_variables', {})
    # Plan B: Materialize calculated variables as first-class controls
    for k, v in calc.items():
        if v.get('is_control') is True:
            friendly = v.get('friendly_name', k)
            cfg_copy = v.copy()
            cfg_copy['is_calculated'] = True
            controls[friendly] = cfg_copy
    return controls

def get_indicator_variables():
    conf = load_model_config()
    indicators = conf.get('indicator_variables', {}).copy()
    calc = conf.get('calculated_variables', {})
    # Plan B: Materialize calculated variables as first-class indicators
    for k, v in calc.items():
        if v.get('is_indicator') is True:
            friendly = v.get('friendly_name', k)
            cfg_copy = v.copy()
            cfg_copy['is_calculated'] = True
            indicators[friendly] = cfg_copy
    return indicators

def get_tag_to_name_map():
    """Maps DB Column Names -> Human Friendly Names"""
    conf = load_model_config()
    mapping = {}
    
    sections = ['control_variables', 'indicator_variables', 'calculated_variables']
    for section in sections:
        for name, data in conf.get(section, {}).items():
            # If tag_name is present, use it. Otherwise, default to the key name.
            tag = data.get('tag_name', name)
            mapping[tag] = name
            
    return mapping

def get_name_to_tag_map():
    """Maps Human Friendly Names -> DB Column Names"""
    tag_map = get_tag_to_name_map()
    return {v: k for k, v in tag_map.items()}

# ==============================================================================
# 3. DATA FORMATTERS (API RESPONSES)
# ==============================================================================
def build_api_response(real_df, match_row, future_df, score, confidence, mode):
    """
    Main Aggregator: Joins raw sensor recommendations with calculated metrics.
    Keeping the Core Engines 100% clean and independent.
    """
    controls = get_control_variables()
    indicators = get_indicator_variables()
    conf = load_model_config()
    calc_vars_cfg = conf.get('calculated_variables', {})

    # 1. SCORE CALCULATION
    # Legacy auto-correction removed to ensure Honest Fallback (0.0%) is preserved.
    if score is None: score = 0.0

    # 2. RAW ACTIONS (From NN/Fingerprint)
    actions = []
    current_state = real_df.iloc[-1].to_dict() if not real_df.empty else {}
    
    for var, data in controls.items():
        col = data.get('tag_name', var)
        try:
            # DataFrames are already renamed to friendly names, so look up by
            # friendly name (var) first, then fall back to raw tag_name (col)
            curr_val = float(current_state.get(var, current_state.get(col, 0.0)))
            target_val = float(match_row.get(var, match_row.get(col, 0.0)))
        except: continue

        diff = target_val - curr_val
        reason = "Stable"
        if abs(diff) > 0.1:
            pct = abs(diff / curr_val) if curr_val != 0 else 0
            reason = "Optimizing" if pct < 0.02 else ("Ramping" if diff > 0 else "Ramping")

        actions.append({
            "var_name": var,
            "current_setpoint": curr_val,
            "fingerprint_set_point": target_val,
            "final_target": target_val,
            "diff": diff,
            "reason": reason,
            "type": "Control"
        })

    # 3. CALCULATED INDEPENDENT ACTIONS
    tag_to_name = get_tag_to_name_map()
    mapped_state = {tag_to_name.get(k, k): v for k, v in current_state.items()}
    
    # Independent calculation join
    calc_actions = generate_calculated_actions(actions, mapped_state, controls, indicators, calc_vars_cfg)
    
    # Remove naive raw actions that are overwritten by calculated targets
    calc_names = {c['var_name'] for c in calc_actions}
    actions = [a for a in actions if a.get('var_name') not in calc_names]
    
    actions.extend(calc_actions)

    # 4. CHART DATA
    live_history = {}
    fingerprint_pred = {}
    
    clean_real = real_df.copy()
    clean_real.columns = [str(c).strip() for c in clean_real.columns]
    clean_future = future_df.copy()
    clean_future.columns = [str(c).strip() for c in clean_future.columns]

    top_vars = list(controls.keys())[:5]
    for v in top_vars:
        col = controls[v].get('tag_name', v)
        # Try friendly name first, then raw tag_name
        real_col = v if v in clean_real.columns else (col if col in clean_real.columns else None)
        fut_col = v if v in clean_future.columns else (col if col in clean_future.columns else None)
        if real_col:
            live_history[v] = clean_real[real_col].fillna(0).tolist()
        if fut_col:
            fingerprint_pred[v] = clean_future[fut_col].fillna(0).tolist()

    return {
        "match_score": score,
        "confidence": confidence,
        "fingerprint_timestamp": str(match_row.get(config.TIMESTAMP_COLUMN, "N/A")),
        "actions": actions,
        "live_history": live_history,
        "fingerprint_prediction": fingerprint_pred,
        "top_variables": top_vars
    }

def build_no_fingerprint_response(current_state):
    return {
        "fingerprint_Found": "False",
        "match_score": 0,
        "actions": [],
        "debug_message": "No valid historical match found."
    }

# ==============================================================================
# 4. UTILS & STRATEGY HELPERS
# ==============================================================================
def get_optimization_weights():
    """
    Returns weights for directional optimization. 
    Default is 0.0 because optimization is strategy-driven.
    """
    conf = load_model_config()
    weights = {}
    for var in conf.get('control_variables', {}).keys():
        weights[var] = 0.0
    return weights

# ==============================================================================
# 4. FORMULA ENGINE (INTEGRATED)
# ==============================================================================
def preprocess_formula(formula, sorted_variable_names):
    """Wraps variable names containing spaces or operators in backticks for Pandas eval()."""
    processed = formula
    for v in sorted_variable_names:
        # Wrap if name contains spaces or common math operators that would break eval()
        if any(c in v for c in ' /-()+*%'):
            pattern = r'(?<!`)\b' + re.escape(v) + r'\b(?!`)'
            processed = re.sub(pattern, f"`{v}`", processed)
    return processed

def evaluate_formulas(state_map, controls_cfg, indicators_cfg, calc_vars_cfg):
    """Evaluates formulas based on the current state_map."""
    if not calc_vars_cfg: return {}
    new_values = {}
    lookup_keys = set(controls_cfg.keys()) | set(indicators_cfg.keys()) | {v.get('friendly_name', k) for k,v in calc_vars_cfg.items()}
    sorted_vars = sorted(list(lookup_keys), key=len, reverse=True)
    try:
        temp_df = pd.DataFrame([state_map])
        for _, cfg in calc_vars_cfg.items():
            formula = cfg.get('formula')
            friendly_name = cfg.get('friendly_name')
            if not formula or not friendly_name: continue
            processed_formula = preprocess_formula(formula, sorted_vars)
            try:
                result = temp_df.eval(processed_formula)
                val = float(result.iloc[0])
                new_values[friendly_name] = val
                temp_df[friendly_name] = val
            except Exception as e:
                # print(f"DEBUG Error for '{friendly_name}': {e}")
                new_values[friendly_name] = 0.0
    except Exception: pass
    return new_values

def materialize_df(df, controls_cfg, indicators_cfg, calc_vars_cfg):
    """Enriches a DataFrame with all calculated variables defined in the config."""
    if df.empty or not calc_vars_cfg: return df
    lookup_keys = set(controls_cfg.keys()) | set(indicators_cfg.keys()) | {v.get('friendly_name', k) for k, v in calc_vars_cfg.items()}
    sorted_vars = sorted(list(lookup_keys), key=len, reverse=True)
    enriched_df = df.copy()
    for _, cfg in calc_vars_cfg.items():
        formula = cfg.get('formula')
        friendly_name = cfg.get('friendly_name')
        if not formula or not friendly_name: continue
        try:
            processed_formula = preprocess_formula(formula, sorted_vars)
            enriched_df[friendly_name] = enriched_df.eval(processed_formula)
        except Exception:
            if friendly_name not in enriched_df.columns: enriched_df[friendly_name] = 0.0
    return enriched_df

def generate_calculated_actions(raw_actions, state_map, controls_cfg, indicators_cfg, calc_vars_cfg):
    """Generates 'Action' objects for derived variables with built-in safety nudging."""
    if not calc_vars_cfg: return []
    
    full_conf = load_model_config()
    nudge_cfg = full_conf.get('nudge_settings', {})
    default_step_fraction = nudge_cfg.get('step_fraction', 0.15)

    target_context = state_map.copy()
    for action in raw_actions:
        # Use absolute targets to evaluate the formula's eventual goal
        target_context[action['var_name']] = action['fingerprint_set_point']
        
    calculated_targets = evaluate_formulas(target_context, controls_cfg, indicators_cfg, calc_vars_cfg)
    calculated_currents = evaluate_formulas(state_map, controls_cfg, indicators_cfg, calc_vars_cfg)
    
    new_actions = []
    for k, cfg in calc_vars_cfg.items():
        if cfg.get('is_control'):
            name = cfg.get('friendly_name', k)
            curr_val = float(calculated_currents.get(name, 0.0))
            target_val = float(calculated_targets.get(name, 0.0))
            
            # 1. Clamping to absolute limits
            def_min, def_max = cfg.get('default_min', -9999), cfg.get('default_max', 9999)
            target_val = max(def_min, min(def_max, target_val))
            
            # 2. Industrial Nudge Calculation (Centralized utility)
            gain = abs(float(cfg.get('nudge_speed', default_step_fraction))) # Treated as gain (0.0-1.0)
            
            nudged_target = apply_industrial_nudge(
                curr_val, target_val, gain, def_min, def_max
            )
            
            if abs(nudged_target - target_val) < 0.001:
                reason = "Calculated (Synced)"
            else:
                reason = "Calculated (Nudge Applied)"

            new_actions.append({
                "var_name": name, 
                "current_setpoint": curr_val,
                "fingerprint_set_point": target_val, # Final absolute target
                "nudge_target": nudged_target,      # Safe absolute step
                "final_target": target_val,
                "diff": nudged_target - curr_val,
                "reason": reason, 
                "type": "Control", 
                "is_calculated": True
            })
    return new_actions

def finalize_setpoints_for_db(recommendation, current_state, config):
    """
    Centralized point-of-entry for the Industrial Nudge.
    Ensures that regardless of which engine (AI/FP) proposed the target, 
    the value written to InfluxDB is ALWAYS the safely nudged one.
    """
    controls_cfg = config.get('control_variables', {})
    nudge_cfg = config.get('nudge_settings', {})
    default_gain = nudge_cfg.get('step_fraction', 0.15)
    
    setpoints = {}
    actions = recommendation.get('actions', [])
    
    for act in actions:
        name = act.get('var_name')
        if not name: continue
        
        # 1. Start with the Final Goal from the Engine
        # We prefer 'fingerprint_set_point' or 'final_target' as the master goal
        target = float(act.get('fingerprint_set_point') or act.get('final_target') or 0.0)
        curr = float(current_state.get(name, 0.0) or 0.0)
        
        # 2. Get Nudge Config
        # Nudge ONLY applies to Control Variables. Indicators/Calculated jump 100%.
        if name in controls_cfg:
            gain = abs(float(controls_cfg[name].get('nudge_speed', default_gain)))
            def_min = float(controls_cfg[name].get('default_min', -9999))
            def_max = float(controls_cfg[name].get('default_max', 9999))
        else:
            # Indicators/Calc/Misc -> 100% gain (Full Jump)
            gain = 1.0
            def_min, def_max = -9999, 9999
            
        # 3. Apply the One-and-Only Industrial Nudge formula
        nudged_val = apply_industrial_nudge(curr, target, gain, def_min, def_max)
        
        # 4. Final output assignment
        setpoints[name] = nudged_val
        
        # Update the action object in-place so UI is synced exactly to DB log
        act['nudge_target'] = round(float(nudged_val), 4)

    return setpoints


def get_setpoint_tag_map():
    """Maps Friendly Name -> PLC Write Tag (Includes Calculated Setpoints)"""
    conf = load_model_config()
    mapping = {}
    
    # Standard Controls
    for name, data in conf.get('control_variables', {}).items():
        if data.get('is_setpoint'):
            mapping[name] = data.get('tag_name', name)
            
    # Calculated Controls
    for name, data in conf.get('calculated_variables', {}).items():
        if data.get('is_setpoint'):
            # Default to friendly_name or key name if tag_name is missing
            mapping[name] = data.get('tag_name', data.get('friendly_name', name))
            
    return mapping

def get_setpoint_scale_factors():
    """Returns scaling factors for all setpoint types."""
    conf = load_model_config()
    factors = {}
    
    # Standard Controls
    for name, data in conf.get('control_variables', {}).items():
        if 'scale_factor' in data or 'scale' in data:
            factors[name] = data.get('scale_factor', data.get('scale', 1.0))
            
    # Calculated Controls
    for name, data in conf.get('calculated_variables', {}).items():
        if 'scale_factor' in data or 'scale' in data:
            factors[name] = data.get('scale_factor', data.get('scale', 1.0))
            
    return factors
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
            
        target_col = friendly_name
        if target_col not in df.columns:
            continue
            
        # 1. Rolling Median (Outlier/Spike Rejection)
        median_window = int(filter_cfg.get('median_window', 1))
        if median_window > 1:
            s = df[target_col].dropna()
            if not s.empty:
                s_events = s.loc[s.shift() != s]
                filtered = s_events.rolling(window=median_window, min_periods=1).median()
                df[target_col] = filtered.reindex(s.index).ffill()
            
        # 2. Exponential Moving Average (High Frequency Noise Smoothing)
        ema_alpha = float(filter_cfg.get('ema_alpha', 1.0))
        if ema_alpha < 1.0:
            s = df[target_col].dropna()
            if not s.empty:
                s_events = s.loc[s.shift() != s]
                filtered = s_events.ewm(alpha=ema_alpha, adjust=False).mean()
                df[target_col] = filtered.reindex(s.index).ffill()
            
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

    # 1. FINAL TARGET CONTEXT (The ultimate goal)
    target_context = state_map.copy()
    # 2. NUDGE CONTEXT (The immediate commanded step)
    nudge_context = state_map.copy()

    for action in raw_actions:
        # Use absolute targets for the final goal
        target_context[action['var_name']] = action.get('fingerprint_set_point', action.get('final_target', state_map.get(action['var_name'])))
        # Use nudged targets for the immediate step
        nudge_context[action['var_name']] = action.get('nudge_target', target_context[action['var_name']])
        
    calculated_targets = evaluate_formulas(target_context, controls_cfg, indicators_cfg, calc_vars_cfg)
    calculated_nudges = evaluate_formulas(nudge_context, controls_cfg, indicators_cfg, calc_vars_cfg)
    calculated_currents = evaluate_formulas(state_map, controls_cfg, indicators_cfg, calc_vars_cfg)
    
    new_actions = []
    for k, cfg in calc_vars_cfg.items():
        if cfg.get('is_control') or cfg.get('is_setpoint'):
            name = cfg.get('friendly_name', k)
            curr_val = float(calculated_currents.get(name, 0.0))
            final_target = float(calculated_targets.get(name, 0.0))
            
            # The nudged target for a calculated variable is the result of the formula
            # applied to the nudged inputs. This ensures perfect synchronicity.
            sync_nudge = float(calculated_nudges.get(name, final_target))
            
            # 1. Clamping to absolute limits
            def_min, def_max = cfg.get('default_min', -9999), cfg.get('default_max', 9999)
            final_target = max(def_min, min(def_max, final_target))
            sync_nudge = max(def_min, min(def_max, sync_nudge))
            
            # 2. Safety Check: If the user explicitly defined a nudge_speed for the CALC variable,
            # we respect it as a secondary damper, but usually it should be 1.0 (fully synchronous).
            gain = abs(float(cfg.get('nudge_speed', 1.0))) 
            if gain < 0.99:
                # Apply secondary damping if configured
                nudged_target = apply_industrial_nudge(curr_val, sync_nudge, gain, def_min, def_max)
            else:
                nudged_target = sync_nudge

            if abs(nudged_target - final_target) < 0.001:
                reason = "Calculated (Synced)"
            else:
                reason = "Calculated (Nudging)"

            new_actions.append({
                "var_name": name, 
                "current_setpoint": curr_val,
                "fingerprint_set_point": final_target, # Final absolute target
                "nudge_target": nudged_target,         # Safe synchronous step
                "final_target": final_target,
                "diff": nudged_target - curr_val,
                "reason": reason, 
                "type": "Control", 
                "is_calculated": True
            })
    return new_actions

def finalize_setpoints_for_db(recommendation, current_state, config):
    """
    Centralized point-of-entry for writing setpoints to InfluxDB.
    Uses the engine's pre-computed nudge_target directly.
    The engine (FP or NN) computes nudge_target using the correct live data (real_df).
    We do NOT recompute here to avoid stale/wrong current_state issues.
    """
    setpoints = {}
    actions = recommendation.get('actions', [])

    for act in actions:
        name = act.get('var_name')
        if not name: continue

        # Use the engine's pre-computed nudge_target.
        # This is what the UI shows, and this is what should be written to the DB.
        nudge_val = act.get('nudge_target')
        if nudge_val is not None:
            setpoints[name] = float(nudge_val)
        else:
            # Fallback: use fingerprint_set_point (raw target) if nudge not available
            raw = act.get('fingerprint_set_point') or act.get('final_target') or act.get('setpoint')
            if raw is not None:
                setpoints[name] = float(raw)

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

def extract_future_from_history(hist_df, match_timestamp, window_min=15):
    """
    Extracts the 'Future Path' for all sensors from a matched batch.
    Used by the Operator Summary page to show dynamic predicted trends.
    """
    if hist_df is None or hist_df.empty or not match_timestamp:
        return {}

    try:
        ts_col = getattr(config, 'TIMESTAMP_COLUMN', "1_timeStamp")
        # Find the index of the match
        match_idx_list = hist_df.index[hist_df[ts_col].astype(str) == str(match_timestamp)].tolist()
        if not match_idx_list:
            return {}
        
        start_idx = match_idx_list[0]
        # Extract the window (assuming 1-minute steps in history, or use row count as proxy)
        # We take 16 points to match the 0-15m window on the UI
        future_slice = hist_df.iloc[start_idx : start_idx + window_min + 1]
        
        predictions = {}
        # Get all relevant tags (Controls and Indicators)
        controls = get_control_variables()
        indicators = get_indicator_variables()
        target_tags = list(controls.keys()) + list(indicators.keys())
        
        for tag in target_tags:
            if tag in future_slice.columns:
                # Fill NaNs with 0 to prevent JSON breakage
                predictions[tag] = future_slice[tag].fillna(0).tolist()
        
        return predictions
    except Exception as e:
        print(f"Error extracting future trend: {e}")
        return {}
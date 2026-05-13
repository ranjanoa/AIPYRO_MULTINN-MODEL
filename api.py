from flask import Blueprint, request, jsonify, current_app
from flask_socketio import emit
from flask_cors import cross_origin
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import os
import plotly.graph_objects as go
import traceback

# --- IMPORTS ---
import config
import database
import process_model
import fingerprint_engine

# Safely import AI
try:
    from modules.ai_core import mbrl_manager
except ImportError:
    mbrl_manager = None
import control_service

api_routes = Blueprint('api', __name__)

# --- PERSISTENCE PATHS ---
TARGET_FILE = os.path.join(config.JSON_DIR, "current_target.json")
STATE_FILE = os.path.join(config.JSON_DIR, "system_state.json")


# --- STATE MANAGEMENT FUNCTIONS ---
def save_system_state():
    """Saves the current control mode, strategy preference, and test mode to disk."""
    state = {
        "control_mode": config.CONTROL_MODE,
        "fingerprint_mode": config.FINGERPRINT_MODE_TYPE,
        "selected_strategy": getattr(config, 'SELECTED_STRATEGY', 'AI'),
        "test_mode": getattr(config, 'TEST_MODE', False),
        "ai_mnm_base_strategy": getattr(config, 'AI_MNM_BASE_STRATEGY', 'FINGERPRINT')
    }
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=4)
    except Exception as e:
        print(f"Failed to save state: {e}")


def load_system_state():
    """Loads the last known state on startup."""
    if not os.path.exists(STATE_FILE): return
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            config.CONTROL_MODE = state.get("control_mode", 0)
            config.FINGERPRINT_MODE_TYPE = state.get("fingerprint_mode", 'AUTO')
            config.TEST_MODE = state.get("test_mode", False)
            config.SELECTED_STRATEGY = state.get("selected_strategy", "AI")
            config.AI_MNM_BASE_STRATEGY = state.get("ai_mnm_base_strategy", "FINGERPRINT")

            print(
                f"System State Restored: Mode={config.CONTROL_MODE}, Strategy={config.SELECTED_STRATEGY}, Test={config.TEST_MODE}")

            if config.CONTROL_MODE > 0:
                control_service.service.set_enabled(True)

    except Exception as e:
        print(f"Failed to load state: {e}")


# Load state immediately when API initializes
load_system_state()


# ==============================================================================
# 1. AUTOPILOT CONTROL (The Engage Button)
# ==============================================================================
@api_routes.route('/autoloop', methods=['POST'])
@cross_origin()
def toggle_autopilot():
    """
    Handles the ENGAGE/DISENGAGE button click from the UI.
    """
    try:
        data = request.get_json()

        strategy = data.get('strategy', 'AI')
        should_enable = data.get('enabled', False)
        target_batch = data.get('target_data') or data.get('target_batch')
        is_test_mode = data.get('test_mode', False)
        # Optional base strategy used when AI_MNM overlays the 6 CV setpoints on
        # top of an existing engine (Fingerprint / AI / Hybrid).
        base_strategy = (data.get('base_strategy') or 'FINGERPRINT').upper()

        config.SELECTED_STRATEGY = strategy
        config.TEST_MODE = bool(is_test_mode)
        config.AI_MNM_BASE_STRATEGY = base_strategy

        if not should_enable:
            config.CONTROL_MODE = 0
            msg = "System Disengaged (Monitor Mode)"
        else:
            if strategy == 'AI':
                config.CONTROL_MODE = 1
                msg = "Engaged: Neural Network Control"

            # === START OF CHANGED BLOCK ===
            elif strategy == 'FINGERPRINT':
                config.CONTROL_MODE = 2

                if target_batch:
                    # Case A: User selected a specific new batch -> MANUAL
                    # We save this selection and lock the mode.
                    with open(TARGET_FILE, 'w') as f:
                        json.dump(target_batch, f, indent=4)
                    config.FINGERPRINT_MODE_TYPE = 'MANUAL'
                    msg = "Engaged: Fingerprint Locked on Selection"

                else:
                    # Case B: No batch selected -> Force AUTO
                    # We explicitly DELETE the old target file so the system doesn't
                    # accidentally "Resume" an old target from the past.
                    if os.path.exists(TARGET_FILE):
                        try:
                            os.remove(TARGET_FILE)
                        except Exception as e:
                            print(f"Warning: Could not remove old target file: {e}")

                    config.FINGERPRINT_MODE_TYPE = 'AUTO'
                    msg = "Engaged: Fingerprint Auto-Search"
            # === END OF CHANGED BLOCK ===

            elif strategy == 'HYBRID':
                config.CONTROL_MODE = 3
                msg = "Engaged: Hybrid Auto-Arbitration Mode"

            elif strategy == 'AI_MNM':
                # AI_MNM overlays 6 CV setpoints sourced from cimpor_data_result on
                # top of a configurable base engine. CONTROL_MODE 4 is the AI_MNM tag.
                config.CONTROL_MODE = 4
                msg = f"Engaged: AI_MNM Overlay (Base={base_strategy})"

            else:
                config.CONTROL_MODE = 0
                msg = "Unknown Strategy"

        control_service.service.set_enabled(should_enable)
        
        # --- IMMEDIATE UI RESET ---
        # Force the dashboard to clear stale AI/FP curves immediately on mode switch
        emit('autopilot_recommendation', {
            "active_strategy": "MANUAL" if not should_enable else strategy,
            "driver": "SWITCHING...",
            "actions": [],
            "match_score": 0,
            "fingerprint_prediction": {}
        }, broadcast=True, namespace='/')

        if config.TEST_MODE:
            msg += " [TEST MODE ACTIVE]"

        print(f"SYSTEM {msg}")
        save_system_state()

        return jsonify({
            "status": "success",
            "message": msg,
            "mode": config.CONTROL_MODE,
            "fingerprint_type": getattr(config, 'FINGERPRINT_MODE_TYPE', 'AUTO'),
            "enabled": should_enable
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# 1b. STATUS CHECK
# ==============================================================================
@api_routes.route('/fingerprint/mode', methods=['POST'])
@cross_origin()
def set_fingerprint_mode():
    """Update the preferred fingerprint search mode (AUTO/MANUAL) without engaging."""
    try:
        data = request.get_json()
        mode = data.get('mode', 'AUTO')
        config.FINGERPRINT_MODE_TYPE = mode
        save_system_state()
        return jsonify({"status": "success", "mode": mode})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_routes.route('/status', methods=['GET'])
@cross_origin()
def get_system_status():
    active_target = {}
    if config.FINGERPRINT_MODE_TYPE == 'MANUAL' and os.path.exists(TARGET_FILE):
        try:
            with open(TARGET_FILE, 'r') as f:
                active_target = json.load(f)
        except:
            pass

    strategy_pref = getattr(config, 'SELECTED_STRATEGY', 'AI')

    return jsonify({
        "enabled": config.CONTROL_MODE > 0,
        "mode": config.CONTROL_MODE,
        "strategy": strategy_pref,
        "fingerprint_type": config.FINGERPRINT_MODE_TYPE,
        "test_mode": getattr(config, 'TEST_MODE', False),
        "active_target": active_target
    })


# ==============================================================================
# 2. FINGERPRINT SEARCH
# ==============================================================================
@api_routes.route('/fingerprint', methods=['POST'])
@cross_origin()
def find_fingerprint():
    try:
        # --- FIXED LOGIC: Only Lock if ENGAGED (Mode 2) ---
        # If we are in Monitor Mode (Mode 0), we skip this block and run the full search below.
        if config.CONTROL_MODE == 2 and config.FINGERPRINT_MODE_TYPE == 'MANUAL' and os.path.exists(TARGET_FILE):
            try:
                with open(TARGET_FILE, 'r') as f:
                    saved_target = json.load(f)

                # RECONSTRUCT RAW ROW (Restores values if missing)
                controls_cfg = process_model.get_control_variables()
                reconstructed_row = {}

                if 'actions' in saved_target:
                    for act in saved_target['actions']:
                        friendly_name = act.get('var_name')
                        val = act.get('fingerprint_set_point', 0)

                        if friendly_name:
                            reconstructed_row[friendly_name] = val
                            if friendly_name in controls_cfg:
                                tag_name = controls_cfg[friendly_name].get('tag_name', friendly_name)
                                reconstructed_row[tag_name] = val

                if not reconstructed_row:
                    reconstructed_row = saved_target

                # Retrieve current real-time data
                tag_map = process_model.get_tag_to_name_map()
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(minutes=30)
                real_df = database.get_realtime_data_window(start_time, end_time, list(tag_map.keys()), tag_map)

                # Reconstruct process context
                controls_cfg = process_model.get_control_variables()
                indicators_cfg = process_model.get_indicator_variables()
                
                # ARCHIVAL FIX: Calculate teal similarity for the engaged manual target
                sim_pct = fingerprint_engine.calculate_match_percentage(
                    current_state.to_dict() if hasattr(current_state, 'to_dict') else dict(current_state), 
                    reconstructed_row, 
                    controls_cfg,
                    indicators_cfg
                )

                future_df = pd.DataFrame([reconstructed_row] * 30)
                api_obj = process_model.build_api_response(real_df, reconstructed_row, future_df, sim_pct, 0, 0)

                if 'fingerprint_timestamp' in saved_target:
                    api_obj['fingerprint_timestamp'] = saved_target['fingerprint_timestamp']

                api_obj['match_score'] = sim_pct

                return jsonify({"data": [api_obj]})
            except Exception as e:
                print(f"Manual Load Error: {e}")
                pass
                # --- END FIXED LOGIC ---

        # === STANDARD SEARCH LOGIC (Runs for Disengaged/Monitor Mode) ===
        req_data = request.get_json()
        engine_logger = fingerprint_engine.engine_logger
        engine_logger.info(f"[API] Search Request received. Constraints: {list(req_data.get('deviation', {}).keys())}")
        
        prev_time = req_data.get("previous_Time", config.DEFAULT_PREVIOUS_TIME)
        future_time = 60
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=prev_time)
        tag_map = process_model.get_tag_to_name_map()

        real_df = database.get_realtime_data_window(start_time, end_time, list(tag_map.keys()), tag_map)

        hist_df = current_app.config.get('df_fingerprint')
        if hist_df is not None:
            hist_df.columns = [str(c).strip() for c in hist_df.columns]
            if config.TIMESTAMP_COLUMN in hist_df.columns:
                hist_df[config.TIMESTAMP_COLUMN] = pd.to_datetime(hist_df[config.TIMESTAMP_COLUMN])

        if real_df.empty:
            if hist_df is not None and not hist_df.empty:
                real_df = hist_df.tail(30).copy()
            else:
                return jsonify({"error": "No data available"}), 500

        current_state = real_df.iloc[-1]

        # 1. Configuration & Weights
        weights = process_model.get_optimization_weights()
        controls_cfg = process_model.get_control_variables()
        indicators_cfg = process_model.get_indicator_variables()
        
        # 2. Unified Advanced Search (Consistent with AUTO mode)
        # This applies the Golden Filter, Multi-Phase Search, and Slope-Aware Ranking.
        strategy = req_data.get("deviation", {})
        top_matches_raw, is_fallback = fingerprint_engine.find_best_fingerprint_advanced(
            real_df, hist_df, strategy, current_state, weights
        )

        formatted_results = []
        ts_col = config.TIMESTAMP_COLUMN
        
        for i, row_dict in enumerate(top_matches_raw):
            try:
                # Reconstruct row from dict for build_api_response compatibility
                row = pd.Series(row_dict)
                ts = row.get(ts_col)
                
                # Retrieve the 60-minute future window from history for visualization
                target_ts = pd.to_datetime(ts)
                matches = hist_df.index[pd.to_datetime(hist_df[ts_col]) == target_ts].tolist()
                
                pred_df = None
                if matches:
                    idx = matches[0]
                    future_time = 60
                    pred_df = hist_df.iloc[idx: idx + future_time].copy()
                    
                    if len(pred_df) < future_time:
                        last_row = pred_df.iloc[-1:]
                        padding = pd.concat([last_row] * (future_time - len(pred_df)))
                        pred_df = pd.concat([pred_df, padding])
                else:
                    engine_logger.warning(f"  [API] Visualization window not found for {ts}. Using dummy padding.")
                    pred_df = pd.DataFrame([row_dict] * 60)

                # Calculate physical similarity score (0-100%)
                sim_pct = fingerprint_engine.calculate_match_percentage(
                    current_state.to_dict() if hasattr(current_state, 'to_dict') else dict(current_state), 
                    row_dict, 
                    controls_cfg,
                    indicators_cfg
                )

                if is_fallback: sim_pct = 0.0

                api_obj = process_model.build_api_response(real_df, row, pred_df, sim_pct, 0, 0)
                formatted_results.append(api_obj)
            except Exception as e:
                engine_logger.error(f"  [API] Match {i+1} formatting error: {str(e)}")
                continue

        # Final Sort: Ensure the UI shows the highest Similarity % first
        formatted_results.sort(key=lambda x: float(x.get('match_score', 0)), reverse=True)

        if not formatted_results:
            engine_logger.warning("[API] All matches failed formatting. Returning no-fingerprint response.")
            return jsonify({"data": [process_model.build_no_fingerprint_response(current_state)]})

        return jsonify({"data": formatted_results})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# 3. CONFIGURATION MANAGEMENT
# ==============================================================================
@api_routes.route('/config', methods=['GET', 'POST'])
@cross_origin()
def handle_config():
    if request.method == 'GET':
        return jsonify(process_model.load_model_config())
    elif request.method == 'POST':
        success, msg = process_model.save_model_config(request.get_json())
        if success:
            process_model.load_model_config()
            return jsonify({"status": "success"})
        return jsonify({"error": msg}), 500


@api_routes.route('/history/sync', methods=['POST'])
@cross_origin()
def sync_history():
    return jsonify({"status": "success", "message": "Sync initiated"})


# ==============================================================================
# 3b. AI_MNM ENDPOINTS
# ==============================================================================
@api_routes.route('/aimnm/values', methods=['GET'])
@cross_origin()
def get_aimnm_values():
    """
    Returns latest AI_MNM Curr/SP pairs for the operator AI_MNM tab.
    Source-of-truth field names come from model_config.json -> ai_mnm:
      cv_parameters[<param>].curr_field   (read from cimpor_data_result)
      cv_parameters[<param>].sp_field     (read from cimpor_data_result)
    Side effect: every CV pair just read is mirrored into kiln2 as aimnm_<param> SP fields.
    """
    try:
        cfg = process_model.load_model_config() or {}
        ai_mnm_cfg = cfg.get('ai_mnm', {}) or {}
        cv_spec  = ai_mnm_cfg.get('cv_parameters', {}) or {}
        ind_spec = ai_mnm_cfg.get('indicator_parameters', {}) or {}

        cdr = database.get_aimnm_results(window_minutes=10) or {}
        ts = cdr.pop('_time', None)
        cdr_keys_lower = {k.lower(): k for k in cdr.keys()}

        # --- MEASUREMENT NAME SAFETY CHECK ---
        # Try primary config name, but fallback to singular if plural (or vice-versa) if empty
        if not cdr:
            alt_measurement = "cimpor_data_result" if config.DB_MEASUREMENT_AI_MNM_RESULT.endswith('s') else config.DB_MEASUREMENT_AI_MNM_RESULT + 's'
            cdr = database.get_aimnm_results(window_minutes=10, measurement_override=alt_measurement) or {}
            if cdr:
                print(f"[AI_MNM] Data found in alternate measurement: {alt_measurement}")
                ts = cdr.pop('_time', None)
                cdr_keys_lower = {k.lower(): k for k in cdr.keys()}

        def _resolve(field_name):
            if not field_name:
                return None
            if field_name in cdr:
                return field_name
            lk = str(field_name).lower()
            if lk in cdr_keys_lower:
                return cdr_keys_lower[lk]
            for cand in (lk.replace(' ', '_'), lk.replace('_', ' ')):
                if cand in cdr_keys_lower:
                    return cdr_keys_lower[cand]
            return None

        # --- STRICT SOURCE ROUTING ---
        # 1. Current Values: ALWAYS from live PLC (kiln1/opc/pi)
        missing_cv_vars = [spec.get('target_var') for spec in cv_spec.values() if spec.get('target_var')]
        live_kiln1 = database.get_live_current_values(missing_cv_vars, window_minutes=10) or {}

        # 2. Target Values: ALWAYS from AI database results (cdr)
        values = {}
        missing = []
        for param, spec in cv_spec.items():
            curr_field = spec.get('curr_field') # This is the label in the DB
            sp_field   = spec.get('sp_field')
            target_var = spec.get('target_var') # This is the tag in kiln1

            row = {}
            
            # CURR comes from Live PLC
            if target_var in live_kiln1:
                row['curr'] = live_kiln1[target_var]
            else:
                missing.append(target_var)

            # SP comes from AI Results
            sp_resolved = _resolve(sp_field)
            if sp_resolved:
                row['sp'] = cdr[sp_resolved]
            else:
                missing.append(sp_field)

            values[param] = row

        if missing:
            print(f"[AI_MNM] Missing strictly-routed fields ({len(missing)}): {missing[:6]}{'...' if len(missing)>6 else ''}")

        try:
            mirrored = database.mirror_aimnm_cv_to_kiln2(values)
            if not mirrored:
                print("[AI_MNM] kiln2 mirror returned False (nothing written)")
        except Exception as mirror_err:
            print(f"[AI_MNM] kiln2 mirror failed: {mirror_err}")

        # Indicators — ALWAYS from live PLC (kiln1/opc/pi)
        indicators = {}
        
        # Gather target vars for indicators
        ind_target_vars = [spec.get('field') for spec in ind_spec.values() if spec.get('field')]
        live_ind_kiln1 = database.get_live_current_values(ind_target_vars, window_minutes=10) or {}

        for key, spec in ind_spec.items():
            field = spec.get('field') or key
            if field in live_ind_kiln1:
                indicators[key] = {'curr': live_ind_kiln1[field]}
            else:
                indicators[key] = {}

        return jsonify({"timestamp": ts, "values": values, "indicators": indicators})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e), "values": {}, "indicators": {}}), 500


@api_routes.route('/aimnm/debug', methods=['GET'])
@cross_origin()
def get_aimnm_debug():
    """
    Diagnostic endpoint — returns raw field names in cimpor_data_result and kiln1.
    Hit from browser: /api/aimnm/debug
    """
    try:
        cfg = process_model.load_model_config() or {}
        ai_mnm_cfg = cfg.get('ai_mnm', {}) or {}
        cv_spec  = ai_mnm_cfg.get('cv_parameters', {}) or {}
        ind_spec = ai_mnm_cfg.get('indicator_parameters', {}) or {}

        cdr = database.get_aimnm_results(window_minutes=10) or {}
        cdr_time = cdr.pop('_time', None)

        ind_fields = [s.get('field') for s in ind_spec.values() if s.get('field')]
        kiln1_row = database.get_kiln1_latest_fields(ind_fields, window_minutes=10) or {}
        kiln1_time = kiln1_row.pop('_time', None)

        resolution = {}
        cdr_keys_lower = {k.lower(): k for k in cdr.keys()}
        for param, spec in cv_spec.items():
            cf = spec.get('curr_field'); sf = spec.get('sp_field')
            resolution[param] = {
                'curr_field': cf, 'curr_found': cf in cdr or (cf and str(cf).lower() in cdr_keys_lower),
                'curr_value': cdr.get(cf), 'sp_field': sf,
                'sp_found': sf in cdr or (sf and str(sf).lower() in cdr_keys_lower),
                'sp_value': cdr.get(sf),
            }

        return jsonify({
            'cimpor_data_result': {'timestamp': cdr_time, 'field_count': len(cdr), 'fields': sorted(list(cdr.keys()))},
            'kiln1_indicators': {'timestamp': kiln1_time, 'requested_fields': ind_fields,
                                 'found_fields': sorted(list(kiln1_row.keys())),
                                 'missing_fields': sorted([f for f in ind_fields if f not in kiln1_row])},
            'cv_resolution': resolution,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_routes.route('/aimnm/save', methods=['POST'])
@cross_origin()
def save_aimnm_setpoints():
    """
    No-op endpoint (spec: AI_MNM config persisted exclusively to model_config.json
    via /api/config). Retained for frontend backward compatibility.
    """
    try:
        body = request.get_json() or {}
        section = body.get('section', 'cv')
        count = len(body.get('parameters', {}) or {})
        return jsonify({"status": "success", "section": section, "count": count,
                        "note": "kiln2 storage skipped (config in model_config.json only)"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# 4. VISUALIZATION & TRENDS
# ==============================================================================
@api_routes.route('/trend/history', methods=['GET'])
@cross_origin()
def get_trend_history():
    try:
        tag = request.args.get('tag')
        mins = int(request.args.get('minutes', 60))
        tag_map = process_model.get_name_to_tag_map()
        db_field = tag_map.get(tag, tag)
        end = datetime.utcnow()
        start = end - timedelta(minutes=mins)

        df = database.get_realtime_data_window(start, end, [db_field], {db_field: tag})

        if df.empty:
            hist = current_app.config.get('df_fingerprint')
            if hist is not None:
                hist.columns = [str(c).strip() for c in hist.columns]
                if tag in hist.columns:
                    df = hist.tail(mins).copy()
                    if config.TIMESTAMP_COLUMN in df.columns:
                        df[config.TIMESTAMP_COLUMN] = pd.to_datetime(df[config.TIMESTAMP_COLUMN])

        if df.empty: return jsonify({"labels": [], "data": []})

        if config.TIMESTAMP_COLUMN in df:
            lbls = df[config.TIMESTAMP_COLUMN].dt.strftime('%Y-%m-%dT%H:%M:%SZ').tolist()
        else:
            lbls = [str(i) for i in range(len(df))]

        return jsonify({"labels": lbls, "data": df[tag].fillna(0).tolist()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_routes.route('/history/visualize', methods=['POST'])
@cross_origin()
def generate_simulation_plot():
    try:
        req = request.get_json()
        tags = req.get('tags', [])
        mins = int(req.get('minutes', 1440))
        color = req.get('color_by')

        df = current_app.config.get('df_fingerprint')
        if df is None: return jsonify({"error": "No data"}), 500

        df.columns = [str(c).strip() for c in df.columns]
        valid = [t for t in tags if t in df.columns]

        if len(valid) < 2: return jsonify({"error": "Select 2+"}), 400

        if mins > 0 and config.TIMESTAMP_COLUMN in df:
            df[config.TIMESTAMP_COLUMN] = pd.to_datetime(df[config.TIMESTAMP_COLUMN])
            max_time = df[config.TIMESTAMP_COLUMN].max()
            start_time = max_time - timedelta(minutes=mins)
            df = df[df[config.TIMESTAMP_COLUMN] > start_time].copy()
        else:
            df = df.tail(mins if mins > 0 else 10000).copy()

        df = df.fillna(0)
        dims = [dict(range=[float(df[c].min()), float(df[c].max())], label=c, values=df[c].tolist()) for c in valid]
        cvals = df[color].tolist() if color and color in df else df[valid[0]].tolist()

        fig = go.Figure(data=go.Parcoords(line=dict(color=cvals, colorscale='Jet', showscale=True), dimensions=dims))
        return jsonify(fig.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# 5. AI & SOFT SENSOR
# ==============================================================================
@api_routes.route('/softsensor/predict', methods=['GET'])
@cross_origin()
def get_softsensor_prediction():
    try:
        tag = request.args.get('tag', 'sinteringZoneTemp')
        name_map = process_model.get_name_to_tag_map()
        db_tags = list(name_map.values())
        end = datetime.utcnow()
        start = end - timedelta(minutes=60)

        real_df = database.get_realtime_data_window(start, end, db_tags, {v: k for k, v in name_map.items()})

        if real_df.empty:
            hist = current_app.config.get('df_fingerprint')
            if hist is not None:
                real_df = hist.tail(60).copy()
                real_df.columns = [str(c).strip() for c in real_df.columns]

        if tag not in real_df.columns: return jsonify({"error": "Tag not found"}), 400

        if mbrl_manager:
            preds = mbrl_manager.predict_soft_sensor_rollout(real_df, tag, steps=60)
        else:
            preds = []

        if not preds: preds = [float(real_df[tag].iloc[-1])] * 60

        last_ts = real_df[config.TIMESTAMP_COLUMN].iloc[-1] if config.TIMESTAMP_COLUMN in real_df else datetime.now()
        p_data = [[(last_ts + timedelta(minutes=i + 1)).strftime("%Y-%m-%dT%H:%M:%SZ"), round(v, 2)] for i, v in
                  enumerate(preds)]
        h_data = [[r[config.TIMESTAMP_COLUMN].strftime("%Y-%m-%dT%H:%M:%SZ"), round(float(r[tag]), 2)] for _, r in
                  real_df.tail(30).iterrows()]

        unit = process_model.get_indicator_variables().get(tag, {}).get('unit', '')
        return jsonify({"variable": tag, "unit": unit, "prediction": p_data, "history": h_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_routes.route('/softsensor/simulate', methods=['POST', 'OPTIONS'])
@cross_origin()
def run_simulation():
    try:
        req = request.get_json()
        ctrls = req.get('controls', {})
        target = req.get('target_variable', 'sinteringZoneTemp')

        name_map = process_model.get_name_to_tag_map()
        db_tags = list(name_map.values())
        end = datetime.utcnow()
        start = end - timedelta(minutes=10)

        real_df = database.get_realtime_data_window(start, end, db_tags, {v: k for k, v in name_map.items()})
        if real_df.empty:
            hist = current_app.config.get('df_fingerprint')
            if hist is not None:
                real_df = hist.tail(10).copy()
                real_df.columns = [str(c).strip() for c in real_df.columns]

        if real_df.empty: return jsonify({"error": "No data"}), 500

        if mbrl_manager:
            res = mbrl_manager.simulate_what_if(real_df, ctrls, target, steps=60)
        else:
            res = {'baseline': [], 'simulated': []}

        ts = [(datetime.now() + timedelta(minutes=i)).strftime('%H:%M') for i in range(60)]

        return jsonify({
            "variable": target,
            "timestamps": ts,
            "baseline": res['baseline'],
            "simulated": res['simulated']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
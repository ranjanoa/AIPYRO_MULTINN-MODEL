import eventlet
eventlet.monkey_patch(all=True)
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="eventlet")
import os
import pandas as pd
import sys
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from datetime import datetime, timedelta
import threading
import traceback
import logging
# Fix for PyInstaller: Do not attempt to activate venv if compiled
if not getattr(sys, 'frozen', False):
    venv_script = os.path.join(os.getcwd(), '.venv', 'Scripts', 'activate_this.py')
    if os.path.exists(venv_script):
        exec(open(venv_script).read(), {'__file__': venv_script})
    else:
        print("Warning: Virtual environment not found. Running with system Python.")

# [START] SILENCE OPC LOGS (Critical for Performance)
# This prevents the console from flooding with "received header"
logging.getLogger("opcua").setLevel(logging.WARNING)
logging.getLogger("asyncua").setLevel(logging.WARNING)
logging.getLogger("uaclient").setLevel(logging.WARNING)

# --- PATH SETUP (CRITICAL) ---
# Ensure we are using the absolute path to the project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'modules'))

# --- DYNAMIC EXTERNAL LOADER ---
import importlib.util

if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = BASE_DIR

def load_external_module(module_name, file_name):
    """Dynamically load a python file overriding any bundled versions."""
    file_path = os.path.join(APP_DIR, file_name)
    if os.path.exists(file_path):
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            print(f"[OK] Loaded external override for module: {module_name}")
            return True
        except Exception as e:
            print(f"[ERR] Failed to load external module {module_name}: {e}")
    return False

# Attempt to load external configs BEFORE they are imported by anything else
load_external_module("config", "config.py")
load_external_module("control_service", "control_service.py")

# --- IMPORTS ---
import config
import database
import process_model
import fingerprint_engine


# Wrap AI import in try/except so it doesn't crash if you are only testing Fingerprint
try:
    from modules.ai_core import mbrl_manager
except ImportError:
    print("[WARN] AI Module (mbrl_manager) not found. AI Strategy will be disabled.")
    mbrl_manager = None

import control_service  # <--- REQUIRED for PLC Control

from api import api_routes
from previousInfo import previous_info_routes
from authentication import auth_routes
from Interactive_plot_duna import create_dash_app

# --- LOGGING ---
from logging.handlers import RotatingFileHandler

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 1. Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# 2. File Handler (Rotating)
# Max 5MB per file, keep 5 backups
log_file_path = os.path.join(config.LOG_DIR, 'app.log')
file_handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=5)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# Ensure the APP_DIR variables exist via config
template_dir = os.path.join(config.BASE_DIR, 'templates')
static_dir = os.path.join(config.BASE_DIR, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config.from_object('config')
socketio = SocketIO(app, 
                    cors_allowed_origins="*", 
                    async_mode='eventlet',
                    ping_timeout=60,
                    ping_interval=25)


# Note: We use config.CONTROL_MODE instead of a local variable now.

def initialize_system():
    logger.info("System Initializing...")

    # 1. Force Config Load with Absolute Path
    # Use config.APP_DIR to ensure it references the executable path, not the temp _MEIPASS folder.
    target_config_path = os.path.join(config.APP_DIR, 'files', 'json', 'model_config.json')
    logger.info(f"Target Config Path: {target_config_path}")

    if not os.path.exists(target_config_path):
        logger.error(f"CRITICAL: Config file DOES NOT EXIST at {target_config_path}")
    else:
        # Force the config module to use this specific path
        config.MODEL_CONFIG_PATH = target_config_path
        process_model.load_model_config()

    # 2. Verify Variables Count
    ctrls = process_model.get_control_variables()
    inds = process_model.get_indicator_variables()
    total_vars = len(ctrls) + len(inds)

    logger.info(f"Variables Loaded: {len(ctrls)} Controls + {len(inds)} Indicators = {total_vars} Total")

    # 3. Load History
    try:
        csv_path = os.path.join(config.APP_DIR, 'files', 'data', 'fingerprint4.csv')
        config.HISTORICAL_DATA_CSV_PATH = csv_path

        # Changed: Use the Parquet auto-optimizer instead of hard-loading CSV
        df = fingerprint_engine.robust_read_csv(csv_path)

        # === DATE FIX APPLIED HERE ===
        if config.TIMESTAMP_COLUMN in df.columns:
            # Let Pandas dynamically infer the datetime format to prevent strict assertion errors
            df[config.TIMESTAMP_COLUMN] = pd.to_datetime(df[config.TIMESTAMP_COLUMN], format='mixed', errors='coerce')

        app.config['df_fingerprint'] = df
        logger.info(f"History Loaded: {len(df)} rows")
    except Exception as e:
        logger.error(f"History Load Failed: {e}")
        app.config['df_fingerprint'] = pd.DataFrame()


# Run Init Logic
initialize_system()

# Register Blueprints
app.register_blueprint(api_routes, url_prefix="/api")
app.register_blueprint(previous_info_routes, url_prefix="/previous")
app.register_blueprint(auth_routes, url_prefix="/auth")
dash_app = create_dash_app(app)


# --- ROUTE: Serve Frontend ---
@app.route('/')
def index():
    """Serves the main HTML interface."""
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    """Serves the favicon from the root directory."""
    return send_from_directory(config.APP_DIR, 'logo.ico', mimetype='image/vnd.microsoft.icon')


# --- BACKGROUND TASK: Data Stream ---
def background_data_emitter():
    """Reads real-time data from InfluxDB and pushes it to the UI every 2 seconds."""
    socketio.sleep(2)
    while True:
        try:
            tag_map = process_model.get_tag_to_name_map()
            tag_list = list(tag_map.keys())
            if tag_list:
                end_time = datetime.utcnow()
                # Use 15 minutes of history so stateful filters (EMA) can converge 
                # fully before extracting the final row for the live UI.
                start_time = end_time - timedelta(minutes=15)

                # Fetch live data
                df = database.get_realtime_data_window(start_time, end_time, tag_list, tag_map)

                if not df.empty:
                    conf = process_model.load_model_config()
                    calc_vars_cfg = conf.get('calculated_variables', {})
                    controls_cfg = conf.get('control_variables', {})
                    indicators_cfg = conf.get('indicator_variables', {})
                    latest = df.iloc[-1].to_dict()

                    # [LIVE CALC] Evaluate all formulas for current state
                    # Correct order: (state_map, controls_cfg, indicators_cfg, calc_vars_cfg)
                    calculated_vals = process_model.evaluate_formulas(latest, controls_cfg, indicators_cfg, calc_vars_cfg)
                    if calculated_vals:
                        latest.update(calculated_vals)

                    # Convert timestamps for JSON serialization
                    if config.TIMESTAMP_COLUMN in latest:
                        latest[config.TIMESTAMP_COLUMN] = str(latest[config.TIMESTAMP_COLUMN])

                    socketio.emit('live_values', latest)
        except Exception as e:
            logger.error(f"Stream Error: {e}")
        socketio.sleep(2)


# --- BACKGROUND TASK: Autopilot Logic ---
def automated_control_loop():
    """
    The Core Intelligence Loop.
    Features:
    - Fast Cycle (2s): Sends Heartbeat (Watchdog) to PLC.
    - Slow Cycle (10s): Runs AI/Fingerprint calculations and executes Writes.
    """
    logger.info("Autopilot Thread Started")
    socketio.sleep(5)

    loop_counter = 0
    watchdog_val = 0

    # Timers pulled from config with safe fallbacks
    AI_INTERVAL_SECONDS = getattr(config, 'AI_INTERVAL_SECONDS', 30)
    FAST_CYCLE_SECONDS = getattr(config, 'FAST_CYCLE_SECONDS', 2)

    # SAFETY THRESHOLD (Adjust as needed)
    MAX_DATA_DELAY_SECONDS = 120

    _physics_buffer = {
        "bzt": [],
        "fuel": [],
        "timestamps": []
    }

    # PERSISTENCE TIMER: Tracks how long scores have been below threshold
    _low_trust_timer = 0

    # Persistent storage for recommendation to ensure UI stays updated 
    # even between 30-second AI optimization cycles.
    recommendation = {"active_strategy": "MANUAL", "driver": "MONITOR", "actions": []}

    while True:
        try:
            # 1. READ GLOBAL STATE
            current_mode = getattr(config, 'CONTROL_MODE', 0)

            # AI_MNM is mode 4 — it is an OVERLAY: the base engine (Fingerprint /
            # AI / Hybrid) generates a full recommendation, then we overwrite the
            # CV setpoints with values read from cimpor_data_result. We map mode 4
            # to the chosen base mode for computing the recommendation and remember
            # the overlay flag so the post-processing block can apply the override.
            original_mode = getattr(config, 'CONTROL_MODE', 0)
            current_mode = original_mode

            ai_mnm_overlay_active = (original_mode == 4)
            if ai_mnm_overlay_active:
                base_strat = getattr(config, 'AI_MNM_BASE_STRATEGY', 'FINGERPRINT')
                if base_strat == 'AI':
                    current_mode = 1
                elif base_strat == 'HYBRID':
                    current_mode = 3
                else:  # default — fingerprint
                    current_mode = 2

            # --- CRITICAL: DATA STALL CHECK ---
            tag_map = process_model.get_tag_to_name_map()
            all_tags = list(tag_map.keys())

            check_end = datetime.utcnow()
            check_start = check_end - timedelta(minutes=1)

            # Quick fetch to check freshness
            fresh_df = database.get_realtime_data_window(check_start, check_end, all_tags, tag_map)

            is_stalled = False

            if fresh_df.empty:
                is_stalled = True
            else:
                last_ts = fresh_df.iloc[-1].get(config.TIMESTAMP_COLUMN)
                if last_ts:
                    if isinstance(last_ts, str):
                        last_ts = pd.to_datetime(last_ts)

                    # Timezone fix
                    if hasattr(last_ts, 'tzinfo') and last_ts.tzinfo is not None:
                        last_ts = last_ts.tz_convert(None)

                    delay = (datetime.utcnow() - last_ts).total_seconds()

                    if delay > MAX_DATA_DELAY_SECONDS:
                        is_stalled = True
                        if loop_counter == 0:
                            logger.warning(
                                f"[WARN] DATA STALL: Last data was {delay:.1f}s ago (Limit: {MAX_DATA_DELAY_SECONDS}s)")

            # --- SAFETY ENFORCEMENT (PAUSE LOGIC) ---
            if is_stalled:
                # 1. Tell PLC we are OFF (Safety), even if internally engaged
                plc_status_code = 0
                
                # 2. Force Trust to 0 (Internal Interlock)
                recommendation['system_trust'] = 0

                # 3. Update UI to show "PAUSED" state and zero trust
                if current_mode > 0 and loop_counter == 0:
                    logger.warning("[PAUSE] SYSTEM PAUSED: Waiting for data connectivity...")
                    socketio.emit('autopilot_update', {
                        "match_score": "SYSTEM-PAUSED",
                        "system_trust": 0,
                        "actions": [],
                        "reason": "Data Connection Lost - Retrying..."
                    })
                    
                    # Record the loss of trust in the DB so logs are accurate
                    try:
                        setpoint_map = process_model.get_setpoint_tag_map()
                        database.write_setpoints(datetime.utcnow(), {'AI_SYSTEM_TRUST': 0}, setpoint_map, {})
                    except:
                        pass
            else:
                # Data is fresh, send actual mode to PLC (0, 1, 2, 3, or 4)
                plc_status_code = original_mode

            # --- FAST CYCLE (Heartbeat) ---
            # Send Watchdog and Status Code to PLC
            control_service.service.send_handshake(watchdog_val, plc_status_code)

            watchdog_val = (watchdog_val + 1) % 100
            loop_counter += FAST_CYCLE_SECONDS

            # --- SLOW CYCLE (Control Optimization) ---
            if loop_counter >= AI_INTERVAL_SECONDS:
                loop_counter = 0

                # If stalled, skip calculation but keep loop alive
                if is_stalled:
                    socketio.sleep(FAST_CYCLE_SECONDS)
                    continue

                # 1. FETCH CONFIG & DATA IMMEDIATELY
                conf = process_model.load_model_config()
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(minutes=30)
                real_df = database.get_realtime_data_window(start_time, end_time, all_tags, tag_map)

                # Simulation Fallback (Strictly for Test Mode)
                is_test = getattr(config, 'TEST_MODE', False)
                if real_df.empty and is_test and app.config.get('df_fingerprint') is not None:
                    real_df = app.config['df_fingerprint'].iloc[-30:].copy()

                if real_df.empty:
                    socketio.sleep(FAST_CYCLE_SECONDS)
                    continue

                # 2. PREPARE MAPPED STATE
                raw_latest = real_df.iloc[-1].to_dict()
                mapped_state = {tag_map.get(k, k): v for k, v in raw_latest.items()}

                # HCF is calculated inside upset_manager from hcf_config in
                # model_config.json — main.py stays clean.
                hcf = 1.0

                if not real_df.empty:
                    # Slow Cycle AI Optimization
                    # (recommendation persists from the top of the function)

                    # Load config for fingerprint and AI
                    calc_cfg = conf.get('calculated_variables', {})
                    controls_cfg = conf.get('control_variables', {})
                    indicators_cfg = conf.get('indicator_variables', {})
                    deviation_config = conf.get('deviation_config', {})
                    # raw_state uses raw_latest already defined above

                    trust_cfg = conf.get('trust_interlock_config', {})
                    trust_thresholds = trust_cfg.get('thresholds', {'fingerprint': 85.0, 'ai': 80.0, 'hybrid_bias': 5.0})
                    
                    if current_mode > 0:
                        # --- ALWAYS CALCULATE FINGERPRINT BACKGROUND SCAN ---
                        # We do this so the similarity score (batch scan number) is always available 
                        # as a grounding metric for trust, even when AI is driving.
                        fp_rec = fingerprint_engine.get_live_fingerprint_action(real_df)
                        fp_score = float(fp_rec.get('match_score', 0)) if fp_rec and isinstance(fp_rec.get('match_score'), (int, float)) else 0
                        
                        ai_rec = None
                        if mbrl_manager and current_mode in (1, 3, 4):
                            try:
                                import concurrent.futures
                                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as _nn_executor:
                                    _nn_future = _nn_executor.submit(mbrl_manager.get_optimal_action, real_df.copy())
                                    try:
                                        ai_rec = _nn_future.result(timeout=25)
                                    except concurrent.futures.TimeoutError:
                                        logger.error("[NN-TIMEOUT] get_optimal_action exceeded 25s. Skipping NN cycle to keep app responsive.")
                                        ai_rec = None
                            except Exception as _nn_err:
                                logger.error(f"[NN-ERROR] get_optimal_action failed: {_nn_err}")
                                ai_rec = None

                            # [PIRL-MPC] Intercept and correct AI actions via First-Principles Physics
                            if ai_rec:
                                try:
                                    from modules.pirl_mpc import engine as pirl_engine
                                    ai_rec = pirl_engine.evaluate_and_correct(ai_rec, mapped_state)
                                except Exception as _pe:
                                    logger.warning(f"PIRL MPC Error (Continuing with raw AI): {_pe}")
                        
                        ai_score = float(ai_rec.get('confidence', 0)) if ai_rec and ai_rec.get('confidence') is not None else 0

                        # --- STRATEGY ARBITRATION ---
                        if current_mode == 3:  # HYBRID
                            # Arbitration logic (History Bias)
                            if (fp_score + trust_thresholds.get('hybrid_bias', 5.0)) >= ai_score:
                                recommendation = fp_rec
                                if recommendation:
                                    recommendation['active_strategy'] = "FINGERPRINT"
                                    recommendation['driver'] = "HISTORY"
                            elif ai_rec:
                                recommendation = ai_rec
                                if recommendation:
                                    recommendation['active_strategy'] = "AI"
                                    recommendation['driver'] = "AI-NN"
                                    # ATTACH FINGERPRINT DATA FOR UI GROUNDING
                                    if fp_rec and 'match_meta' in fp_rec:
                                        recommendation['match_meta'] = fp_rec['match_meta']
                            else:
                                recommendation = fp_rec
                                if recommendation:
                                    recommendation['driver'] = "HISTORY"
                        
                        elif current_mode == 2:  # FINGERPRINT ONLY
                            recommendation = fp_rec
                            if recommendation:
                                recommendation['active_strategy'] = "FINGERPRINT"
                                recommendation['driver'] = "HISTORY"
                        
                        elif current_mode == 1:  # AI ONLY
                            if ai_rec:
                                recommendation = ai_rec
                                if recommendation:
                                    recommendation['active_strategy'] = "AI"
                                    recommendation['driver'] = "AI-NN"
                                    # ATTACH FINGERPRINT DATA FOR UI GROUNDING
                                    if fp_rec and 'match_meta' in fp_rec:
                                        recommendation['match_meta'] = fp_rec['match_meta']
                            else:
                                # Fallback to history if AI failed
                                recommendation = fp_rec
                                if recommendation:
                                    recommendation['active_strategy'] = "FINGERPRINT" 
                                    recommendation['driver'] = "HISTORY-FALLBACK"
                        
                        elif current_mode == 4:  # AI_MNM (Overlay Mode)
                            # Choose the base engine for non-overridden parameters
                            base_type = getattr(config, 'AI_MNM_BASE_STRATEGY', 'FINGERPRINT')
                            
                            if base_type == 'AI':
                                recommendation = ai_rec or fp_rec
                                if recommendation:
                                    recommendation['active_strategy'] = "AI"
                                    recommendation['driver'] = "AI-NN (MNM-Base)"
                            elif base_type == 'HYBRID':
                                # Re-run standard Hybrid arbitration
                                if (fp_score + trust_thresholds.get('hybrid_bias', 5.0)) >= ai_score:
                                    recommendation = fp_rec
                                    if recommendation:
                                        recommendation['active_strategy'] = "FINGERPRINT"
                                        recommendation['driver'] = "HISTORY (MNM-Base)"
                                elif ai_rec:
                                    recommendation = ai_rec
                                    if recommendation:
                                        recommendation['active_strategy'] = "AI"
                                        recommendation['driver'] = "AI-NN (MNM-Base)"
                                else:
                                    recommendation = fp_rec
                            else: # Default to FINGERPRINT
                                recommendation = fp_rec
                                if recommendation:
                                    recommendation['active_strategy'] = "FINGERPRINT"
                                    recommendation['driver'] = "HISTORY (MNM-Base)"
                            
                            ai_mnm_overlay_active = True

                        # Scores attached — final broadcast happens after nudge finalization below.
                        # (Removed early emit here to ensure UI always matches what is written to DB)
                        else:
                            logger.warning("[AUTOPILOT] No recommendation available this cycle. Skipping broadcast.")

                    elif current_mode == 0:  # MONITOR
                        if mbrl_manager:
                            recommendation = mbrl_manager.get_optimal_action(real_df)
                            recommendation['active_strategy'] = "AI"
                            recommendation['match_score'] = "MONITOR"
                            recommendation['driver'] = "MONITOR"

                    if current_mode > 0 and recommendation and isinstance(recommendation, dict):
                        # [LIVE SETPOINT SYNC] Inject calculated actions (Priority 0)
                        calc_cfg = conf.get('calculated_variables', {})
                        controls_cfg = conf.get('control_variables', {})
                        indicators_cfg = conf.get('indicator_variables', {})
                        
                        raw_actions = recommendation.get('actions', [])
                        
                        calc_actions = process_model.generate_calculated_actions(
                            raw_actions, mapped_state, controls_cfg, indicators_cfg, calc_cfg
                        )
                        
                        # Replace naive generic actions with the fully calculated ones
                        calc_names = {c['var_name'] for c in calc_actions}
                        recommendation['actions'] = [a for a in recommendation['actions'] if a.get('var_name') not in calc_names]
                        recommendation['actions'].extend(calc_actions)

                        # Attach dual-scores now so they are present on the single final emit
                        if 'fp_score' not in recommendation:
                            recommendation['fp_score'] = fp_score if 'fp_score' in dir() else 0
                            recommendation['ai_score'] = ai_score if 'ai_score' in dir() else 0
                            recommendation['selected_strategy'] = recommendation.get('active_strategy', 'FINGERPRINT')

                        score = recommendation.get('match_score', '0')
                        if score == "SAFETY-CLAMP":
                            logger.warning("[SEC] Guardian Blocked Control")
                        else:
                            # -------------------------------------------------------
                            # [UPSET OVERRIDE] Evaluate upset conditions.
                            # The recommendation (charts, score, UI) is ALWAYS kept
                            # intact. Only the setpoints written to InfluxDB may be
                            # overridden when a timed upset condition fires.
                            # If upset_manager fails for any reason it returns []
                            # and the standard pipeline continues unaffected.
                            # -------------------------------------------------------
                            try:
                                from modules.upset_manager import evaluate_upsets
                                upset_actions = evaluate_upsets(mapped_state, conf, recent_df=real_df)
                            except Exception as _ue:
                                logger.warning(f"[UpsetManager] Import/eval error (pipeline continues): {_ue}")
                                upset_actions = []

                            # ---------------------------------------------------
                            # [CENTRALIZED NUDGE FINALIZATION]
                            # Ensures Kiln2 DB and PLC always receive a safe, nudged value.
                            # regardless of which engine (AI/FP) generated the goal.
                            # ---------------------------------------------------
                            setpoints = process_model.finalize_setpoints_for_db(recommendation, mapped_state, conf)

                            if upset_actions:
                                logger.warning(f"[UPSET-OVERRIDE] {len(upset_actions)} action(s) active.")
                                for act in upset_actions:
                                    target = act.get("target")
                                    if not target or act.get("type") in ("system_halt", "mode_switch"):
                                        continue
                                    curr = float(mapped_state.get(target, 0.0) or 0.0)
                                    adj  = act.get("step_adjustment", 0.0)
                                    setpoints[target] = curr * (1.0 + adj/100.0) if act.get("is_percentage") else curr + adj
                                
                                recommendation['upset_active'] = True
                                recommendation['upset_summary'] = [f"{a.get('rule_id','?')}: {a.get('description', '')}" for a in upset_actions]
                            else:
                                recommendation['upset_active'] = False

                            # --- UI SYNCHRONIZATION ---
                            # Rebuild recommendation['actions'] so the dashboard always 
                            # reflects exactly what is being written to InfluxDB.
                            new_ui_actions = []
                            upset_targets = {a.get('target') for a in upset_actions if a.get('target')}
                            
                            for vn, val in setpoints.items():
                                # Skip backend metadata bits to keep the table clean
                                if vn in ('AI_SYSTEM_TRUST', 'AI_SYSTEM_TRUST_STATUS', 'AI_CONTROL_SIGNAL'):
                                    continue
                                
                                # Find original action to preserve metadata/reasoning if possible
                                orig = next((a for a in recommendation.get('actions', []) if a['var_name'] == vn), None)

                                # Use current_setpoint from the engine action — it used real_df correctly.
                                # mapped_state can give 0 for variables with key name mismatches.
                                if orig and orig.get('current_setpoint') is not None:
                                    try:
                                        curr = float(orig['current_setpoint'])
                                    except (ValueError, TypeError):
                                        curr = float(mapped_state.get(vn, 0.0) or 0.0)
                                else:
                                    curr = float(mapped_state.get(vn, 0.0) or 0.0)

                                # Restore unthrottled target metadata for UI parsing
                                fingerprint_absolute = orig.get('fingerprint_set_point') if orig else val
                                final_tgt = orig.get('final_target') if orig else fingerprint_absolute

                                new_ui_actions.append({
                                    "var_name": vn,
                                    "current_setpoint": curr,
                                    "fingerprint_set_point": round(fingerprint_absolute, 4),
                                    "nudge_target": round(val, 4),
                                    "final_target": round(final_tgt, 4),
                                    "diff": round(val - curr, 4),
                                    "reason": 'Upset Override' if vn in upset_targets else (orig.get('reason', 'Optimizing') if orig else 'Optimizing'),
                                    "type": "Control"
                                })
                            
                            recommendation['actions'] = new_ui_actions

                            # --- SYSTEM TRUST CALCULATION ---
                            if trust_cfg.get('enabled', True):
                                # 1. Determine "Instant" Trust (is the current state good?)
                                instant_trust = 0
                                strategy = recommendation.get('active_strategy', 'BALANCED')
                                
                                # Upset override (highest priority) - always trustworthy if configured
                                if recommendation.get('upset_active'):
                                    instant_trust = trust_cfg.get('behavior', {}).get('upset_trust', 1)
                                
                                else:
                                    try:
                                        # In NN mode, recommendation.match_score is "SAC-MBRL" (a string).
                                        # Use the outer fp_rec (fingerprint engine score) as the ground-truth
                                        # similarity score so trust revocation reflects real plant state.
                                        raw_ms = recommendation.get('match_score', 0)
                                        fp_score = float(raw_ms) if isinstance(raw_ms, (int, float)) else float(fp_rec.get('match_score', 0)) if fp_rec and isinstance(fp_rec.get('match_score'), (int, float)) else 0.0
                                    except (ValueError, TypeError):
                                        fp_score = 0.0
                                        
                                    nn_score = float(recommendation.get('confidence', 0) or 0)
                                    
                                    fp_limit = trust_thresholds.get('fingerprint', 85.0)
                                    ai_limit = trust_thresholds.get('ai', 80.0)

                                    if strategy == "FINGERPRINT":
                                        if fp_score >= fp_limit: instant_trust = 1
                                    elif strategy in ("AI", "SAC-MBRL", "AI-ASSIST"):  # NN mode
                                        # In NN mode: trust if fingerprint is high (grounding signal)
                                        # OR if NN confidence itself is high enough
                                        if fp_score >= fp_limit or nn_score >= ai_limit:
                                            instant_trust = 1
                                    elif strategy == "HYBRID":
                                        if fp_score >= fp_limit or nn_score >= ai_limit:
                                            instant_trust = 1
                                    else:
                                        # Fallback for any unrecognised strategy: trust on fingerprint
                                        if fp_score >= fp_limit: instant_trust = 1

                                # 2. Apply Persistence Timer (Debounce)
                                persistence_limit = trust_cfg.get('persistence_sec', 60)
                                
                                if instant_trust == 1:
                                    # RECOVERY: Score is good, restore trust immediately
                                    _low_trust_timer = 0
                                    final_trust_bit = 1
                                else:
                                    # DEGRADATION: Score is bad, increment timer
                                    _low_trust_timer += AI_INTERVAL_SECONDS
                                    
                                    # If we haven't hit the time limit yet, keep trust at 1
                                    if _low_trust_timer < persistence_limit:
                                        final_trust_bit = 1
                                        logger.info(f"[TRUST-TIMER] Score low ({fp_score:.1f}%). Revoking trust in {persistence_limit - _low_trust_timer}s...")
                                    else:
                                        final_trust_bit = 0
                                        if _low_trust_timer == persistence_limit:
                                            logger.warning(f"[TRUST-REVOKED] Score low for >={persistence_limit}s. Trust set to 0.")
                                
                                setpoints['AI_SYSTEM_TRUST'] = final_trust_bit
                                recommendation['system_trust'] = final_trust_bit

                            # --- PROCESS INSIGHT GENERATION ---
                            insights = []
                            opt_cfg = conf.get('optimisation_target', {})
                            if opt_cfg:
                                target_tag = opt_cfg.get('primary_tag', 'None')
                                t_min, t_max = opt_cfg.get('primary_min', 0), opt_cfg.get('primary_max', 0)
                                insights.append({"type": "goal", "text": f"TARGET: {target_tag} ({t_min}-{t_max})"})
                            
                            driver = recommendation.get('driver', 'None')
                            strat_name = recommendation.get('active_strategy', 'BALANCED')
                            strategies_cfg = conf.get('strategies', {})
                            active_strat_cfg = strategies_cfg.get(strat_name, {})
                            strat_desc = active_strat_cfg.get('description', f"Mode: {strat_name}")
                            insights.append({"type": "strategy", "text": f"STRATEGY: {strat_desc}"})

                            if strat_name == "FINGERPRINT":
                                val = round(float(recommendation.get('match_score', 0)), 1)
                                insights.append({"type": "logic", "text": f"BATCH SIMILARITY: {val}%"})
                            elif strat_name == "AI":
                                val = recommendation.get('confidence', 0)
                                insights.append({"type": "logic", "text": f"LOGIC: AI-NN Strategy (Conf: {val}%)"})
                            
                            if recommendation.get('upset_active'):
                                for summ in recommendation.get('upset_summary', []):
                                    insights.append({"type": "safety", "text": f"UPSET: {summ}"})
                            
                            if recommendation.get('match_score') == "SAFETY-CLAMP":
                                insights.append({"type": "safety", "text": "SAFETY: Guardian Clamp Active"})
                            
                            if recommendation.get('hcf') and abs(float(recommendation['hcf']) - 1.0) > 0.001:
                                insights.append({"type": "hcf", "text": f"HCF: {float(recommendation['hcf']):.3f} Thermal Adjust"})

                            recommendation['insights'] = insights

                            # ---------- AI_MNM OVERLAY ----------
                            # If AI_MNM is engaged (mode 4), override the CV setpoints with
                            # AI-optimised values from cimpor_data_result. The rest of the
                            # recommendation (charts, score, trust, insights) keeps its
                            # base-mode reasoning intact.
                            if ai_mnm_overlay_active:
                                try:
                                    cdr_row = database.get_aimnm_results(window_minutes=10) or {}
                                    cdr_row.pop('_time', None)
                                    cv_spec_overlay = (conf.get('ai_mnm', {}) or {}).get('cv_parameters', {}) or {}

                                    cdr_lower = {str(k).lower(): k for k in cdr_row.keys()}
                                    def _lookup_cdr(name):
                                        if not name:
                                            return None
                                        if name in cdr_row:
                                            return cdr_row[name]
                                        lk = str(name).lower()
                                        if lk in cdr_lower:
                                            return cdr_row[cdr_lower[lk]]
                                        for cand in (lk.replace(' ', '_'), lk.replace('_', ' ')):
                                            if cand in cdr_lower:
                                                return cdr_row[cdr_lower[cand]]
                                        return None

                                    overlay_count = 0
                                    for cv_param, spec in cv_spec_overlay.items():
                                        sp_field = spec.get('sp_field')
                                        target_var = spec.get('target_var') or spec.get('description') or cv_param
                                        sp_val = _lookup_cdr(sp_field)
                                        if sp_val is None:
                                            continue
                                        try:
                                            sp_float = float(sp_val)
                                        except (TypeError, ValueError):
                                            continue

                                        setpoints[target_var] = sp_float
                                        overlay_count += 1

                                        existing = next((a for a in recommendation['actions'] if a.get('var_name') == target_var), None)
                                        curr_val = float(mapped_state.get(target_var, 0.0) or 0.0) if not existing else float(existing.get('current_setpoint', 0.0) or 0.0)
                                        
                                        # Part C: Use Gradual Nudge for AI_MNM targets
                                        # Get nudge speed from config for this variable
                                        ctrl_cfg = controls_cfg.get(target_var, {})
                                        gain = abs(float(ctrl_cfg.get('nudge_speed', 0.15)))
                                        def_min, def_max = ctrl_cfg.get('default_min', -9999), ctrl_cfg.get('default_max', 9999)
                                        
                                        nudged_target = process_model.apply_industrial_nudge(
                                            curr_val, sp_float, gain, def_min, def_max
                                        )

                                        if existing:
                                            existing['fingerprint_set_point'] = round(sp_float, 4)
                                            existing['nudge_target'] = round(nudged_target, 4)
                                            existing['final_target'] = round(sp_float, 4)
                                            existing['diff'] = round(nudged_target - curr_val, 4)
                                            existing['reason'] = 'AI_MNM Override (Nudge)'
                                            existing['source'] = 'AI_MNM'
                                        else:
                                            recommendation['actions'].append({
                                                'var_name': target_var, 'current_setpoint': curr_val,
                                                'fingerprint_set_point': round(sp_float, 4),
                                                'nudge_target': round(nudged_target, 4),
                                                'final_target': round(sp_float, 4),
                                                'diff': round(nudged_target - curr_val, 4),
                                                'reason': 'AI_MNM Override (Nudge)', 'source': 'AI_MNM', 'type': 'Control'
                                            })
                                        
                                        # Ensure the final write-back uses the NUDGED value, not the raw target
                                        setpoints[target_var] = nudged_target

                                    recommendation['active_strategy'] = 'AI_MNM'
                                    recommendation['driver'] = f"AI_MNM ({getattr(config, 'AI_MNM_BASE_STRATEGY', 'FINGERPRINT')})"
                                    recommendation['ai_mnm_overlay_count'] = overlay_count
                                    if overlay_count:
                                        logger.info(f"[AI_MNM] Overlay applied to {overlay_count} CV setpoint(s) | base={getattr(config, 'AI_MNM_BASE_STRATEGY', 'FINGERPRINT')}")
                                    else:
                                        logger.warning("[AI_MNM] Overlay engaged but cimpor_data_result returned no SP fields — base setpoints unchanged.")
                                except Exception as overlay_err:
                                    logger.error(f"[AI_MNM] Overlay failed (continuing with base setpoints): {overlay_err}")

                            if setpoints:
                                setpoint_map = process_model.get_setpoint_tag_map()
                                scale_factors = process_model.get_setpoint_scale_factors()
                                logger.info(f"[DB-WRITE] Measurement: {config.DB_MEASUREMENT_SETPOINTS} | Points: {len(setpoints)}")
                                for vn, v in setpoints.items():
                                    raw_tgt = next((a.get('fingerprint_set_point', v) for a in recommendation.get('actions', []) if a.get('var_name') == vn), v)
                                    sf = scale_factors.get(vn, 1)
                                    written = round(float(v) * sf, 4)
                                    logger.info(f"  [DB-WRITE] {vn}: nudged={round(float(v),3)} | raw_target={round(float(raw_tgt),3)} | scale={sf} | written_to_db={written}")
                                database.write_setpoints(datetime.utcnow(), setpoints, setpoint_map, scale_factors)
                                control_service.service.execute_recommendation(recommendation)

                    if recommendation:
                        socketio.emit('autopilot_update', recommendation)

        except Exception as e:
            logger.error(f"Autopilot Cycle Error: {e}")
            traceback.print_exc()

        socketio.sleep(FAST_CYCLE_SECONDS)


# --- THREAD MANAGEMENT ---
thread = None
thread_lock = threading.Lock()


@socketio.on("connect")
def on_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = True  # Mark thread as started to prevent explosion
            socketio.start_background_task(background_data_emitter)
            socketio.start_background_task(automated_control_loop)


if __name__ == "__main__":
    # Ensure templates folder exists for the new route
    if not os.path.exists(os.path.join(config.APP_DIR, 'templates')):
        os.makedirs(os.path.join(config.APP_DIR, 'templates'), exist_ok=True)
        # print("⚠️ WARNING: Created 'templates' folder. Please move 'index.html' there.")

    socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
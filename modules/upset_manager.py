"""
upset_manager.py
================
Modular Upset Condition Engine for CIMPOR Kiln 2 Application.

ALL business logic (thresholds, timers, actions) is defined EXCLUSIVELY in
model_config.json under the key "upset_conditions".

This module is a DUMB INTERPRETER — it contains zero plant-specific hardcoded
logic. If the JSON is empty, this module does absolutely nothing and returns
an empty list, leaving the standard AI/Fingerprint pipeline completely intact.

Designed to be completely non-destructive to existing features:
  - Fingerprint matching still runs and generates chart + score data.
  - AI recommendations still run.
  - ONLY the final `actions` list sent to InfluxDB/PLC is overridden when an
    upset condition is actively confirmed (with persistence timer satisfied).
  - If ANY error occurs inside this module it is caught, logged, and the
    standard pipeline resumes unaffected.
"""

import logging
import time
from collections import deque

try:
    import pandas as pd
except ImportError:
    pd = None

logger = logging.getLogger(__name__)


class UpsetConditionEngine:
    """
    Evaluates upset condition rules loaded from model_config.json.

    State is maintained in memory (reset on server restart). Rules are
    re-read from the live config dict on every call, so JSON edits take
    effect on the very next evaluation cycle — no restart required.
    """

    def __init__(self):
        # Maps rule_id -> timestamp (float) when trigger first became True
        self._trigger_start: dict = {}
        # Maps rule_id -> timestamp when cascade first started
        self._cascade_start: dict = {}
        # Maps variable_name -> deque of (timestamp, value) for rate-of-change
        self._history: dict = {}

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def evaluate(self, current_data: dict, config: dict, hcf: float = 1.0) -> list:
        """
        Evaluate all upset_conditions rules against current_data.

        Parameters
        ----------
        current_data : dict
            Mapping of friendly_name -> current numeric value.
            Missing/None/NaN values are handled gracefully.
        config : dict
            The full model_config dict (loaded fresh each cycle).
        hcf : float, optional
            Heat Compensation Factor (Lab_CV / Effective_CV).
            Used to scale fuel-based setpoint adjustments.

        Returns
        -------
        list
            List of action dicts to apply as overrides, or [] if nothing
            triggered. Format matches the standard actions list so the
            existing pipeline needs zero changes to consume it.
        """
        try:
            rules = config.get("upset_conditions", {})
            if not rules:
                return []

            active_actions = []
            now = time.monotonic()

            for rule_id, rule in rules.items():
                if not rule.get("enabled", True):
                    continue

                try:
                    active_actions.extend(
                        self._evaluate_rule(rule_id, rule, current_data, config, now, hcf)
                    )
                except Exception as e:
                    logger.warning(
                        f"[UpsetManager] Error evaluating rule '{rule_id}': {e}"
                    )
                    # Always fail safe — skip this rule, don't crash pipeline

            return active_actions

        except Exception as e:
            logger.error(f"[UpsetManager] Unexpected error in evaluate(): {e}")
            return []  # NEVER crash the calling pipeline

    # ------------------------------------------------------------------
    # RULE EVALUATION
    # ------------------------------------------------------------------

    def _evaluate_rule(self, rule_id, rule, data, config, now, hcf=1.0):
        trigger_logic = rule.get("trigger_logic")
        if not trigger_logic:
            return []

        is_triggered = self._eval_condition(trigger_logic, data, config, now)

        if not is_triggered:
            # Reset timers cleanly when condition resolves
            self._trigger_start.pop(rule_id, None)
            self._cascade_start.pop(rule_id, None)
            return []

        actions_out = []

        # --- Simple single action or multiple concurrent actions ---
        persistence = trigger_logic.get("persistence_sec", 0)
        potential_actions = []
        if "action" in rule:
            potential_actions.append(rule["action"])
        if "actions" in rule:
            potential_actions.extend(rule.get("actions", []))

        if potential_actions:
            if rule_id not in self._trigger_start:
                self._trigger_start[rule_id] = now
                logger.info(
                    f"[UpsetManager] Trigger START: '{rule_id}' "
                    f"(needs {persistence}s persistence)"
                )

            elapsed = now - self._trigger_start[rule_id]
            if elapsed >= persistence:
                for raw_act in potential_actions:
                    action = dict(raw_act)
                    
                    # Apply Heat Compensation if flagged and action is a fuel bias
                    if hcf != 1.0 and action.get("type") == "bias" and action.get("heat_compensated"):
                        orig = action.get("step_adjustment", 0.0)
                        action["step_adjustment"] = round(orig * hcf, 3)
                        action["heat_scale_factor"] = round(hcf, 3)
                        action["uncompensated_step"] = orig

                    action.update({
                        "rule_id": rule_id,
                        "group": rule.get("group", ""),
                        "description": rule.get("description", ""),
                        "elapsed_sec": round(elapsed, 1),
                    })
                    
                    if action.get("type") == "no_action":
                        if elapsed < persistence + 1: # Only log once per trigger
                             logger.info(f"[UpsetManager] SCENARIO DETECTED: '{rule_id}' - {action['description']}")

                    actions_out.append(action)

        # --- Cascading actions with multiple time steps ---
        if "actions_cascade" in rule:
            if rule_id not in self._cascade_start:
                self._cascade_start[rule_id] = now
                logger.info(
                    f"[UpsetManager] Cascade START: '{rule_id}'"
                )

            elapsed = now - self._cascade_start[rule_id]

            # Find the highest cascade tier whose persistence is satisfied
            best_step = None
            for step in rule["actions_cascade"]:
                if elapsed >= step.get("persistence_sec", 0):
                    if (best_step is None or
                            step["persistence_sec"] > best_step["persistence_sec"]):
                        best_step = step

            if best_step:
                for act in best_step.get("actions", []):
                    a = dict(act)
                    
                    # Apply Heat Compensation if flagged and action is a fuel bias
                    if hcf != 1.0 and a.get("type") == "bias" and a.get("heat_compensated"):
                        orig = a.get("step_adjustment", 0.0)
                        a["step_adjustment"] = round(orig * hcf, 3)
                        a["heat_scale_factor"] = round(hcf, 3)
                        a["uncompensated_step"] = orig

                    a.update({
                        "rule_id": rule_id,
                        "group": rule.get("group", ""),
                        "cascade_tier": best_step.get("description", ""),
                        "elapsed_sec": round(elapsed, 1),
                    })
                    actions_out.append(a)

        return actions_out

    # ------------------------------------------------------------------
    # CONDITION EVALUATION (recursive, handles AND/OR/absolute/etc.)
    # ------------------------------------------------------------------

    def _eval_condition(self, cond, data, config, now):
        ctype = cond.get("type", "absolute")

        if ctype == "and_composite":
            return all(
                self._eval_condition(c, data, config, now)
                for c in cond.get("conditions", [])
            )

        if ctype == "or_composite":
            return any(
                self._eval_condition(c, data, config, now)
                for c in cond.get("conditions", [])
            )

        if ctype == "absolute":
            return self._eval_absolute(cond, data, config)

        if ctype == "difference_threshold":
            return self._eval_difference(cond, data)

        if ctype == "sum_threshold":
            return self._eval_sum(cond, data)

        if ctype == "sum_difference_threshold":
            return self._eval_sum_difference(cond, data)

        if ctype == "rate_of_change":
            return self._eval_rate_of_change(cond, data, now)

        logger.warning(f"[UpsetManager] Unknown condition type: '{ctype}'")
        return False

    def _safe_val(self, var_name, data):
        """Returns float value or None if missing/NaN/None."""
        val = data.get(var_name)
        if val is None:
            return None
        try:
            f = float(val)
            # Reject NaN and Inf — both are invalid sensor readings
            if f != f or abs(f) == float("inf"):
                return None
            return f
        except (TypeError, ValueError):
            return None

    def _compare(self, val, op, threshold):
        if val is None:
            return False  # Missing sensor = never trigger
        if op == ">":  return val > threshold
        if op == ">=": return val >= threshold
        if op == "<":  return val < threshold
        if op == "<=": return val <= threshold
        if op == "==": return val == threshold
        return False

    def _eval_absolute(self, cond, data, config):
        var = cond.get("variable")
        val = self._safe_val(var, data)
        op  = cond.get("operator", "")

        # Dynamic limit operators — reads from variable's own config
        if op in ("HH_LIMIT_TRIGGER", "LL_LIMIT_TRIGGER"):
            if val is None:
                return False
            var_cfg = (
                config.get("indicator_variables", {}).get(var) or
                config.get("control_variables", {}).get(var) or {}
            )
            if op == "HH_LIMIT_TRIGGER":
                limit = var_cfg.get("default_max")
                return limit is not None and val >= limit
            else:
                limit = var_cfg.get("default_min")
                return limit is not None and val <= limit

        return self._compare(val, op, cond.get("threshold", 0))

    def _eval_difference(self, cond, data):
        vars_ = cond.get("variables", [])
        if len(vars_) != 2:
            return False
        v1_val = self._safe_val(vars_[0], data)
        v2_val = self._safe_val(vars_[1], data)
        if v1_val is None or v2_val is None:
            return False
        
        diff = abs(v1_val - v2_val)
        is_triggered = self._compare(diff, cond.get("operator", ">"), cond.get("threshold", 0))
        
        if is_triggered:
            logger.debug(f"[UpsetManager] Diff Threshold TRIGGERED: |{vars_[0]}({v1_val}) - {vars_[1]}({v2_val})| = {diff}")
            
        return is_triggered

    def _eval_sum(self, cond, data):
        vals = [self._safe_val(v, data) for v in cond.get("variables", [])]
        if any(v is None for v in vals):
            return False  # If any sensor missing, don't falsely trigger
        return self._compare(sum(vals), cond.get("operator", "<="), cond.get("threshold", 0))

    def _eval_rate_of_change(self, cond, data, now):
        var = cond.get("variable")
        val = self._safe_val(var, data)
        if val is None:
            return False

        window = cond.get("time_window_sec", 60)
        buf = self._history.setdefault(var, deque())
        buf.append((now, val))

        # Prune old entries outside the time window
        while buf and (now - buf[0][0]) > window:
            buf.popleft()

        if len(buf) < 2:
            return False

        delta = val - buf[0][1]
        return self._compare(delta, cond.get("operator", ">"), cond.get("threshold", 0))

    def _eval_sum_difference(self, cond, data):
        """
        Calculates abs(sum(group_1) - sum(group_2)) and compares to threshold.
        Useful for multi-line feeders (e.g., RDF1 + RDF2 vs RDF1_SP + RDF2_SP).
        """
        group1_vars = cond.get("variables_group_1", [])
        group2_vars = cond.get("variables_group_2", [])
        
        if not group1_vars or not group2_vars:
            return False
            
        v1_vals = [self._safe_val(v, data) for v in group1_vars]
        v2_vals = [self._safe_val(v, data) for v in group2_vars]
        
        if any(v is None for v in v1_vals) or any(v is None for v in v2_vals):
            return False
            
        sum1 = sum(v1_vals)
        sum2 = sum(v2_vals)
        diff = abs(sum1 - sum2)
        
        is_triggered = self._compare(diff, cond.get("operator", ">"), cond.get("threshold", 0))
        
        if is_triggered:
            logger.debug(f"[UpsetManager] Sum Diff TRIGGERED: |{group1_vars}({sum1}) - {group2_vars}({sum2})| = {diff}")
            
        return is_triggered


# ---------------------------------------------------------------------------
# HCF: BZT-TREND CORRELATION (config-driven, no hardcoded values)
# ---------------------------------------------------------------------------

def calculate_hcf(current_state: dict, recent_df, config: dict) -> float:
    """
    Operational Heat Compensation Factor based on BZT thermal response.

    Logic (all parameters come from hcf_config in model_config.json):
      - Observes the last N minutes of BZT temperature and total fuel flow.
      - If BZT rises MORE than expected from the fuel change → kiln
        over-responds → HCF < 1.0 (scale down fuel-related adjustments).
      - If BZT rises LESS than expected → fuel less effective → HCF > 1.0.
      - No significant fuel change → HCF = 1.0 (no adjustment).

    Returns 1.0 (neutral) on any error so the pipeline is never affected.

    Config keys (all under hcf_config in model_config.json):
        enabled       : bool  - turn feature on/off (default: false)
        bzt_tag       : str   - friendly name of BZT temperature tag
        bzt_tag_alt   : str   - fallback tag if primary is missing
        fuel_tags     : list  - list of fuel flow tags to sum
        bzt_per_tph   : float - expected °C rise per extra t/h of fuel (default: 10.0)
        hcf_min       : float - minimum allowed HCF (default: 0.85)
        hcf_max       : float - maximum allowed HCF (default: 1.15)
        window_rows   : int   - number of recent rows to use (default: 10)
        min_fuel_delta: float - minimum fuel change (t/h) to trigger HCF (default: 0.2)
    """
    try:
        hcf_cfg = config.get('hcf_config', {})
        if not hcf_cfg.get('enabled', False):
            return 1.0
        if pd is None or recent_df is None:
            return 1.0
        if hasattr(recent_df, 'empty') and recent_df.empty:
            return 1.0

        bzt_tag       = hcf_cfg.get('bzt_tag', 'Kiln BZT1')
        bzt_tag_alt   = hcf_cfg.get('bzt_tag_alt', 'Kiln BZT1')
        fuel_tags     = hcf_cfg.get('fuel_tags', ['Petcoke (Kiln)', 'RDF (Kiln)', 'Petcoke (PC)'])
        bzt_per_tph   = float(hcf_cfg.get('bzt_per_tph', 10.0))
        hcf_min       = float(hcf_cfg.get('hcf_min', 0.85))
        hcf_max       = float(hcf_cfg.get('hcf_max', 1.15))
        window_rows   = int(hcf_cfg.get('window_rows', 10))
        min_fuel_delta= float(hcf_cfg.get('min_fuel_delta', 0.2))

        trend_df = recent_df.tail(window_rows)
        if len(trend_df) < 5:
            return 1.0  # Not enough data to form a trend

        # --- BZT trend ---
        bzt_series = trend_df.get(bzt_tag) if bzt_tag in trend_df.columns else None
        if bzt_series is None or bzt_series.dropna().empty:
            bzt_series = trend_df.get(bzt_tag_alt) if bzt_tag_alt in trend_df.columns else None
        if bzt_series is None or bzt_series.dropna().empty:
            return 1.0

        bzt_series = bzt_series.ffill().fillna(0.0)
        bzt_delta = float(bzt_series.iloc[-1] - bzt_series.iloc[0])

        # --- Total fuel flow trend ---
        def _row_fuel(row):
            return sum(float(row.get(t, 0) or 0) for t in fuel_tags if t in row)

        fuel_start = _row_fuel(trend_df.iloc[0])
        fuel_end   = _row_fuel(trend_df.iloc[-1])
        fuel_delta = fuel_end - fuel_start

        if abs(fuel_delta) < min_fuel_delta:
            return 1.0  # Fuel barely changed — no basis for HCF adjustment

        expected_bzt = fuel_delta * bzt_per_tph
        if abs(expected_bzt) < 0.5:
            return 1.0

        responsiveness = bzt_delta / expected_bzt
        if responsiveness <= 0:
            hcf = hcf_max  # BZT moving wrong direction — apply max compensation
        else:
            hcf_raw = 1.0 / max(responsiveness, 0.1)
            hcf = round(max(hcf_min, min(hcf_max, hcf_raw)), 3)

        logger.info(
            f"[HCF] BZT Δ={bzt_delta:+.1f}°C | Fuel Δ={fuel_delta:+.3f} t/h | "
            f"Expected Δ={expected_bzt:+.1f}°C | Responsiveness={responsiveness:.2f} | HCF={hcf:.3f}"
        )
        return hcf

    except Exception as e:
        logger.debug(f"[HCF] Skipped (non-critical): {e}")
        return 1.0


# ---------------------------------------------------------------------------
# MODULE-LEVEL SINGLETON — one instance for the whole application lifetime
# ---------------------------------------------------------------------------
_engine = UpsetConditionEngine()


def evaluate_upsets(current_data: dict, config: dict, hcf: float = 1.0,
                    recent_df=None) -> list:
    """
    Public entry point. Call this once per control cycle.

    If `recent_df` is provided (the last N minutes of real-time data as a
    DataFrame), HCF is calculated automatically from hcf_config in
    model_config.json. This keeps main.py completely free of HCF logic.

    Returns a list of override actions if any upset conditions are active,
    or an empty list if everything is normal (pipeline runs as-is).
    """
    if recent_df is not None:
        hcf = calculate_hcf(current_data, recent_df, config)
    return _engine.evaluate(current_data, config, hcf)

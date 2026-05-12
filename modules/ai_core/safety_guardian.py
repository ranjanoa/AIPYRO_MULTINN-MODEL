import sys
import os

# Ensure we can import process_model from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import process_model


class SafetyGuardian:
    def __init__(self):
        self.config = process_model.load_model_config()
        self.controls = process_model.get_control_variables()
        self.indicators = process_model.get_indicator_variables()

        # --- NEW: Load Safety Defaults from Config ---
        self.defaults = self.config.get('safety_defaults', {})
        self.fallback_temp = self.defaults.get('fallback_sintering_temp', 1200)
        self.fallback_coal = self.defaults.get('fallback_coal_feed', 2500)
        self.default_stable_min = self.defaults.get('default_stable_min', 1100)
        self.coal_bump = self.defaults.get('emergency_coal_increase', 50)

    def check_action(self, current_state_dict, proposed_action_dict):
        """
        Intervention Logic:
        If the kiln is already unstable, FORCE the action back to a safe known state.
        If the AI proposes a massive jump, CLAMP it.
        """
        safe_action = proposed_action_dict.copy()
        intervention_triggered = False
        reason = ""

        # 1. Stability Check (Example: Kiln Cold)
        # REFACTORED: Use loaded defaults
        temp = float(current_state_dict.get('sinteringZoneTemp', self.fallback_temp))
        stable_min = self.indicators.get('sinteringZoneTemp', {}).get('stable_min', self.default_stable_min)

        if temp < stable_min:
            # If AI tries to lower coal, block it.
            coal_tag = 'coalMainBurner'
            if coal_tag in safe_action:
                current_coal = float(current_state_dict.get(coal_tag, self.fallback_coal))
                if safe_action[coal_tag] < current_coal:
                    # REFACTORED: Use configured bump value
                    safe_action[coal_tag] = current_coal + self.coal_bump
                    intervention_triggered = True
                    reason = "CRITICAL: Kiln Cold. Prevented Coal reduction."

        # 2. Rate of Change Clamp
        for tag, target_val in proposed_action_dict.items():
            current_val = float(current_state_dict.get(tag, target_val))

            # Get max step from config (e.g., max 100kg change)
            max_step = self.controls.get(tag, {}).get('max_step', 9999)

            delta = target_val - current_val
            if abs(delta) > max_step:
                # Clamp the move
                sign = 1 if delta > 0 else -1
                safe_action[tag] = current_val + (max_step * sign)
                intervention_triggered = True
                reason += f" [Clamped {tag}]"

        return safe_action, intervention_triggered, reason
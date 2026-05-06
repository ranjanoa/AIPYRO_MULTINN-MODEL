"""
pirl_mpc.py
===========
Physics-Informed Reinforcement Learning (PIRL) Model Predictive Controller.
This module acts as the "Grey-Box" safety and rollout engine.
"""

import logging
import copy
import numpy as np
import process_model

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# LITERATURE DEFAULTS (Used ONLY if not explicitly defined in model_config.json)
# -------------------------------------------------------------------------
LITERATURE_DEFAULTS = {
    'petcoke_cv_kcal_kg': 8200.0, 'rdf_cv_kcal_kg': 4500.0,
    'stoichiometric_air_ratio': 11.2, 'rdf_air_ratio': 6.5,
    'feed_to_clinker_ratio': 1.55, 'feed_moisture_pct': 0.5,
    'rdf_moisture_pct': 15.0, 'latent_heat_water': 540.0,
    'cp_clinker': 0.25, 'cp_gas': 0.26,
    'heat_of_calcination': 445.0, 'heat_of_clinkerization': -100.0,
    'combustion_efficiency': 0.98, 'radiation_loss_factor': 0.08,
    'fan_draft_to_air_mass': 0.15, 'base_kiln_pressure': -1.5,
    'draft_suction_factor': 0.012, 'gas_expansion_factor': 0.001,
    'gas_velocity_factor': 0.05, 'mill_resistance_penalty': 0.25,
    'clinker_melt_point': 1380.0, 'liquid_phase_multiplier': 0.015,
    'base_torque_factor': 5.72, 'base_co_ppm': 50.0, 'rdf_co_factor': 15.0,
    'tau_fuel_mins': 8.0, 'tau_draft_mins': 1.5, 'tau_thermal_refractory': 15.0,
    'max_safe_bzt': 1550.0, 'min_safe_bzt': 1350.0,
    'min_safe_torque': 100.0, 'max_safe_torque': 350.0,
    'min_o2_excess': 1.2, 'max_safe_pressure': -0.5,
    'max_exhaust_temp': 1050.0, 'max_safe_co_ppm': 800.0,
    'correction_factor': 0.5,
    'bz_residence_time_mins': 20.0  # Burning zone material residence time (mins). Typical: 15-30 min.
}


class FirstPrinciplesDigitalTwin:
    """
    Advanced State-Space Mathematical Model of the Kiln & Precalciner.
    """
    def __init__(self, config: dict, bias_correction: dict = None):
        mpc_cfg = config.get('pirl_mpc_config', {})
        self.bias = bias_correction or {'heat_efficiency_modifier': 1.0}
        
        # Dynamically load all parameters from config, falling back to literature ONLY if missing
        self.params = {}
        for key, default_val in LITERATURE_DEFAULTS.items():
            self.params[key] = float(mpc_cfg.get(key, default_val))
            
        # Apply the auto-tuning bias dynamically
        self.params['combustion_efficiency'] *= self.bias.get('heat_efficiency_modifier', 1.0)

    def simulate_step(self, state: dict, action_vector: dict, dt_mins: float = 1.0) -> dict:
        next_state = copy.deepcopy(state)
        
        feed_tph = action_vector.get('feed', state.get('feed', 0.0))
        target_rdf = action_vector.get('rdf', state.get('rdf', 0.0))
        target_draft = action_vector.get('draft', state.get('draft', 0.0))
        speed_rpm = action_vector.get('speed', state.get('speed', 1.0))
        
        target_pc_fuel = action_vector.get('pc_fuel', state.get('pc_fuel', 0.0))
        target_kiln_fuel = action_vector.get('kiln_fuel', state.get('kiln_fuel', 0.0))
        
        # If specific fuel targets are near zero, fall back to total generic fuel to prevent physics collapse
        if target_pc_fuel < 0.1 and target_kiln_fuel < 0.1:
            total_fuel = action_vector.get('fuel', state.get('fuel', 0.0))
            if total_fuel > 0.1:
                target_pc_fuel = total_fuel * 0.60
                target_kiln_fuel = total_fuel * 0.40

        coal_mill_on = float(state.get('coal_mill_on', 1.0))
        sec_air_temp = float(state.get('sec_air_temp', 25.0)) 

        # Process Delay & Hysteresis 
        alpha_fuel = 1.0 - np.exp(-dt_mins / max(self.params['tau_fuel_mins'], 0.1))
        alpha_draft = 1.0 - np.exp(-dt_mins / max(self.params['tau_draft_mins'], 0.1))
        
        eff_pc_fuel = state.get('effective_pc_fuel', target_pc_fuel) + alpha_fuel * (target_pc_fuel - state.get('effective_pc_fuel', target_pc_fuel))
        eff_kiln_fuel = state.get('effective_kiln_fuel', target_kiln_fuel) + alpha_fuel * (target_kiln_fuel - state.get('effective_kiln_fuel', target_kiln_fuel))
        eff_rdf = state.get('effective_rdf', target_rdf) + alpha_fuel * (target_rdf - state.get('effective_rdf', target_rdf))
        eff_draft = state.get('effective_draft', target_draft) + alpha_draft * (target_draft - state.get('effective_draft', target_draft))
        
        next_state['effective_pc_fuel'] = eff_pc_fuel
        next_state['effective_kiln_fuel'] = eff_kiln_fuel
        next_state['effective_rdf'] = eff_rdf
        next_state['effective_draft'] = eff_draft

        # Mass Balance 
        clinker_tph = feed_tph / self.params['feed_to_clinker_ratio']
        clinker_kg_min = (clinker_tph * 1000) / 60.0
        pc_fuel_kg_min = (eff_pc_fuel * 1000) / 60.0
        kiln_fuel_kg_min = (eff_kiln_fuel * 1000) / 60.0
        rdf_kg_min = (eff_rdf * 1000) / 60.0
        
        total_fuel_kg_min = pc_fuel_kg_min + kiln_fuel_kg_min
        
        # Mass in burning zone: feed_rate (kg/min) × residence_time (mins).
        # This is the standard cement kiln engineering formula and removes any
        # dependency on kiln motor speed RPM (which may be unavailable).
        mass_in_bz_kg = clinker_kg_min * self.params['bz_residence_time_mins']

        # Stoichiometry & Air Balance 
        required_air_kg_min = (total_fuel_kg_min * self.params['stoichiometric_air_ratio']) + (rdf_kg_min * self.params['rdf_air_ratio'])
        resistance_modifier = 1.0 - (coal_mill_on * self.params['mill_resistance_penalty'])
        actual_air_kg_min = eff_draft * self.params['fan_draft_to_air_mass'] * resistance_modifier * 60.0
        
        excess_air_ratio = (actual_air_kg_min - required_air_kg_min) / max(required_air_kg_min, 1.0)
        o2_excess_pct = excess_air_ratio * 21.0 
        combustion_yield = min(1.0, actual_air_kg_min / max(required_air_kg_min, 1.0)) * self.params['combustion_efficiency']

        # CO Emissions 
        co_multiplier = np.exp(-max(0, o2_excess_pct - 1.0)) 
        sim_co = self.params['base_co_ppm'] + (eff_rdf * self.params['rdf_co_factor'] * co_multiplier)

        # HEAT BALANCE 
        water_kg_min = (feed_tph * (self.params['feed_moisture_pct'] / 100.0) * 1000) / 60.0
        rdf_water_kg_min = (eff_rdf * (self.params['rdf_moisture_pct'] / 100.0) * 1000) / 60.0
        latent_heat_penalty = (water_kg_min + rdf_water_kg_min) * self.params['latent_heat_water']
        
        cooler_recup_kcal_min = actual_air_kg_min * self.params['cp_gas'] * (sec_air_temp - 25.0)

        pc_q_in = ((pc_fuel_kg_min * self.params['petcoke_cv_kcal_kg']) + (rdf_kg_min * self.params['rdf_cv_kcal_kg'])) * combustion_yield
        pc_q_reaction = clinker_kg_min * self.params['heat_of_calcination']
        pc_q_net = pc_q_in - pc_q_reaction - latent_heat_penalty

        kiln_q_in = (kiln_fuel_kg_min * self.params['petcoke_cv_kcal_kg']) * combustion_yield
        kiln_q_reaction = clinker_kg_min * self.params['heat_of_clinkerization'] 
        kiln_q_net = kiln_q_in - kiln_q_reaction + cooler_recup_kcal_min + (pc_q_net * 0.1) 
        
        global_q_loss = (kiln_q_in + pc_q_in) * self.params['radiation_loss_factor']
        q_net_bz_kcal_min = kiln_q_net - global_q_loss
        
        thermal_inertia = mass_in_bz_kg * self.params['cp_clinker']
        raw_delta_temp = q_net_bz_kcal_min / max(thermal_inertia, 1.0)
        
        alpha_thermal = 1.0 - np.exp(-dt_mins / max(self.params['tau_thermal_refractory'], 0.1))
        current_bzt = state.get('bzt', self.params['min_safe_bzt'] + 50.0)
        equilibrium_bzt = current_bzt + raw_delta_temp
        next_bzt = current_bzt + alpha_thermal * (equilibrium_bzt - current_bzt)
        
        # KILN TORQUE
        liquid_phase = max(0.0, next_bzt - self.params['clinker_melt_point'])
        rheology_factor = 1.0 + (liquid_phase * self.params['liquid_phase_multiplier'])
        sim_torque = self.params['base_torque_factor'] * (mass_in_bz_kg / 1000.0) * rheology_factor

        # AERODYNAMICS
        co2_release_kg_min = ((feed_tph - clinker_tph) * 1000) / 60.0
        total_gas_mass_min = co2_release_kg_min + total_fuel_kg_min + rdf_kg_min + actual_air_kg_min + water_kg_min
        
        effective_suction = eff_draft * self.params['draft_suction_factor'] * resistance_modifier
        sim_pressure = self.params['base_kiln_pressure'] + (total_gas_mass_min * self.params['gas_expansion_factor']) - effective_suction
        
        gas_velocity = eff_draft * self.params['gas_velocity_factor'] * resistance_modifier
        pc_thermal_contribution = (pc_q_in / max(pc_q_reaction, 1.0)) * 800.0 
        sim_exhaust_temp = state.get('exhaust_temp', 850.0) + alpha_thermal * ((pc_thermal_contribution * 0.8) + gas_velocity - state.get('exhaust_temp', 850.0))

        next_state['bzt'] = next_bzt
        next_state['torque'] = sim_torque
        next_state['pressure'] = sim_pressure
        next_state['exhaust_temp'] = sim_exhaust_temp
        next_state['o2_excess'] = o2_excess_pct
        next_state['co_ppm'] = sim_co
        next_state['clinker_production'] = clinker_tph
        
        return next_state

    def simulate_rollout(self, initial_state: dict, action_vector: dict, horizon_mins: int = 45) -> dict:
        sim_state = copy.deepcopy(initial_state)
        violations = []
        
        for t in range(horizon_mins):
            sim_state = self.simulate_step(sim_state, action_vector, dt_mins=1.0)
            
            if sim_state['co_ppm'] > self.params['max_safe_co_ppm']:
                violations.append(f"CO Spike / ESP Explosion Risk at T+{t}m (CO: {sim_state['co_ppm']:.0f} ppm). Reduce RDF/Alternative Fuel!")
                break
            if sim_state['pressure'] > self.params['max_safe_pressure']:
                violations.append(f"Positive Pressure / Blowback risk at T+{t}m (Pressure: {sim_state['pressure']:.1f})")
                break
            if sim_state['o2_excess'] < self.params['min_o2_excess']:
                violations.append(f"Oxygen starvation at T+{t}m (O2: {sim_state['o2_excess']:.1f}%)")
                break
            if sim_state['exhaust_temp'] > self.params['max_exhaust_temp']:
                violations.append(f"Preheater pluggage risk at T+{t}m (Exhaust Temp: {sim_state['exhaust_temp']:.0f}°C)")
                break
            if sim_state['torque'] < self.params['min_safe_torque']:
                violations.append(f"Kiln Torque Crash at T+{t}m (Amps: {sim_state['torque']:.1f}) - Raw Meal Flush risk!")
                break
            if sim_state['torque'] > self.params['max_safe_torque']:
                violations.append(f"Kiln Over-Torque at T+{t}m (Amps: {sim_state['torque']:.1f}) - Ring formation risk!")
                break
            if sim_state['bzt'] < self.params['min_safe_bzt']:
                violations.append(f"Thermal collapse at T+{t}m (BZT: {sim_state['bzt']:.0f}°C)")
                break
            if sim_state['bzt'] > self.params['max_safe_bzt']:
                violations.append(f"Refractory damage at T+{t}m (BZT: {sim_state['bzt']:.0f}°C)")
                break
                
        return {
            "stable": len(violations) == 0,
            "violations": violations,
            "final_sim_state": sim_state
        }


class PIRL_MPC_Controller:
    def __init__(self):
        self.enabled = True
        self._role_mapping_cache = {}
        self._bias_cache = {'heat_efficiency_modifier': 1.0}
        self._last_simulated_bzt = None

    def _get_role_mapping(self, config: dict) -> dict:
        mapping = {}
        all_vars = {**config.get('control_variables', {}), **config.get('indicator_variables', {})}
        
        for friendly_name, var_cfg in all_vars.items():
            role = var_cfg.get('physics_role')
            if role:
                mapping[friendly_name] = role.lower()
                
        if not mapping:
            for friendly_name in all_vars.keys():
                fn_lower = friendly_name.lower()
                if 'feed' in fn_lower: mapping[friendly_name] = 'feed'
                elif 'rdf' in fn_lower or 'tyre' in fn_lower or 'alternative' in fn_lower or 'af' in fn_lower: mapping[friendly_name] = 'rdf'
                elif 'mill' in fn_lower and ('status' in fn_lower or 'run' in fn_lower or 'on' in fn_lower): mapping[friendly_name] = 'coal_mill_on'
                elif ('pc' in fn_lower or 'calciner' in fn_lower) and ('fuel' in fn_lower or 'petcoke' in fn_lower or 'coal' in fn_lower): mapping[friendly_name] = 'pc_fuel'
                elif ('kiln' in fn_lower or 'main_burner' in fn_lower) and ('fuel' in fn_lower or 'petcoke' in fn_lower or 'coal' in fn_lower): mapping[friendly_name] = 'kiln_fuel'
                elif 'fuel' in fn_lower or 'petcoke' in fn_lower or 'coal' in fn_lower: mapping[friendly_name] = 'fuel'
                elif 'id fan' in fn_lower or 'id_fan' in fn_lower: mapping[friendly_name] = 'draft'
                elif 'kiln speed' in fn_lower: mapping[friendly_name] = 'speed'
                elif 'bzt' in fn_lower or 'burning' in fn_lower: mapping[friendly_name] = 'bzt'
                elif 'torque' in fn_lower or ('kiln' in fn_lower and ('amps' in fn_lower or 'kw' in fn_lower)): mapping[friendly_name] = 'torque'
                elif 'pressure' in fn_lower or 'hood' in fn_lower or 'inlet' in fn_lower: mapping[friendly_name] = 'pressure'
                elif 'exhaust' in fn_lower or 'preheater' in fn_lower or 'egt' in fn_lower: mapping[friendly_name] = 'exhaust_temp'
                elif 'co' in fn_lower and 'ppm' in fn_lower: mapping[friendly_name] = 'co_ppm'
                elif 'secondary' in fn_lower and 'temp' in fn_lower: mapping[friendly_name] = 'sec_air_temp'
                
        self._role_mapping_cache = mapping
        return mapping

    def _extract_action_vector(self, ai_actions: list, mapping: dict) -> dict:
        vec = {}
        for act in ai_actions:
            name = act['var_name']
            role = mapping.get(name)
            if role:
                # Prefer nudge_target (the safe, throttled step value) over final_target (the raw NN goal).
                # Using final_target can give extreme/zero values at the first cycle
                # that collapse the physics simulation (e.g. feed=134 tph → zero simulated torque).
                val = act.get('nudge_target') or act.get('final_target') or act.get('fingerprint_set_point', 0.0)
                vec[role] = vec.get(role, 0.0) + float(val)
        return vec


    def _get_dynamic_fallback(self, config: dict, role: str) -> float:
        """Dynamically extracts a sensible baseline for a missing sensor using config boundaries."""
        all_vars = {**config.get('control_variables', {}), **config.get('indicator_variables', {})}
        for var_cfg in all_vars.values():
            if var_cfg.get('physics_role') == role:
                if 'min' in var_cfg and 'max' in var_cfg:
                    return (float(var_cfg['min']) + float(var_cfg['max'])) / 2.0
                if 'target' in var_cfg:
                    return float(var_cfg['target'])
        return 0.0

    def _extract_state_vector(self, current_data: dict, mapping: dict, config: dict) -> dict:
        state = {}
        for name, role in mapping.items():
            val = current_data.get(name)
            if val is not None:
                try:
                    state[role] = state.get(role, 0.0) + float(val)
                except:
                    pass
                    
        # Replace hardcoded numbers with dynamic config lookups
        expected_roles = ['feed', 'fuel', 'pc_fuel', 'kiln_fuel', 'rdf', 'draft', 'speed', 
                          'bzt', 'torque', 'pressure', 'exhaust_temp', 'coal_mill_on', 'co_ppm', 'sec_air_temp']
                          
        for role in expected_roles:
            if role not in state:
                state[role] = self._get_dynamic_fallback(config, role)
                
        # Special logic to prevent 0.0 crash for speed/draft if completely missing
        if state['speed'] == 0.0: state['speed'] = 1.0

        # Guard: if torque is 0.0 it means the Kiln Motor Amps sensor is missing/disconnected
        # (not a real plant state). Use the mid-point of the safe range as a neutral fallback
        # to prevent PIRL-MPC from raising a false "Kiln Torque Crash" physics violation.
        if state.get('torque', 0.0) == 0.0:
            state['torque'] = (self.params['min_safe_torque'] + self.params['max_safe_torque']) / 2.0

        return state

    def _update_auto_tuning_bias(self, current_bzt: float):
        if self._last_simulated_bzt is not None and current_bzt is not None and current_bzt > 0:
            error = current_bzt - self._last_simulated_bzt
            kalman_gain = 0.005 
            new_modifier = self._bias_cache['heat_efficiency_modifier'] + (error * kalman_gain)
            self._bias_cache['heat_efficiency_modifier'] = max(0.75, min(1.25, new_modifier))

    def evaluate_and_correct(self, ai_recommendation: dict, current_data: dict) -> dict:
        if not self.enabled or not ai_recommendation or not ai_recommendation.get('actions'):
            return ai_recommendation
            
        try:
            config = process_model.load_model_config()
            mapping = self._get_role_mapping(config)
            state_vec = self._extract_state_vector(current_data, mapping, config)
            
            self._update_auto_tuning_bias(state_vec.get('bzt'))
            
            twin = FirstPrinciplesDigitalTwin(config, bias_correction=self._bias_cache)
            action_vec = self._extract_action_vector(ai_recommendation['actions'], mapping)
            
            if not action_vec:
                return ai_recommendation
                
            for k, v in state_vec.items():
                if k not in action_vec: action_vec[k] = v

            rollout = twin.simulate_rollout(state_vec, action_vec, horizon_mins=45)
            self._last_simulated_bzt = twin.simulate_step(state_vec, action_vec, dt_mins=1.0)['bzt']
            
            corrected_rec = copy.deepcopy(ai_recommendation)
            
            if not rollout['stable']:
                logger.warning(f"[PIRL-MPC] Physics Violation Detected: {rollout['violations'][0]}")
                correction_factor = twin.params['correction_factor']
                
                for act in corrected_rec['actions']:
                    curr = float(act.get('current_setpoint', 0.0))
                    tgt = float(act.get('final_target', 0.0))
                    diff = tgt - curr
                    
                    is_fuel = any(k in act['var_name'].lower() for k in ['petcoke', 'fuel', 'rdf'])
                    
                    if is_fuel and tgt <= 0.001:
                        safe_tgt = curr
                        act['reason'] = "MPC Blocked (Unsafe Zero Target)"
                    elif 'Thermal Collapse' in rollout['violations'][0] and is_fuel and tgt < curr:
                        safe_tgt = curr
                        act['reason'] = "MPC Blocked (Thermal Collapse)"
                    else:
                        safe_tgt = curr + (diff * correction_factor)
                        act['reason'] = f"MPC Corrected ({rollout['violations'][0]})"
                    
                    act['final_target'] = safe_tgt
                    act['fingerprint_set_point'] = safe_tgt
                    
                corrected_rec['mpc_intervened'] = True
                corrected_rec['mpc_reason'] = rollout['violations'][0]
                
            return corrected_rec
            
        except Exception as e:
            logger.error(f"[PIRL-MPC] Error in physics evaluation: {e}. Falling back to raw AI.")
            return ai_recommendation

engine = PIRL_MPC_Controller()

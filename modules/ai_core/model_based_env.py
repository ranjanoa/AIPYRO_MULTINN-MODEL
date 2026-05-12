import numpy as np
import torch
import sys
import os

# --- PATH SETUP ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import process_model


class PessimisticVirtualEnv:
    """
    A Virtual Environment that uses the trained World Model to simulate the plant.
    It allows the SAC Agent to learn 'Offline' without touching the real plant.
    """

    def __init__(self, world_model, history_df, env_params, history_window=5, strategy_name="BALANCED"):
        self.wm = world_model
        self.df = history_df
        self.hw = history_window

        # --- UNPACK PARAMS ---
        self.stats = env_params
        self.s_cols = env_params['s_cols']
        self.a_cols = env_params['a_cols']

        self.s_dim = len(self.s_cols)
        self.a_dim = len(self.a_cols)

        # --- REFACTORED: Load Optimization Goals from Config ---
        config = process_model.load_model_config()
        self.opt_settings = config.get('optimization_settings', {})
        
        # New: Pull from strategy first
        self.strategy_cfg = config.get('strategies', {}).get(strategy_name, {})
        
        # Load specific goals (Strategy weights take precedence over global weights)
        self.weights = self.strategy_cfg.get('weights', self.opt_settings.get('weights', {}))
        self.target_setpoint = self.strategy_cfg.get('target_setpoint', self.opt_settings.get('target_setpoint', 1450.0))
        self.deviation_penalty = self.strategy_cfg.get('deviation_penalty', self.opt_settings.get('deviation_penalty', 0.1))

        # Identify Target Variable
        bindings = config.get('ai_bindings', {})
        self.target_var = bindings.get('primary_prediction_target', 'sinteringZoneTemp')

        # Internal State
        self.current_obs = None
        self.last_norm_s = None
        self.steps = 0
        self.max_steps = 100
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def reset(self):
        # ... (Same as original) ...
        idx = np.random.randint(self.hw, len(self.df) - 1)

        def norm(vals, vtype):
            mn = self.stats[vtype]['min']
            rng = self.stats[vtype]['range']
            return (vals - mn) / rng

        raw_s = self.df[self.s_cols].iloc[idx - self.hw: idx].values
        raw_a = self.df[self.a_cols].iloc[idx - self.hw: idx].values

        norm_s = norm(raw_s, 'state')
        norm_a = norm(raw_a, 'action')

        self.current_obs = np.concatenate([norm_s, norm_a], axis=1).flatten()
        self.last_norm_s = norm_s[-1]
        self.steps = 0
        return self.current_obs

    def sample_random_action(self):
        return np.random.uniform(0, 1, size=self.a_dim)

    def step(self, action):
        self.steps += 1

        # 1. PREDICT NEXT STATE
        inp_tensor = torch.FloatTensor(self.current_obs).unsqueeze(0).to(self.device)
        with torch.no_grad():
            mean_delta, _ = self.wm.predict(inp_tensor)

        delta = mean_delta.cpu().numpy()[0]
        next_norm_s = self.last_norm_s + delta

        # 2. CALCULATE REWARD
        def denorm(val, idx, vtype='state'):
            mn = self.stats[vtype]['min'][idx]
            rng = self.stats[vtype]['range'][idx]
            return (val * rng) + mn

        reward = 0.0

        # A. Target Deviation Penalty (REFACTORED)
        try:
            t_idx = self.s_cols.index(self.target_var)
            pred_val = denorm(next_norm_s[t_idx], t_idx)

            # Use loaded target setpoint and penalty weight
            reward -= abs(pred_val - self.target_setpoint) * self.deviation_penalty
        except:
            pass

        # B. Action Penalties
        for i, tag in enumerate(self.a_cols):
            if tag in self.weights:
                w = self.weights[tag]
                action_val = action[i]
                reward += action_val * w

        # 3. UPDATE OBSERVATION
        step_len = len(self.last_norm_s) + len(action)
        new_obs = self.current_obs[step_len:]
        new_obs = np.concatenate([new_obs, next_norm_s, action])

        self.current_obs = new_obs
        self.last_norm_s = next_norm_s
        done = self.steps >= self.max_steps

        return self.current_obs, reward, done, {}
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class EnsembleMember(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(EnsembleMember, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.SiLU(),
            nn.Linear(512, 512),
            nn.SiLU(),
            nn.Linear(512, 512),
            nn.SiLU(),
            nn.Linear(512, output_dim)
        )

    def forward(self, x):
        return self.net(x)

class RobustWorldModel:
    def __init__(self, state_dim, action_dim, history_window=5, num_models=5):
        self.models = []
        self.optimizers = []
        self.num_models = num_models

        # Input: (State + Action) * History_Window
        self.input_dim = (state_dim + action_dim) * history_window
        self.output_dim = state_dim

        for _ in range(num_models):
            m = EnsembleMember(self.input_dim, self.output_dim).to(device)
            self.models.append(m)
            # Lower learning rate for industrial stability
            self.optimizers.append(optim.Adam(m.parameters(), lr=1e-4))

    def predict(self, history_tensor):
        # --- STABILITY: Ensure input is finite ---
        history_tensor = torch.nan_to_num(history_tensor, nan=0.0, posinf=1.0, neginf=-1.0)
        
        valid_predictions = []
        with torch.no_grad():
            for model in self.models:
                model.eval()
                delta = model(history_tensor)
                
                # Check for NaNs in this specific model's output
                if torch.isfinite(delta).all():
                    valid_predictions.append(delta.unsqueeze(0))

        if not valid_predictions:
            # Fallback if all models failed: return zero delta
            return torch.zeros(1, self.output_dim).to(device), torch.zeros(1, self.output_dim).to(device)

        preds = torch.cat(valid_predictions, dim=0)
        mean_delta = torch.mean(preds, dim=0) / 100.0
        
        # Safe variance (at least 2 models needed for variance)
        if len(valid_predictions) > 1:
            variance = torch.var(preds, dim=0) / 10000.0
        else:
            variance = torch.zeros_like(mean_delta)

        return mean_delta, variance

    def train_step(self, history_batch, target_delta_batch):
        # --- STABILITY: Sanitize training batch ---
        history_batch = torch.nan_to_num(history_batch, nan=0.0)
        target_delta_batch = torch.nan_to_num(target_delta_batch, nan=0.0)
        
        # Clip targets to prevent huge gradients (deltas > 10.0 are likely noise)
        target_delta_batch = torch.clamp(target_delta_batch, -10.0, 10.0)

        total_loss = 0
        for i, model in enumerate(self.models):
            model.train()
            pred_delta = model(history_batch)
            loss = nn.HuberLoss(delta=0.5)(pred_delta, target_delta_batch)

            self.optimizers[i].zero_grad()
            loss.backward()
            
            # --- DUAL CLIPPING ---
            torch.nn.utils.clip_grad_value_(model.parameters(), 1.0)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 0.5)
            
            self.optimizers[i].step()
            
            l_val = loss.item()
            if not np.isnan(l_val):
                total_loss += l_val
            else:
                total_loss += 1.0 # Penalty for nan loss to keep training moving

        return total_loss / self.num_models

    def save(self, path_prefix):
        for i, model in enumerate(self.models):
            torch.save(model.state_dict(), f"{path_prefix}_member_{i}.pth")

    def load(self, path_prefix):
        loaded_count = 0
        for i, model in enumerate(self.models):
            p = f"{path_prefix}_member_{i}.pth"
            if os.path.exists(p):
                model.load_state_dict(torch.load(p, map_location=device))
                loaded_count += 1
        print(f"Loaded {loaded_count}/{self.num_models} World Models.")
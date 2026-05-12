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
            self.optimizers.append(optim.Adam(m.parameters(), lr=1e-3))

    def predict(self, history_tensor):
        predictions = []
        with torch.no_grad():
            for model in self.models:
                model.eval()
                delta = model(history_tensor)
                predictions.append(delta.unsqueeze(0))

        preds = torch.cat(predictions, dim=0)
        mean_delta = torch.mean(preds, dim=0) / 100.0
        variance = torch.var(preds, dim=0) / 10000.0

        return mean_delta, variance

    def train_step(self, history_batch, target_delta_batch):
        total_loss = 0
        for i, model in enumerate(self.models):
            model.train()
            pred_delta = model(history_batch)
            loss = nn.HuberLoss(delta=0.1)(pred_delta, target_delta_batch)

            self.optimizers[i].zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            self.optimizers[i].step()
            total_loss += loss.item()

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
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import os
import random

# --- CONFIGURATION ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
LOG_SIG_MAX = 2
LOG_SIG_MIN = -20
epsilon = 1e-6


# ==============================================================================
# 1. REPLAY BUFFER (The Memory)
# ==============================================================================
class ReplayBuffer:
    def __init__(self, capacity, state_dim, action_dim):
        self.capacity = capacity
        self.ptr = 0
        self.size = 0
        self.state = np.zeros((capacity, state_dim))
        self.action = np.zeros((capacity, action_dim))
        self.reward = np.zeros((capacity, 1))
        self.next_state = np.zeros((capacity, state_dim))
        self.done = np.zeros((capacity, 1))

    def push(self, state, action, reward, next_state, done):
        self.state[self.ptr] = state
        self.action[self.ptr] = action
        self.reward[self.ptr] = reward
        self.next_state[self.ptr] = next_state
        self.done[self.ptr] = done

        self.ptr = (self.ptr + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size):
        ind = np.random.randint(0, self.size, size=batch_size)
        return (
            torch.FloatTensor(self.state[ind]).to(device),
            torch.FloatTensor(self.action[ind]).to(device),
            torch.FloatTensor(self.reward[ind]).to(device),
            torch.FloatTensor(self.next_state[ind]).to(device),
            torch.FloatTensor(self.done[ind]).to(device)
        )


# ==============================================================================
# 2. NEURAL NETWORKS (Value & Policy)
# ==============================================================================
def weights_init_(m):
    if isinstance(m, nn.Linear):
        torch.nn.init.xavier_uniform_(m.weight, gain=1)
        torch.nn.init.constant_(m.bias, 0)


class SoftQNetwork(nn.Module):
    def __init__(self, num_inputs, num_actions, hidden_dim=256):
        super(SoftQNetwork, self).__init__()
        self.linear1 = nn.Linear(num_inputs + num_actions, hidden_dim)
        self.linear2 = nn.Linear(hidden_dim, hidden_dim)
        self.linear3 = nn.Linear(hidden_dim, 1)
        self.apply(weights_init_)

    def forward(self, state, action):
        x = torch.cat([state, action], 1)
        x = F.relu(self.linear1(x))
        x = F.relu(self.linear2(x))
        x = self.linear3(x)
        return x


class PolicyNetwork(nn.Module):
    def __init__(self, num_inputs, num_actions, hidden_dim=256):
        super(PolicyNetwork, self).__init__()
        self.linear1 = nn.Linear(num_inputs, hidden_dim)
        self.linear2 = nn.Linear(hidden_dim, hidden_dim)
        self.mean_linear = nn.Linear(hidden_dim, num_actions)
        self.log_std_linear = nn.Linear(hidden_dim, num_actions)
        self.apply(weights_init_)

    def forward(self, state):
        x = F.relu(self.linear1(state))
        x = F.relu(self.linear2(x))
        mean = self.mean_linear(x)
        log_std = self.log_std_linear(x)
        log_std = torch.clamp(log_std, min=LOG_SIG_MIN, max=LOG_SIG_MAX)
        return mean, log_std

    def sample(self, state):
        mean, log_std = self.forward(state)
        std = log_std.exp()
        normal = torch.distributions.Normal(mean, std)
        x_t = normal.rsample()
        y_t = torch.tanh(x_t)
        action = y_t
        log_prob = normal.log_prob(x_t)

        # Enforcing Action Bound
        log_prob -= torch.log(1 - y_t.pow(2) + epsilon)
        log_prob = log_prob.sum(1, keepdim=True)
        return action, log_prob, mean


# ==============================================================================
# 3. SAC AGENT (The Brain)
# ==============================================================================
class SACAgent:
    def __init__(self, num_inputs, action_space, hidden_size=256, lr=0.0003, gamma=0.99, tau=0.005, alpha=0.2):
        self.gamma = gamma
        self.tau = tau
        self.alpha = alpha
        self.action_space = action_space

        self.critic = SoftQNetwork(num_inputs, action_space, hidden_size).to(device)
        self.critic_optim = optim.Adam(self.critic.parameters(), lr=lr)
        self.critic_target = SoftQNetwork(num_inputs, action_space, hidden_size).to(device)
        self.critic_target.load_state_dict(self.critic.state_dict())

        self.critic2 = SoftQNetwork(num_inputs, action_space, hidden_size).to(device)
        self.critic2_optim = optim.Adam(self.critic2.parameters(), lr=lr)
        self.critic2_target = SoftQNetwork(num_inputs, action_space, hidden_size).to(device)
        self.critic2_target.load_state_dict(self.critic2.state_dict())

        self.policy = PolicyNetwork(num_inputs, action_space, hidden_size).to(device)
        self.policy_optim = optim.Adam(self.policy.parameters(), lr=lr)

    def select_action(self, state, evaluate=False):
        state = torch.FloatTensor(state).to(device).unsqueeze(0)
        if evaluate:
            _, _, mean = self.policy.sample(state)
            action = torch.tanh(mean)
        else:
            action, _, _ = self.policy.sample(state)
        return action.detach().cpu().numpy()[0]

    def update_parameters(self, memory, batch_size):
        # Sample a batch from memory
        state_batch, action_batch, reward_batch, next_state_batch, mask_batch = memory.sample(batch_size)

        with torch.no_grad():
            next_state_action, next_state_log_pi, _ = self.policy.sample(next_state_batch)
            qf1_next_target = self.critic_target(next_state_batch, next_state_action)
            qf2_next_target = self.critic2_target(next_state_batch, next_state_action)
            min_qf_next_target = torch.min(qf1_next_target, qf2_next_target) - self.alpha * next_state_log_pi
            next_q_value = reward_batch + (1 - mask_batch) * self.gamma * min_qf_next_target

        qf1 = self.critic(state_batch, action_batch)
        qf2 = self.critic2(state_batch, action_batch)

        qf1_loss = F.mse_loss(qf1, next_q_value)
        qf2_loss = F.mse_loss(qf2, next_q_value)

        self.critic_optim.zero_grad()
        qf1_loss.backward()
        self.critic_optim.step()

        self.critic2_optim.zero_grad()
        qf2_loss.backward()
        self.critic2_optim.step()

        pi, log_pi, _ = self.policy.sample(state_batch)
        qf1_pi = self.critic(state_batch, pi)
        qf2_pi = self.critic2(state_batch, pi)
        min_qf_pi = torch.min(qf1_pi, qf2_pi)

        policy_loss = ((self.alpha * log_pi) - min_qf_pi).mean()

        self.policy_optim.zero_grad()
        policy_loss.backward()
        self.policy_optim.step()

        # Soft Updates
        for target_param, param in zip(self.critic_target.parameters(), self.critic.parameters()):
            target_param.data.copy_(target_param.data * (1.0 - self.tau) + param.data * self.tau)

        for target_param, param in zip(self.critic2_target.parameters(), self.critic2.parameters()):
            target_param.data.copy_(target_param.data * (1.0 - self.tau) + param.data * self.tau)

        return qf1_loss.item(), policy_loss.item()

    def save(self, path):
        # Save as dictionary to handle multiple networks
        state = {
            'policy': self.policy.state_dict(),
            'critic': self.critic.state_dict(),
            'critic2': self.critic2.state_dict()
        }
        torch.save(state, path + ".pth")

    def load(self, path):
        checkpoint = torch.load(path + ".pth", map_location=device)
        self.policy.load_state_dict(checkpoint['policy'])
        self.critic.load_state_dict(checkpoint['critic'])
        self.critic2.load_state_dict(checkpoint['critic2'])
        self.critic_target.load_state_dict(checkpoint['critic'])
        self.critic2_target.load_state_dict(checkpoint['critic2'])
import sys
import os
import pandas as pd
import numpy as np
import torch

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from modules.ai_core import mbrl_manager
from fingerprint_engine import robust_read_csv
import config

def main():
    print("="*60)
    print("   SAC AGENT RE-TRAINING (EXPRESS MODE)")
    print("="*60)
    print("Goal: Rebuild the Policy/Critic from scratch using the existing World Model.")
    
    # 1. Load Data
    print(f"Loading data from: {config.HISTORICAL_DATA_CSV_PATH}")
    df = robust_read_csv(config.HISTORICAL_DATA_CSV_PATH)
    if df.empty:
        print("Error: No data found.")
        return

    # 2. Initialize System
    # This will load the World Model but fail to load the (deleted) SAC Agent
    mbrl_manager._initialize_system()
    
    if mbrl_manager._world_model is None:
        print("Error: World Model could not be loaded. Please train World Model first.")
        return

    # 3. Train SAC Agent
    # 5,000 steps for initial validation test
    mbrl_manager.train_sac_agent(df, steps=5000)

    print("\n✅ RE-TRAINING COMPLETE.")

if __name__ == "__main__":
    main()

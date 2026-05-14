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
    print("   WORLD MODEL TEST TRAINING (20 EPOCHS)")
    print("="*60)
    
    # 1. Load Data
    df = robust_read_csv(config.HISTORICAL_DATA_CSV_PATH)
    
    # 2. Initialize System
    mbrl_manager._initialize_system()
    
    # 3. Train World Model
    # Reduced to 20 epochs for quick testing
    print("\nStarting World Model Training (20 epochs)...")
    mbrl_manager.train_world_model(df, epochs=20)

    print("\n✅ DEEP TRAINING COMPLETE.")

if __name__ == "__main__":
    main()

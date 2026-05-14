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
    print(">>> SAC SMOKE TEST (2,000 Steps)")
    df = robust_read_csv(config.HISTORICAL_DATA_CSV_PATH)
    mbrl_manager._initialize_system()
    
    # Force save after 1000 steps for this test
    # We'll just run the training
    mbrl_manager.train_sac_agent(df, steps=2000)
    
    # Save manually at the end
    if mbrl_manager._sac_agent:
        mbrl_manager._sac_agent.save("files/models/sac_agent")
        print(">>> Smoke Test: Model Saved.")

if __name__ == "__main__":
    main()

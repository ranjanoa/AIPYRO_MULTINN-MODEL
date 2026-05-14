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
    print(">>> MICRO TEST (100 Steps)")
    # Load a small slice
    df = robust_read_csv(config.HISTORICAL_DATA_CSV_PATH).iloc[:1000]
    
    # Manually initialize to avoid double load
    mbrl_manager._initialize_system()
    
    # Run training
    print("Starting Training...")
    mbrl_manager.train_sac_agent(df, steps=100)
    
    # Save
    if mbrl_manager._sac_agent:
        print("Saving Model...")
        mbrl_manager._sac_agent.save("files/models/sac_agent")
        print(">>> Micro Test: SUCCESS.")

if __name__ == "__main__":
    main()

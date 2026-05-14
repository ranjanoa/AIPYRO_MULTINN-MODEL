import sys
import os
import traceback

# Add the project root to system path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from modules.ai_core import mbrl_manager as sac_manager
    from fingerprint_engine import robust_read_csv
    import config
    print("Success: Imported modules.")
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import modules: {e}")
    sys.exit(1)

if __name__ == "__main__":
    print("\n==================================================")
    print("   INNOMOTICS SAC: RESUME TRAINING (SAC ONLY)")
    print("==================================================")

    try:
        # 1. Initialize system (loads WM and existing SAC weights)
        sac_manager._initialize_system()
        
        if sac_manager._world_model is None:
            print("❌ Error: World Model not found. Please train WM first.")
            sys.exit(1)

        # 2. Load Data
        print(f"⏳ Loading data from {config.HISTORICAL_DATA_CSV_PATH}...")
        df = robust_read_csv(config.HISTORICAL_DATA_CSV_PATH)
        
        # 3. Train SAC Only
        print("🚀 Starting SAC Training Loop (Resuming from last save)...")
        sac_manager.train_sac_agent(df, steps=50000)

        print("\n✅ SUCCESS: SAC Training Complete.")

    except Exception as e:
        print(f"\n❌ CRITICAL FAILURE DURING TRAINING: {e}")
        traceback.print_exc()

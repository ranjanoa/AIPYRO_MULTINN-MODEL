import sys
import os
import traceback

# ==============================================================================
# 1. PATH SETUP
# ==============================================================================
# Get the absolute path of the directory containing this script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the project root to system path
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Also add the 'modules' folder directly to path
modules_dir = os.path.join(current_dir, 'modules')
if os.path.exists(modules_dir) and modules_dir not in sys.path:
    sys.path.append(modules_dir)

# ==============================================================================
# 2. ROBUST IMPORT LOGIC
# ==============================================================================
print(f"🔍 DEBUG: Project Root set to: {current_dir}")

try:
    # Attempt 1: Standard Project Structure (Preferred)
    from modules.ai_core import mbrl_manager as sac_manager

    print("✅ Success: Imported 'modules.ai_core.mbrl_manager'")
except ImportError as e:
    print(f"⚠️ Primary Import Failed: {e}")
    try:
        # Attempt 2: Direct Import (Fallback)
        # We import 'mbrl_manager' but alias it as 'sac_manager'
        # so the variable is defined for the rest of the script.
        import mbrl_manager as sac_manager

        print("✅ Success: Imported 'mbrl_manager' directly as 'sac_manager'")
    except ImportError as e2:
        print(f"❌ CRITICAL ERROR: Could not import 'mbrl_manager'.")
        print(f"   Reason 1: {e}")
        print(f"   Reason 2: {e2}")
        print("\n   Please ensure 'mbrl_manager.py' exists in 'modules/ai_core/' or the root folder.")
        # Define it as None so the script fails gracefully in the main block instead of crashing here
        sac_manager = None

# ==============================================================================
# 3. MAIN TRAINING LOOP
# ==============================================================================
if __name__ == "__main__":
    print("\n==================================================")
    print("   INNOMOTICS MBRL: OFFLINE TRAINING SEQUENCE")
    print("==================================================")

    if sac_manager is None:
        print("❌ Error: AI Manager module could not be loaded. Exiting.")
        sys.exit(1)

    print("1. Initialization")
    print("2. Training Loop (This may take hours)")
    print("--------------------------------------------------")

    try:
        # Verify the function exists
        if hasattr(sac_manager, 'train_system_offline'):
            # The actual training call
            sac_manager.train_system_offline()

            print("\n✅ SUCCESS: Training Complete.")
            print("Models saved to files/models/")
        else:
            print(f"❌ Error: The module '{sac_manager}' does not have a 'train_system_offline' function.")
            print("Please check the content of 'mbrl_manager.py'.")

    except Exception as e:
        print(f"\n❌ CRITICAL FAILURE DURING TRAINING: {e}")
        traceback.print_exc()
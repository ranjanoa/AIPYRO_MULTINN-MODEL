import os
import sys

# Setup Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'modules'))
sys.path.append(os.path.join(BASE_DIR, 'modules', 'ai_core'))

print(f"📂 Current Directory: {BASE_DIR}")

# 1. Check if PyTorch is installed
print("\n🔍 Checking PyTorch...")
try:
    import torch
    print(f"✅ PyTorch is installed! Version: {torch.__version__}")
except ImportError as e:
    print(f"❌ PyTorch Import Failed: {e}")
    print("👉 SOLUTION: Run 'pip install torch' in your terminal.")
    sys.exit()

# 2. Check if Files Exist
print("\n🔍 Checking Model Files...")
wm_path = os.path.join(BASE_DIR, 'files', 'models', 'ensemble_wm')
sac_path = os.path.join(BASE_DIR, 'files', 'models', 'sac_agent')

if os.path.exists(wm_path):
    print(f"✅ World Model file found at: {wm_path}")
else:
    print(f"❌ World Model NOT FOUND at: {wm_path}")

if os.path.exists(sac_path):
    print(f"✅ SAC Agent file found at: {sac_path}")
else:
    print(f"❌ SAC Agent NOT FOUND at: {sac_path}")

# 3. Attempt to Import Modules (The likely failure point)
print("\n🔍 Attempting to Import AI Modules...")
try:
    from modules.ai_core import world_model
    print("✅ world_model.py imported successfully.")
except ImportError as e:
    print(f"❌ Failed to import world_model.py: {e}")
except Exception as e:
    print(f"❌ Crash inside world_model.py: {e}")

try:
    from modules.ai_core import sac_components
    print("✅ sac_components.py imported successfully.")
except ImportError as e:
    print(f"❌ Failed to import sac_components.py: {e}")

# 4. Attempt to Load the Models
print("\n🔍 Attempting to Load Models...")
try:
    if os.path.exists(wm_path):
        # We try to mimic how the code loads it
        try:
            checkpoint = torch.load(wm_path, map_location='cpu')
            print("✅ World Model loaded into memory successfully!")
        except Exception as e:
            print(f"❌ CRITICAL: File exists, but torch.load failed: {e}")
except Exception as e:
    print(f"❌ Load Error: {e}")

print("\n--- DIAGNOSTIC COMPLETE ---")
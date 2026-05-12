import os
import sys
import subprocess

target_dir = r"c:\Users\ranja\projects\to send"
print(f"Changing directory to: {target_dir}")
os.chdir(target_dir)

# Ensure the pyarmor runtime is found if it's in the same directory
sys.path.append(target_dir)

print("Starting app.py...")
# Using subprocess.run or Popen
# We'll use Popen to let it run and we can monitor it if needed, 
# but for a background command, the wrapper script will just stay alive.
try:
    process = subprocess.Popen([sys.executable, "app.py"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.STDOUT, 
                               text=True,
                               bufsize=1)
    for line in process.stdout:
        print(line, end="")
except Exception as e:
    print(f"Error starting app: {e}")

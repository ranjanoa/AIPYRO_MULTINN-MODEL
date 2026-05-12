import json
import pandas as pd
from fingerprint_engine import get_live_fingerprint_action, get_model_config_safe, get_active_strategy

# Load config
conf = get_model_config_safe()
strategy_name, frontend_strategy = get_active_strategy(conf)

state = {
    'Kiln BZT1': 1400.0,
    'O2 (Kiln)': 2.5,
    'CO (kiln)': 0.1,
    'Kiln feed': 220.0,
    'Kiln motor 1 Amps': 290.0,
    'Free CaO': 1.0,
    'ID fan speed': 900.0,
    'Kiln speed': 3.5,
    'Petcoke (Kiln)': 3.0,
    '% TSR (total)': 50.0
}

dummy_window = pd.DataFrame([state, state, state, state, state]) # No slopes for test

print('Testing Fingerprint Golden Envelope Logic...')
result = get_live_fingerprint_action('AUTO', strategy_name, frontend_strategy, state, 1.0, dummy_window)

if result:
    print('SUCCESS! Valid matches found:')
    print(f"Target TS: {result.get('target_timestamp')}")
    num_actions = len(result.get('actions', []))
    print(f"Golden Envelope Generated with {num_actions} actions.")
else:
    print('FAILED: Result was None.')

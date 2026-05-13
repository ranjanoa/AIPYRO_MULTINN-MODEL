import os
import sys
import pandas as pd
import numpy as np
import torch
import json
from datetime import datetime, timedelta

# Setup Paths to match main app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'modules'))

import config
import database
import process_model

def run_advanced_diagnostic():
    print("="*60)
    print("      AIPYRO AI SYSTEM DIAGNOSTIC (ADVANCED)")
    print("="*60)
    
    # 1. Check Model Files specifically
    print("\n[1] MODEL FILE CHECK")
    models_dir = config.MODELS_DIR
    print(f"Models Directory: {models_dir}")
    if os.path.exists(models_dir):
        files = os.listdir(models_dir)
        print(f"Files found: {files}")
        has_wm = any("ensemble_wm" in f for f in files)
        has_sac = any("sac_agent" in f for f in files)
        print(f"World Model Presence: {'[OK]' if has_wm else '[MISSING]'}")
        print(f"SAC Agent Presence: {'[OK]' if has_sac else '[MISSING]'}")
    else:
        print("[ERR] Models directory does not exist!")

    # 2. Variable Configuration Audit
    print("\n[2] VARIABLE CONFIGURATION AUDIT")
    conf = process_model.load_model_config()
    controls = process_model.get_control_variables()
    indicators = process_model.get_indicator_variables()
    
    # Map friendly names to tags
    name_to_tag = {name: data.get('tag_name') for name, data in {**controls, **indicators}.items() if data.get('tag_name')}
    
    print(f"Total defined variables: {len(name_to_tag)}")

    # 3. InfluxDB Discovery (Last 1 Hour)
    print("\n[3] INFLUXDB DISCOVERY (TAGS IN DATABASE)")
    client = database.get_db_client()
    if not client:
        print("[ERR] Could not connect to InfluxDB. Check config.py URL/TOKEN.")
        return

    try:
        # Query all unique fields in the bucket for the last hour
        query = f'''
        import "influxdata/influxdb/schema"
        schema.fieldKeys(bucket: "{config.DB_BUCKET}")
        '''
        results = client.query_api().query(org=config.DB_ORG, query=query)
        db_tags = []
        for table in results:
            for record in table.records:
                db_tags.append(record.get_value())
        
        print(f"Found {len(db_tags)} unique tags in bucket '{config.DB_BUCKET}'")
        
        # Cross-reference with config
        missing_in_db = []
        matched_in_db = []
        for name, tag in name_to_tag.items():
            if tag in db_tags:
                matched_in_db.append(tag)
            else:
                missing_in_db.append((name, tag))
        
        print(f"Matches: {len(matched_in_db)}")
        print(f"Mismatches: {len(missing_in_db)}")
        
        if missing_in_db:
            print("\n⚠️  VARIABLES MISSING FROM DATABASE (NOT FOUND IN INFLUX):")
            for name, tag in missing_in_db[:10]:
                print(f"   - '{name}' (Expected Tag: '{tag}')")
            if len(missing_in_db) > 10: print(f"   ... and {len(missing_in_db)-10} more.")
            print("\n👉 ACTION: Verify your OPC/PI exporter is sending these tags with EXACTLY these names.")

    except Exception as e:
        print(f"[ERR] InfluxDB Query Error: {e}")
    finally:
        client.close()

    # 4. Neural Network Observation Check
    print("\n[4] NEURAL NETWORK OBSERVATION INTEGRITY")
    try:
        from modules.ai_core import mbrl_manager
        mbrl_manager._initialize_system()
        
        # Check normalization ranges
        stats = mbrl_manager._env_config['stats']
        s_cols = mbrl_manager._env_config['s_cols']
        
        print(f"Checking {len(s_cols)} sensors for range validity...")
        
        invalid_ranges = []
        for i, col in enumerate(s_cols):
            mn = stats['state']['min'][i]
            mx = stats['state']['max'][i]
            rg = stats['state']['range'][i]
            if rg < 1e-6:
                invalid_ranges.append((col, mn, mx))
        
        if invalid_ranges:
            print(f"⚠️  {len(invalid_ranges)} sensors have ZERO range in the historical training data!")
            for col, mn, mx in invalid_ranges[:5]:
                print(f"   - {col}: Min={mn}, Max={mx}")
            print("   👉 IMPACT: These sensors provide zero information to the AI.")
        else:
            print("[OK] All sensors have valid variance in training history.")

    except Exception as e:
        print(f"[ERR] AI Initialization Error: {e}")

    print("\n" + "="*60)
    print("ADVANCED DIAGNOSTIC COMPLETE")
    print("="*60)

if __name__ == "__main__":
    run_advanced_diagnostic()

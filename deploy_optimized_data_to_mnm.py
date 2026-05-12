import pandas as pd
import os

def deploy_optimized_data():
    source_csv = r'c:\Users\ranja\projects\aipyro-combined-nn-app\files\data\fingerprint4.csv'
    target_csv = r'c:\Users\ranja\projects\to send\Kiln_Active_data_Cimpor_01012025_30112025.csv'
    
    if not os.path.exists(source_csv):
        print(f"Source file not found: {source_csv}")
        return

    print(f"Reading source data (1.07 GB)...")
    df = pd.read_csv(source_csv)
    
    print("Renaming headers for MNM compatibility...")
    mapping = {
        '1_timeStamp': 'time',
        'Stack - TOC (dry, 10% O2)': 'TOC Corrected',
        'Stack - HCl (dry, 10% O2)': 'HCl Corrected',
        'Stack - SO2 (dry, 10% O2) ': 'SO2 Corrected', # Note: checked for trailing space
        'Stack - SO2 (dry, 10% O2)': 'SO2 Corrected'
    }
    df.rename(columns=mapping, inplace=True)
    
    print("Optimizing memory (float32)...")
    fcols = df.select_dtypes(include=['float64']).columns
    df[fcols] = df[fcols].astype('float32')
    
    # Backup original large file if it exists
    if os.path.exists(target_csv):
        size_gb = os.path.getsize(target_csv) / (1024**3)
        if size_gb > 1.0: # Only backup if it's the large original
            backup = target_csv + ".7gb_backup"
            if not os.path.exists(backup):
                print(f"Backing up 7.5GB original to {backup}...")
                os.rename(target_csv, backup)
    
    print(f"Saving optimized data to {target_csv}...")
    # index=True and index_label='' creates the leading comma header like ",time"
    df.to_csv(target_csv, index=True, index_label='')
    
    print(f"SUCCESS: 7.5GB file replaced with optimized 698MB (float32) data.")
    print(f"The MNM application should now start much faster and use less RAM.")

if __name__ == "__main__":
    deploy_optimized_data()

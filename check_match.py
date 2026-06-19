import pandas as pd
import re

PROCESSI_NIOSH_ALTO_ITK1 = {
    "pick": "SDC PICK",
    "palletize - case": "SDC PALLETIZE",
    "case transfer in": "SDC STOW",
    "cart/pallet builder": "SDC CART BUILDER",
    "line load injection": "SDC SCARICO FLUIDO",
    "cart handler trans": "SDC RUNNER STOW",
}

df = pd.read_csv(r'c:\Users\bonvinod\Documents\BOARD NUOVA\dashboard\data\snapshot_2026-06-18.csv')

# Trova chi ha Lead/PA in ITK1 che matcha i processi NIOSH alto
for _, row in df.iterrows():
    itk1 = row['ITK1_Processes_7d']
    if pd.isna(itk1):
        continue
    parts = str(itk1).split("|")
    for part in parts:
        part = part.strip()
        match = re.match(r'(.+?)\s+([\d.]+)%', part)
        if match:
            proc_name = match.group(1).strip()
            if proc_name.lower() in PROCESSI_NIOSH_ALTO_ITK1:
                if 'lead' in proc_name.lower() or '/pa' in proc_name.lower() or 'leadpa' in proc_name.lower():
                    print(f"PROBLEMA: {row['login']} - {proc_name} matchato come {PROCESSI_NIOSH_ALTO_ITK1[proc_name.lower()]}")

# Controlla anche "Stow to Prime LeadPA" - contiene "stow"?
print("\nCheck exact match per 'Stow to Prime LeadPA':")
test = "stow to prime leadpa"
print(f"  '{test}' in dict? {test in PROCESSI_NIOSH_ALTO_ITK1}")
print(f"  'cart/pallet builder' in dict? {'cart/pallet builder' in PROCESSI_NIOSH_ALTO_ITK1}")

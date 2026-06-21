import pandas as pd
import re
import sys
sys.path.insert(0, r'c:\Users\bonvinod\Documents\BOARD NUOVA\dashboard')

PROCESSI_NIOSH_ALTO_NON_ITK1 = {
    "Cart Handler Stow": "RUNNER STOW (2.05)",
    "Fluid Loader": "SCARICO FLUIDO (2.51)",
    "Water Spider": "WATERSPIDER/RUNNER (2.53)",
}

PROCESSI_NIOSH_ALTO_ITK1 = {
    "pick": "SDC PICK",
    "palletize - case": "SDC PALLETIZE",
    "case transfer in": "SDC STOW",
    "cart/pallet builder": "SDC CART BUILDER",
    "line load injection": "SDC SCARICO FLUIDO",
    "cart handler trans": "SDC RUNNER STOW",
}

df = pd.read_csv(r'c:\Users\bonvinod\Documents\BOARD NUOVA\dashboard\data\snapshot_2026-06-20.csv')
row = df[df['login'] == 'vpetrone'].iloc[0]

processes_str = row['Processes_7d_weighted']
itk1_procs_str = row['ITK1_Processes_7d']
itk1_pct = row['ITK1_HoursPercent']

print(f"Processes: {processes_str}")
print(f"ITK1 Processes: {itk1_procs_str}")
print(f"ITK1 HoursPercent: {itk1_pct}")
print()

# Determina processi in ITK1
itk1_procs = set()
if not pd.isna(itk1_procs_str):
    for part in str(itk1_procs_str).split("|"):
        match = re.match(r'(.+?)\s+[\d.]+%', part.strip())
        if match:
            itk1_procs.add(match.group(1).strip().lower())
print(f"ITK1 procs set: {itk1_procs}")

# Non-ITK1
non_itk1_pct = 0.0
parts = str(processes_str).split("|")
for part in parts:
    part = part.strip()
    for target in PROCESSI_NIOSH_ALTO_NON_ITK1.keys():
        if target.lower() in part.lower():
            if target.lower() not in itk1_procs:
                match = re.search(r'([\d.]+)%', part)
                if match:
                    val = float(match.group(1))
                    print(f"  NON-ITK1 match: {target} -> {val}%")
                    non_itk1_pct += val
            else:
                print(f"  SKIPPED (in ITK1): {target}")
            break

print(f"\nNon-ITK1 total: {non_itk1_pct}%")

# ITK1
itk1_niosh_pct = 0.0
if not pd.isna(itk1_procs_str):
    parts = str(itk1_procs_str).split("|")
    for part in parts:
        part = part.strip()
        match = re.match(r'(.+?)\s+([\d.]+)%', part)
        if match:
            proc_name = match.group(1).strip().lower()
            proc_pct = float(match.group(2))
            if proc_name in PROCESSI_NIOSH_ALTO_ITK1:
                contrib = (proc_pct / 100) * float(itk1_pct) * 100
                print(f"  ITK1 match: {proc_name} -> {proc_pct}% of ITK1, contributo: {contrib:.1f}%")
                itk1_niosh_pct += contrib

print(f"\nITK1 total: {itk1_niosh_pct:.1f}%")
print(f"\nTOTALE NIOSH >2: {non_itk1_pct + itk1_niosh_pct:.1f}%")
print(f"Alert (>50%)? {'SI' if non_itk1_pct + itk1_niosh_pct > 50 else 'NO'}")

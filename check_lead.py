import pandas as pd
import re

df = pd.read_csv(r'c:\Users\bonvinod\Documents\BOARD NUOVA\dashboard\data\snapshot_2026-06-18.csv')

# Cerca tutti i processi che contengono "lead" o "PA" nei nomi
all_processes = set()
for val in df['Processes_7d_weighted'].dropna():
    parts = str(val).split('|')
    for part in parts:
        part = part.strip()
        match = re.match(r'(.+?)\s+[\d.]+%', part)
        if match:
            name = match.group(1).strip()
            if 'lead' in name.lower() or '/pa' in name.lower() or 'lead/pa' in name.lower():
                all_processes.add(name)

print("Processi con 'Lead' o 'PA':")
for p in sorted(all_processes):
    print(f"  {p}")

# Ora cerca nei ITK1_Processes_7d
print("\nProcessi Lead/PA in ITK1:")
itk1_leads = set()
for val in df['ITK1_Processes_7d'].dropna():
    parts = str(val).split('|')
    for part in parts:
        part = part.strip()
        match = re.match(r'(.+?)\s+[\d.]+%', part)
        if match:
            name = match.group(1).strip()
            if 'lead' in name.lower() or '/pa' in name.lower():
                itk1_leads.add(name)

for p in sorted(itk1_leads):
    print(f"  {p}")

import pandas as pd
import re

df = pd.read_csv(r'c:\Users\bonvinod\Documents\BOARD NUOVA\dashboard\data\snapshot_2026-06-18.csv')

all_processes = set()
for val in df['Processes_7d_weighted'].dropna():
    parts = str(val).split('|')
    for part in parts:
        part = part.strip()
        match = re.match(r'(.+?)\s+[\d.]+%', part)
        if match:
            all_processes.add(match.group(1).strip())

for p in sorted(all_processes):
    print(p)
print(f'\nTotale processi unici: {len(all_processes)}')

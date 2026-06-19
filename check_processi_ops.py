import pandas as pd
import re

df = pd.read_csv(r'c:\Users\bonvinod\Documents\BOARD NUOVA\dashboard\data\snapshot_2026-06-18.csv')

# Conta quanti AA hanno ogni processo come principale
process_stats = {}
for val in df['Processes_7d_weighted'].dropna():
    parts = str(val).split('|')
    if parts:
        first = parts[0].strip()
        match = re.match(r'(.+?)\s+[\d.]+%', first)
        if match:
            proc = match.group(1).strip()
            process_stats[proc] = process_stats.get(proc, 0) + 1

# Mostra quelli sotto 30 (quelli che escludiamo)
print("PROCESSI ESCLUSI (< 30 AAs):")
excluded = []
for proc, count in sorted(process_stats.items(), key=lambda x: x[1]):
    if count < 30:
        excluded.append(proc)
        print(f"  {proc}: {count}")

print(f"\nTotale processi esclusi: {len(excluded)}")
print(f"\nPROCESSI INCLUSI (>= 30 AAs):")
for proc, count in sorted(process_stats.items(), key=lambda x: -x[1]):
    if count >= 30:
        print(f"  {proc}: {count}")

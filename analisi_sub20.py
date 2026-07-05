import pandas as pd
import re

df = pd.read_csv(r'c:\Users\bonvinod\Documents\BOARD NUOVA\dashboard\data\snapshot_2026-06-30.csv')

# Filtra rotazione < 20%
df_sub20 = df[df['RotationPercent'] * 100 < 20]

# Estrai processo principale per ognuno
main_procs = []
for val in df_sub20['Processes_7d_weighted'].dropna():
    parts = str(val).split('|')
    if parts:
        match = re.match(r'(.+?)\s+[\d.]+%', parts[0].strip())
        if match:
            main_procs.append(match.group(1).strip())

# Conta
from collections import Counter
counts = Counter(main_procs)

print(f"Persone con rotazione < 20%: {len(df_sub20)}")
print(f"\nProcesso principale - Top 15:")
for proc, count in counts.most_common(15):
    print(f"  {proc}: {count} AAs")

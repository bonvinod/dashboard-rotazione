import pandas as pd

df24 = pd.read_csv('data/snapshot_2026-06-24.csv')
df26 = pd.read_csv('data/snapshot_2026-06-26.csv')

# Rimuovi duplicati per login (tieni primo)
df24 = df24.drop_duplicates(subset='login', keep='first')
df26 = df26.drop_duplicates(subset='login', keep='first')

# Login comuni
common = set(df24['login']).intersection(set(df26['login']))

df24_c = df24[df24['login'].isin(common)].set_index('login')
df26_c = df26[df26['login'].isin(common)].set_index('login')

numeric_cols = ['TotalHours', 'DifferentProcesses', 'MainProcessShare', 'RotationPercent', 'ITK1_HoursPercent', 'ITK1_TotalHours']

df25 = df24_c.copy()
for col in numeric_cols:
    if col in df24_c.columns and col in df26_c.columns:
        df25[col] = (df24_c[col].fillna(0) + df26_c.loc[df24_c.index, col].fillna(0)) / 2

df25 = df25.reset_index()
df25.to_csv('data/snapshot_2026-06-25.csv', index=False, encoding='utf-8-sig')
print(f'Snapshot 25 creato: {len(df25)} righe')

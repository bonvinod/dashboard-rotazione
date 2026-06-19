import pandas as pd
df = pd.read_csv(r'c:\Users\bonvinod\Documents\BOARD NUOVA\dashboard\data\snapshot_2026-06-18.csv')
row = df[df['login'] == 'mesaqibc']
if len(row) > 0:
    r = row.iloc[0]
    for col in df.columns:
        print(f"{col}: {r[col]}")
else:
    print("Login non trovato")

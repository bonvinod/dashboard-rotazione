import pandas as pd
df = pd.read_csv(r'c:\Users\bonvinod\Documents\BOARD NUOVA\dashboard\data\snapshot_2026-06-18.csv')
samples = df[df['ITK1_Processes_7d'].notna() & (df['ITK1_Processes_7d'] != '')].head(15)
for _, row in samples.iterrows():
    login = row['login']
    itk1 = row['ITK1_Processes_7d']
    itk1_pct = row['ITK1_HoursPercent']
    procs = row['Processes_7d_weighted']
    print(f"LOGIN: {login}")
    print(f"  ITK1_Processes: {itk1}")
    print(f"  ITK1_Hours%: {itk1_pct}")
    print(f"  All Processes: {procs[:100]}")
    print()

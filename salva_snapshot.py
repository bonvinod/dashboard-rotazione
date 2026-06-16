"""
Salva uno snapshot giornaliero dal file Excel con Power Query.
Eseguito automaticamente dopo il refresh del file.
"""
import pandas as pd
import os
from datetime import datetime

# === CONFIGURAZIONE ===
EXCEL_PATH = r"\\ant\dept-eu\MXP5\Operations\FC\Outbound\Rotazione Percentuale AAs.xlsx"
SHEET_NAME = "Processi e rotazioni"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def main():
    # Crea cartella data se non esiste
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Leggi il foglio principale
    print(f"Lettura file: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
    
    # Salva snapshot con data di oggi
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(DATA_DIR, f"snapshot_{today}.csv")
    
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    print(f"Snapshot salvato: {output_path}")
    print(f"Righe: {len(df)}, Colonne: {len(df.columns)}")
    print(f"Data: {today}")

if __name__ == "__main__":
    main()

"""
Apre il file Excel, esegue il refresh delle Power Query, salva e chiude.
Poi salva lo snapshot per la dashboard.
"""
import subprocess
import time
import os
import sys

EXCEL_PATH = r"\\ant\dept-eu\MXP5\Operations\FC\Outbound\Rotazione Percentuale AAs.xlsx"

def refresh_excel():
    """Usa COM automation per aprire Excel, refresh e salvare."""
    try:
        import win32com.client
    except ImportError:
        print("Installazione pywin32...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pywin32", "--quiet"])
        import win32com.client
    
    print("Apertura Excel...")
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False  # Esegui in background
    excel.DisplayAlerts = False
    
    try:
        wb = excel.Workbooks.Open(EXCEL_PATH)
        print("Refresh Power Query in corso...")
        wb.RefreshAll()
        
        # Attendi che il refresh finisca
        time.sleep(30)  # Attendi 30 secondi per il refresh
        
        # Salva
        wb.Save()
        print("File salvato.")
        
    finally:
        wb.Close(SaveChanges=False)
        excel.Quit()
        print("Excel chiuso.")

def main():
    # Step 1: Refresh Excel
    refresh_excel()
    
    # Step 2: Salva snapshot
    print("\nSalvataggio snapshot...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    snapshot_script = os.path.join(script_dir, "salva_snapshot.py")
    subprocess.run([sys.executable, snapshot_script])
    
    print("\n✓ Tutto completato!")

if __name__ == "__main__":
    main()

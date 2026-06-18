import win32com.client
import time
import pythoncom

pythoncom.CoInitialize()

EXCEL_PATH = r"\\ant\dept-eu\MXP5\Operations\FC\Outbound\Rotazione Percentuale AAs.xlsx"

try:
    print("Apertura Excel...")
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = True
    excel.DisplayAlerts = False
    
    print(f"Apertura file...")
    wb = excel.Workbooks.Open(EXCEL_PATH)
    
    # Disabilita background query per forzare refresh sincrono
    print("Disabilito background query...")
    for conn in wb.Connections:
        try:
            conn.OLEDBConnection.BackgroundQuery = False
        except:
            pass
        try:
            conn.ODBCConnection.BackgroundQuery = False
        except:
            pass
    
    print("Refresh di tutte le connessioni...")
    wb.RefreshAll()
    
    # Attendi che il calcolo sia completo
    print("Attendo completamento refresh...")
    time.sleep(120)  # 2 minuti di attesa
    
    # Forza ricalcolo
    excel.CalculateFullRebuild()
    time.sleep(5)
    
    # Salva esplicitamente
    print("Salvataggio...")
    wb.Save()
    time.sleep(3)
    
    # Verifica che sia salvato
    print(f"File salvato: {wb.Saved}")
    
    print("Chiusura...")
    wb.Close(SaveChanges=True)
    time.sleep(2)
    excel.Quit()
    print("FATTO! File refreshato e salvato.")
    
except Exception as e:
    print(f"ERRORE: {e}")
    try:
        excel.Quit()
    except:
        pass
finally:
    pythoncom.CoUninitialize()

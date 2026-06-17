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
    
    print("Refresh di tutte le connessioni...")
    # Refresh una connessione alla volta con BackgroundQuery=False
    for conn in wb.Connections:
        try:
            print(f"  Refreshing: {conn.Name}")
            conn.OLEDBConnection.BackgroundQuery = False
            conn.Refresh()
        except:
            try:
                conn.ODBCConnection.BackgroundQuery = False
                conn.Refresh()
            except:
                pass
    
    print("Attendo 10 secondi di sicurezza...")
    time.sleep(10)
    
    print("Salvataggio...")
    wb.Save()
    print("Chiusura...")
    wb.Close(False)
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

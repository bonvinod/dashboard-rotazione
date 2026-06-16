import streamlit as st
import pandas as pd
import os
import glob
from datetime import datetime, timedelta

# === CONFIGURAZIONE ===
DATA_DIR = "data"  # Cartella con gli snapshot giornalieri

# Processi da monitorare specificamente
PROCESSI_MONITORATI = ["Pick", "SDC", "Palletize Case", "Case Palletizer"]

st.set_page_config(page_title="Rotazione AAs - Dashboard", layout="wide")

# === FUNZIONI ===
@st.cache_data(ttl=300)
def load_all_snapshots():
    """Carica tutti gli snapshot giornalieri disponibili."""
    files = sorted(glob.glob(os.path.join(DATA_DIR, "snapshot_*.csv")))
    if not files:
        return None, []
    
    all_data = []
    dates_available = []
    for f in files:
        # Estrai data dal nome file: snapshot_2025-01-15.csv
        basename = os.path.basename(f)
        date_str = basename.replace("snapshot_", "").replace(".csv", "")
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            continue
        df = pd.read_csv(f)
        df["snapshot_date"] = date
        all_data.append(df)
        dates_available.append(date)
    
    if not all_data:
        return None, []
    
    return pd.concat(all_data, ignore_index=True), sorted(dates_available)

def calc_process_hours_pct(processes_str, target_processes):
    """Calcola la % di ore su processi target da stringa tipo 'Pick 80.3% | Water Spider 18.5%'."""
    if not processes_str or pd.isna(processes_str):
        return 0.0
    total_pct = 0.0
    parts = str(processes_str).split("|")
    for part in parts:
        part = part.strip()
        for target in target_processes:
            if target.lower() in part.lower():
                # Estrai percentuale
                import re
                match = re.search(r'([\d.]+)%', part)
                if match:
                    total_pct += float(match.group(1))
                break
    return total_pct

def get_last_refresh_date(dates):
    """Restituisce la data dell'ultimo refresh."""
    if dates:
        return max(dates)
    return None

# === LAYOUT PRINCIPALE ===
st.title("📊 Rotazione AAs - Dashboard")

# Carica dati
df_all, dates_available = load_all_snapshots()

if df_all is None or len(dates_available) == 0:
    st.warning("⚠️ Nessun dato disponibile. Esegui il primo refresh per popolare la dashboard.")
    st.info("Esegui `AGGIORNA_DASHBOARD.bat` per caricare il primo snapshot.")
    st.stop()

# === HEADER: Info refresh e filtri ===
col1, col2, col3 = st.columns([1, 2, 2])

with col1:
    last_refresh = get_last_refresh_date(dates_available)
    st.metric("Ultimo Refresh", last_refresh.strftime("%d/%m/%Y") if last_refresh else "N/A")

with col2:
    # Selettore periodo
    date_range = st.date_input(
        "Periodo",
        value=(min(dates_available), max(dates_available)),
        min_value=min(dates_available),
        max_value=max(dates_available),
    )

# Gestisci selezione singola data vs range
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

# Filtra per periodo
df_filtered = df_all[(df_all["snapshot_date"] >= start_date) & (df_all["snapshot_date"] <= end_date)]

# Filtro manager
with col3:
    managers = sorted(df_filtered["manager_alias"].dropna().unique().tolist())
    selected_manager = st.selectbox("Filtro Manager", ["Tutti"] + managers)

if selected_manager != "Tutti":
    df_filtered = df_filtered[df_filtered["manager_alias"] == selected_manager]

# === SOGLIA ROTAZIONE ===
st.divider()
soglia_col1, soglia_col2 = st.columns([1, 3])
with soglia_col1:
    soglia_rotazione = st.slider("Soglia rotazione critica (%)", 0, 100, 20, 5)

# === CALCOLI KPI ===
# Media rotazione sul periodo (media per persona, poi media totale)
df_person_avg = df_filtered.groupby("login").agg({
    "RotationPercent": "mean",
    "TotalHours": "mean",
    "DifferentProcesses": "mean",
    "Processes_7d_weighted": "last",
    "manager_alias": "last",
    "Limitazione": "last",
}).reset_index()

# Calcola % ore sui processi monitorati per persona
df_person_avg["PctProcessiMonitorati"] = df_person_avg["Processes_7d_weighted"].apply(
    lambda x: calc_process_hours_pct(x, PROCESSI_MONITORATI)
)

rotation_media = df_person_avg["RotationPercent"].mean() * 100
pct_monitorati_media = df_person_avg["PctProcessiMonitorati"].mean()
n_sotto_soglia = (df_person_avg["RotationPercent"] * 100 < soglia_rotazione).sum()
n_totale = len(df_person_avg)
pct_sotto_soglia = (n_sotto_soglia / n_totale * 100) if n_totale > 0 else 0


# === KPI CARDS ===
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Rotazione Media", f"{rotation_media:.1f}%")
with kpi2:
    st.metric("% Ore Pick/SDC/Pall.", f"{pct_monitorati_media:.1f}%")
with kpi3:
    st.metric(f"Persone sotto {soglia_rotazione}%", f"{n_sotto_soglia} ({pct_sotto_soglia:.0f}%)")
with kpi4:
    st.metric("Persone totali", f"{n_totale}")

# === TREND NEL TEMPO ===
st.divider()
st.subheader("📈 Trend Rotazione nel Tempo")

if len(dates_available) > 1:
    df_trend = df_filtered.groupby("snapshot_date").agg({
        "RotationPercent": "mean",
    }).reset_index()
    df_trend["RotationPercent"] = df_trend["RotationPercent"] * 100
    df_trend = df_trend.rename(columns={"snapshot_date": "Data", "RotationPercent": "Rotazione Media %"})
    st.line_chart(df_trend.set_index("Data")["Rotazione Media %"])
else:
    st.info("Servono almeno 2 giorni di dati per mostrare il trend.")

# === TREND % PROCESSI MONITORATI ===
st.subheader("📈 Trend % Ore su Pick / SDC / Palletize Case")

if len(dates_available) > 1:
    # Calcola per ogni giorno
    trend_proc = []
    for date in df_filtered["snapshot_date"].unique():
        df_day = df_filtered[df_filtered["snapshot_date"] == date]
        pct_day = df_day["Processes_7d_weighted"].apply(
            lambda x: calc_process_hours_pct(x, PROCESSI_MONITORATI)
        ).mean()
        trend_proc.append({"Data": date, "% Ore Monitorati": pct_day})
    df_trend_proc = pd.DataFrame(trend_proc)
    if not df_trend_proc.empty:
        st.line_chart(df_trend_proc.set_index("Data")["% Ore Monitorati"])
else:
    st.info("Servono almeno 2 giorni di dati per mostrare il trend.")


# === TABELLE TOP/BOTTOM ===
st.divider()
tab1, tab2 = st.columns(2)

with tab1:
    st.subheader("🔴 Top 10 - Rotazione più bassa")
    df_bottom = df_person_avg.nsmallest(10, "RotationPercent")[
        ["login", "manager_alias", "RotationPercent", "DifferentProcesses", "Limitazione"]
    ].copy()
    df_bottom["RotationPercent"] = (df_bottom["RotationPercent"] * 100).round(1)
    df_bottom["Ha Limitazione"] = df_bottom["Limitazione"].apply(
        lambda x: "Sì" if x and str(x) not in ("", "nan", "0") else "No"
    )
    df_bottom = df_bottom.rename(columns={
        "login": "Login",
        "manager_alias": "Manager",
        "RotationPercent": "Rotazione %",
        "DifferentProcesses": "N° Processi",
    })
    st.dataframe(df_bottom[["Login", "Manager", "Rotazione %", "N° Processi", "Ha Limitazione"]], 
                 use_container_width=True, hide_index=True)

with tab2:
    st.subheader("🟠 Top 10 - Più ore su Pick/SDC/Pall.")
    df_top_proc = df_person_avg.nlargest(10, "PctProcessiMonitorati")[
        ["login", "manager_alias", "PctProcessiMonitorati", "RotationPercent", "Limitazione"]
    ].copy()
    df_top_proc["RotationPercent"] = (df_top_proc["RotationPercent"] * 100).round(1)
    df_top_proc["PctProcessiMonitorati"] = df_top_proc["PctProcessiMonitorati"].round(1)
    df_top_proc["Ha Limitazione"] = df_top_proc["Limitazione"].apply(
        lambda x: "Sì" if x and str(x) not in ("", "nan", "0") else "No"
    )
    df_top_proc = df_top_proc.rename(columns={
        "login": "Login",
        "manager_alias": "Manager",
        "PctProcessiMonitorati": "% Ore Monitorati",
        "RotationPercent": "Rotazione %",
    })
    st.dataframe(df_top_proc[["Login", "Manager", "% Ore Monitorati", "Rotazione %", "Ha Limitazione"]], 
                 use_container_width=True, hide_index=True)

# === TABELLA COMPLETA (espandibile) ===
st.divider()
with st.expander("📋 Tabella completa - Tutti i lavoratori"):
    df_full = df_person_avg[["login", "manager_alias", "RotationPercent", 
                              "DifferentProcesses", "PctProcessiMonitorati", "TotalHours", "Limitazione"]].copy()
    df_full["RotationPercent"] = (df_full["RotationPercent"] * 100).round(1)
    df_full["PctProcessiMonitorati"] = df_full["PctProcessiMonitorati"].round(1)
    df_full["TotalHours"] = df_full["TotalHours"].round(1)
    df_full = df_full.rename(columns={
        "login": "Login",
        "manager_alias": "Manager", 
        "RotationPercent": "Rotazione %",
        "DifferentProcesses": "N° Processi",
        "PctProcessiMonitorati": "% Pick/SDC/Pall.",
        "TotalHours": "Ore Totali",
        "Limitazione": "Limitazione Medica",
    })
    st.dataframe(df_full, use_container_width=True, hide_index=True)

import streamlit as st
import pandas as pd
import os
import glob
import re
from datetime import datetime, timedelta

# === CONFIGURAZIONE ===
DATA_DIR = "data"

# Processi con NIOSH > 2 (scenario peggiore) e loro nomi nello snapshot
# NOTA: Pick e Palletize-Case contano come NIOSH alto SOLO se in area ITK1 (SDC)
# Pick normale (non ITK1) ha NIOSH < 2, quindi non va incluso qui
PROCESSI_NIOSH_ALTO_NON_ITK1 = {
    "Robotics Operator": "CORRAL OPERATOR / PID OPERATOR (2.32)",
    "Cart Handler Stow": "RUNNER STOW (2.05)",
    "Fluid Loader": "SCARICO FLUIDO (2.51)",
    "Water Spider": "WATERSPIDER/RUNNER (2.53)",
}
# Per SDC (Pick/Palletize-Case in ITK1), usiamo la colonna ITK1_HoursPercent

st.set_page_config(page_title="Rotazione AAs - Dashboard", layout="wide")

# === FUNZIONI ===
@st.cache_data(ttl=300)
def load_all_snapshots():
    """Carica tutti gli snapshot giornalieri."""
    files = sorted(glob.glob(os.path.join(DATA_DIR, "snapshot_*.csv")))
    if not files:
        return None, []
    all_data = []
    dates_available = []
    for f in files:
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

def calc_niosh_alto_pct(row):
    """Calcola % tempo su processi con NIOSH > 2 (non-ITK1 + ITK1)."""
    processes_str = row.get("Processes_7d_weighted", "")
    itk1_pct = row.get("ITK1_HoursPercent", 0)
    
    # Parte 1: processi non-ITK1 con NIOSH alto
    non_itk1_pct = 0.0
    if processes_str and not pd.isna(processes_str):
        parts = str(processes_str).split("|")
        for part in parts:
            part = part.strip()
            for target in PROCESSI_NIOSH_ALTO_NON_ITK1.keys():
                if target.lower() in part.lower():
                    match = re.search(r'([\d.]+)%', part)
                    if match:
                        non_itk1_pct += float(match.group(1))
                    break
    
    # Parte 2: ITK1 (SDC) - usa ITK1_HoursPercent (è già un ratio 0-1)
    itk1_pct_value = 0.0
    if itk1_pct and not pd.isna(itk1_pct):
        itk1_pct_value = float(itk1_pct) * 100  # Converti a percentuale
    
    return non_itk1_pct + itk1_pct_value

def extract_processes_list(processes_str):
    """Estrae lista di (nome_processo, percentuale) dalla stringa."""
    if not processes_str or pd.isna(processes_str):
        return []
    result = []
    parts = str(processes_str).split("|")
    for part in parts:
        part = part.strip()
        match = re.match(r'(.+?)\s+([\d.]+)%', part)
        if match:
            result.append((match.group(1).strip(), float(match.group(2))))
    return result

# === CARICA DATI ===
df_all, dates_available = load_all_snapshots()

if df_all is None or len(dates_available) == 0:
    st.warning("Nessun dato disponibile. Esegui AGGIORNA_DASHBOARD.bat.")
    st.stop()

# === SIDEBAR FILTRI ===
st.sidebar.title("Filtri")

last_refresh = max(dates_available)
st.sidebar.metric("Ultimo Refresh", last_refresh.strftime("%d/%m/%Y"))

# Selettore periodo
date_range = st.sidebar.date_input(
    "Periodo",
    value=(min(dates_available), max(dates_available)),
    min_value=min(dates_available),
    max_value=max(dates_available),
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

# Filtro manager
managers = sorted(df_all["manager_alias"].dropna().unique().tolist())
selected_managers = st.sidebar.multiselect("Manager", managers, default=[])

# Soglia rotazione
soglia_rotazione = st.sidebar.slider("Soglia rotazione critica (%)", 0, 100, 20, 5)


# === FILTRAGGIO DATI ===
df_filtered = df_all[(df_all["snapshot_date"] >= start_date) & (df_all["snapshot_date"] <= end_date)]
if selected_managers:
    df_filtered = df_filtered[df_filtered["manager_alias"].isin(selected_managers)]

# === CALCOLI ===
# Media per persona nel periodo
df_person = df_filtered.groupby("login").agg({
    "RotationPercent": "mean",
    "TotalHours": "mean",
    "DifferentProcesses": "mean",
    "Processes_7d_weighted": "last",
    "manager_alias": "last",
    "Limitazione": "last",
    "RotationSeverity": "last",
    "ITK1_HoursPercent": "mean",
}).reset_index()

# Calcola % NIOSH alto per persona
df_person["PctNioshAlto"] = df_person.apply(calc_niosh_alto_pct, axis=1)

# === TABS ===
tab_main, tab_grafici = st.tabs(["📊 Dati", "📈 Grafici e Andamenti"])

# =====================
# TAB PRINCIPALE
# =====================
with tab_main:
    st.title("Dashboard Rotazione AAs")
    
    # --- KPI ---
    n_totale = len(df_person)
    rotation_media = df_person["RotationPercent"].mean() * 100
    n_sotto_soglia = (df_person["RotationPercent"] * 100 < soglia_rotazione).sum()
    pct_sotto_soglia = (n_sotto_soglia / n_totale * 100) if n_totale > 0 else 0
    n_niosh_alto = (df_person["PctNioshAlto"] > 50).sum()
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Rotazione Media", f"{rotation_media:.1f}%")
    with kpi2:
        st.metric(f"AAs sotto {soglia_rotazione}%", f"{n_sotto_soglia} ({pct_sotto_soglia:.0f}%)")
    with kpi3:
        st.metric("AAs >50% su NIOSH alto", f"{n_niosh_alto}")
    with kpi4:
        st.metric("AAs totali", f"{n_totale}")


    st.divider()
    
    # --- SEZIONE 1: AAs con >50% tempo su processi NIOSH alto ---
    st.subheader("🔴 AAs con >50% del tempo su processi NIOSH > 2")
    df_niosh_alert = df_person[df_person["PctNioshAlto"] > 50].sort_values("PctNioshAlto", ascending=False)
    if len(df_niosh_alert) > 0:
        df_show = df_niosh_alert[["login", "manager_alias", "PctNioshAlto", "RotationPercent", "Processes_7d_weighted"]].copy()
        df_show["RotationPercent"] = (df_show["RotationPercent"] * 100).round(1)
        df_show["PctNioshAlto"] = df_show["PctNioshAlto"].round(1)
        df_show = df_show.rename(columns={
            "login": "Login",
            "manager_alias": "Manager",
            "PctNioshAlto": "% Tempo NIOSH alto",
            "RotationPercent": "Rotazione %",
            "Processes_7d_weighted": "Processi (ultimi 7gg)",
        })
        st.dataframe(df_show, use_container_width=True, hide_index=True)
    else:
        st.success("Nessun AA supera il 50% del tempo su processi NIOSH > 2")
    
    st.divider()
    
    # --- SEZIONE 2: Rotazione % media (filtrabile per manager) ---
    st.subheader("📋 Rotazione % media per AAs")
    df_rotation = df_person[["login", "manager_alias", "RotationPercent", "DifferentProcesses", "PctNioshAlto"]].copy()
    df_rotation["RotationPercent"] = (df_rotation["RotationPercent"] * 100).round(1)
    df_rotation["PctNioshAlto"] = df_rotation["PctNioshAlto"].round(1)
    df_rotation = df_rotation.sort_values("RotationPercent", ascending=True)
    df_rotation = df_rotation.rename(columns={
        "login": "Login",
        "manager_alias": "Manager",
        "RotationPercent": "Rotazione %",
        "DifferentProcesses": "N° Processi",
        "PctNioshAlto": "% NIOSH alto",
    })
    st.dataframe(df_rotation, use_container_width=True, hide_index=True)


    st.divider()
    
    # --- SEZIONE 3: % AAs sotto soglia ---
    st.subheader(f"⚠️ AAs con rotazione < {soglia_rotazione}%")
    df_sotto = df_person[df_person["RotationPercent"] * 100 < soglia_rotazione].sort_values("RotationPercent")
    if len(df_sotto) > 0:
        df_sotto_show = df_sotto[["login", "manager_alias", "RotationPercent", "RotationSeverity", "Limitazione"]].copy()
        df_sotto_show["RotationPercent"] = (df_sotto_show["RotationPercent"] * 100).round(1)
        df_sotto_show["Ha Limitazione"] = df_sotto_show["Limitazione"].apply(
            lambda x: "Sì" if x and str(x) not in ("", "nan", "0") else "No"
        )
        df_sotto_show = df_sotto_show.rename(columns={
            "login": "Login",
            "manager_alias": "Manager",
            "RotationPercent": "Rotazione %",
            "RotationSeverity": "Severità",
        })
        st.dataframe(df_sotto_show[["Login", "Manager", "Rotazione %", "Severità", "Ha Limitazione"]], 
                     use_container_width=True, hide_index=True)
    else:
        st.success(f"Nessun AA sotto la soglia del {soglia_rotazione}%")
    
    st.divider()
    
    # --- SEZIONE 4: Rotation alert per manager (dipartimento) ---
    st.subheader("🏢 Rotation Alert per Manager")
    df_alert_mgr = df_person[df_person["RotationPercent"] * 100 < soglia_rotazione].groupby("manager_alias").agg(
        N_AAs_sotto_soglia=("login", "count"),
        Rotazione_media=("RotationPercent", "mean"),
    ).reset_index()
    df_alert_mgr["Rotazione_media"] = (df_alert_mgr["Rotazione_media"] * 100).round(1)
    # Aggiungi totale AAs per manager
    totale_per_mgr = df_person.groupby("manager_alias")["login"].count().reset_index()
    totale_per_mgr.columns = ["manager_alias", "Totale_AAs"]
    df_alert_mgr = df_alert_mgr.merge(totale_per_mgr, on="manager_alias", how="left")
    df_alert_mgr["% sotto soglia"] = (df_alert_mgr["N_AAs_sotto_soglia"] / df_alert_mgr["Totale_AAs"] * 100).round(0)
    df_alert_mgr = df_alert_mgr.sort_values("N_AAs_sotto_soglia", ascending=False)
    df_alert_mgr = df_alert_mgr.rename(columns={
        "manager_alias": "Manager",
        "N_AAs_sotto_soglia": "AAs sotto soglia",
        "Rotazione_media": "Rotazione media %",
        "Totale_AAs": "Totale AAs",
    })
    st.dataframe(df_alert_mgr[["Manager", "AAs sotto soglia", "Totale AAs", "% sotto soglia", "Rotazione media %"]], 
                 use_container_width=True, hide_index=True)


    st.divider()
    
    # --- SEZIONE 5: Processi top offender ---
    st.subheader("🎯 Processi Top Offender (rotazione peggiore)")
    # Per ogni persona, prendi il processo principale e la sua rotazione
    process_stats = []
    for _, row in df_person.iterrows():
        procs = extract_processes_list(row["Processes_7d_weighted"])
        if procs:
            main_proc = procs[0][0]  # Processo con più ore
            main_pct = procs[0][1]
            process_stats.append({
                "Processo": main_proc,
                "Rotazione": row["RotationPercent"],
                "MainShare": main_pct,
            })
    
    if process_stats:
        df_proc_stats = pd.DataFrame(process_stats)
        # Aggrega per processo: media rotazione di chi lo ha come principale
        df_proc_agg = df_proc_stats.groupby("Processo").agg(
            N_AAs=("Rotazione", "count"),
            Rotazione_media=("Rotazione", "mean"),
            Share_media=("MainShare", "mean"),
        ).reset_index()
        df_proc_agg["Rotazione_media"] = (df_proc_agg["Rotazione_media"] * 100).round(1)
        df_proc_agg["Share_media"] = df_proc_agg["Share_media"].round(1)
        # Filtra solo processi con almeno 3 persone
        df_proc_agg = df_proc_agg[df_proc_agg["N_AAs"] >= 3]
        df_proc_agg = df_proc_agg.sort_values("Rotazione_media", ascending=True).head(15)
        df_proc_agg = df_proc_agg.rename(columns={
            "Processo": "Processo Principale",
            "N_AAs": "N° AAs",
            "Rotazione_media": "Rotazione Media %",
            "Share_media": "% Tempo Medio",
        })
        st.dataframe(df_proc_agg, use_container_width=True, hide_index=True)


# =====================
# TAB GRAFICI
# =====================
with tab_grafici:
    st.title("📈 Grafici e Andamenti")
    
    # --- Trend rotazione media nel tempo ---
    st.subheader("Trend Rotazione Media")
    if len(dates_available) > 1:
        # Applica filtro manager anche qui
        df_trend_base = df_all[(df_all["snapshot_date"] >= start_date) & (df_all["snapshot_date"] <= end_date)]
        if selected_managers:
            df_trend_base = df_trend_base[df_trend_base["manager_alias"].isin(selected_managers)]
        
        df_trend = df_trend_base.groupby("snapshot_date").agg({
            "RotationPercent": "mean",
        }).reset_index()
        df_trend["RotationPercent"] = df_trend["RotationPercent"] * 100
        df_trend = df_trend.rename(columns={"snapshot_date": "Data", "RotationPercent": "Rotazione Media %"})
        st.line_chart(df_trend.set_index("Data")["Rotazione Media %"])
    else:
        st.info("Servono almeno 2 giorni di dati per mostrare il trend.")
    
    st.divider()
    
    # --- Trend % AAs sotto soglia ---
    st.subheader(f"Trend % AAs sotto soglia ({soglia_rotazione}%)")
    if len(dates_available) > 1:
        trend_soglia = []
        for date in sorted(df_trend_base["snapshot_date"].unique()):
            df_day = df_trend_base[df_trend_base["snapshot_date"] == date]
            n_tot = len(df_day)
            n_sotto = (df_day["RotationPercent"] * 100 < soglia_rotazione).sum()
            pct = (n_sotto / n_tot * 100) if n_tot > 0 else 0
            trend_soglia.append({"Data": date, f"% AAs sotto {soglia_rotazione}%": pct})
        df_trend_soglia = pd.DataFrame(trend_soglia)
        st.line_chart(df_trend_soglia.set_index("Data"))
    else:
        st.info("Servono almeno 2 giorni di dati.")
    
    st.divider()
    
    # --- Trend % tempo su NIOSH alto ---
    st.subheader("Trend % Tempo Medio su Processi NIOSH > 2")
    if len(dates_available) > 1:
        trend_niosh = []
        for date in sorted(df_trend_base["snapshot_date"].unique()):
            df_day = df_trend_base[df_trend_base["snapshot_date"] == date]
            pct_niosh = df_day.apply(calc_niosh_alto_pct, axis=1).mean()
            trend_niosh.append({"Data": date, "% Tempo NIOSH > 2": pct_niosh})
        df_trend_niosh = pd.DataFrame(trend_niosh)
        st.line_chart(df_trend_niosh.set_index("Data"))
    else:
        st.info("Servono almeno 2 giorni di dati.")
    
    st.divider()
    
    # --- Distribuzione rotazione (istogramma) ---
    st.subheader("Distribuzione Rotazione AAs")
    import numpy as np
    hist_data = (df_person["RotationPercent"] * 100).clip(0, 100)
    bins = list(range(0, 105, 10))
    hist_counts, _ = np.histogram(hist_data, bins=bins)
    df_hist = pd.DataFrame({
        "Fascia Rotazione %": [f"{bins[i]}-{bins[i+1]}%" for i in range(len(bins)-1)],
        "N° AAs": hist_counts,
    })
    st.bar_chart(df_hist.set_index("Fascia Rotazione %"))

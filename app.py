import streamlit as st
import pandas as pd
import os
import glob
import re
import numpy as np
from datetime import datetime, timedelta

# === CONFIGURAZIONE ===
DATA_DIR = "data"

PROCESSI_NIOSH_ALTO_NON_ITK1 = {
    "Cart Handler Stow": "RUNNER STOW (2.05)",
    "Fluid Loader": "SCARICO FLUIDO (2.51)",
    "Water Spider": "WATERSPIDER/RUNNER (2.53)",
}

PROCESSI_NIOSH_ALTO_ITK1 = {
    "pick": "SDC PICK",
    "palletize - case": "SDC PALLETIZE",
    "case transfer in": "SDC STOW",
    "cart/pallet builder": "SDC CART BUILDER",
    "line load injection": "SDC SCARICO FLUIDO",
    "cart handler trans": "SDC RUNNER STOW",
}

st.set_page_config(page_title="Rotazione AAs - Dashboard", layout="wide")

# === FUNZIONI ===
@st.cache_data(ttl=300)
def load_all_snapshots():
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
    processes_str = row.get("Processes_7d_weighted", "")
    itk1_procs_str = row.get("ITK1_Processes_7d", "")
    itk1_pct = row.get("ITK1_HoursPercent", 0)
    
    itk1_procs = set()
    if itk1_procs_str and not pd.isna(itk1_procs_str):
        for part in str(itk1_procs_str).split("|"):
            match = re.match(r'(.+?)\s+[\d.]+%', part.strip())
            if match:
                itk1_procs.add(match.group(1).strip().lower())
    
    non_itk1_pct = 0.0
    if processes_str and not pd.isna(processes_str):
        parts = str(processes_str).split("|")
        for part in parts:
            part = part.strip()
            for target in PROCESSI_NIOSH_ALTO_NON_ITK1.keys():
                if target.lower() in part.lower():
                    if target.lower() not in itk1_procs:
                        match = re.search(r'([\d.]+)%', part)
                        if match:
                            non_itk1_pct += float(match.group(1))
                    break
    
    itk1_niosh_pct = 0.0
    if itk1_procs_str and not pd.isna(itk1_procs_str):
        parts = str(itk1_procs_str).split("|")
        for part in parts:
            part = part.strip()
            match = re.match(r'(.+?)\s+([\d.]+)%', part)
            if match:
                proc_name = match.group(1).strip().lower()
                proc_pct = float(match.group(2))
                if proc_name in PROCESSI_NIOSH_ALTO_ITK1:
                    if itk1_pct and not pd.isna(itk1_pct):
                        itk1_niosh_pct += (proc_pct / 100) * float(itk1_pct) * 100
    
    return non_itk1_pct + itk1_niosh_pct

def format_processes_display(processes_str, itk1_processes_str):
    if not processes_str or pd.isna(processes_str):
        return ""
    itk1_procs = set()
    if itk1_processes_str and not pd.isna(itk1_processes_str):
        for part in str(itk1_processes_str).split("|"):
            match = re.match(r'(.+?)\s+[\d.]+%', part.strip())
            if match:
                itk1_procs.add(match.group(1).strip().lower())
    parts = str(processes_str).split("|")
    new_parts = []
    for part in parts:
        part = part.strip()
        match = re.match(r'(.+?)\s+([\d.]+%)', part)
        if match:
            proc_name = match.group(1).strip()
            pct = match.group(2)
            if proc_name.lower() in itk1_procs:
                if proc_name.lower() in PROCESSI_NIOSH_ALTO_ITK1:
                    proc_name = PROCESSI_NIOSH_ALTO_ITK1[proc_name.lower()]
                else:
                    proc_name = f"SDC {proc_name}"
            new_parts.append(f"{proc_name} {pct}")
        else:
            new_parts.append(part)
    return " | ".join(new_parts)

def extract_processes_list(processes_str):
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

def get_main_process(processes_str):
    if not processes_str or pd.isna(processes_str):
        return ""
    parts = str(processes_str).split("|")
    if parts:
        match = re.match(r'(.+?)\s+[\d.]+%', parts[0].strip())
        if match:
            return match.group(1).strip()
    return ""

def has_limitation(lim):
    return lim is not None and not pd.isna(lim) and str(lim).strip() not in ("", "0", "nan")

# === CARICA DATI ===
df_all, dates_available = load_all_snapshots()

if df_all is None or len(dates_available) == 0:
    st.warning("Nessun dato disponibile. Esegui AGGIORNA_DASHBOARD.bat.")
    st.stop()

# === SIDEBAR FILTRI ===
st.sidebar.title("Filtri")
last_refresh = max(dates_available)
st.sidebar.metric("Ultimo Refresh", last_refresh.strftime("%d/%m/%Y"))

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

managers = sorted(df_all["manager_alias"].dropna().unique().tolist())
selected_managers = st.sidebar.multiselect("Manager", managers, default=[])
soglia_rotazione = st.sidebar.slider("Soglia rotazione critica (%)", 0, 100, 20, 5)

# === TABS ===
tab_main, tab_grafici, tab_search, tab_settings = st.tabs(["📊 Dati", "📈 Grafici e Andamenti", "🔍 Cerca AA", "⚙️ Impostazioni"])

# === TAB IMPOSTAZIONI ===
with tab_settings:
    st.title("⚙️ Parametri avanzati")
    st.caption("Attiva e configura filtri aggiuntivi. Le modifiche si applicano immediatamente a tutte le tab.")
    
    st.divider()
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        use_hour_filter = st.checkbox("Filtra per ore minime lavorate", value=False)
        min_hours = st.number_input("Ore minime", min_value=0, max_value=40, value=16, step=2, disabled=not use_hour_filter)
    
    with col_s2:
        use_weighted_avg = st.checkbox("Media pesata per ore lavorate", value=False,
                                       help="Chi lavora più ore pesa di più nel calcolo della rotazione media")
    
    st.divider()
    
    use_limitation_filter = st.checkbox("Escludi AAs con limitazione medica e rotazione sotto soglia", value=False,
                                        help="Esclude dal conteggio chi non ruota per motivi medici")
    limitation_threshold = st.number_input("Soglia rotazione per esclusione (%)", min_value=0, max_value=50, value=10, step=5, disabled=not use_limitation_filter)

# === FILTRAGGIO DATI ===
df_filtered = df_all[(df_all["snapshot_date"] >= start_date) & (df_all["snapshot_date"] <= end_date)]
if selected_managers:
    df_filtered = df_filtered[df_filtered["manager_alias"].isin(selected_managers)]

# Ultimo giorno per alert
latest_date = df_filtered["snapshot_date"].max()
df_latest = df_filtered[df_filtered["snapshot_date"] == latest_date]

df_person = df_latest.copy()

# Applica filtri avanzati se attivati
if use_hour_filter:
    df_person = df_person[df_person["TotalHours"] >= min_hours]

if use_limitation_filter:
    df_person["HasLimitation"] = df_person["Limitazione"].apply(has_limitation)
    df_person = df_person[~((df_person["RotationPercent"] * 100 < limitation_threshold) & (df_person["HasLimitation"]))].copy()

df_person["PctNioshAlto"] = df_person.apply(calc_niosh_alto_pct, axis=1)
df_person["MainProcess"] = df_person["Processes_7d_weighted"].apply(get_main_process)

process_counts = df_person["MainProcess"].value_counts()
# Soglia dinamica: 30 senza filtro manager, 3 con filtro
ops_threshold = 3 if selected_managers else 30
processi_operations = set(process_counts[process_counts >= ops_threshold].index)
df_person["IsOperations"] = df_person["MainProcess"].isin(processi_operations)

df_person["Processi_Display"] = df_person.apply(
    lambda row: format_processes_display(row["Processes_7d_weighted"], row["ITK1_Processes_7d"]), axis=1
)

# === TAB DATI ===
with tab_main:
    st.title("Rotazione Media - MXP5")
    st.caption(f"Dati riferiti al: **{latest_date.strftime('%d/%m/%Y')}**")
    
    # KPI
    n_totale = len(df_person)
    if use_weighted_avg and df_person["TotalHours"].sum() > 0:
        rotation_media = (df_person["RotationPercent"] * df_person["TotalHours"]).sum() / df_person["TotalHours"].sum() * 100
    else:
        rotation_media = df_person["RotationPercent"].mean() * 100 if n_totale > 0 else 0
    n_sotto_soglia = (df_person["RotationPercent"] * 100 < soglia_rotazione).sum()
    pct_sotto_soglia = (n_sotto_soglia / n_totale * 100) if n_totale > 0 else 0
    n_niosh_alto = (df_person["PctNioshAlto"] > 50).sum()
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Rotazione Media", f"{rotation_media:.1f}%")
    with kpi2:
        st.metric(f"AAs con rotazione < {soglia_rotazione}%", f"{n_sotto_soglia} ({pct_sotto_soglia:.0f}%)")
    with kpi3:
        st.metric("AAs con >50% ore su processi NIOSH >2", f"{n_niosh_alto}")
    with kpi4:
        st.metric("AAs attivi (ultimi 7gg)", f"{n_totale}")
    
    st.divider()
    
    # SEZIONE 1: NIOSH alert
    st.subheader("🔴 AAs con esposizione >50% a processi NIOSH >2")
    df_niosh_alert = df_person[df_person["PctNioshAlto"] > 50].sort_values("PctNioshAlto", ascending=False)
    if len(df_niosh_alert) > 0:
        df_show = df_niosh_alert[["login", "manager_alias", "PctNioshAlto", "RotationPercent", "Processi_Display"]].copy()
        df_show["RotationPercent"] = (df_show["RotationPercent"] * 100).round(1)
        df_show["PctNioshAlto"] = df_show["PctNioshAlto"].round(1)
        df_show = df_show.rename(columns={
            "login": "Login", "manager_alias": "Manager",
            "PctNioshAlto": "% Tempo NIOSH >2", "RotationPercent": "Rotazione %",
            "Processi_Display": "Processi (ultimi 7gg)",
        })
        st.dataframe(df_show, use_container_width=True, hide_index=True)
    else:
        st.success("Nessun AA supera il 50% del tempo su processi NIOSH > 2")
    
    st.divider()
    
    # SEZIONE 2: Dettaglio rotazione
    st.subheader("📋 Dettaglio rotazione per ogni AA")
    df_rotation = df_person[["login", "manager_alias", "RotationPercent", "DifferentProcesses", "PctNioshAlto"]].copy()
    df_rotation["RotationPercent"] = (df_rotation["RotationPercent"] * 100).round(1)
    df_rotation["PctNioshAlto"] = df_rotation["PctNioshAlto"].round(1)
    df_rotation = df_rotation.sort_values("RotationPercent", ascending=True)
    df_rotation = df_rotation.rename(columns={
        "login": "Login", "manager_alias": "Manager",
        "RotationPercent": "Rotazione %", "DifferentProcesses": "N° Processi",
        "PctNioshAlto": "% NIOSH >2",
    })
    st.dataframe(df_rotation, use_container_width=True, hide_index=True)

    st.divider()
    
    # SEZIONE 3: AAs sotto soglia
    st.subheader(f"⚠️ AAs con rotazione < {soglia_rotazione}%")
    df_sotto = df_person[(df_person["RotationPercent"] * 100 < soglia_rotazione) & (df_person["IsOperations"])].sort_values("RotationPercent")
    if len(df_sotto) > 0:
        df_sotto_show = df_sotto[["login", "manager_alias", "RotationPercent", "MainProcessShare", "MainProcess", "Limitazione"]].copy()
        df_sotto_show["RotationPercent"] = (df_sotto_show["RotationPercent"] * 100).round(1)
        df_sotto_show["MainProcessShare"] = (df_sotto_show["MainProcessShare"] * 100).round(1)
        df_sotto_show["Ha Limitazione"] = df_sotto_show["Limitazione"].apply(
            lambda x: "Sì" if x and str(x) not in ("", "nan", "0") else "No"
        )
        df_sotto_show = df_sotto_show.rename(columns={
            "login": "Login", "manager_alias": "Manager",
            "RotationPercent": "Rotazione %", "MainProcess": "Processo Principale",
            "MainProcessShare": "% Tempo su Principale",
        })
        st.dataframe(df_sotto_show[["Login", "Manager", "Rotazione %", "Processo Principale", "% Tempo su Principale", "Ha Limitazione"]], 
                     use_container_width=True, hide_index=True)
    else:
        st.success(f"Nessun AA sotto la soglia del {soglia_rotazione}%")
    
    st.divider()
    
    # SEZIONE 4: Alert per manager
    st.subheader("🏢 Situazione per Manager: quanti AAs non ruotano abbastanza")
    df_alert_mgr = df_person[df_person["RotationPercent"] * 100 < soglia_rotazione].groupby("manager_alias").agg(
        N_AAs_sotto_soglia=("login", "count"),
        Rotazione_media=("RotationPercent", "mean"),
    ).reset_index()
    df_alert_mgr["Rotazione_media"] = (df_alert_mgr["Rotazione_media"] * 100).round(1)
    totale_per_mgr = df_person.groupby("manager_alias")["login"].count().reset_index()
    totale_per_mgr.columns = ["manager_alias", "Totale_AAs"]
    df_alert_mgr = df_alert_mgr.merge(totale_per_mgr, on="manager_alias", how="left")
    df_alert_mgr["% sotto soglia"] = (df_alert_mgr["N_AAs_sotto_soglia"] / df_alert_mgr["Totale_AAs"] * 100).round(0)
    df_alert_mgr = df_alert_mgr.sort_values("N_AAs_sotto_soglia", ascending=False)
    df_alert_mgr = df_alert_mgr.rename(columns={
        "manager_alias": "Manager", "N_AAs_sotto_soglia": "AAs sotto soglia",
        "Rotazione_media": "Rotazione media %", "Totale_AAs": "Totale AAs",
    })
    st.dataframe(df_alert_mgr[["Manager", "AAs sotto soglia", "Totale AAs", "% sotto soglia", "Rotazione media %"]], 
                 use_container_width=True, hide_index=True)
    
    st.divider()
    
    # SEZIONE 5: Processi stagnazione
    st.subheader("🎯 Processi con più stagnazione")
    process_stats = []
    for _, row in df_person.iterrows():
        procs = extract_processes_list(row["Processes_7d_weighted"])
        if procs:
            main_proc = procs[0][0]
            main_pct = procs[0][1]
            process_stats.append({"Processo": main_proc, "Rotazione": row["RotationPercent"], "MainShare": main_pct})
    
    if process_stats:
        df_proc_stats = pd.DataFrame(process_stats)
        df_proc_agg = df_proc_stats.groupby("Processo").agg(
            N_AAs=("Rotazione", "count"), Rotazione_media=("Rotazione", "mean"), Share_media=("MainShare", "mean"),
        ).reset_index()
        df_proc_agg["Rotazione_media"] = (df_proc_agg["Rotazione_media"] * 100).round(1)
        df_proc_agg["Share_media"] = df_proc_agg["Share_media"].round(1)
        # Soglia dinamica: 30 senza filtro manager, 3 con filtro
        min_aas = 3 if selected_managers else 30
        df_proc_agg = df_proc_agg[df_proc_agg["N_AAs"] >= min_aas]
        df_proc_agg = df_proc_agg.sort_values("Rotazione_media", ascending=True).head(15)
        df_proc_agg = df_proc_agg.rename(columns={
            "Processo": "Processo Principale", "N_AAs": "N° AAs",
            "Rotazione_media": "Rotazione Media %", "Share_media": "% Tempo Medio",
        })
        st.dataframe(df_proc_agg, use_container_width=True, hide_index=True)

# === TAB GRAFICI ===
with tab_grafici:
    st.title("📈 Andamento nel tempo")
    
    # Prepara dati trend con stessi filtri
    df_trend_base = df_all[(df_all["snapshot_date"] >= start_date) & (df_all["snapshot_date"] <= end_date)]
    if selected_managers:
        df_trend_base = df_trend_base[df_trend_base["manager_alias"].isin(selected_managers)]
    if use_hour_filter:
        df_trend_base = df_trend_base[df_trend_base["TotalHours"] >= min_hours]
    if use_limitation_filter:
        df_trend_base["_has_lim"] = df_trend_base["Limitazione"].apply(has_limitation)
        df_trend_base = df_trend_base[~((df_trend_base["RotationPercent"] * 100 < limitation_threshold) & (df_trend_base["_has_lim"]))]
    
    st.subheader("Rotazione media giornaliera (%)")
    if len(dates_available) > 1:
        trend_data = []
        for date in sorted(df_trend_base["snapshot_date"].unique()):
            df_day = df_trend_base[df_trend_base["snapshot_date"] == date]
            if use_weighted_avg and df_day["TotalHours"].sum() > 0:
                weighted_rot = (df_day["RotationPercent"] * df_day["TotalHours"]).sum() / df_day["TotalHours"].sum() * 100
            else:
                weighted_rot = df_day["RotationPercent"].mean() * 100 if len(df_day) > 0 else 0
            trend_data.append({"Data": date, "Rotazione media (%)": weighted_rot})
        df_trend = pd.DataFrame(trend_data).set_index("Data")
        df_trend["Trend"] = df_trend["Rotazione media (%)"].expanding().mean()
        st.line_chart(df_trend)
    else:
        st.info("Servono almeno 2 giorni di dati per mostrare il trend.")
    
    st.divider()
    
    st.subheader(f"% di AAs con rotazione inferiore al {soglia_rotazione}% — andamento giornaliero")
    if len(dates_available) > 1:
        trend_soglia = []
        for date in sorted(df_trend_base["snapshot_date"].unique()):
            df_day = df_trend_base[df_trend_base["snapshot_date"] == date]
            n_tot = len(df_day)
            n_sotto = (df_day["RotationPercent"] * 100 < soglia_rotazione).sum()
            pct = (n_sotto / n_tot * 100) if n_tot > 0 else 0
            trend_soglia.append({"Data": date, "% sul totale AAs": pct})
        df_trend_soglia = pd.DataFrame(trend_soglia).set_index("Data")
        df_trend_soglia["Trend"] = df_trend_soglia["% sul totale AAs"].expanding().mean()
        st.line_chart(df_trend_soglia)
    else:
        st.info("Servono almeno 2 giorni di dati.")
    
    st.divider()
    
    st.subheader("% media del turno spesa su processi NIOSH >2 — andamento giornaliero")
    if len(dates_available) > 1:
        trend_niosh = []
        for date in sorted(df_trend_base["snapshot_date"].unique()):
            df_day = df_trend_base[df_trend_base["snapshot_date"] == date]
            pct_niosh = df_day.apply(calc_niosh_alto_pct, axis=1).mean()
            trend_niosh.append({"Data": date, "% del turno su NIOSH >2": pct_niosh})
        df_trend_niosh = pd.DataFrame(trend_niosh).set_index("Data")
        df_trend_niosh["Trend"] = df_trend_niosh["% del turno su NIOSH >2"].expanding().mean()
        st.line_chart(df_trend_niosh)
    else:
        st.info("Servono almeno 2 giorni di dati.")
    
    st.divider()
    
    st.subheader("Distribuzione della rotazione — numero di AAs per fascia (%)")
    hist_data = (df_person["RotationPercent"] * 100).clip(0, 100)
    bins = list(range(0, 105, 10))
    hist_counts, _ = np.histogram(hist_data, bins=bins)
    df_hist = pd.DataFrame({
        "Fascia rotazione (%)": [f"{bins[i]}-{bins[i+1]}%" for i in range(len(bins)-1)],
        "Numero AAs": hist_counts,
    })
    st.bar_chart(df_hist.set_index("Fascia rotazione (%)"))

# === TAB CERCA AA ===
with tab_search:
    st.title("🔍 Cerca Associate")
    
    # Selectbox con autofill (lista di tutti i login nel periodo)
    all_logins = sorted(df_filtered["login"].dropna().unique().tolist())
    search_login = st.selectbox("Seleziona login AA", [""] + all_logins, index=0)
    
    if search_login:
        # Dati nel periodo selezionato per questo AA
        df_search = df_filtered[df_filtered["login"] == search_login]
        
        if len(df_search) == 0:
            st.warning(f"Login '{search_login}' non trovato nel periodo selezionato.")
        else:
            # Media sul periodo
            avg_rotation = df_search["RotationPercent"].mean() * 100
            avg_hours = df_search["TotalHours"].mean()
            avg_procs = df_search["DifferentProcesses"].mean()
            manager = df_search["manager_alias"].iloc[-1]
            lim = df_search["Limitazione"].iloc[-1]
            n_snapshots = len(df_search)
            
            st.subheader(f"📋 {search_login}")
            st.caption(f"Media su {n_snapshots} giorni nel periodo selezionato")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Manager", manager)
            with col2:
                st.metric("Rotazione media", f"{avg_rotation:.1f}%")
            
            col4, col5 = st.columns(2)
            with col4:
                st.metric("N° Processi diversi (media)", f"{avg_procs:.1f}")
            with col5:
                has_lim = "Sì" if lim and not pd.isna(lim) and str(lim).strip() not in ("", "0", "nan") else "No"
                st.metric("Limitazione medica", has_lim)
            
            if has_lim == "Sì":
                st.info(f"**Limitazione:** {lim}")
            
            st.divider()
            
            # Distribuzione processi media nel periodo
            st.subheader("Distribuzione processi — media nel periodo")
            
            # Accumula processi da tutti gli snapshot
            from collections import defaultdict
            proc_totals = defaultdict(list)
            for _, row in df_search.iterrows():
                procs = extract_processes_list(row["Processes_7d_weighted"])
                itk1_procs_set = set()
                if row["ITK1_Processes_7d"] and not pd.isna(row["ITK1_Processes_7d"]):
                    for part in str(row["ITK1_Processes_7d"]).split("|"):
                        m = re.match(r'(.+?)\s+[\d.]+%', part.strip())
                        if m:
                            itk1_procs_set.add(m.group(1).strip().lower())
                
                for proc_name, pct in procs:
                    display_name = proc_name
                    if proc_name.lower() in itk1_procs_set:
                        if proc_name.lower() in PROCESSI_NIOSH_ALTO_ITK1:
                            display_name = PROCESSI_NIOSH_ALTO_ITK1[proc_name.lower()]
                        else:
                            display_name = f"SDC {proc_name}"
                    proc_totals[display_name].append(pct)
            
            # Calcola media per processo
            proc_data = [{"Processo": name, "% Tempo (media)": round(sum(vals)/len(vals), 1)} 
                         for name, vals in proc_totals.items()]
            proc_data.sort(key=lambda x: x["% Tempo (media)"], reverse=True)
            
            if proc_data:
                df_procs = pd.DataFrame(proc_data)
                st.dataframe(df_procs, use_container_width=True, hide_index=True)
                st.bar_chart(df_procs.set_index("Processo"))
            
            # Trend rotazione nel periodo
            if len(df_search) > 1:
                st.divider()
                st.subheader("Andamento rotazione nel periodo")
                df_trend_aa = df_search[["snapshot_date", "RotationPercent"]].copy()
                df_trend_aa["RotationPercent"] = df_trend_aa["RotationPercent"] * 100
                df_trend_aa = df_trend_aa.rename(columns={"snapshot_date": "Data", "RotationPercent": "Rotazione (%)"})
                st.line_chart(df_trend_aa.set_index("Data")["Rotazione (%)"])

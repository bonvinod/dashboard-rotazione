with open(r'c:\Users\bonvinod\Documents\BOARD NUOVA\dashboard\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    ('st.title("Dashboard Rotazione AAs")', 'st.title("Rotazione Processi - Outbound")'),
    ('st.subheader("\U0001f534 AAs con >50% del tempo su processi NIOSH > 2")', 'st.subheader("\U0001f534 Chi passa pi\u00f9 del 50% del turno su processi pesanti (NIOSH >2)")'),
    ('st.subheader("\U0001f4cb Rotazione % media per AAs")', 'st.subheader("\U0001f4cb Dettaglio rotazione per ogni AA")'),
    ('st.subheader("\U0001f3e2 Rotation Alert per Manager")', 'st.subheader("\U0001f3e2 Situazione per Manager: quanti AAs non ruotano abbastanza")'),
    ('st.subheader("\U0001f3af Processi Top Offender (rotazione peggiore)")', 'st.subheader("\U0001f3af Processi con la peggior rotazione media")'),
    ('st.title("\U0001f4c8 Grafici e Andamenti")', 'st.title("\U0001f4c8 Andamento nel tempo")'),
    ('st.subheader("Trend Rotazione Media")', 'st.subheader("Rotazione media giornaliera")'),
    ('st.subheader("Trend % Tempo Medio su Processi NIOSH > 2")', 'st.subheader("Quanto tempo in media si passa su processi pesanti (NIOSH >2)")'),
    ('st.subheader("Distribuzione Rotazione AAs")', 'st.subheader("Come si distribuisce la rotazione tra gli AAs")'),
]

for old, new in replacements:
    content = content.replace(old, new)

with open(r'c:\Users\bonvinod\Documents\BOARD NUOVA\dashboard\app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Titoli aggiornati!")

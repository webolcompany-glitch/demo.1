import streamlit as st
import pandas as pd
import os
import smtplib
import math
from email.mime.text import MIMEText

st.set_page_config(page_title="Fuel SaaS", layout="wide")

# =========================
# 🏢 AZIENDA
# =========================
azienda = st.query_params.get("azienda", "demo")
if isinstance(azienda, list):
    azienda = azienda[0]

FILE = f"clienti_{azienda}.csv"

st.markdown(f"## 🏢 Azienda: {azienda.upper()}")

# =========================
# 📧 EMAIL
# =========================
EMAIL_MITTENTE = "webolcompany@gmail.com"
PASSWORD_APP = "YOUR_APP_PASSWORD"

def invia_email(destinatario, prezzo):
    try:
        msg = MIMEText(f"Buongiorno,\n\nIl prezzo di oggi è {prezzo:.3f} €/L\n\nGrazie")
        msg["Subject"] = "Prezzo carburante"
        msg["From"] = EMAIL_MITTENTE
        msg["To"] = destinatario

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_MITTENTE, PASSWORD_APP)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        st.error(f"Errore email: {e}")

# =========================
# 🔒 3 DECIMALI NO ROUND
# =========================
def trim_3_decimals(x):
    if x is None or pd.isna(x):
        return None
    return math.floor(float(x) * 1000) / 1000

# =========================
# 🇮🇹 FORMAT EURO
# =========================
def format_euro(x):
    if x is None or pd.isna(x):
        return "0,000"
    return f"{trim_3_decimals(x):.3f}".replace(".", ",")

# =========================
# 💾 DATA
# =========================
def load_data():
    if os.path.exists(FILE):
        df = pd.read_csv(FILE)

        if "UltimoPrezzo" not in df.columns:
            df["UltimoPrezzo"] = None

        # ✅ FIX TIPI (FONDAMENTALE)
        df["Margine"] = pd.to_numeric(df["Margine"], errors="coerce")
        df["Trasporto"] = pd.to_numeric(df["Trasporto"], errors="coerce")
        df["UltimoPrezzo"] = pd.to_numeric(df["UltimoPrezzo"], errors="coerce")

        return df

    return pd.DataFrame(columns=[
        "ID","Nome","PIVA","Telefono","Email",
        "Margine","Trasporto","UltimoPrezzo"
    ])

def save_data(df):
    df.to_csv(FILE, index=False)

# =========================
# 🔍 SEARCH SAFE
# =========================
def filtra_clienti(df, search):
    if not search:
        return df

    return df[
        df["Nome"].astype(str).str.contains(search, case=False, na=False) |
        df["PIVA"].astype(str).str.contains(search, case=False, na=False) |
        df["Telefono"].astype(str).str.contains(search, case=False, na=False)
    ]

# =========================
# INIT
# =========================
if "clienti" not in st.session_state:
    st.session_state.clienti = load_data()

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

if "prezzo_base" not in st.session_state:
    st.session_state.prezzo_base = 1.000

df = st.session_state.clienti

# =========================
# NAV
# =========================
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"

with c2:
    if st.button("👤 Clienti", use_container_width=True):
        st.session_state.page = "clienti"

with c3:
    if st.button("➕ Nuovo", use_container_width=True):
        st.session_state.page = "cliente"

st.divider()

# =========================================================
# ➕ CLIENTE
# =========================================================
if st.session_state.page == "cliente":

    st.markdown("## ➕ Cliente")

    editing = st.session_state.edit_id is not None

    if editing:
        c = df[df["ID"] == st.session_state.edit_id].iloc[0]
    else:
        c = {"Nome":"","PIVA":"","Telefono":"","Email":"","Margine":0.0,"Trasporto":0.0}

    nome = st.text_input("Nome", value=c["Nome"])
    piva = st.text_input("P.IVA", value=c["PIVA"])
    tel = st.text_input("Telefono", value=c["Telefono"])
    email = st.text_input("Email", value=c["Email"])

    margine = st.number_input("Margine", value=float(c["Margine"]), step=0.001, format="%.3f")
    trasporto = st.number_input("Trasporto", value=float(c["Trasporto"]), step=0.001, format="%.3f")

    if st.button("💾 Salva"):

        if editing:
            idx = st.session_state.clienti["ID"] == st.session_state.edit_id

            # ✅ UPDATE SICURO (NO ERRORE)
            st.session_state.clienti.loc[idx, "Nome"] = nome
            st.session_state.clienti.loc[idx, "PIVA"] = piva
            st.session_state.clienti.loc[idx, "Telefono"] = tel
            st.session_state.clienti.loc[idx, "Email"] = email
            st.session_state.clienti.loc[idx, "Margine"] = float(margine)
            st.session_state.clienti.loc[idx, "Trasporto"] = float(trasporto)

            st.session_state.edit_id = None

        else:
            new_id = 1 if df.empty else int(df["ID"].max()) + 1

            new = pd.DataFrame([{
                "ID": new_id,
                "Nome": nome,
                "PIVA": piva,
                "Telefono": tel,
                "Email": email,
                "Margine": float(margine),
                "Trasporto": float(trasporto),
                "UltimoPrezzo": None
            }])

            st.session_state.clienti = pd.concat([df, new], ignore_index=True)

        save_data(st.session_state.clienti)
        st.success("Salvato")
        st.session_state.page = "clienti"
        st.rerun()

# =========================================================
# 👤 CLIENTI
# =========================================================
elif st.session_state.page == "clienti":

    st.markdown("## 👤 Clienti attivi")

    for _, c in df.iterrows():
        st.write(c["Nome"])

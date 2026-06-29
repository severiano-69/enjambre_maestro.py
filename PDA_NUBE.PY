import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="PDA VENDING PRO", layout="centered")
st.title("📟 CONTROL DE RECAUDACIÓN")

# --- MEMORIA TEMPORAL ---
if 'historico' not in st.session_state:
    st.session_state.historico = []

# --- FORMULARIO (ENTRADA DE DATOS) ---
with st.sidebar:
    st.header("🚚 REGISTRO DE CALLE")
    id_m = st.number_input("Nº Máquina", min_value=1, max_value=100, step=1)
    eur = st.number_input("Dinero (€)", min_value=0.0, step=0.01)

    if st.button("ENVIAR A CASA 🚀"):
        ahora = datetime.now()
        dato = {
            "Fecha": ahora.strftime("%d/%m %H:%M"),
            "Maquina": f"M-{id_m}",
            "Euros": eur
        }
        st.session_state.historico.append(dato)
        st.success(f"✅ ¡Datos enviados!")

# --- MONITOR (VISTA DE RECUENTO) ---
st.subheader("🏠 Recuento en Tiempo Real")
if st.session_state.historico:
    df = pd.DataFrame(st.session_state.historico)

    # Mostrar tabla
    st.table(df.tail(10))

    st.divider()

    # Cuadros de resumen
    col1, col2 = st.columns(2)
    total_acumulado = df["Euros"].sum()
    col1.metric("TOTAL RECAUDADO", f"{total_acumulado:.2f} €")
    col2.metric("Nº OPERACIONES", len(df))
else:
    st.info("Esperando que alguien envíe datos desde la calle...")

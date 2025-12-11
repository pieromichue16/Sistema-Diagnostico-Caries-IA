import streamlit as st
import numpy as np
import cv2
from PIL import Image
import time
import os
from datetime import datetime

# --- IMPORTAMOS NUESTROS MÓDULOS ---
import database as db
import logic

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Dental Hada - IA", layout="wide", page_icon="🦷", initial_sidebar_state="expanded")

CARPETA_HISTORIAL = "historial_imgs"
if not os.path.exists(CARPETA_HISTORIAL): os.makedirs(CARPETA_HISTORIAL)

# Inicializar BD al arrancar
db.init_db()

# --- CARGAR MODELO (Usando logic.py) ---
@st.cache_resource
def get_model():
    return logic.cargar_modelo_ia()

model = get_model()

# --- ESTILOS CSS "DENTAL HADA" ---
st.markdown("""
<style>
    /* Fondo Claro */
    .stApp { background-color: #F4F6F9; color: #333333; }
    
    /* Barra Lateral Morada */
    section[data-testid="stSidebar"] { background-color: #6A4C93; }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span { color: white !important; }
    
    /* Tarjetas Métricas */
    div[data-testid="metric-container"] { background-color: #FFFFFF; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 10px; }
    div[data-testid="metric-container"] label { color: #6A4C93 !important; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #333 !important; }

    /* Botones Morados */
    div.stButton > button:first-child { background-color: #6A4C93; color: white; border: none; padding: 12px; border-radius: 5px; }
    div.stButton > button:first-child:hover { background-color: #553C7B; color: white; }

    /* Inputs y Textos */
    h1, h2 { color: #6A4C93 !important; }
    [data-testid='stFileUploader'] { background-color: #FFFFFF; border: 2px dashed #6A4C93; border-radius: 10px; padding: 20px; }
    [data-testid='stFileUploader'] section > div > div > span { display: none; }
    [data-testid='stFileUploader'] section > div > div::after { content: "📂 Seleccionar Radiografía"; color: #6A4C93; display: block; text-align: center; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- ESTADO DE SESIÓN ---
if 'usuario_id' not in st.session_state: st.session_state.usuario_id = None
if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
if 'analisis_listo' not in st.session_state: st.session_state.analisis_listo = False
if 'temp_ia_count' not in st.session_state: st.session_state.temp_ia_count = 0
if 'temp_contours' not in st.session_state: st.session_state.temp_contours = []
if 'hora_inicio' not in st.session_state: st.session_state.hora_inicio = 0.0

# ================= VISTA: LOGIN =================
if st.session_state.usuario_id is None:
    _, c2, _ = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container():
            st.markdown("""<div style='background-color: white; padding: 40px; border-radius: 15px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); text-align: center;'>
                <h1 style='color: #6A4C93; margin:0;'>🔐 Iniciar Sesión</h1>
                <p style='color: gray;'>Módulo IA - Dental Hada</p></div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            with st.form("login"):
                u = st.text_input("Usuario")
                p = st.text_input("Contraseña", type="password")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("Entrar al Sistema"):
                    user = db.verificar_login(u, p)
                    if user:
                        st.session_state.usuario_id = user[0]
                        st.session_state.usuario_nombre = user[1]
                        st.rerun()
                    else: st.error("Acceso denegado")
            st.info("Demo: admin / admin123")

# ================= VISTA: SISTEMA =================
else:
    # BARRA LATERAL
    with st.sidebar:
        st.title("👨‍⚕️ Dental Hada")
        st.write(f"Doctor: **{st.session_state.usuario_nombre}**")
        if st.button("Cerrar Sesión"):
            st.session_state.usuario_id = None
            st.rerun()
        st.markdown("---")
        
        # INDICADORES (Llamando a DB)
        st.subheader("📊 Indicadores Globales")
        df_m = db.obtener_metricas_globales()
        if not df_m.empty:
            st.metric("✅ Precisión Media", f"{df_m['precision'].mean():.1f}%")
            st.metric("❌ Errores Totales", f"{df_m['errores'].sum()}")
            st.metric("⏱️ Tiempo Promedio", f"{df_m['tiempo_analisis_ms'].mean():.2f} s")
            st.caption(f"Total Diagnósticos: {len(df_m)}")
        else: st.info("Sin datos.")

    st.title("Sistema de Diagnóstico de Caries")
    
    if model is None:
        st.error(f"Error: Falta {logic.MODELO_PATH}"); st.stop()

    # 1. GESTIÓN PACIENTES
    st.subheader("1. Gestión de Paciente")
    df_p = db.obtener_pacientes()
    t1, t2 = st.tabs(["📂 Buscar", "➕ Nuevo"])
    pid = None
    
    with t1:
        if not df_p.empty:
            dic = dict(zip(df_p['nombre_completo'], df_p['id_paciente']))
            sel = st.selectbox("Seleccionar:", df_p['nombre_completo'])
            pid = dic[sel]
            
            with st.expander(f"📷 Historial Visual de {sel}"):
                hist = db.obtener_historial_visual(pid)
                if not hist.empty:
                    for _, row in hist.iterrows():
                        st.markdown("---")
                        ch1, ch2 = st.columns([1,4])
                        with ch1:
                            if os.path.exists(row['ruta_archivo']): st.image(row['ruta_archivo'], width=150)
                        with ch2:
                            st.write(f"📅 **{row['fecha_toma']}**")
                            c_m1, c_m2, c_m3 = st.columns(3)
                            c_m1.metric("Errores", row['errores'])
                            c_m2.metric("Tiempo", f"{row['tiempo_analisis_ms']}s")
                            c_m3.metric("Precisión", f"{row['precision']:.1f}%")
                else: st.info("Sin historial.")
        else: st.warning("Sin pacientes.")

    with t2:
        c_n1, c_n2 = st.columns(2)
        nn, na = c_n1.text_input("Nombres"), c_n2.text_input("Apellidos")
        ni = st.text_input("DNI")
        if st.button("Guardar Paciente"):
            if nn and na:
                db.registrar_paciente(nn, na, ni)
                st.success("Guardado"); time.sleep(1); st.rerun()

    # 2. ANÁLISIS
    if pid:
        st.markdown("---")
        st.subheader("2. Análisis Radiográfico")
        uf = st.file_uploader("", type=["jpg","png"], label_visibility="collapsed", key=f"up_{st.session_state.uploader_key}")
        
        if uf:
            img = Image.open(uf).convert('RGB')
            arr = np.array(img)
            c_i1, c_i2 = st.columns(2)
            with c_i1: st.image(img, caption="Original", width=450)
            
            if not st.session_state.analisis_listo:
                if st.button("⚡ Analizar con IA"):
                    with st.spinner("Procesando..."):
                        st.session_state.hora_inicio = time.time()
                        
                        # LLAMADA A LOGIC.PY
                        cnts, num = logic.procesar_y_predecir(model, arr)
                        
                        st.session_state.temp_contours = cnts
                        st.session_state.temp_ia_count = num
                        st.session_state.analisis_listo = True
                        st.rerun()
            
            if st.session_state.analisis_listo:
                res = arr.copy()
                cv2.drawContours(res, st.session_state.temp_contours, -1, (255,0,0), 4)
                with c_i2: 
                    st.image(res, caption="Resultado IA", width=450)
                    st.info(f"Hallazgos: {st.session_state.temp_ia_count} lesiones")
                
                st.markdown("---")
                st.subheader("3. Validar y Guardar")
                with st.form("val"):
                    real = st.number_input("Validación Real (Experto)", min_value=0, value=st.session_state.temp_ia_count)
                    if st.form_submit_button("✅ Guardar en Historial"):
                        tt = round(time.time() - st.session_state.hora_inicio, 2)
                        ia = st.session_state.temp_ia_count
                        err = abs(ia - real)
                        prec = (min(ia, real)/real*100) if real > 0 else (100 if ia==0 else 0)
                        
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        ruta = os.path.join(CARPETA_HISTORIAL, f"{pid}_{ts}.jpg")
                        img.save(ruta)
                        
                        # LLAMADA A DATABASE.PY
                        db.guardar_analisis_completo(pid, st.session_state.usuario_id, ruta, tt, ia, real, err, prec)
                        
                        st.session_state.analisis_listo = False
                        st.session_state.uploader_key += 1
                        st.success("Guardado Exitosamente"); time.sleep(1.5); st.rerun()
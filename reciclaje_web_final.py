import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import csv
import os
from datetime import datetime
from io import BytesIO

# --- LIBRERÍAS DE LA NUBE ---
import firebase_admin
from firebase_admin import credentials, db

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Configuración de la Web App
st.set_page_config(page_title="Reciclaje Pro", page_icon="♻️", layout="centered", initial_sidebar_state="collapsed")

# --- ESTILOS VISUALES Y ANTI-PARPADEO ---
st.markdown("""
<style>
    :root, .stApp { color-scheme: light !important; background-color: #f1f5f9 !important; color: #0f172a !important; }
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .block-container { padding-top: 1rem !important; padding-bottom: 2.5rem !important; max-width: 650px !important; }
    h1, h2, h3, h4, h5, h6, [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span, [data-testid="stMarkdownContainer"] li, [data-testid="stWidgetLabel"] p, label { color: #0f172a !important; }
    
    /* ANTI-PARPADEO EXTREMO */
    div[data-testid="stVerticalBlock"] { opacity: 1 !important; transition: none !important; filter: none !important; }
    div[data-testid="stVerticalBlock"] > div { opacity: 1 !important; transition: none !important; filter: none !important; }
    .element-container { opacity: 1 !important; transition: none !important; filter: none !important; }
    [data-testid="stStatusWidget"] { visibility: hidden; display: none; }
    [data-testid="stAppViewBlockContainer"] { opacity: 1 !important; transition: none !important; filter: none !important; }
    
    .app-header { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important; padding: 20px 24px; border-radius: 18px; margin-bottom: 18px; box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25); display: flex; justify-content: space-between; align-items: center; }
    .app-header .app-title { font-size: 24px; font-weight: 800; margin: 0; color: #ffffff !important; letter-spacing: -0.5px; }
    .app-header .app-subtitle { font-size: 13px; color: #38bdf8 !important; font-weight: 600; margin: 2px 0 0 0; }
    .app-header .app-badge { background-color: rgba(59, 130, 246, 0.2); color: #60a5fa !important; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; border: 1px solid rgba(96, 165, 250, 0.3); }
    
    .stTabs [data-baseweb="tab-list"] { gap: 6px; background-color: #cbd5e1 !important; padding: 6px; border-radius: 14px; }
    .stTabs [data-baseweb="tab"] { height: 44px; border-radius: 10px; background-color: transparent !important; flex: 1; justify-content: center; border: none !important; }
    .stTabs [data-baseweb="tab"] p { color: #334155 !important; font-weight: 700 !important; font-size: 14px !important; }
    .stTabs [aria-selected="true"] { background-color: #ffffff !important; box-shadow: 0 2px 8px rgba(0,0,0,0.12) !important; }
    .stTabs [aria-selected="true"] p { color: #0f172a !important; font-weight: 800 !important; }
    
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input { background-color: #ffffff !important; color: #0f172a !important; -webkit-text-fill-color: #0f172a !important; caret-color: #2563eb !important; border: 2px solid #cbd5e1 !important; border-radius: 12px !important; font-weight: 700 !important; font-size: 18px !important; height: 54px !important; opacity: 1 !important; }
    div[data-testid="stNumberInput"] input { font-size: 26px !important; font-weight: 800 !important; height: 60px !important; }
    div[data-testid="stTextInput"] input::placeholder, div[data-testid="stNumberInput"] input::placeholder { color: #94a3b8 !important; -webkit-text-fill-color: #94a3b8 !important; }
    div[data-testid="stNumberInput"] button { display: none !important; }
    
    div[data-baseweb="select"] > div { background-color: #ffffff !important; color: #0f172a !important; border: 2px solid #cbd5e1 !important; border-radius: 12px !important; min-height: 50px !important; font-weight: 700 !important; opacity: 1 !important; }
    div[data-baseweb="select"] span, div[data-baseweb="select"] div { color: #0f172a !important; }
    div[data-baseweb="select"] svg { fill: #0f172a !important; }
    
    div.stButton > button, div.stDownloadButton > button { border-radius: 14px !important; height: 56px !important; font-weight: 700 !important; font-size: 15px !important; transition: all 0.1s ease-in-out !important; opacity: 1 !important; }
    div.stButton > button[kind="secondary"] { background-color: #ffffff !important; color: #0f172a !important; border: 2px solid #cbd5e1 !important; }
    div.stButton > button[kind="secondary"] p { color: #0f172a !important; }
    div.stButton > button[kind="primary"], div.stDownloadButton > button[kind="primary"] { background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important; color: #ffffff !important; border: none !important; box-shadow: 0 6px 15px rgba(37, 99, 235, 0.25) !important; }
    div.stButton > button[kind="primary"] p, div.stDownloadButton > button[kind="primary"] p { color: #ffffff !important; }
    
    [data-testid="stExpander"] { background-color: #ffffff !important; border: 2px solid #bfdbfe !important; border-left: 6px solid #2563eb !important; border-radius: 12px !important; margin-bottom: 10px !important; box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04) !important; opacity: 1 !important; }
    [data-testid="stExpander"] details, [data-testid="stExpander"] summary { background-color: #ffffff !important; color: #0f172a !important; border-radius: 12px !important; }
    [data-testid="stExpander"] summary p { color: #0f172a !important; font-weight: 800 !important; font-size: 15px !important; }
    
    .total-card { background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); padding: 18px 22px; border-radius: 16px; border: 2px solid #6ee7b7; margin: 15px 0; display: flex; justify-content: space-between; align-items: center; }
    .total-label { color: #065f46 !important; font-weight: 800; font-size: 13px; letter-spacing: 0.5px; }
    .total-amount { color: #047857 !important; font-weight: 900; font-size: 36px; line-height: 1; }
    .selected-pill { background-color: #eff6ff; border: 1px solid #bfdbfe; color: #1d4ed8 !important; padding: 10px 16px; border-radius: 12px; font-weight: 700; font-size: 15px; margin-bottom: 10px; display: flex; justify-content: space-between; }
    .selected-pill span { color: #1d4ed8 !important; }
</style>
""", unsafe_allow_html=True)

# Forzar teclado numérico decimal en móviles
components.html("""
<script>
const forceDecimalKeypad = () => {
    const inputs = window.parent.document.querySelectorAll('input[type="number"]');
    inputs.forEach(input => {
        if (input.getAttribute('inputmode') !== 'decimal') {
            input.setAttribute('inputmode', 'decimal');
            input.setAttribute('autocomplete', 'off');
        }
    });
};
forceDecimalKeypad();
const observer = new MutationObserver(forceDecimalKeypad);
observer.observe(window.parent.document.body, { childList: true, subtree: true });
</script>
""", height=0, width=0)

# --- CONEXIÓN A FIREBASE EN LA NUBE ---
if not firebase_admin._apps:
    try:
        cert_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(cert_dict)
    except:
        cred = credentials.Certificate("firebase_key.json")
    
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://reciclajepro-afaa7-default-rtdb.firebaseio.com'
    })

# --- FUNCIONES OPTIMIZADAS CON CACHÉ (TURBO) ---
@st.cache_data(ttl=60)
def cargar_materiales():
    mat = db.reference('materiales').get()
    if not mat:
        mat = {"Botella": 1.30, "Aluminio": 5.00, "Carton": 0.20, "Cobre": 30.00, "Chatarra": 0.80}
        db.reference('materiales').set(mat)
    return mat

def guardar_materiales(materiales_actualizados):
    db.reference('materiales').set(materiales_actualizados)
    st.cache_data.clear() # Limpia la memoria para ver cambios

@st.cache_data(ttl=10)
def cargar_historial():
    return db.reference('historial').get()

def guardar_en_historial(filas):
    ref = db.reference('historial')
    for fila in filas:
        ref.push(fila)
    st.cache_data.clear() # Limpia la memoria para actualizar tablas

@st.cache_data(ttl=30)
def cargar_caja():
    caja = db.reference('caja').get()
    if not caja:
        caja = {"fecha": "", "inicial": 0.0}
        db.reference('caja').set(caja)
    return caja

def guardar_caja(fecha, inicial):
    db.reference('caja').set({"fecha": fecha, "inicial": inicial})
    st.cache_data.clear()

def borrar_registro_historial(val_fecha, val_hora, val_mat):
    ref = db.reference('historial')
    hist = ref.get()
    if not hist: return
    
    es_grupo = val_mat.startswith("📦")
    borrado = False
    
    for key, row in hist.items():
        if len(row) >= 5:
            if es_grupo and row[0] == val_fecha and row[1] == val_hora:
                ref.child(key).delete()
            elif not es_grupo and row[0] == val_fecha and row[1] == val_hora and row[2] == val_mat and not borrado:
                ref.child(key).delete()
                borrado = True
    st.cache_data.clear()
    st.toast("✅ Registro eliminado de la nube")

def vaciar_historial_completo():
    db.reference('historial').delete()
    st.cache_data.clear()
    st.toast("⚠️ Historial reseteado en la nube")

def generar_imagen_ticket_bytes(detalles, total, fecha, hora):
    ancho = 400
    alto = 320 + (len(detalles) * 60)
    img = Image.new('RGB', (ancho, alto), color='white')
    d = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arialbd.ttf", 26)
        font_text = ImageFont.truetype("arial.ttf", 18)
        font_bold = ImageFont.truetype("arialbd.ttf", 20)
        font_total = ImageFont.truetype("arialbd.ttf", 28)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_total = ImageFont.load_default()

    y = 30
    d.text((ancho/2, y), "RECICLAJE MIA S.A.C", fill="black", font=font_title, anchor="mt")
    y += 45
    d.text((ancho/2, y), f"Fecha: {fecha}  Hora: {hora}", fill="#475569", font=font_text, anchor="mt")
    y += 40
    d.line([(30, y), (ancho-30, y)], fill="black", width=2)
    y += 20

    for m, p, s in detalles:
        d.text((30, y), f"{m}", fill="black", font=font_bold, anchor="lt")
        y += 25
        d.text((30, y), f"{p:.2f} kg", fill="#475569", font=font_text, anchor="lt")
        d.text((ancho-30, y), f"S/. {s:.2f}", fill="black", font=font_bold, anchor="rt")
        y += 35

    d.line([(30, y), (ancho-30, y)], fill="black", width=2)
    y += 30
    d.text((ancho-30, y), f"TOTAL: S/. {total:.2f}", fill="#047857", font=font_total, anchor="rs")

    y += 60
    d.text((ancho/2, y), "¡Gracias por tu preferencia!", fill="#475569", font=font_text, anchor="mt")

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- CARGA INICIAL INSTANTÁNEA ---
materiales = cargar_materiales()

if "carrito" not in st.session_state: st.session_state.carrito = []
if "mat_unico" not in st.session_state: st.session_state.mat_unico = list(materiales.keys())[0] if materiales else None
if "mat_mult" not in st.session_state: st.session_state.mat_mult = list(materiales.keys())[0] if materiales else None
if "reset_u" not in st.session_state: st.session_state.reset_u = 0
if "reset_m" not in st.session_state: st.session_state.reset_m = 0

if materiales:
    if st.session_state.mat_unico not in materiales: st.session_state.mat_unico = list(materiales.keys())[0]
    if st.session_state.mat_mult not in materiales: st.session_state.mat_mult = list(materiales.keys())[0]

# --- ENCABEZADO ---
st.markdown(f"""
<div class="app-header">
    <div>
        <p class="app-title">☁️ RECICLAJE PRO</p>
        <p class="app-subtitle">Nube Activa • {datetime.now().strftime('%d/%m/%Y')}</p>
    </div>
    <div class="app-badge">⚡ TURBO</div>
</div>
""", unsafe_allow_html=True)

tab_rapido, tab_multiple, tab_caja, tab_historial, tab_precios = st.tabs([
    "⚡ Rápido", 
    "🛒 Múltiple", 
    "💰 Caja",
    "📋 Historial", 
    "⚙️ Ajustes"
])

# ==========================================
# 1. PESTAÑA: CLIENTE RÁPIDO
# ==========================================
with tab_rapido:
    if "ticket_u" in st.session_state:
        st.success("✅ Subido a la Nube Exitosamente")
        t = st.session_state.ticket_u
        if PILLOW_AVAILABLE:
            st.image(t['imagen'], use_container_width=True)
            st.download_button("📥 Descargar Ticket (Imagen)", data=t['imagen'], file_name=f"Ticket_{t['fecha']}_{t['hora'].replace(':', '')}.png", mime="image/png", type="primary", use_container_width=True)
            st.info("💡 En iPhone: Mantén presionada la imagen para 'Compartir' directo a WhatsApp.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅️ NUEVA COMPRA RÁPIDA", type="secondary", use_container_width=True):
            del st.session_state.ticket_u
            st.session_state.reset_u += 1
            st.rerun()
    else:
        if not materiales:
            st.warning("No hay materiales registrados.")
        else:
            st.markdown("**1. Toca el material:**")
            cols_u = st.columns(2)
            for idx, (mat, precio) in enumerate(materiales.items()):
                es_activo = (st.session_state.mat_unico == mat)
                if cols_u[idx % 2].button(f"{'✅' if es_activo else '♻️'} {mat} • S/. {precio:.2f}", key=f"btn_u_{mat}", type="primary" if es_activo else "secondary", use_container_width=True):
                    st.session_state.mat_unico = mat
                    st.rerun()

            mat_sel = st.session_state.mat_unico
            precio_sel = materiales[mat_sel]
            st.markdown(f"""<div class="selected-pill"><span>Material: {mat_sel}</span><span>S/. {precio_sel:.2f} / kg</span></div>""", unsafe_allow_html=True)
            
            peso_input = st.number_input("2. Ingresa el peso recibido (kg):", min_value=0.0, value=None, step=0.1, format="%.2f", placeholder="Toca aquí para escribir...", key=f"peso_u_{st.session_state.reset_u}")
            peso_u = peso_input if peso_input is not None else 0.0
            total_u = peso_u * precio_sel

            st.markdown(f"""
            <div class="total-card">
                <div><div class="total-label">TOTAL A PAGAR</div><div style="color:#047857; font-size:13px; font-weight:600;">{peso_u:.2f} kg × S/. {precio_sel:.2f}</div></div>
                <div class="total-amount">S/. {total_u:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("✓ REGISTRAR COMPRA", key="reg_unico", type="primary", use_container_width=True):
                if peso_u <= 0:
                    st.error("⚠️ Ingresa un peso mayor a 0.")
                else:
                    now = datetime.now()
                    fecha, hora = now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")
                    guardar_en_historial([[fecha, hora, mat_sel, f"{peso_u:.2f}", f"{total_u:.2f}"]])
                    
                    if PILLOW_AVAILABLE:
                        img_bytes = generar_imagen_ticket_bytes([(mat_sel, peso_u, total_u)], total_u, fecha, hora)
                        st.session_state.ticket_u = {"imagen": img_bytes, "fecha": fecha, "hora": hora}
                    st.rerun()

# ==========================================
# 2. PESTAÑA: COMPRA MÚLTIPLE
# ==========================================
with tab_multiple:
    if "ticket_m" in st.session_state:
        st.success("✅ Subido a la Nube Exitosamente")
        t = st.session_state.ticket_m
        if PILLOW_AVAILABLE:
            st.image(t['imagen'], use_container_width=True)
            st.download_button("📥 Descargar Ticket (Imagen)", data=t['imagen'], file_name=f"Ticket_{t['fecha']}_{t['hora'].replace(':', '')}.png", mime="image/png", type="primary", use_container_width=True)
            st.info("💡 En iPhone: Mantén presionada la imagen para 'Compartir' directo a WhatsApp.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅️ NUEVA COMPRA MÚLTIPLE", type="secondary", use_container_width=True):
            del st.session_state.ticket_m
            st.session_state.reset_m += 1
            st.rerun()
    else:
        if not materiales:
            st.warning("No hay materiales registrados.")
        else:
            st.markdown("**1. Selecciona material:**")
            cols_m = st.columns(2)
            for idx, (mat, precio) in enumerate(materiales.items()):
                es_activo_m = (st.session_state.mat_mult == mat)
                if cols_m[idx % 2].button(f"{'✅' if es_activo_m else '♻️'} {mat} • S/. {precio:.2f}", key=f"btn_m_{mat}", type="primary" if es_activo_m else "secondary", use_container_width=True):
                    st.session_state.mat_mult = mat
                    st.rerun()

            mat_m = st.session_state.mat_mult
            precio_m = materiales[mat_m]
            st.markdown(f"""<div class="selected-pill"><span>Agregando: {mat_m}</span><span>S/. {precio_m:.2f} / kg</span></div>""", unsafe_allow_html=True)

            peso_m_input = st.number_input("2. Peso (kg):", min_value=0.0, value=None, step=0.1, format="%.2f", placeholder="Escribe el peso...", key=f"peso_m_{st.session_state.reset_m}")
            peso_m = peso_m_input if peso_m_input is not None else 0.0

            if st.button("➕ AÑADIR AL TICKET", key="add_cart", type="secondary", use_container_width=True):
                if peso_m <= 0:
                    st.warning("⚠️ Escribe un peso mayor a 0.")
                else:
                    st.session_state.carrito.append({"material": mat_m, "peso": peso_m, "subtotal": peso_m * precio_m})
                    st.session_state.reset_m += 1
                    st.rerun()

            st.divider()
            st.markdown("#### 🧾 Ticket del Cliente")

            if len(st.session_state.carrito) == 0:
                st.info("El ticket está vacío.")
            else:
                for idx, item in enumerate(st.session_state.carrito):
                    c_info, c_sub, c_del = st.columns([4, 3, 2])
                    c_info.markdown(f"**{item['material']}**<br><span style='color:#475569; font-size:13px;'>{item['peso']:.2f} kg</span>", unsafe_allow_html=True)
                    c_sub.markdown(f"<div style='text-align:right; font-weight:800; font-size:16px; padding-top:8px; color:#0f172a;'>S/. {item['subtotal']:.2f}</div>", unsafe_allow_html=True)
                    if c_del.button("🗑️", key=f"del_cart_{idx}", use_container_width=True):
                        st.session_state.carrito.pop(idx)
                        st.rerun()

                total_peso_m = sum(i["peso"] for i in st.session_state.carrito)
                total_monto_m = sum(i["subtotal"] for i in st.session_state.carrito)

                st.markdown(f"""
                <div class="total-card">
                    <div><div class="total-label">TOTAL ({len(st.session_state.carrito)} items)</div><div style="color:#047857; font-size:14px; font-weight:700;">Peso: {total_peso_m:.2f} kg</div></div>
                    <div class="total-amount">S/. {total_monto_m:.2f}</div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("✅ COMPLETAR Y COBRAR", type="primary", use_container_width=True):
                    now = datetime.now()
                    fecha, hora = now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")

                    filas_guardar = [[fecha, hora, f"📦 COMPRA MÚLTIPLE ({len(st.session_state.carrito)} items)", f"{total_peso_m:.2f}", f"{total_monto_m:.2f}"]]
                    detalles_ticket = []
                    for item in st.session_state.carrito:
                        filas_guardar.append([fecha, hora, f"↳ {item['material']}", f"{item['peso']:.2f}", f"{item['subtotal']:.2f}"])
                        detalles_ticket.append((item['material'], item['peso'], item['subtotal']))

                    guardar_en_historial(filas_guardar)
                    
                    if PILLOW_AVAILABLE:
                        img_bytes = generar_imagen_ticket_bytes(detalles_ticket, total_monto_m, fecha, hora)
                        st.session_state.ticket_m = {"imagen": img_bytes, "fecha": fecha, "hora": hora}
                        
                    st.session_state.carrito.clear()
                    st.rerun()

# ==========================================
# 3. PESTAÑA: CONTROL DE CAJA
# ==========================================
with tab_caja:
    hoy_str = datetime.now().strftime("%Y-%m-%d")
    caja_data = cargar_caja()
    
    if caja_data["fecha"] != hoy_str:
        caja_data = {"fecha": hoy_str, "inicial": 0.0}
        
    st.markdown("#### 💵 Apertura de Caja")
    st.markdown("¿Con cuánto efectivo empezaste hoy?")
    
    caja_ini_input = st.number_input("Capital Inicial (S/.):", min_value=0.0, value=float(caja_data["inicial"]), step=10.0, format="%.2f")
    if st.button("💾 Guardar Capital en Nube", type="secondary", use_container_width=True):
        guardar_caja(hoy_str, caja_ini_input)
        st.toast("✅ Capital sincronizado")
        st.rerun()
        
    st.divider()
    
    gastos_hoy = 0.0
    kilos_hoy = {}
    list_mat = []
    
    hist_data = cargar_historial()
    if hist_data:
        for key, row in hist_data.items():
            if len(row) >= 5 and row[0] == hoy_str:
                mat = row[2]
                if mat.startswith("📦"): continue 
                if mat.startswith("↳ "): mat = mat.replace("↳ ", "")
                peso = float(row[3])
                monto = float(row[4])
                gastos_hoy += monto
                
                if mat in kilos_hoy:
                    kilos_hoy[mat]['peso'] += peso
                    kilos_hoy[mat]['monto'] += monto
                else:
                    kilos_hoy[mat] = {'peso': peso, 'monto': monto}
                    
                encontrado = False
                for d in list_mat:
                    if d["Material"] == mat:
                        d["Peso Total (kg)"] += peso; d["Gasto Total (S/.)"] += monto; encontrado = True; break
                if not encontrado: list_mat.append({"Material": mat, "Peso Total (kg)": peso, "Gasto Total (S/.)": monto})

    sobrante = caja_ini_input - gastos_hoy
    
    st.markdown("#### 📊 Cuadre de Caja")
    st.markdown(f"""
    <div style="display:flex; gap:10px; margin-bottom:15px;">
        <div style="flex:1; background:white; padding:15px; border-radius:12px; border:1px solid #cbd5e1;">
            <div style="font-size:11px; color:#64748b; font-weight:bold;">CAPITAL</div>
            <div style="font-size:18px; color:#0f172a; font-weight:900;">S/. {caja_ini_input:.2f}</div>
        </div>
        <div style="flex:1; background:#fee2e2; padding:15px; border-radius:12px; border:1px solid #fecaca;">
            <div style="font-size:11px; color:#991b1b; font-weight:bold;">GASTOS</div>
            <div style="font-size:18px; color:#7f1d1d; font-weight:900;">- S/. {gastos_hoy:.2f}</div>
        </div>
    </div>
    
    <div style="background:{'#ecfdf5' if sobrante >= 0 else '#fef2f2'}; padding:20px; border-radius:12px; border:1px solid {'#6ee7b7' if sobrante >= 0 else '#fca5a5'}; margin-bottom:20px; text-align:center;">
        <div style="font-size:14px; color:{'#065f46' if sobrante >= 0 else '#991b1b'}; font-weight:bold;">EFECTIVO EXACTO QUE DEBE HABER</div>
        <div style="font-size:42px; color:{'#047857' if sobrante >= 0 else '#7f1d1d'}; font-weight:900;">S/. {sobrante:.2f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    df_resumen = pd.DataFrame([{"Fecha": hoy_str, "Capital Inicial (S/.)": caja_ini_input, "Total Gastos (S/.)": gastos_hoy, "Efectivo en Caja (S/.)": sobrante}])
    df_mat = pd.DataFrame(list_mat)
    
    output_caja = BytesIO()
    with pd.ExcelWriter(output_caja, engine='openpyxl') as writer:
        df_resumen.to_excel(writer, index=False, sheet_name='Resumen_Diario')
        if not df_mat.empty:
            df_mat.to_excel(writer, index=False, sheet_name='Detalle_Materiales')
            
    st.download_button(
        label="📊 Descargar Cuadre a Excel (.xlsx)",
        data=output_caja.getvalue(),
        file_name=f"Cuadre_Caja_{hoy_str}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    
    st.markdown("#### 📦 Kilos Comprados Hoy")
    if not kilos_hoy:
        st.info("Aún no hay compras registradas hoy.")
    else:
        for m, d in kilos_hoy.items():
            st.markdown(f"""
            <div style="background:white; padding:12px 16px; border-radius:10px; border:1px solid #cbd5e1; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:700; color:#0f172a;">{m}</span>
                <div style="text-align:right;">
                    <span style="color:#0f172a; font-weight:800;">{d['peso']:.2f} kg</span><br>
                    <span style="color:#64748b; font-size:12px;">S/. {d['monto']:.2f} gastados</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# 4. PESTAÑA: HISTORIAL Y BORRADO
# ==========================================
with tab_historial:
    st.subheader("Historial de la Nube")
    
    if not hist_data:
        st.info("La nube está vacía. Aún no hay operaciones registradas.")
    else:
        filas_df = list(hist_data.values())
        df_historial = pd.DataFrame(filas_df, columns=["Fecha", "Hora", "Material", "Peso (kg)", "Monto Pagado"])
        
        output_hist = BytesIO()
        with pd.ExcelWriter(output_hist, engine='openpyxl') as writer:
            df_historial.to_excel(writer, index=False, sheet_name='Historial_Nube')
        
        st.download_button(
            label="📊 Descargar Historial Completo (.xlsx)",
            data=output_hist.getvalue(),
            file_name=f"Historial_Nube_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )
        
        col_espacio, col_vaciar = st.columns([2, 1])
        if col_vaciar.button("⚠️ Vaciar Nube", type="secondary", use_container_width=True):
            vaciar_historial_completo()
            st.rerun()

        st.divider()
        
        transacciones = []
        actual = None
        for key, row in hist_data.items():
            if len(row) < 5: continue
            if row[2].startswith("📦 COMPRA MÚLTIPLE"):
                actual = {"padre": row, "hijos": []}
                transacciones.append(actual)
            elif row[2].startswith("↳ ") and actual is not None:
                actual["hijos"].append(row)
            else:
                actual = None
                transacciones.append({"padre": row, "hijos": []})
        
        for idx_g, grupo in enumerate(reversed(transacciones)):
            p = grupo["padre"]
            if grupo["hijos"]:
                with st.expander(f"{p[2]} • {p[3]} kg • Total: S/. {p[4]}"):
                    for h in grupo["hijos"]:
                        st.markdown(f"<div style='padding:6px 0; border-bottom:1px solid #e2e8f0; display:flex; justify-content:space-between;'><span style='color:#0f172a'><b>{h[2]}</b> ({h[3]}kg)</span><span style='color:#047857; font-weight:800;'>S/. {h[4]}</span></div>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑️ Eliminar esta Compra", key=f"del_g_{idx_g}", use_container_width=True):
                        borrar_registro_historial(p[0], p[1], p[2])
                        st.rerun()
            else:
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    st.markdown(f"""
                    <div style="background:white; padding:12px 16px; border-radius:12px; border:1px solid #cbd5e1; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-weight:800; color:#0f172a; font-size:15px;">{p[2]}</span> • <span style="color:#334155; font-weight:600;">{p[3]} kg</span><br>
                            <span style="font-size:12px; color:#64748b;">{p[0]} a las {p[1]}</span>
                        </div>
                        <div style="font-weight:800; font-size:18px; color:#047857;">S/. {p[4]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    if st.button("🗑️", key=f"del_i_{idx_g}", use_container_width=True):
                        borrar_registro_historial(p[0], p[1], p[2])
                        st.rerun()

# ==========================================
# 5. PESTAÑA: GESTIÓN DE PRECIOS
# ==========================================
with tab_precios:
    st.markdown("#### ➕ Agregar Material")
    nuevo_mat = st.text_input("Nombre del Material:", placeholder="Ej: Bronce")
    nuevo_precio_in = st.number_input("Precio por Kg (S/.):", min_value=0.0, value=None, step=0.1, format="%.2f", placeholder="0.00")
    
    if st.button("💾 Guardar en la Nube", type="primary", use_container_width=True):
        if nuevo_mat.strip() and nuevo_precio_in is not None and nuevo_precio_in >= 0:
            materiales[nuevo_mat.strip()] = nuevo_precio_in
            guardar_materiales(materiales)
            st.toast(f"✅ Nube actualizada: {nuevo_mat} a S/. {nuevo_precio_in:.2f}")
            st.rerun()
        else:
            st.error("Completa el nombre y un precio válido.")
            
    st.divider()
    st.markdown("#### 🗑️ Eliminar Material")
    if materiales:
        mat_borrar = st.selectbox("Selecciona para eliminar:", list(materiales.keys()))
        if st.button("🗑️ Eliminar Seleccionado", type="secondary", use_container_width=True):
            del materiales[mat_borrar]
            guardar_materiales(materiales)
            st.toast("✅ Material eliminado de la nube")
            st.rerun()

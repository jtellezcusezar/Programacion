"""
app.py
======
Interfaz Streamlit para el generador de reportes semanales de obra.

Ejecución local:
    streamlit run app.py

Deploy en Streamlit Cloud:
    1. Sube los 4 archivos a un repositorio GitHub:
       app.py  processor.py  renderer.py  requirements.txt
    2. Ve a share.streamlit.io → New app → conecta el repo
    3. Listo — la URL queda pública y accesible desde cualquier lugar
"""

import streamlit as st
from datetime import date, timedelta
import json

from processor import process_project
from renderer  import render_dashboard


# ─── Configuración de página ───────────────────────────────────────────────────

st.set_page_config(
    page_title="Reportes Semanales de Obra",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── CSS global ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
  #MainMenu {visibility: hidden;}
  footer     {visibility: hidden;}
  .block-container {padding-top: 1.5rem; padding-bottom: 1rem;}

  .app-title {font-size:22px; font-weight:700; color:#1e293b; margin-bottom:2px;}
  .app-sub   {font-size:13px; color:#64748b;   margin-bottom:20px;}

  .file-card {
    background:#f0fdf4; border:1px solid #bbf7d0;
    border-left:4px solid #16a34a; border-radius:7px;
    padding:10px 14px; margin-bottom:8px;
    font-size:12.5px; color:#1e293b;
  }
  .file-card .fc-name {font-weight:600;}
  .file-card .fc-meta {color:#64748b; font-size:11.5px; margin-top:2px;}
  .file-error {background:#fef2f2; border-left-color:#dc2626; border-color:#fecaca;}
</style>
""", unsafe_allow_html=True)


# ─── Constantes ───────────────────────────────────────────────────────────────

MONTHS = ["","Ene","Feb","Mar","Abr","May","Jun",
           "Jul","Ago","Sep","Oct","Nov","Dic"]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def render_project_tab(fname: str, data: dict, ref_date: date) -> None:
    """Muestra el dashboard de un proyecto y su botón de descarga."""

    html = render_dashboard(data)

    # Botón de descarga
    slug          = data["project_name"][:30].replace(" ", "_").replace("/", "-")
    download_name = f"reporte_{slug}_{ref_date}.html"

    col1, col2 = st.columns([1, 5])
    with col1:
        st.download_button(
            label="⬇️ Descargar HTML",
            data=html.encode("utf-8"),
            file_name=download_name,
            mime="text/html",
            use_container_width=True,
        )
    with col2:
        st.caption(
            "💡 Abre el archivo en tu browser y usa "
            "**Ctrl+P → Guardar como PDF** para exportar a PDF."
        )

    st.markdown("---")

    # Altura dinámica según cantidad de filas
    n_tasks  = sum(len(tw["tasks"])  for tw in data["towers"])
    n_groups = sum(len(tw["groups"]) for tw in data["towers"])
    height   = max(800, 220 + n_tasks * 30 + n_groups * 28)

    st.components.v1.html(html, height=height, scrolling=True)


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🏗️ Reportes de Obra")
    st.markdown("---")

    # Fecha de corte
    st.markdown("### 📅 Fecha de corte")
    today  = date.today()
    monday = today - timedelta(days=today.weekday())

    ref_date = st.date_input(
        "Selecciona la fecha",
        value=monday,
        help="Generalmente el lunes de la semana a reportar.",
    )
    week_end = ref_date + timedelta(days=4)
    st.caption(
        f"Semana: **{ref_date.day} {MONTHS[ref_date.month]}** – "
        f"**{week_end.day} {MONTHS[week_end.month]} {week_end.year}**"
    )

    st.markdown("---")

    # Subida de archivos
    st.markdown("### 📂 Archivos de proyecto")
    st.caption("Geniebelt → Proyecto → Exportar → JSON")

    uploaded_files = st.file_uploader(
        "Arrastra uno o varios archivos",
        type=["json", "txt"],
        accept_multiple_files=True,
        help="Puedes subir varios proyectos a la vez.",
    )

    st.markdown("---")
    st.caption("v1.0 · Geniebelt Weekly Reporter")


# ─── Página principal ─────────────────────────────────────────────────────────

st.markdown('<div class="app-title">Reportes Semanales de Obra</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-sub">Sube los archivos JSON exportados desde Geniebelt '
    'para generar los reportes automáticamente.</div>',
    unsafe_allow_html=True,
)

# Estado vacío
if not uploaded_files:
    st.info(
        "👈 **Para comenzar:** sube uno o más archivos JSON desde el panel izquierdo.\n\n"
        "Exporta desde Geniebelt: **Proyecto → ··· → Exportar → JSON**",
        icon="📋",
    )
    with st.expander("¿Cómo funciona?"):
        st.markdown("""
        1. **Exporta** el JSON de cada proyecto desde Geniebelt
        2. **Sube** los archivos en el panel izquierdo (uno o varios a la vez)
        3. **Selecciona** la fecha de corte (lunes de la semana a reportar)
        4. La app genera el reporte automáticamente para cada proyecto
        5. **Descarga** el HTML → ábrelo en el browser → **Ctrl+P → Guardar como PDF**

        **El reporte incluye:**
        - Actividades que inician durante la semana seleccionada
        - Actividades atrasadas que ya tienen progreso registrado
        - Agrupadas por torre y sección (Obra Gris, Obra Blanca, etc.)
        - Fechas de CTO por torre en el encabezado
        - Diagrama Gantt semanal con barras de color por estado
        - Funciona con cualquier proyecto de Geniebelt sin configuración adicional
        """)
    st.stop()


# ─── Procesar archivos ─────────────────────────────────────────────────────────

processed = []   # lista de (filename, data | None, error | None)

with st.spinner("Procesando archivos..."):
    for f in uploaded_files:
        try:
            raw  = json.load(f)
            data = process_project(raw, reference_date=ref_date)
            processed.append((f.name, data, None))
        except Exception as e:
            processed.append((f.name, None, str(e)))

ok_files    = [(n, d) for n, d, e in processed if d is not None]
error_files = [(n, e) for n, d, e in processed if e is not None]


# ─── Panel de estado de archivos ──────────────────────────────────────────────

label = f"📂 {len(ok_files)} proyecto(s) cargado(s)"
if error_files:
    label += f" · ⚠️ {len(error_files)} con error"

with st.expander(label, expanded=True):
    cols = st.columns(min(len(processed), 3))
    for i, (fname, data, err) in enumerate(processed):
        with cols[i % 3]:
            if data:
                n_towers = len(data["towers"])
                n_tasks  = sum(len(tw["tasks"]) for tw in data["towers"])
                st.markdown(f"""
                <div class="file-card">
                  <div class="fc-name">✅ {fname}</div>
                  <div class="fc-meta">{data['project_name']}</div>
                  <div class="fc-meta">
                    {n_towers} torres · {n_tasks} actividades ·
                    {data['overall_progress']*100:.1f}% avance general
                  </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="file-card file-error">
                  <div class="fc-name">❌ {fname}</div>
                  <div class="fc-meta">{err}</div>
                </div>""", unsafe_allow_html=True)

if not ok_files:
    st.error("No se pudo procesar ningún archivo. Verifica que sean exportaciones válidas de Geniebelt.")
    st.stop()


# ─── Renderizar dashboards ────────────────────────────────────────────────────

if len(ok_files) == 1:
    fname, data = ok_files[0]
    render_project_tab(fname, data, ref_date)
else:
    tab_labels = [d["project_name"][:35] for _, d in ok_files]
    tabs = st.tabs(tab_labels)
    for tab, (fname, data) in zip(tabs, ok_files):
        with tab:
            render_project_tab(fname, data, ref_date)

"""
app.py  v2
==========
Cambios vs v1:
 - Múltiples proyectos sin tabs: todo en una página continua
 - Botón PDF directo (print del browser, sin librerías externas)
 - Usa renderer_v2 que acepta lista de proyectos
"""

import streamlit as st
import streamlit.components.v1 as components
from datetime import date, timedelta
import json

from processor import process_project
from renderer  import render_dashboard


# ─── Configuración ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Reportes Semanales de Obra",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  #MainMenu {visibility:hidden;} footer{visibility:hidden;}
  .block-container{padding-top:1.5rem;padding-bottom:1rem;}
  .app-title{font-size:22px;font-weight:700;color:#1e293b;margin-bottom:2px}
  .app-sub  {font-size:13px;color:#64748b;margin-bottom:20px}
  .file-card{background:#f0fdf4;border:1px solid #bbf7d0;
             border-left:4px solid #16a34a;border-radius:7px;
             padding:10px 14px;margin-bottom:8px;font-size:12.5px;color:#1e293b}
  .file-card .fc-name{font-weight:600}
  .file-card .fc-meta{color:#64748b;font-size:11.5px;margin-top:2px}
  .file-error{background:#fef2f2;border-left-color:#dc2626;border-color:#fecaca}
</style>
""", unsafe_allow_html=True)

MONTHS = ["","Ene","Feb","Mar","Abr","May","Jun",
           "Jul","Ago","Sep","Oct","Nov","Dic"]


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🏗️ Reportes de Obra")
    st.markdown("---")

    st.markdown("### 📅 Fecha de corte")
    today  = date.today()
    monday = today - timedelta(days=today.weekday())

    ref_date = st.date_input(
        "Selecciona la fecha",
        value=monday,
        help="Generalmente el lunes de la semana a reportar.",
    )
    week_end = ref_date + timedelta(days=5)   # sábado
    st.caption(
        f"Semana: **{ref_date.day} {MONTHS[ref_date.month]}** – "
        f"**{week_end.day} {MONTHS[week_end.month]} {week_end.year}**"
    )

    st.markdown("---")
    st.markdown("### 📂 Archivos de proyecto")
    st.caption("Geniebelt → Proyecto → Exportar → JSON")

    uploaded_files = st.file_uploader(
        "Arrastra uno o varios archivos",
        type=["json", "txt"],
        accept_multiple_files=True,
        help="Todos los proyectos se muestran en una sola página.",
    )

    st.markdown("---")
    st.caption("v2.0 · Geniebelt Weekly Reporter")


# ─── Página principal ─────────────────────────────────────────────────────────

st.markdown('<div class="app-title">Reportes Semanales de Obra</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="app-sub">Sube los archivos JSON exportados desde Geniebelt. '
    'Todos los proyectos se muestran en una sola página.</div>',
    unsafe_allow_html=True,
)

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
        4. La app genera el reporte de todos los proyectos en una sola página
        5. Usa **Imprimir / Guardar como PDF** para exportar a PDF directamente

        **El reporte incluye:**
        - Actividades que inician durante la semana (lunes a sábado)
        - Actividades atrasadas con progreso registrado
        - Agrupadas por torre y sección
        - Fechas CTO ordenadas por fecha
        - Gantt semanal con barras por estado
        - Campo de comentarios por actividad y por CTO
        """)
    st.stop()


# ─── Procesar archivos ─────────────────────────────────────────────────────────

processed = []

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


# ─── Panel de estado ──────────────────────────────────────────────────────────

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
                    {data['overall_progress']*100:.1f}% avance
                  </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="file-card file-error">
                  <div class="fc-name">❌ {fname}</div>
                  <div class="fc-meta">{err}</div>
                </div>""", unsafe_allow_html=True)

if not ok_files:
    st.error("No se pudo procesar ningún archivo.")
    st.stop()


# ─── Generar HTML combinado ───────────────────────────────────────────────────

all_data = [d for _, d in ok_files]
html     = render_dashboard(all_data)   # un solo HTML con todos los proyectos


# ─── Botones de acción ────────────────────────────────────────────────────────

col1, col2, col3 = st.columns([1, 1, 5])

# Botón descargar HTML
project_names = "_".join(d["project_name"][:15].replace(" ", "_") for d in all_data)
download_name = f"reporte_{project_names}_{ref_date}.html"

with col1:
    st.download_button(
        label="⬇️ Descargar HTML",
        data=html.encode("utf-8"),
        file_name=download_name,
        mime="text/html",
        use_container_width=True,
        help="Descarga el HTML para guardarlo o compartirlo.",
    )

# Botón PDF: inyecta un script que llama window.print() dentro del iframe
with col2:
    if st.button("🖨️ Imprimir / PDF", use_container_width=True,
                  help="Abre el diálogo de impresión. Selecciona 'Guardar como PDF'."):
        st.session_state["trigger_print"] = True

with col3:
    st.caption(
        "💡 Para PDF: haz clic en **Imprimir / PDF** → elige destino "
        "**'Guardar como PDF'** → guarda. Los comentarios se incluyen en el PDF."
    )

st.markdown("---")


# ─── Renderizar dashboard ─────────────────────────────────────────────────────

# Si se pidió imprimir, inyectamos window.print() al final del HTML
trigger_print = st.session_state.pop("trigger_print", False)

if trigger_print:
    html_to_render = html.replace(
        "</body>",
        "<script>window.addEventListener('load', function(){ window.print(); });</script></body>"
    )
else:
    html_to_render = html

# Altura dinámica
n_tasks  = sum(len(tw["tasks"])  for d in all_data for tw in d["towers"])
n_groups = sum(len(tw["groups"]) for d in all_data for tw in d["towers"])
height   = max(900, 250 + n_tasks * 30 + n_groups * 28 + len(all_data) * 120)

components.html(html_to_render, height=height, scrolling=True)

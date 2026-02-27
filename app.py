"""
app.py  v4  — Chronos
=====================
- Selector modo: fecha única vs rango de fechas
- Rango activa Gantt adaptativo en renderer
- Sin botón descarga HTML
- Botón PDF y toggle firmas dentro del HTML
"""

import streamlit as st
import streamlit.components.v1 as components
from datetime import date, timedelta
import json

from processor import process_project
from renderer  import render_dashboard

st.set_page_config(
    page_title="Chronos — Reportes de Obra",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  #MainMenu{visibility:hidden} footer{visibility:hidden}
  header[data-testid="stHeader"]{background:transparent}
  .block-container{padding-top:3.5rem;padding-bottom:1rem}
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
    st.markdown("## 🏗️ Chronos")
    st.markdown("Reportes Semanales de Obra")
    st.markdown("---")

    # ── Modo de fecha ────────────────────────────────────────────────────────
    st.markdown("### 📅 Modo de fecha")
    modo = st.radio(
        "Selecciona el modo",
        ["📆 Fecha única", "📅 Rango de fechas"],
        label_visibility="collapsed",
    )

    today  = date.today()
    monday = today - timedelta(days=today.weekday())

    if modo == "📆 Fecha única":
        ref_date = st.date_input(
            "Fecha de corte",
            value=monday,
            help="Se mostrará la semana correspondiente (lunes a sábado).",
        )
        date_end = None
        # Mostrar semana calculada
        ws = ref_date - timedelta(days=ref_date.weekday())
        we = ws + timedelta(days=5)
        st.caption(
            f"Semana: **{ws.day} {MONTHS[ws.month]}** – "
            f"**{we.day} {MONTHS[we.month]} {we.year}**"
        )
    else:
        ref_date = st.date_input(
            "Fecha inicio",
            value=monday,
            help="Inicio del rango. El atraso se calcula desde esta fecha.",
        )
        date_end = st.date_input(
            "Fecha fin",
            value=monday + timedelta(weeks=4),
            help="Fin del rango.",
        )
        if date_end <= ref_date:
            st.error("La fecha fin debe ser posterior a la fecha inicio.")
            date_end = None
        else:
            range_days = (date_end - ref_date).days + 1
            # Mostrar escala que se usará
            if range_days <= 6:
                escala = "días"
            elif range_days <= 27:
                escala = "semanas"
            elif range_days <= 89:
                escala = "semanas (con mes)"
            elif range_days <= 365:
                escala = "meses"
            else:
                escala = "trimestres"
            st.caption(
                f"Rango: **{range_days} días** · Escala: **{escala}**"
            )

    st.markdown("---")

    # ── Subida de archivos ───────────────────────────────────────────────────
    st.markdown("### 📂 Proyectos")
    st.caption("Geniebelt → Proyecto → Exportar → JSON")

    uploaded_files = st.file_uploader(
        "Arrastra uno o varios archivos",
        type=["json", "txt"],
        accept_multiple_files=True,
    )

    st.markdown("---")
    st.caption("Chronos v4.0")


# ─── Página principal ─────────────────────────────────────────────────────────

st.markdown('<div class="app-title">🏗️ Chronos</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-sub">Reportes de obra · '
    'Sube los archivos JSON exportados desde Geniebelt.</div>',
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
        **Modo fecha única** → muestra la semana (lun–sáb) de la fecha seleccionada.

        **Modo rango** → muestra todas las actividades entre las dos fechas.
        El Gantt se adapta automáticamente:
        - ≤ 6 días → columnas por día
        - 7–27 días → columnas por semana
        - 28–89 días → columnas por semana (con mes)
        - 90–365 días → columnas por mes
        - más de 365 días → columnas por trimestre

        **Botones dentro del reporte:**
        - 🖨️ Imprimir / Guardar como PDF
        - ✍️ Habilitar / Ocultar firmas
        """)
    st.stop()


# ─── Procesar ─────────────────────────────────────────────────────────────────

processed = []
with st.spinner("Procesando archivos..."):
    for f in uploaded_files:
        try:
            raw  = json.load(f)
            data = process_project(raw, reference_date=ref_date, date_end=date_end)
            processed.append((f.name, data, None))
        except Exception as e:
            processed.append((f.name, None, str(e)))

ok_files    = [(n, d) for n, d, e in processed if d is not None]
error_files = [(n, e) for n, d, e in processed if e is not None]

# Panel de estado
label = f"📂 {len(ok_files)} proyecto(s) cargado(s)"
if error_files:
    label += f" · ⚠️ {len(error_files)} con error"

with st.expander(label, expanded=True):
    cols = st.columns(min(len(processed), 3))
    for i, (fname, data, err) in enumerate(processed):
        with cols[i % 3]:
            if data:
                n_tw = len(data["towers"])
                n_t  = sum(len(tw["tasks"]) for tw in data["towers"])
                scale = data["gantt_meta"]["scale"]
                scale_lbl = {"day":"días","week":"semanas","week_month":"sem+mes",
                              "month":"meses","quarter":"trimestres"}.get(scale, scale)
                st.markdown(f"""
                <div class="file-card">
                  <div class="fc-name">✅ {fname}</div>
                  <div class="fc-meta">{data['project_name']}</div>
                  <div class="fc-meta">{n_tw} torres · {n_t} actividades · escala: {scale_lbl}</div>
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

st.markdown("---")

# ─── Renderizar ───────────────────────────────────────────────────────────────

all_data = [d for _, d in ok_files]
html     = render_dashboard(all_data)

n_tasks  = sum(len(tw["tasks"])  for d in all_data for tw in d["towers"])
n_groups = sum(len(tw["groups"]) for d in all_data for tw in d["towers"])
n_cols   = max((len(d["gantt_cols"]) for d in all_data), default=6)
# Altura dinámica: más columnas = tabla más ancha pero no más alta
height   = max(900, 280 + n_tasks * 30 + n_groups * 26 + len(all_data) * 100)

components.html(html, height=height, scrolling=True)

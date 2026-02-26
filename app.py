"""
app.py  v3  — Chronos
=====================
- Nombre: Chronos
- Sin botón descarga HTML
- Botón PDF vive dentro del HTML (persiste comentarios)
- Múltiples JSONs en una sola página con encabezado unificado
"""

import streamlit as st
import streamlit.components.v1 as components
from datetime import date, timedelta
import json

from processor import process_project
from renderer  import render_dashboard

# ─── Configuración ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Chronos — Reportes de Obra",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  #MainMenu{visibility:hidden} footer{visibility:hidden}
  .block-container{padding-top:1.5rem;padding-bottom:1rem}
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

    st.markdown("### 📅 Fecha de corte")
    today  = date.today()
    monday = today - timedelta(days=today.weekday())

    ref_date = st.date_input(
        "Selecciona la fecha",
        value=monday,
        help="Generalmente el lunes de la semana a reportar.",
    )
    week_end = ref_date + timedelta(days=5)
    st.caption(
        f"Semana: **{ref_date.day} {MONTHS[ref_date.month]}** – "
        f"**{week_end.day} {MONTHS[week_end.month]} {week_end.year}**"
    )

    st.markdown("---")
    st.markdown("### 📂 Proyectos")
    st.caption("Geniebelt → Proyecto → Exportar → JSON")

    uploaded_files = st.file_uploader(
        "Arrastra uno o varios archivos",
        type=["json", "txt"],
        accept_multiple_files=True,
        help="Todos los proyectos se muestran en una sola página.",
    )

    st.markdown("---")
    st.caption("Chronos v3.0")


# ─── Página principal ─────────────────────────────────────────────────────────

st.markdown('<div class="app-title">🏗️ Chronos</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-sub">Reportes semanales de obra · '
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
        1. **Exporta** el JSON de cada proyecto desde Geniebelt
        2. **Sube** los archivos en el panel izquierdo
        3. **Selecciona** la fecha de corte (lunes de la semana)
        4. El reporte se genera automáticamente con todos los proyectos
        5. Usa el botón **🖨️ Imprimir / Guardar como PDF** dentro del reporte

        **El botón PDF está dentro del reporte** — así los comentarios
        que escribas se incluyen en el PDF.
        """)
    st.stop()


# ─── Procesar ─────────────────────────────────────────────────────────────────

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
                st.markdown(f"""
                <div class="file-card">
                  <div class="fc-name">✅ {fname}</div>
                  <div class="fc-meta">{data['project_name']}</div>
                  <div class="fc-meta">{n_tw} torres · {n_t} actividades · {data['overall_progress']*100:.1f}% avance</div>
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
height   = max(900, 300 + n_tasks * 30 + n_groups * 28 + len(all_data) * 100)

components.html(html, height=height, scrolling=True)

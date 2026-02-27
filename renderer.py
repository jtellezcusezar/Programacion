"""
renderer.py  v4
===============
Cambios:
 1. Comentario de actividad como toggle (igual que CTO)
 2. Desplegable en encabezado de torre (siempre)
 3. Desplegable en agrupadores internos (solo en rango >= semana)
 4. Filtro corregido: oculta agrupadores vacíos
 6. Autocomplete en filtro
 4b. Sección de firmas (toggle habilitar/ocultar)
 5. Gantt adaptativo según escala
"""

from datetime import date, timedelta

_TOWER_PALETTE = [
    {"border": "#6366f1", "bg": "#eef2ff"},
    {"border": "#0284c7", "bg": "#e0f2fe"},
    {"border": "#0d9488", "bg": "#f0fdfa"},
    {"border": "#d97706", "bg": "#fffbeb"},
    {"border": "#dc2626", "bg": "#fef2f2"},
    {"border": "#7c3aed", "bg": "#faf5ff"},
    {"border": "#059669", "bg": "#ecfdf5"},
    {"border": "#db2777", "bg": "#fdf2f8"},
]
_MONTHS  = ["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]

def _tc(idx):  return _TOWER_PALETTE[idx % len(_TOWER_PALETTE)]
def _fmt(d):   return f"{d.day:02d}/{_MONTHS[d.month]}"


# ── CSS ───────────────────────────────────────────────────────────────────────
def _css() -> str:
    return """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --red:#dc2626;  --red-bg:#fef2f2; --red-b:#fecaca;
  --amb:#b45309;  --amb-bg:#fffbeb; --amb-b:#fde68a;
  --blue:#1d4ed8; --blue-bg:#eff6ff;--blue-b:#bfdbfe;
  --grn:#15803d;  --grn-bg:#f0fdf4; --grn-b:#bbf7d0;
  --sl:#475569;   --sl-bg:#f8fafc;  --sl-b:#e2e8f0;
  --pur:#6d28d9;
  --txt:#1e293b; --mut:#64748b; --bor:#e2e8f0;
}
body{font-family:'Inter',sans-serif;background:#fff;color:var(--txt);
     font-size:12px;padding:22px 26px;max-width:1300px;margin:0 auto}

/* HEADER */
.ph{display:flex;justify-content:space-between;align-items:flex-start;
    padding-bottom:12px;border-bottom:2.5px solid var(--txt);margin-bottom:14px}
.ph h1{font-size:19px;font-weight:700;letter-spacing:-.3px}
.ph .sub{font-size:11px;color:var(--mut);margin-top:3px}
.ph-meta{text-align:right;font-size:10.5px;color:var(--mut);
          font-family:'JetBrains Mono',monospace;line-height:1.7}
.ph-meta strong{color:var(--txt)}

/* PDF BTN */
.pdf-btn{display:inline-flex;align-items:center;gap:6px;
  background:#1d4ed8;color:#fff;border:none;border-radius:6px;
  padding:7px 16px;font-size:12px;font-weight:600;cursor:pointer;
  font-family:'Inter',sans-serif;margin-bottom:12px}
.pdf-btn:hover{background:#1e40af}

/* CTO */
.cto-banner{background:#faf5ff;border:1px solid #ddd6fe;
            border-left:4px solid var(--pur);border-radius:7px;
            padding:11px 15px;margin-bottom:13px}
.cto-banner h3{font-size:10px;font-weight:700;text-transform:uppercase;
               letter-spacing:.7px;color:var(--pur);margin-bottom:9px}
.cto-scroll{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px}
.cto-scroll::-webkit-scrollbar{height:4px}
.cto-scroll::-webkit-scrollbar-thumb{background:#c4b5fd;border-radius:2px}
.cto-card{background:#fff;border:1px solid #e9d5ff;border-radius:6px;
          padding:8px 11px;min-width:150px;flex-shrink:0}
.cto-tw{font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}
.cto-row{display:flex;gap:10px;margin-top:5px}
.ci .cl{font-size:9.5px;color:var(--mut)}
.ci .cd{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;color:var(--txt);margin-top:1px}
.ci .cdiff{font-size:9px;margin-top:1px}
.toggle-link{font-size:9px;color:var(--pur);cursor:pointer;margin-top:6px;
              display:inline-block;user-select:none;background:none;border:none;
              font-family:'Inter',sans-serif;padding:0}
.toggle-link:hover{text-decoration:underline}
.collapsible{display:none;margin-top:5px}
.collapsible textarea{
  width:100%;min-height:24px;resize:none;overflow:hidden;
  font-size:10px;font-family:'Inter',sans-serif;line-height:1.4;
  border:1px solid #ddd6fe;border-radius:4px;
  padding:3px 6px;color:var(--txt);background:#faf5ff;
  outline:none;display:block;
}
.collapsible textarea:focus{border-color:var(--pur)}

/* KPI */
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:13px}
.kpi{background:var(--sl-bg);border:1px solid var(--bor);border-radius:7px;padding:10px 13px}
.kpi-lbl{font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.6px;color:var(--mut)}
.kpi-val{font-size:22px;font-weight:700;margin-top:2px;line-height:1.1}
.v-blue{color:var(--blue)} .v-red{color:var(--red)}
.v-amb{color:var(--amb)}   .v-grn{color:var(--grn)}

/* LEGEND */
.legend{display:flex;gap:12px;flex-wrap:wrap;align-items:center;
        padding:7px 12px;background:var(--sl-bg);border:1px solid var(--bor);
        border-radius:6px;font-size:10px;color:var(--mut);margin-bottom:11px}
.li{display:flex;align-items:center;gap:4px}
.ld{width:9px;height:9px;border-radius:2px;flex-shrink:0}
.l-note{margin-left:auto;font-size:9.5px;color:var(--blue);font-family:'JetBrains Mono',monospace}

/* FILTER + AUTOCOMPLETE */
.filter-wrap{margin-bottom:11px;position:relative}
.filter-wrap input{
  width:100%;padding:7px 12px;font-size:12px;font-family:'Inter',sans-serif;
  border:1px solid var(--bor);border-radius:6px;outline:none;color:var(--txt);
}
.filter-wrap input:focus{border-color:var(--blue)}
.filter-wrap input::placeholder{color:#94a3b8}
.ac-dropdown{
  position:absolute;top:calc(100% + 2px);left:0;right:0;
  background:#fff;border:1px solid var(--bor);border-radius:6px;
  box-shadow:0 4px 12px rgba(0,0,0,.1);z-index:100;
  max-height:220px;overflow-y:auto;display:none;
}
.ac-item{
  padding:6px 12px;font-size:11px;cursor:pointer;color:var(--txt);
  border-bottom:1px solid #f1f5f9;
}
.ac-item:last-child{border-bottom:none}
.ac-item:hover,.ac-item.active{background:var(--blue-bg);color:var(--blue)}
.ac-item mark{background:transparent;color:var(--blue);font-weight:700}

/* PROJECT */
.proj-block{margin-bottom:26px}
.proj-hdr{font-size:13px;font-weight:700;color:var(--txt);
           padding:5px 0;border-bottom:1.5px solid var(--bor);margin-bottom:10px}

/* TOWER */
.tw-wrap{margin-bottom:16px}
.tw-hdr{
  display:flex;align-items:center;gap:8px;
  padding:7px 13px;border-radius:6px;
  cursor:pointer;user-select:none;
}
.tw-hdr:hover{filter:brightness(0.97)}
.tw-chevron{font-size:11px;transition:transform .2s;flex-shrink:0}
.tw-chevron.collapsed{transform:rotate(-90deg)}
.tw-name{font-size:12px;font-weight:700}
.tw-stats{margin-left:auto;font-size:10px;color:var(--mut)}
.tw-stats .alert{color:var(--red);font-weight:600}
.tw-body{overflow:hidden;transition:max-height .25s ease}

/* TABLE */
.gantt-wrap{border:1px solid var(--bor);border-radius:0 0 6px 6px;overflow:hidden}
table{width:100%;border-collapse:collapse;font-size:10.5px}
thead tr{background:#f8fafc}
th{padding:5px 7px;font-size:9px;font-weight:600;text-transform:uppercase;
   letter-spacing:.5px;color:var(--mut);text-align:left;
   border-bottom:1px solid var(--bor);white-space:nowrap}
th.dc{text-align:center}
th.today-th{color:var(--blue)}
th.comment-th{width:30px;min-width:30px;text-align:center}
th.dep-th{width:24px;min-width:24px;text-align:center}

/* DEP POPOVER */
td.dep-td{width:24px;min-width:24px;text-align:center;padding:2px 2px;vertical-align:middle}
.dep-btn{background:none;border:none;font-size:11px;cursor:pointer;
          color:#94a3b8;line-height:1;padding:1px 3px;border-radius:3px}
.dep-btn:hover{color:var(--pur);background:#faf5ff}
.dep-btn.active{color:var(--pur)}
.dep-popover{
  position:fixed;z-index:999;
  background:#fff;border:1px solid #ddd6fe;border-radius:8px;
  padding:10px 13px;min-width:220px;max-width:320px;
  box-shadow:0 8px 24px rgba(0,0,0,.12);
  font-size:10.5px;line-height:1.5;
  display:none;
}
.dep-popover.visible{display:block}
.dep-popover-title{font-size:9px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.5px;color:var(--pur);margin-bottom:6px}
.dep-section{margin-bottom:6px}
.dep-section:last-child{margin-bottom:0}
.dep-label{font-size:9px;font-weight:600;color:var(--mut);margin-bottom:3px}
.dep-item{padding:2px 0;color:var(--txt);display:flex;gap:5px;align-items:flex-start}
.dep-item .dep-arrow{flex-shrink:0;color:var(--pur)}
.dep-none{color:#94a3b8;font-style:italic;font-size:10px}

/* GROUP ROW */
tr.gr td{
  padding:4px 8px;background:#f1f5f9;font-size:9.5px;font-weight:600;
  color:var(--sl);border-bottom:1px solid var(--bor);border-top:1px solid var(--bor);
}
tr.gr.collapsible-group td{cursor:pointer;user-select:none}
tr.gr.collapsible-group td:hover{background:#e9eef5}
tr.gr .cs{color:#94a3b8;margin:0 3px}
tr.gr .gr-chevron{font-size:9px;margin-right:4px;transition:transform .15s;display:inline-block}
tr.gr.collapsed-grp .gr-chevron{transform:rotate(-90deg)}
tr.gr.hg{display:none}

/* TASK ROW */
tr.tr td{padding:4px 7px;border-bottom:1px solid #f1f5f9;vertical-align:middle}
tr.tr:last-child td{border-bottom:none}
tr.tr:hover td{background:#fafafa}
tr.tr.ht{display:none}
.tn{font-weight:500;white-space:normal;word-break:break-word;max-width:190px;line-height:1.35}

/* PILL */
.pill{display:inline-block;font-size:8.5px;font-weight:700;
       padding:1px 5px;border-radius:20px;white-space:nowrap}
.p-red {background:var(--red-bg);color:var(--red); border:1px solid var(--red-b)}
.p-amb {background:var(--amb-bg);color:var(--amb); border:1px solid var(--amb-b)}
.p-blue{background:var(--blue-bg);color:var(--blue);border:1px solid var(--blue-b)}
.p-grn {background:var(--grn-bg);color:var(--grn); border:1px solid var(--grn-b)}
.p-sl  {background:var(--sl-bg); color:var(--sl);  border:1px solid var(--sl-b)}

/* DELAY */
.dl{font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:600;color:var(--red)}
.dl.none{color:#cbd5e1}

/* GANTT CELL */
td.dc{padding:2px 1px;text-align:center}
td.tday{background:#eff6ff!important}
.bar{position:relative;height:17px;border-radius:3px;overflow:hidden;border:1px solid transparent;min-width:8px}
.bbg{position:absolute;inset:0}
.bpg{position:absolute;left:0;top:0;bottom:0}
.btx{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
     font-size:8.5px;font-weight:700;font-family:'JetBrains Mono',monospace;white-space:nowrap}
.bv-red {border-color:var(--red-b)!important}
.bv-red .bbg{background:var(--red-bg)}.bv-red .bpg{background:var(--red);opacity:.3}.bv-red .btx{color:var(--red)}
.bv-amb {border-color:var(--amb-b)!important}
.bv-amb .bbg{background:var(--amb-bg)}.bv-amb .bpg{background:var(--amb);opacity:.35}.bv-amb .btx{color:var(--amb)}
.bv-blue{border-color:var(--blue-b)!important}
.bv-blue .bbg{background:var(--blue-bg)}.bv-blue .bpg{background:var(--blue);opacity:.3}.bv-blue .btx{color:var(--blue)}
.bv-grn {border-color:var(--grn-b)!important}
.bv-grn .bbg{background:var(--grn-bg)}.bv-grn .bpg{background:var(--grn);opacity:.4}.bv-grn .btx{color:var(--grn)}
.bv-sl  {border-color:var(--sl-b)!important}
.bv-sl  .bbg{background:var(--sl-bg)}.bv-sl .bpg{background:var(--sl);opacity:.25}.bv-sl .btx{color:var(--sl)}

/* COMMENT TOGGLE IN ROW */
td.comment-td{width:30px;min-width:30px;text-align:center;padding:2px 3px;vertical-align:middle}
.cmt-btn{background:none;border:none;font-size:13px;cursor:pointer;
          color:#94a3b8;line-height:1;padding:1px 3px;border-radius:3px}
.cmt-btn:hover{color:var(--blue);background:var(--blue-bg)}
.cmt-btn.active{color:var(--blue)}
/* Fila de comentario */
tr.comment-row td{
  padding:3px 8px 5px 24px;background:#f8fafc;
  border-bottom:1px solid #f1f5f9;
}
tr.comment-row.hidden{display:none}
tr.comment-row textarea{
  width:100%;min-height:24px;resize:none;overflow:hidden;
  font-size:10px;font-family:'Inter',sans-serif;line-height:1.4;
  border:1px solid var(--bor);border-radius:4px;
  padding:3px 6px;color:var(--txt);background:#fff;
  outline:none;display:block;
}
tr.comment-row textarea:focus{border-color:var(--blue)}

hr.sep{border:none;border-top:1px solid var(--bor);margin:12px 0}

/* SIGNATURES */
.sig-section{margin-top:24px;border-top:2px solid var(--txt);padding-top:16px}
.sig-title{font-size:13px;font-weight:700;margin-bottom:12px}
.sig-table{width:100%;border-collapse:collapse}
.sig-table th{
  padding:6px 10px;font-size:10px;font-weight:600;text-transform:uppercase;
  letter-spacing:.5px;color:var(--mut);text-align:left;
  border-bottom:2px solid var(--bor);background:var(--sl-bg);
}
.sig-table td{padding:6px 8px;border-bottom:1px solid var(--bor);vertical-align:middle}
.sig-table .name-cell input{
  width:100%;border:none;border-bottom:1px solid var(--bor);
  font-size:11px;font-family:'Inter',sans-serif;color:var(--txt);
  padding:3px 4px;background:transparent;outline:none;
}
.sig-table .name-cell input:focus{border-bottom-color:var(--blue)}
.sig-table .sig-cell{height:48px;min-width:180px;border-left:1px solid var(--bor)}
.sig-add-row td{padding:6px 8px}
.add-sig-btn{
  background:none;border:1px dashed var(--bor);border-radius:5px;
  padding:5px 12px;font-size:11px;color:var(--mut);cursor:pointer;
  font-family:'Inter',sans-serif;
}
.add-sig-btn:hover{border-color:var(--blue);color:var(--blue);background:var(--blue-bg)}

/* PRINT */
@media print{
  .no-print{display:none!important}
  body{padding:8px;font-size:9px;max-width:100%}
  .tw-wrap{page-break-inside:avoid}
  .proj-block+.proj-block{page-break-before:always}
  .tw-body{max-height:none!important;display:block!important}
  tr.comment-row.hidden{display:none!important}
  tr.comment-row textarea,.collapsible textarea{
    overflow:visible!important;white-space:pre-wrap;word-break:break-word;
    border:1px solid #ccc;background:#fff;
  }
  .collapsible{display:block!important}
  .toggle-link{display:none!important}
  .cto-scroll{overflow:visible;flex-wrap:wrap}
  .bar{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .sig-table .sig-cell{height:60px}
  .ac-dropdown{display:none!important}
}
</style>"""


# ── Render principal ───────────────────────────────────────────────────────────

def render_dashboard(projects) -> str:
    if isinstance(projects, dict):
        projects = [projects]

    ref        = projects[0]["reference_date"]
    is_range   = any(p.get("is_range") for p in projects)

    # KPIs sumados
    global_kpis = {"starting":0,"delayed":0,"in_progress":0,"completed":0}
    for data in projects:
        for k in global_kpis:
            global_kpis[k] += data["kpis"][k]

    # CTO global ordenado por fecha
    all_cto = []
    for data in projects:
        for c in data["cto_items"]:
            days_diff = (c["date"] - ref).days
            all_cto.append({**c, "days_from_reference": days_diff,
                             "project": data["project_name"]})
    all_cto.sort(key=lambda x: x["date"])

    # Nombre(s) proyecto
    proj_names = " · ".join(d["project_name"] for d in projects)
    ws = projects[0]["week_start"]
    we = projects[0]["week_end"]
    week_lbl = f"{ws.day} {_MONTHS[ws.month]} – {we.day} {_MONTHS[we.month]} {we.year}"

    # Recolectar todos los nombres de actividades para autocomplete
    all_names = sorted(set(
        t["name"] for d in projects
        for tw in d["towers"] for t in tw["tasks"]
    ))

    header = f"""
<div class="ph">
  <div>
    <h1>Reporte Semanal de Obra</h1>
    <div class="sub">{proj_names}</div>
  </div>
  <div class="ph-meta">
    <div><strong>{'Rango' if is_range else 'Semana'}:</strong> {week_lbl}</div>
    <div><strong>Fecha de corte:</strong> {_fmt(ref)}/{ref.year}</div>
  </div>
</div>"""

    pdf_btn  = """<div class="no-print" style="display:flex;gap:8px;margin-bottom:12px;align-items:center">
  <button class="pdf-btn" style="margin-bottom:0" onclick="window.print()">🖨️ Imprimir / Guardar como PDF</button>
  <button class="pdf-btn" style="margin-bottom:0;background:#f8fafc;color:#475569;border:1px solid #e2e8f0"
          id="sig-toggle-btn" onclick="toggleSigSection()">✍️ Habilitar firmas</button>
</div>"""
    cto_html = _cto_banner(all_cto, projects)
    kpis_html= _kpis(global_kpis)
    legend   = _legend(str(ref))
    filt     = _filter_bar(all_names)

    # Secciones por proyecto
    sections = []
    col_offset = 0
    for pidx, data in enumerate(projects):
        sections.append(_project_block(data, pidx, col_offset, len(projects) > 1))
        col_offset += len(data["towers"])

    sigs = _signatures_section()

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Chronos — Reportes de Obra</title>
{_css()}
</head>
<body>
{header}
{pdf_btn}
{cto_html}
{kpis_html}
{legend}
{filt}
{"".join(sections)}
{sigs}
{_scripts(all_names, is_range)}
</body>
</html>"""


# ── CTO Banner ────────────────────────────────────────────────────────────────

def _cto_banner(all_cto, projects):
    if not all_cto: return ""
    tower_color_map = {}
    offset = 0
    for data in projects:
        for tw in data["towers"]:
            tower_color_map[tw["id"]] = _tc(offset)["border"]
            offset += 1

    by_tower = {}
    for c in all_cto:
        key = (c["tower"], c.get("project",""))
        by_tower.setdefault(key, []).append(c)

    cards = ""
    cidx  = 0
    for (tower_id, proj_name), items in by_tower.items():
        color    = tower_color_map.get(tower_id, "#6366f1")
        subtitle = (f'<div style="font-size:8.5px;color:#94a3b8;margin-top:1px">{proj_name}</div>'
                    if len(projects) > 1 else "")
        rows_html = ""
        for item in items:
            diff = item["days_from_reference"]
            if diff > 0:   diff_txt, dc = f"en {diff}d", "#6d28d9"
            elif diff == 0: diff_txt, dc = "Hoy", "#dc2626"
            else:           diff_txt, dc = f"hace {-diff}d", "#dc2626"
            rows_html += f"""
        <div class="ci">
          <div class="cl">{item['label']}</div>
          <div class="cd">{_fmt(item['date'])}</div>
          <div class="cdiff" style="color:{dc}">{diff_txt}</div>
        </div>"""
        uid = f"cto_{cidx}"
        cards += f"""
    <div class="cto-card">
      <div class="cto-tw" style="color:{color}">{tower_id}</div>
      {subtitle}
      <div class="cto-row">{rows_html}</div>
      <button class="toggle-link" onclick="toggleCollapsible('{uid}',this,'＋ Comentario','－ Ocultar')">＋ Comentario</button>
      <div class="collapsible" id="{uid}">
        <textarea placeholder="Comentario CTO..."></textarea>
      </div>
    </div>"""
        cidx += 1

    return f"""
<div class="cto-banner">
  <h3>🏛 Certificados Técnicos de Ocupación (CTO)</h3>
  <div class="cto-scroll">{cards}</div>
</div>"""


# ── KPIs ─────────────────────────────────────────────────────────────────────

def _kpis(kpis):
    return f"""
<div class="kpi-row">
  <div class="kpi"><div class="kpi-lbl">Programadas esta semana</div>
    <div class="kpi-val v-blue">{kpis['starting']}</div></div>
  <div class="kpi"><div class="kpi-lbl">Con atraso (c/progreso)</div>
    <div class="kpi-val v-red">{kpis['delayed']}</div></div>
  <div class="kpi"><div class="kpi-lbl">En progreso</div>
    <div class="kpi-val v-amb">{kpis['in_progress']}</div></div>
  <div class="kpi"><div class="kpi-lbl">Completadas</div>
    <div class="kpi-val v-grn">{kpis['completed']}</div></div>
</div>"""


# ── Legend ────────────────────────────────────────────────────────────────────

def _legend(today_str):
    d = date.fromisoformat(today_str)
    days_es = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
    lbl = f"{days_es[d.weekday()]} {d.day}"
    return f"""
<div class="legend">
  <div class="li"><div class="ld" style="background:#dc2626"></div>Atrasada (con progreso)</div>
  <div class="li"><div class="ld" style="background:#b45309"></div>En progreso con atraso</div>
  <div class="li"><div class="ld" style="background:#1d4ed8"></div>Programada</div>
  <div class="li"><div class="ld" style="background:#15803d"></div>Completada</div>
  <div class="li"><div class="ld" style="background:#475569"></div>Pendiente</div>
  <div class="l-note no-print">★ Hoy = {lbl} {d.year}</div>
</div>"""


# ── Filter bar ────────────────────────────────────────────────────────────────

def _filter_bar(all_names):
    return """
<div class="filter-wrap no-print">
  <input type="text" id="global-filter"
         oninput="onFilterInput(this)"
         onkeydown="onFilterKey(event)"
         placeholder="🔍  Filtrar actividades por nombre..."
         autocomplete="off">
  <div class="ac-dropdown" id="ac-dropdown"></div>
</div>"""


# ── Project block ─────────────────────────────────────────────────────────────

def _project_block(data, pidx, col_offset, show_title):
    title = f'<div class="proj-hdr">📁 {data["project_name"]}</div>' if show_title else ""
    gantt_cols = data["gantt_cols"]
    gantt_meta = data["gantt_meta"]
    today_str  = str(data["reference_date"])
    is_range   = data.get("is_range", False)
    col_w      = gantt_meta["col_width"]

    parts = []
    for i, tw in enumerate(data["towers"]):
        if i > 0: parts.append('<hr class="sep">')
        parts.append(_tower_section(tw, col_offset + i, gantt_cols, gantt_meta,
                                    today_str, is_range, col_w))

    return f'<div class="proj-block">{title}{"".join(parts)}</div>'


# ── Tower section ─────────────────────────────────────────────────────────────

def _tower_section(tower, idx, gantt_cols, gantt_meta, today_str, is_range, col_w):
    color  = _tc(idx)
    n_del  = sum(1 for t in tower["tasks"] if t["category"] == "delayed")
    n_st   = sum(1 for t in tower["tasks"] if t["category"] == "starting")
    alert  = f' &nbsp;·&nbsp;<span class="alert">{n_del} con atraso</span>' if n_del else ""
    tw_id  = f"tw_{idx}"

    day_ths = "".join(
        f'<th class="dc{"  today-th" if gantt_meta["scale"]=="day" and str(c["col_start"])==today_str else ""}" '
        f'style="width:{col_w}px;min-width:{col_w}px">'
        f'{c["label"]}</th>'
        for c in gantt_cols
    )

    body = _table_body(tower["groups"], gantt_cols, gantt_meta, today_str, is_range, idx)

    return f"""
<div class="tw-wrap" id="{tw_id}">
  <div class="tw-hdr" style="background:{color['bg']};border-left:4px solid {color['border']};border-radius:6px"
       onclick="toggleTower('{tw_id}')">
    <span class="tw-chevron" id="{tw_id}-chev">▼</span>
    <span class="tw-name">{tower['label']}</span>
    <span class="tw-stats no-print">{n_st} programadas{alert}</span>
  </div>
  <div class="tw-body" id="{tw_id}-body">
    <div class="gantt-wrap">
      <table>
        <thead><tr>
          <th style="min-width:175px">Actividad</th>
          <th style="min-width:105px">Estado</th>
          <th style="text-align:center">Atraso</th>
          <th style="text-align:center;white-space:nowrap">Ini.</th>
          <th style="text-align:center;white-space:nowrap">Fin</th>
          {day_ths}
          <th class="dep-th" title="Dependencias">🔗</th>
          <th class="comment-th" title="Comentarios">💬</th>
        </tr></thead>
        <tbody>{body}</tbody>
      </table>
    </div>
  </div>
</div>"""


# ── Table body ────────────────────────────────────────────────────────────────

def _table_body(groups, gantt_cols, gantt_meta, today_str, is_range, tw_idx):
    rows = []
    scale = gantt_meta["scale"]
    # Desplegable interno solo en rango con escala >= semana
    inner_collapsible = is_range and scale != "day"

    for gi, (crumb_key, tasks) in enumerate(groups.items()):
        parts      = crumb_key.split(" › ")
        crumb_html = '<span class="cs">›</span>'.join(f"<span>{p}</span>" for p in parts)
        n_cols     = 7 + len(gantt_cols)
        gid        = f"g_{tw_idx}_{gi}"

        if inner_collapsible:
            chev = '<span class="gr-chevron">▼</span>'
            rows.append(
                f'<tr class="gr collapsible-group" id="{gid}" '
                f'onclick="toggleGroup(\'{gid}\')">'
                f'<td colspan="{n_cols}">{chev}{crumb_html}</td></tr>'
            )
        else:
            rows.append(
                f'<tr class="gr" id="{gid}">'
                f'<td colspan="{n_cols}">{crumb_html}</td></tr>'
            )

        for ti, t in enumerate(tasks):
            task_id    = f"t_{tw_idx}_{gi}_{ti}"
            comment_id = f"cm_{tw_idx}_{gi}_{ti}"
            rows.append(_task_row(t, gantt_cols, gantt_meta, today_str, gid,
                                  task_id, comment_id))
            rows.append(_comment_row(comment_id, len(gantt_cols)))

    return "\n".join(rows)


# ── Task row ──────────────────────────────────────────────────────────────────

def _task_row(task, gantt_cols, gantt_meta, today_str, gid, task_id, comment_id):
    scale = gantt_meta["scale"]
    col_w = gantt_meta["col_width"]

    # Bar variant
    if task["state"] == "completed":                              bv = "bv-grn"
    elif task["category"] == "delayed" and task["progress"] > 0: bv = "bv-red"
    elif task["delay_str"] != "—" and task["progress"] > 0:      bv = "bv-amb"
    elif task["delay_str"] != "—":                                bv = "bv-sl"
    else:                                                         bv = "bv-blue"

    # Pill
    if task["state"] == "completed":
        pill = '<span class="pill p-grn">✓ Completada</span>'
    elif task["category"] == "delayed" and task["progress"] > 0:
        pill = '<span class="pill p-red">Atrasada · en progreso</span>'
    elif task["delay_str"] != "—" and task["progress"] > 0:
        pill = '<span class="pill p-amb">En progreso</span>'
    elif task["delay_str"] != "—":
        pill = '<span class="pill p-sl">Pendiente</span>'
    else:
        pill = '<span class="pill p-blue">Programada</span>'

    ds = task["delay_str"]
    delay_cell = (f'<span class="dl">{ds}</span>'
                  if ds != "—" else '<span class="dl none">—</span>')

    # Gantt bars
    ts  = task["start"]
    te  = task["end"]
    pct = 100 if task["state"] == "completed" else task["progress"]
    lbl = f"{pct}%" if pct > 0 else "·"
    cells = []

    for ci, col in enumerate(gantt_cols):
        cs = col["col_start"]
        ce = col["col_end"]
        is_today_col = scale == "day" and str(cs) == today_str
        td_cls = " tday" if is_today_col else ""

        # Overlap: task overlaps this column?
        overlaps = ts <= ce and te >= cs
        if not overlaps:
            cells.append(f'<td class="dc{td_cls}" style="width:{col_w}px"></td>')
            continue

        # Find span: how many consecutive columns this bar covers starting here
        if ci == 0 or not (gantt_cols[ci-1]["col_end"] >= ts):
            # First column of the bar
            span = 1
            for cj in range(ci + 1, len(gantt_cols)):
                if ts <= gantt_cols[cj]["col_end"] and te >= gantt_cols[cj]["col_start"]:
                    span += 1
                else:
                    break
            # Ensure minimum visibility: span >= 1 always
            span = max(1, span)
            bar_lbl = lbl if span > 1 or col_w >= 48 else ("·" if pct == 0 else "")
            cells.append(
                f'<td class="dc{td_cls}" colspan="{span}" style="padding:2px 2px;width:{col_w*span}px">'
                f'<div class="bar {bv}" style="min-width:{max(8,col_w*span-4)}px">'
                f'<div class="bbg"></div>'
                f'<div class="bpg" style="width:{pct}%"></div>'
                f'<div class="btx">{bar_lbl}</div>'
                f'</div></td>'
            )
        # Subsequent columns handled by colspan — skip
        # (We detect "already covered" by checking if previous col ended >= ts)

    gantt = "".join(cells)
    sl = f"{ts.month:02d}/{ts.day:02d}"
    el = f"{te.month:02d}/{te.day:02d}"
    name_safe = task['name'].replace('"', '&quot;')

    import json as _json
    preds    = task.get('predecessors', [])
    succs    = task.get('successors',   [])
    has_deps = bool(preds or succs)
    dep_icon = '\U0001f517' if has_deps else '\xb7'
    dep_clr  = 'color:var(--pur)' if has_deps else 'color:#e2e8f0'

    tname    = task["name"]
    tname_lc = tname.lower()

    # Encode as base64 to avoid any quoting issues with special chars in names
    import base64 as _b64
    preds_b64 = _b64.b64encode(_json.dumps(preds, ensure_ascii=False).encode()).decode()
    succs_b64 = _b64.b64encode(_json.dumps(succs, ensure_ascii=False).encode()).decode()
    dep_cell = (
        '<td class="dep-td">'
        '<button class="dep-btn" style="' + dep_clr + '" '
        'data-preds="' + preds_b64 + '" '
        'data-succs="' + succs_b64 + '" '
        'onclick="toggleDepPopover(this)" '
        'title="Ver dependencias">' + dep_icon + '</button>'
        '</td>'
    )
    mono = "font-family:'JetBrains Mono',monospace;font-size:9px;color:#475569;text-align:center"
    return (
        '<tr class="tr" id="' + task_id + '" data-name="' + tname_lc + '" data-grp="' + gid + '">'
        '<td><div class="tn">' + tname + '</div></td>'
        + dep_cell +
        '<td>' + pill + '</td>'
        '<td style="text-align:center">' + delay_cell + '</td>'
        '<td style="' + mono + '">' + sl + '</td>'
        '<td style="' + mono + '">' + el + '</td>'
        + gantt +
        '<td class="comment-td">'
        '<button class="cmt-btn" id="btn_' + comment_id + '" '
        'onclick="toggleComment(\'' + comment_id + '\')" title="Agregar comentario">\U0001f4ac</button>'
        '</td>'
        '</tr>'
    )



def _comment_row(comment_id, n_day_cols):
    n_cols = 7 + n_day_cols
    return (
        f'<tr class="comment-row hidden" id="{comment_id}">'
        f'<td colspan="{n_cols}">'
        f'<textarea placeholder="Comentario / compromiso..."></textarea>'
        f'</td></tr>'
    )


# ── Signatures section ────────────────────────────────────────────────────────

def _signatures_section():
    return """
<div class="sig-section no-print" id="sig-section" style="display:none">
  <div class="sig-title">✍️ Firmas</div>
  <table class="sig-table" id="sig-table">
    <thead>
      <tr>
        <th style="width:45%">Encargado</th>
        <th>Firma</th>
      </tr>
    </thead>
    <tbody id="sig-tbody">
      <tr>
        <td class="name-cell"><input type="text" placeholder="Nombre del encargado"></td>
        <td class="sig-cell"></td>
      </tr>
    </tbody>
    <tfoot>
      <tr class="sig-add-row">
        <td colspan="2">
          <button class="add-sig-btn" onclick="addSigRow()">＋ Agregar encargado</button>
        </td>
      </tr>
    </tfoot>
  </table>
</div>
<!-- Versión print de firmas -->
<div class="sig-section" id="sig-section-print" style="display:none">
  <div class="sig-title">✍️ Firmas</div>
  <table class="sig-table" id="sig-table-print">
    <thead>
      <tr><th style="width:45%">Encargado</th><th>Firma</th></tr>
    </thead>
    <tbody id="sig-tbody-print"></tbody>
  </table>
</div>"""


# ── Scripts ───────────────────────────────────────────────────────────────────

def _scripts(all_names, is_range) -> str:
    names_json = str(all_names).replace("'", '"')
    return f"""<script>
const ALL_NAMES = {names_json};
let acIndex = -1;

// ── Auto-grow textareas ────────────────────────────────────────────────────
function autoGrow(el) {{
  el.style.height = 'auto';
  el.style.height = el.scrollHeight + 'px';
}}
document.addEventListener('DOMContentLoaded', () => {{
  document.querySelectorAll('textarea').forEach(ta => {{
    ta.addEventListener('input', () => autoGrow(ta));
  }});
  // Observer para nuevos textareas (comentarios que se abren)
  new MutationObserver(muts => {{
    muts.forEach(m => m.addedNodes.forEach(n => {{
      if (n.nodeType===1) n.querySelectorAll && n.querySelectorAll('textarea')
        .forEach(ta => ta.addEventListener('input', () => autoGrow(ta)));
    }}));
  }}).observe(document.body, {{childList:true, subtree:true}});
}});

// ── Tower collapse ────────────────────────────────────────────────────────
function toggleTower(twId) {{
  const body = document.getElementById(twId + '-body');
  const chev = document.getElementById(twId + '-chev');
  const open = body.style.display !== 'none';
  body.style.display = open ? 'none' : '';
  chev.classList.toggle('collapsed', open);
}}

// ── Group collapse (solo en rango) ────────────────────────────────────────
function toggleGroup(gid) {{
  const grRow = document.getElementById(gid);
  const tasks = document.querySelectorAll(`tr.tr[data-grp="${{gid}}"]`);
  const comments = document.querySelectorAll(`tr.comment-row[id^="cm_"]`);
  const isCollapsed = grRow.classList.contains('collapsed-grp');
  grRow.classList.toggle('collapsed-grp', !isCollapsed);
  tasks.forEach(t => {{
    t.style.display = isCollapsed ? '' : 'none';
    // también ocultar su fila de comentario
    const cid = t.id.replace('t_','cm_');
    const cr  = document.getElementById(cid);
    if (cr) cr.style.display = isCollapsed ? '' : 'none';
  }});
}}

// ── Comment toggle ────────────────────────────────────────────────────────
function toggleComment(cid) {{
  const row = document.getElementById(cid);
  const btn = document.getElementById('btn_' + cid);
  const hidden = row.classList.contains('hidden');
  row.classList.toggle('hidden', !hidden);
  btn.classList.toggle('active', hidden);
  if (hidden) {{
    const ta = row.querySelector('textarea');
    ta.focus();
    autoGrow(ta);
  }}
}}

// ── Generic collapsible (CTO) ─────────────────────────────────────────────
function toggleCollapsible(uid, btn, openTxt, closeTxt) {{
  const box  = document.getElementById(uid);
  const open = box.style.display === 'block';
  box.style.display = open ? 'none' : 'block';
  btn.textContent   = open ? openTxt : closeTxt;
  if (!open) {{ const ta = box.querySelector('textarea'); ta.focus(); autoGrow(ta); }}
}}

// ── Filter + Autocomplete ─────────────────────────────────────────────────
const dd = document.getElementById('ac-dropdown');

function onFilterInput(input) {{
  const q = input.value.toLowerCase().trim();
  applyFilter(q);
  showAC(input.value.trim());
}}

function applyFilter(q) {{
  // 1. Mostrar/ocultar tareas
  document.querySelectorAll('tr.tr').forEach(row => {{
    const match = !q || (row.getAttribute('data-name') || '').includes(q);
    row.classList.toggle('ht', !match);
    const cid = row.id.replace('t_','cm_');
    const cr  = document.getElementById(cid);
    if (cr && !match) cr.style.display = 'none';
    else if (cr && match && !cr.classList.contains('hidden')) cr.style.display = '';
  }});
  // 2. Ocultar agrupadores internos sin tareas visibles
  document.querySelectorAll('tr.gr').forEach(grp => {{
    if (!grp.id) return;
    const any = Array.from(document.querySelectorAll(`tr.tr[data-grp="${{grp.id}}"]`))
                     .some(r => !r.classList.contains('ht'));
    grp.classList.toggle('hg', !any);
  }});
  // 3. Ocultar torres sin tareas visibles
  document.querySelectorAll('.tw-wrap').forEach(tw => {{
    const anyVisible = Array.from(tw.querySelectorAll('tr.tr'))
                           .some(r => !r.classList.contains('ht'));
    tw.style.display = anyVisible ? '' : 'none';
  }});
  // 4. Ocultar bloques de proyecto sin torres visibles
  document.querySelectorAll('.proj-block').forEach(pb => {{
    const anyVisible = Array.from(pb.querySelectorAll('.tw-wrap'))
                           .some(tw => tw.style.display !== 'none');
    pb.style.display = anyVisible ? '' : 'none';
  }});
}}

function showAC(query) {{
  if (!query) {{ dd.style.display='none'; return; }}
  const q = query.toLowerCase();
  const matches = ALL_NAMES.filter(n => n.toLowerCase().includes(q)).slice(0, 12);
  if (!matches.length) {{ dd.style.display='none'; return; }}
  acIndex = -1;
  dd.innerHTML = matches.map((n,i) => {{
    const hi = n.replace(new RegExp(query.replace(/[.*+?^${{}}()|[\\]\\\\]/g,'\\\\$&'),'gi'),
                         m => `<mark>${{m}}</mark>`);
    return `<div class="ac-item" data-idx="${{i}}" onmousedown="selectAC('${{n.replace(/'/g,"\\\\'")}}')">
              ${{hi}}</div>`;
  }}).join('');
  dd.style.display = 'block';
}}

function selectAC(name) {{
  const inp = document.getElementById('global-filter');
  inp.value = name;
  dd.style.display = 'none';
  applyFilter(name.toLowerCase());
}}

function onFilterKey(e) {{
  const items = dd.querySelectorAll('.ac-item');
  if (!items.length) return;
  if (e.key === 'ArrowDown') {{ acIndex=Math.min(acIndex+1,items.length-1); highlightAC(items); e.preventDefault(); }}
  else if (e.key === 'ArrowUp') {{ acIndex=Math.max(acIndex-1,0); highlightAC(items); e.preventDefault(); }}
  else if (e.key === 'Enter' && acIndex >= 0) {{ items[acIndex].dispatchEvent(new MouseEvent('mousedown')); e.preventDefault(); }}
  else if (e.key === 'Escape') {{ dd.style.display='none'; }}
}}

function highlightAC(items) {{
  items.forEach((el,i) => el.classList.toggle('active', i===acIndex));
  if (acIndex >= 0) items[acIndex].scrollIntoView({{block:'nearest'}});
}}

document.addEventListener('click', e => {{
  if (!e.target.closest('.filter-wrap')) dd.style.display='none';
  if (!e.target.closest('.dep-btn') && !e.target.closest('.dep-popover')) {{
    document.querySelectorAll('.dep-popover.visible').forEach(p => p.classList.remove('visible'));
  }}
}});

// ── Dependency popover ────────────────────────────────────────────────────
const _popover = (() => {{
  const el = document.createElement('div');
  el.className = 'dep-popover';
  document.body.appendChild(el);
  return el;
}})();

function toggleDepPopover(btn) {{
  const preds = JSON.parse(atob(btn.getAttribute('data-preds') || 'W10='));
  const succs = JSON.parse(atob(btn.getAttribute('data-succs') || 'W10='));
  const isVisible = btn.classList.contains('active');

  // Close any open popover
  document.querySelectorAll('.dep-btn.active').forEach(b => b.classList.remove('active'));
  _popover.classList.remove('visible');

  if (isVisible) return;

  // Build content
  let html = '<div class="dep-popover-title">🔗 Dependencias</div>';
  html += '<div class="dep-section">';
  html += '<div class="dep-label">⬅ Predecesoras</div>';
  if (preds.length) {{
    preds.forEach(p => html += `<div class="dep-item"><span class="dep-arrow">←</span><span>${{p}}</span></div>`);
  }} else {{
    html += '<div class="dep-none">Sin predecesoras</div>';
  }}
  html += '</div><div class="dep-section">';
  html += '<div class="dep-label">➡ Sucesoras</div>';
  if (succs.length) {{
    succs.forEach(s => html += `<div class="dep-item"><span class="dep-arrow">→</span><span>${{s}}</span></div>`);
  }} else {{
    html += '<div class="dep-none">Sin sucesoras</div>';
  }}
  html += '</div>';
  _popover.innerHTML = html;

  // Position near button
  const rect = btn.getBoundingClientRect();
  const top  = rect.bottom + window.scrollY + 4;
  const left = Math.min(rect.left + window.scrollX, window.innerWidth - 330);
  _popover.style.top  = top + 'px';
  _popover.style.left = left + 'px';
  _popover.classList.add('visible');
  btn.classList.add('active');
}}

// ── Signatures toggle ────────────────────────────────────────────────────
function toggleSigSection() {{
  const sec = document.getElementById('sig-section');
  const btn = document.getElementById('sig-toggle-btn');
  const open = sec.style.display !== 'none';
  sec.style.display = open ? 'none' : 'block';
  btn.textContent   = open ? '✍️ Habilitar firmas' : '✍️ Ocultar firmas';
  btn.style.background = open ? '#f8fafc' : '#f0fdf4';
  btn.style.color      = open ? '#475569'  : '#15803d';
  btn.style.borderColor= open ? '#e2e8f0'  : '#bbf7d0';
}}

// ── Signatures rows ───────────────────────────────────────────────────────
function addSigRow() {{
  const tbody = document.getElementById('sig-tbody');
  const tr = document.createElement('tr');
  tr.innerHTML = `<td class="name-cell"><input type="text" placeholder="Nombre del encargado"></td>
                  <td class="sig-cell"></td>`;
  tbody.appendChild(tr);
}}

// ── Before print: sync sig table for print version ────────────────────────
window.addEventListener('beforeprint', () => {{
  const printBody = document.getElementById('sig-tbody-print');
  const liveBody  = document.getElementById('sig-tbody');
  if (!printBody || !liveBody) return;
  printBody.innerHTML = '';
  liveBody.querySelectorAll('tr').forEach(row => {{
    const inp   = row.querySelector('input');
    const name  = inp ? inp.value : '';
    const tr    = document.createElement('tr');
    tr.innerHTML = `<td style="padding:6px 8px;border-bottom:1px solid #e2e8f0">${{name}}</td>
                    <td class="sig-cell" style="border-left:1px solid #e2e8f0;height:60px"></td>`;
    printBody.appendChild(tr);
  }});
  const sigPrint = document.getElementById('sig-section-print');
  const sigLive  = document.getElementById('sig-section');
  if (sigLive && sigLive.style.display !== 'none' && sigPrint) {{
    sigPrint.style.display = 'block';
  }}
}});
window.addEventListener('afterprint', () => {{
  const sigPrint = document.getElementById('sig-section-print');
  if (sigPrint) sigPrint.style.display = 'none';
}});
</script>"""


# ── Test ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '/home/claude')
    from processor_v4 import process_project
    path = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/uploads/Projecto.txt'
    data = process_project(path, reference_date=date(2026, 2, 23))
    html = render_dashboard([data])
    out  = '/mnt/user-data/outputs/dashboard_v4.html'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"OK → {out}  ({len(html):,} chars)")

"""
renderer.py  v3
===============
- Encabezado unificado para N proyectos (KPIs sumados, CTO global, filtro único)
- Botón PDF dentro del HTML (persiste comentarios)
- Textarea de una línea en pantalla, se expande en print
- Completadas → delay siempre '—'
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
_DAYS_ES = ["Lun","Mar","Mié","Jue","Vie","Sáb"]

def _tc(idx):  return _TOWER_PALETTE[idx % len(_TOWER_PALETTE)]
def _fmt(d):   return f"{d.day:02d}/{_MONTHS[d.month]}"
def _day_cols(week_start):
    return [(str(week_start + timedelta(days=i)),
             f"{_DAYS_ES[i]} {(week_start + timedelta(days=i)).day}")
            for i in range(6)]


# ── CSS ───────────────────────────────────────────────────────────────────────
_CSS = """<style>
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
     font-size:12px;padding:22px 26px;max-width:1200px;margin:0 auto}

/* ── HEADER ── */
.ph{display:flex;justify-content:space-between;align-items:flex-start;
    padding-bottom:12px;border-bottom:2.5px solid var(--txt);margin-bottom:16px}
.ph h1{font-size:20px;font-weight:700;letter-spacing:-.3px}
.ph .sub{font-size:11px;color:var(--mut);margin-top:3px}
.ph-meta{text-align:right;font-size:10.5px;color:var(--mut);
          font-family:'JetBrains Mono',monospace;line-height:1.7}
.ph-meta strong{color:var(--txt)}

/* ── PDF BUTTON ── */
.pdf-btn{
  display:inline-flex;align-items:center;gap:6px;
  background:#1d4ed8;color:#fff;border:none;border-radius:6px;
  padding:7px 16px;font-size:12px;font-weight:600;cursor:pointer;
  font-family:'Inter',sans-serif;margin-bottom:14px;
}
.pdf-btn:hover{background:#1e40af}

/* ── CTO BANNER ── */
.cto-banner{background:#faf5ff;border:1px solid #ddd6fe;
            border-left:4px solid var(--pur);border-radius:7px;
            padding:11px 15px;margin-bottom:14px}
.cto-banner h3{font-size:10px;font-weight:700;text-transform:uppercase;
               letter-spacing:.7px;color:var(--pur);margin-bottom:9px}
.cto-scroll{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px}
.cto-scroll::-webkit-scrollbar{height:4px}
.cto-scroll::-webkit-scrollbar-thumb{background:#c4b5fd;border-radius:2px}
.cto-card{background:#fff;border:1px solid #e9d5ff;border-radius:6px;
          padding:8px 11px;min-width:155px;flex-shrink:0}
.cto-tw{font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}
.cto-row{display:flex;gap:11px;margin-top:5px}
.ci .cl{font-size:9.5px;color:var(--mut)}
.ci .cd{font-family:'JetBrains Mono',monospace;font-size:11px;
         font-weight:600;color:var(--txt);margin-top:1px}
.ci .cdiff{font-size:9px;margin-top:1px}
.cto-toggle{font-size:9px;color:var(--pur);cursor:pointer;
             margin-top:6px;display:inline-block;user-select:none}
.cto-cbox{display:none;margin-top:5px}
.cto-cbox textarea{
  width:100%;height:24px;min-height:24px;resize:none;
  font-size:10px;font-family:'Inter',sans-serif;
  border:1px solid #ddd6fe;border-radius:4px;
  padding:3px 6px;color:var(--txt);background:#faf5ff;
  outline:none;overflow:hidden;
}
.cto-cbox textarea:focus{border-color:var(--pur);overflow:auto}

/* ── KPI ── */
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:14px}
.kpi{background:var(--sl-bg);border:1px solid var(--bor);border-radius:7px;padding:10px 13px}
.kpi-lbl{font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.6px;color:var(--mut)}
.kpi-val{font-size:22px;font-weight:700;margin-top:2px;line-height:1.1}
.v-blue{color:var(--blue)} .v-red{color:var(--red)}
.v-amb{color:var(--amb)}   .v-grn{color:var(--grn)}

/* ── LEGEND ── */
.legend{display:flex;gap:13px;flex-wrap:wrap;align-items:center;
        padding:7px 12px;background:var(--sl-bg);border:1px solid var(--bor);
        border-radius:6px;font-size:10px;color:var(--mut);margin-bottom:12px}
.li{display:flex;align-items:center;gap:4px}
.ld{width:9px;height:9px;border-radius:2px;flex-shrink:0}
.l-note{margin-left:auto;font-size:9.5px;color:var(--blue);font-family:'JetBrains Mono',monospace}

/* ── FILTER ── */
.filter-wrap{margin-bottom:12px}
.filter-wrap input{
  width:100%;padding:7px 12px;font-size:12px;font-family:'Inter',sans-serif;
  border:1px solid var(--bor);border-radius:6px;outline:none;color:var(--txt);
}
.filter-wrap input:focus{border-color:var(--blue)}
.filter-wrap input::placeholder{color:#94a3b8}

/* ── PROJECT SECTION ── */
.proj-block{margin-bottom:28px}
.proj-hdr{font-size:13px;font-weight:700;color:var(--txt);
           padding:6px 0;border-bottom:1.5px solid var(--bor);margin-bottom:12px}

/* ── TOWER ── */
.tw-wrap{margin-bottom:18px}
.tw-hdr{display:flex;align-items:center;gap:10px;padding:7px 13px;border-radius:6px 6px 0 0}
.tw-name{font-size:12px;font-weight:700}
.tw-stats{margin-left:auto;font-size:10px;color:var(--mut)}
.tw-stats .alert{color:var(--red);font-weight:600}

/* ── TABLE ── */
.gantt-wrap{border:1px solid var(--bor);border-top:none;border-radius:0 0 6px 6px;overflow:hidden}
table{width:100%;border-collapse:collapse;font-size:10.5px}
thead tr{background:#f8fafc}
th{padding:5px 7px;font-size:9px;font-weight:600;text-transform:uppercase;
   letter-spacing:.5px;color:var(--mut);text-align:left;
   border-bottom:1px solid var(--bor);white-space:nowrap}
th.dc{text-align:center;width:70px;min-width:56px}
th.today-th{color:var(--blue)}
th.comment-th{width:140px;min-width:140px}

/* GROUP ROW */
tr.gr td{padding:3px 8px;background:#f1f5f9;font-size:9.5px;font-weight:600;
          color:var(--sl);border-bottom:1px solid var(--bor);border-top:1px solid var(--bor)}
tr.gr .cs{color:#94a3b8;margin:0 3px}
tr.gr.hg{display:none}

/* TASK ROW */
tr.tr td{padding:4px 7px;border-bottom:1px solid #f1f5f9;vertical-align:middle}
tr.tr:last-child td{border-bottom:none}
tr.tr:hover td{background:#fafafa}
tr.tr.ht{display:none}
.tn{font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:195px}

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
td.dc{padding:2px 2px;width:70px;min-width:56px}
td.tday{background:#eff6ff!important}
.bar{position:relative;height:17px;border-radius:3px;overflow:hidden;border:1px solid transparent}
.bbg{position:absolute;inset:0}
.bpg{position:absolute;left:0;top:0;bottom:0}
.btx{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
     font-size:8.5px;font-weight:700;font-family:'JetBrains Mono',monospace}
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

/* COMMENT CELL */
td.comment-td{width:140px;min-width:140px;padding:3px 4px;vertical-align:middle}
td.comment-td textarea{
  width:132px;height:22px;min-height:22px;
  resize:none;overflow:hidden;
  font-size:10px;font-family:'Inter',sans-serif;
  border:1px solid var(--bor);border-radius:3px;
  padding:3px 5px;color:var(--txt);background:#fafafa;outline:none;
}
td.comment-td textarea:focus{border-color:var(--blue);background:#fff;overflow:auto}

hr.sep{border:none;border-top:1px solid var(--bor);margin:12px 0}

/* ── PRINT ── */
@media print{
  .no-print{display:none!important}
  body{padding:8px;font-size:9px;max-width:100%}
  .tw-wrap{page-break-inside:avoid}
  .proj-block + .proj-block{page-break-before:always}
  /* Expandir textareas en PDF */
  td.comment-td textarea{
    height:auto!important;min-height:22px;
    overflow:visible!important;white-space:pre-wrap;word-break:break-word;
    border:1px solid #ccc;background:#fff;
  }
  .cto-cbox{display:block!important}
  .cto-cbox textarea{
    height:auto!important;min-height:22px;
    overflow:visible!important;white-space:pre-wrap;
    border:1px solid #ccc;background:#fff;
  }
  .cto-toggle{display:none!important}
  .cto-scroll{overflow:visible;flex-wrap:wrap}
  .bar{-webkit-print-color-adjust:exact;print-color-adjust:exact}
}
</style>"""


# ── Render principal ──────────────────────────────────────────────────────────

def render_dashboard(projects) -> str:
    if isinstance(projects, dict):
        projects = [projects]

    # ── Datos globales ──
    ref        = projects[0]["reference_date"]
    week_start = projects[0]["week_start"]
    week_end   = projects[0]["week_end"]
    today_str  = str(ref)
    day_cols   = _day_cols(week_start)

    # KPIs sumados
    global_kpis = {"starting":0,"delayed":0,"in_progress":0,"completed":0}
    for data in projects:
        for k in global_kpis:
            global_kpis[k] += data["kpis"][k]

    # CTO global (todos los proyectos, ordenados por fecha)
    all_cto = []
    for data in projects:
        for c in data["cto_items"]:
            days_diff = (c["date"] - ref).days
            all_cto.append({**c, "days_from_reference": days_diff,
                             "project": data["project_name"]})
    all_cto.sort(key=lambda x: x["date"])

    # Nombres de proyectos para el header
    proj_names = " · ".join(d["project_name"] for d in projects)
    months_str = f"{week_start.day} {_MONTHS[week_start.month]} – {week_end.day} {_MONTHS[week_end.month]} {week_end.year}"

    header  = f"""
<div class="ph">
  <div>
    <h1>Reporte Semanal de Obra</h1>
    <div class="sub">{proj_names}</div>
  </div>
  <div class="ph-meta">
    <div><strong>Semana:</strong> {months_str}</div>
    <div><strong>Fecha de corte:</strong> {_fmt(ref)}/{ref.year}</div>
  </div>
</div>"""

    pdf_btn = """
<button class="pdf-btn no-print" onclick="window.print()">
  🖨️ Imprimir / Guardar como PDF
</button>"""

    cto_html  = _cto_banner(all_cto, projects)
    kpis_html = _kpis(global_kpis)
    legend    = _legend(today_str)
    filt      = _filter_bar()

    # Sección por proyecto
    sections = []
    tower_color_offset = 0
    for pidx, data in enumerate(projects):
        show_proj_title = len(projects) > 1
        sections.append(
            _project_block(data, day_cols, today_str, tower_color_offset, show_proj_title)
        )
        tower_color_offset += len(data["towers"])

    body = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Chronos — Reportes de Obra</title>
{_CSS}
</head>
<body>
{header}
{pdf_btn}
{cto_html}
{kpis_html}
{legend}
{filt}
{body}
{_scripts()}
</body>
</html>"""


# ── CTO Banner (global) ───────────────────────────────────────────────────────

def _cto_banner(all_cto: list, projects: list) -> str:
    if not all_cto:
        return ""

    # Construir mapa torre → color usando offset global
    tower_color_map = {}
    offset = 0
    for data in projects:
        for tw in data["towers"]:
            tower_color_map[tw["id"]] = _tc(offset)["border"]
            offset += 1

    # Agrupar por (tower, project) preservando orden de fecha
    seen = {}
    for c in all_cto:
        key = (c["tower"], c.get("project",""))
        seen.setdefault(key, []).append(c)

    cards = ""
    card_idx = 0
    for (tower_id, proj_name), items in seen.items():
        color = tower_color_map.get(tower_id, "#6366f1")
        subtitle = f'<div style="font-size:8.5px;color:#94a3b8;margin-top:1px">{proj_name}</div>' if len(projects) > 1 else ""

        rows_html = ""
        for item in items:
            diff = item["days_from_reference"]
            if diff > 0:
                diff_txt, diff_col = f"en {diff}d", "#6d28d9"
            elif diff == 0:
                diff_txt, diff_col = "Hoy", "#dc2626"
            else:
                diff_txt, diff_col = f"hace {-diff}d", "#dc2626"
            rows_html += f"""
        <div class="ci">
          <div class="cl">{item['label']}</div>
          <div class="cd">{_fmt(item['date'])}</div>
          <div class="cdiff" style="color:{diff_col}">{diff_txt}</div>
        </div>"""

        uid = f"cto_{card_idx}"
        cards += f"""
    <div class="cto-card">
      <div class="cto-tw" style="color:{color}">{tower_id}</div>
      {subtitle}
      <div class="cto-row">{rows_html}</div>
      <div class="cto-toggle" onclick="toggleCto('{uid}')">＋ Comentario</div>
      <div class="cto-cbox" id="{uid}">
        <textarea placeholder="Comentario CTO..."></textarea>
      </div>
    </div>"""
        card_idx += 1

    return f"""
<div class="cto-banner">
  <h3>🏛 Certificados Técnicos de Ocupación (CTO)</h3>
  <div class="cto-scroll">{cards}</div>
</div>"""


# ── KPIs ─────────────────────────────────────────────────────────────────────

def _kpis(kpis: dict) -> str:
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

def _legend(today_str: str) -> str:
    d = date.fromisoformat(today_str)
    lbl = f"{_DAYS_ES[d.weekday()]} {d.day}"
    return f"""
<div class="legend">
  <div class="li"><div class="ld" style="background:#dc2626"></div>Atrasada (con progreso)</div>
  <div class="li"><div class="ld" style="background:#b45309"></div>En progreso con atraso</div>
  <div class="li"><div class="ld" style="background:#1d4ed8"></div>Programada esta semana</div>
  <div class="li"><div class="ld" style="background:#15803d"></div>Completada</div>
  <div class="li"><div class="ld" style="background:#475569"></div>Pendiente</div>
  <div class="l-note no-print">★ Hoy = {lbl} {d.year}</div>
</div>"""


# ── Filter bar ────────────────────────────────────────────────────────────────

def _filter_bar() -> str:
    return """
<div class="filter-wrap no-print">
  <input type="text" id="global-filter"
         onkeyup="filterTasks(this)"
         placeholder="🔍  Filtrar actividades por nombre...">
</div>"""


# ── Project block ─────────────────────────────────────────────────────────────

def _project_block(data, day_cols, today_str, color_offset, show_title):
    title = f'<div class="proj-hdr">📁 {data["project_name"]}</div>' if show_title else ""
    sections = []
    for i, tw in enumerate(data["towers"]):
        if i > 0:
            sections.append('<hr class="sep">')
        sections.append(_tower_section(tw, color_offset + i, day_cols, today_str))
    return f'<div class="proj-block">{title}{"".join(sections)}</div>'


# ── Tower section ─────────────────────────────────────────────────────────────

def _tower_section(tower, idx, day_cols, today_str):
    color  = _tc(idx)
    n_del  = sum(1 for t in tower["tasks"] if t["category"] == "delayed")
    n_st   = sum(1 for t in tower["tasks"] if t["category"] == "starting")
    alert  = f' &nbsp;·&nbsp;<span class="alert">{n_del} con atraso</span>' if n_del else ""

    day_ths = "".join(
        f'<th class="dc{"  today-th" if d==today_str else ""}">'
        f'{lbl}{"  ★" if d==today_str else ""}</th>'
        for d, lbl in day_cols
    )
    body = _table_body(tower["groups"], day_cols, today_str, idx)

    return f"""
<div class="tw-wrap">
  <div class="tw-hdr" style="background:{color['bg']};border-left:4px solid {color['border']}">
    <span class="tw-name">{tower['label']}</span>
    <span class="tw-stats">{n_st} programadas{alert}</span>
  </div>
  <div class="gantt-wrap">
    <table>
      <thead><tr>
        <th style="min-width:175px">Actividad</th>
        <th style="min-width:108px">Estado</th>
        <th style="text-align:center">Atraso</th>
        <th style="text-align:center">Ini.</th>
        <th style="text-align:center">Fin</th>
        {day_ths}
        <th class="comment-th">Comentario / Compromisos</th>
      </tr></thead>
      <tbody>{body}</tbody>
    </table>
  </div>
</div>"""


def _table_body(groups, day_cols, today_str, tw_idx):
    rows = []
    days = [d for d, _ in day_cols]
    for gi, (crumb_key, tasks) in enumerate(groups.items()):
        parts      = crumb_key.split(" › ")
        crumb_html = '<span class="cs">›</span>'.join(f"<span>{p}</span>" for p in parts)
        n_cols     = 6 + len(day_cols)
        gid        = f"g_{tw_idx}_{gi}"
        rows.append(
            f'<tr class="gr" id="{gid}">'
            f'<td colspan="{n_cols}">{crumb_html}</td></tr>'
        )
        for t in tasks:
            rows.append(_task_row(t, days, today_str, gid))
    return "\n".join(rows)


def _task_row(task, days, today_str, gid):
    # Bar variant
    if task["state"] == "completed":
        bv = "bv-grn"
    elif task["category"] == "delayed" and task["progress"] > 0:
        bv = "bv-red"
    elif task["delay_str"] != "—" and task["progress"] > 0:
        bv = "bv-amb"
    elif task["delay_str"] != "—":
        bv = "bv-sl"
    else:
        bv = "bv-blue"

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

    ts  = str(task["start"])
    te  = str(task["end"])
    pct = 100 if task["state"] == "completed" else task["progress"]
    lbl = f"{pct}%" if pct > 0 else "·"

    is_out = task["category"] == "delayed" and te < days[0]
    if is_out:
        gantt = (f'<td class="dc" colspan="{len(days)}" style="padding:2px 5px">'
                 f'<div class="bar {bv}"><div class="bbg"></div>'
                 f'<div class="bpg" style="width:{pct}%"></div>'
                 f'<div class="btx">Fuera de sem. · {pct}% · {ds}d</div>'
                 f'</div></td>')
    else:
        bar_s = max(ts, days[0])
        bar_e = min(te, days[-1])
        si    = days.index(bar_s) if bar_s in days else -1
        ei    = days.index(bar_e) if bar_e in days else -1
        cells, skip = [], -1
        for i, d in enumerate(days):
            if i < skip:
                continue
            itd = ' tday' if d == today_str else ''
            if si != -1 and ei != -1 and si <= i <= ei:
                if i == si:
                    span = ei - si + 1
                    cells.append(
                        f'<td class="dc{itd}" colspan="{span}" style="padding:2px 2px">'
                        f'<div class="bar {bv}"><div class="bbg"></div>'
                        f'<div class="bpg" style="width:{pct}%"></div>'
                        f'<div class="btx">{lbl}</div></div></td>'
                    )
                    skip = ei + 1
            else:
                cells.append(f'<td class="dc{itd}"></td>')
        gantt = "".join(cells)

    sl = f"{task['start'].month:02d}/{task['start'].day:02d}"
    el = f"{task['end'].month:02d}/{task['end'].day:02d}"
    name_safe = task['name'].replace('"', '&quot;')

    return (f'<tr class="tr" data-name="{task["name"].lower()}" data-grp="{gid}">'
            f'<td><div class="tn" title="{name_safe}">{task["name"]}</div></td>'
            f'<td>{pill}</td>'
            f'<td style="text-align:center">{delay_cell}</td>'
            f'<td style="font-family:\'JetBrains Mono\',monospace;font-size:9px;color:#475569;text-align:center">{sl}</td>'
            f'<td style="font-family:\'JetBrains Mono\',monospace;font-size:9px;color:#475569;text-align:center">{el}</td>'
            f'{gantt}'
            f'<td class="comment-td"><textarea placeholder="Comentario..."></textarea></td>'
            f'</tr>')


# ── Scripts ───────────────────────────────────────────────────────────────────

def _scripts() -> str:
    return """<script>
function filterTasks(input) {
  const q = input.value.toLowerCase().trim();
  document.querySelectorAll('tr.tr').forEach(row => {
    const match = !q || (row.getAttribute('data-name') || '').includes(q);
    row.classList.toggle('ht', !match);
  });
  document.querySelectorAll('tr.gr').forEach(grp => {
    const gid = grp.id;
    const any = Array.from(document.querySelectorAll(`tr.tr[data-grp="${gid}"]`))
                     .some(r => !r.classList.contains('ht'));
    grp.classList.toggle('hg', !any);
  });
}

function toggleCto(uid) {
  const box = document.getElementById(uid);
  const tog = box.previousElementSibling;
  const open = box.style.display === 'block';
  box.style.display = open ? 'none' : 'block';
  tog.textContent   = open ? '＋ Comentario' : '－ Ocultar';
  if (!open) box.querySelector('textarea').focus();
}
</script>"""


# ── Test ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '/home/claude')
    from processor_final import process_project
    path = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/uploads/Projecto.txt'
    data = process_project(path, reference_date=date(2026, 2, 23))
    html = render_dashboard([data])
    out  = '/mnt/user-data/outputs/dashboard_v3.html'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"OK → {out}  ({len(html):,} chars)")

"""
renderer.py  v2
===============
Cambios vs v1:
 - Semana de 6 días (lun–sáb)
 - Columna Comentario/Compromisos con textarea fija por tarea
 - Comentario en cards CTO (toggle)
 - Filtro de búsqueda en JS (client-side, sin recarga)
 - delay_str viene del processor (ya formateado)
 - CTO scroll horizontal, ordenado por fecha
 - Botón PDF via print() del browser (limpio, sin libs externas)
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

_MONTHS = ["","Ene","Feb","Mar","Abr","May","Jun",
            "Jul","Ago","Sep","Oct","Nov","Dic"]
_DAYS_ES = ["Lun","Mar","Mié","Jue","Vie","Sáb"]


def _tc(idx):
    return _TOWER_PALETTE[idx % len(_TOWER_PALETTE)]


def _fmt(d: date) -> str:
    return f"{d.day:02d}/{_MONTHS[d.month]}"


def _day_cols(week_start: date):
    """6 días: lun–sáb"""
    return [
        (str(week_start + timedelta(days=i)),
         f"{_DAYS_ES[i]} {(week_start + timedelta(days=i)).day}")
        for i in range(6)
    ]


# ── CSS ────────────────────────────────────────────────────────────────────────
def _css() -> str:
    return """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --red:#dc2626;    --red-bg:#fef2f2;   --red-b:#fecaca;
  --amb:#b45309;    --amb-bg:#fffbeb;   --amb-b:#fde68a;
  --blue:#1d4ed8;   --blue-bg:#eff6ff;  --blue-b:#bfdbfe;
  --grn:#15803d;    --grn-bg:#f0fdf4;   --grn-b:#bbf7d0;
  --sl:#475569;     --sl-bg:#f8fafc;    --sl-b:#e2e8f0;
  --pur:#6d28d9;
  --txt:#1e293b; --mut:#64748b; --bor:#e2e8f0;
}
body{font-family:'Inter',sans-serif;background:#fff;color:var(--txt);
     font-size:12.5px;padding:24px 28px;max-width:1200px;margin:0 auto}

/* HEADER */
.ph{display:flex;justify-content:space-between;align-items:flex-start;
    padding-bottom:12px;border-bottom:2.5px solid var(--txt);margin-bottom:16px}
.ph h1{font-size:18px;font-weight:700;letter-spacing:-.3px}
.ph .sub{font-size:11px;color:var(--mut);margin-top:3px}
.ph-meta{text-align:right;font-size:10.5px;color:var(--mut);
          font-family:'JetBrains Mono',monospace;line-height:1.7}
.ph-meta strong{color:var(--txt)}

/* PROJECT SEPARATOR */
.proj-sep{border:none;border-top:3px solid var(--txt);margin:32px 0 20px}
.proj-title{font-size:15px;font-weight:700;color:var(--txt);margin-bottom:14px}

/* CTO BANNER */
.cto-banner{background:#faf5ff;border:1px solid #ddd6fe;
            border-left:4px solid var(--pur);border-radius:7px;
            padding:11px 15px;margin-bottom:16px}
.cto-banner h3{font-size:10px;font-weight:700;text-transform:uppercase;
               letter-spacing:.7px;color:var(--pur);margin-bottom:9px}
.cto-scroll{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px}
.cto-scroll::-webkit-scrollbar{height:4px}
.cto-scroll::-webkit-scrollbar-thumb{background:#c4b5fd;border-radius:2px}
.cto-card{background:#fff;border:1px solid #e9d5ff;border-radius:6px;
          padding:9px 12px;min-width:160px;flex-shrink:0}
.cto-tw{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}
.cto-row{display:flex;gap:12px;margin-top:5px}
.ci .cl{font-size:10px;color:var(--mut)}
.ci .cd{font-family:'JetBrains Mono',monospace;font-size:11.5px;
         font-weight:600;color:var(--txt);margin-top:1px}
.ci .cdiff{font-size:9.5px;margin-top:1px}
/* CTO comment toggle */
.cto-comment-toggle{font-size:9.5px;color:var(--pur);cursor:pointer;
                     margin-top:7px;display:inline-block;user-select:none}
.cto-comment-box{display:none;margin-top:6px}
.cto-comment-box textarea{width:100%;height:56px;resize:none;font-size:10.5px;
  font-family:'Inter',sans-serif;border:1px solid #ddd6fe;border-radius:4px;
  padding:5px 7px;color:var(--txt);background:#faf5ff;outline:none}
.cto-comment-box textarea:focus{border-color:var(--pur)}

/* KPI */
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:16px}
.kpi{background:var(--sl-bg);border:1px solid var(--bor);border-radius:7px;padding:10px 13px}
.kpi-lbl{font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.6px;color:var(--mut)}
.kpi-val{font-size:22px;font-weight:700;margin-top:2px;line-height:1.1}
.v-blue{color:var(--blue)} .v-red{color:var(--red)}
.v-amb{color:var(--amb)}   .v-grn{color:var(--grn)}

/* FILTER */
.filter-wrap{margin-bottom:14px}
.filter-wrap input{width:100%;padding:7px 12px;font-size:12px;font-family:'Inter',sans-serif;
  border:1px solid var(--bor);border-radius:6px;outline:none;color:var(--txt)}
.filter-wrap input:focus{border-color:var(--blue)}
.filter-wrap input::placeholder{color:#94a3b8}

/* LEGEND */
.legend{display:flex;gap:14px;flex-wrap:wrap;align-items:center;
        margin-bottom:14px;padding:7px 12px;
        background:var(--sl-bg);border:1px solid var(--bor);border-radius:6px;
        font-size:10px;color:var(--mut)}
.li{display:flex;align-items:center;gap:5px}
.ld{width:9px;height:9px;border-radius:2px;flex-shrink:0}
.l-note{margin-left:auto;font-size:9.5px;color:var(--blue);font-family:'JetBrains Mono',monospace}

/* TOWER */
.tw-wrap{margin-bottom:20px}
.tw-hdr{display:flex;align-items:center;gap:10px;padding:7px 13px;border-radius:6px 6px 0 0}
.tw-name{font-size:12.5px;font-weight:700}
.tw-stats{margin-left:auto;font-size:10px;color:var(--mut)}
.tw-stats .alert{color:var(--red);font-weight:600}

/* TABLE */
.gantt-wrap{border:1px solid var(--bor);border-top:none;border-radius:0 0 6px 6px;overflow:hidden}
table{width:100%;border-collapse:collapse;font-size:10.5px}
thead tr{background:#f8fafc}
th{padding:5px 8px;font-size:9px;font-weight:600;text-transform:uppercase;
   letter-spacing:.5px;color:var(--mut);text-align:left;
   border-bottom:1px solid var(--bor);white-space:nowrap}
th.dc{text-align:center;width:72px;min-width:58px}
th.today-th{color:var(--blue)}
th.comment-th{min-width:150px;width:150px}

/* GROUP ROW */
tr.gr td{padding:4px 8px;background:#f1f5f9;font-size:9.5px;font-weight:600;
          color:var(--sl);letter-spacing:.3px;
          border-bottom:1px solid var(--bor);border-top:1px solid var(--bor)}
tr.gr .cs{color:#94a3b8;margin:0 3px}
tr.gr.hidden-group{display:none}

/* TASK ROW */
tr.tr td{padding:4px 8px;border-bottom:1px solid #f1f5f9;vertical-align:middle}
tr.tr:last-child td{border-bottom:none}
tr.tr:hover td{background:#fafafa}
tr.tr.hidden-task{display:none}
.tn{font-weight:500;color:var(--txt);white-space:nowrap;overflow:hidden;
    text-overflow:ellipsis;max-width:200px}

/* PILL */
.pill{display:inline-block;font-size:8.5px;font-weight:700;
       padding:2px 5px;border-radius:20px;white-space:nowrap}
.p-red {background:var(--red-bg);color:var(--red);border:1px solid var(--red-b)}
.p-amb {background:var(--amb-bg);color:var(--amb);border:1px solid var(--amb-b)}
.p-blue{background:var(--blue-bg);color:var(--blue);border:1px solid var(--blue-b)}
.p-grn {background:var(--grn-bg);color:var(--grn);border:1px solid var(--grn-b)}
.p-sl  {background:var(--sl-bg);color:var(--sl);border:1px solid var(--sl-b)}

/* DELAY */
.dl{font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:600;color:var(--red)}
.dl.none{color:#cbd5e1}

/* GANTT CELL */
td.dc{padding:2px 2px;width:72px;min-width:58px}
td.tday{background:#eff6ff!important}
.bar{position:relative;height:18px;border-radius:3px;overflow:hidden;border:1px solid transparent}
.bbg{position:absolute;inset:0}
.bpg{position:absolute;left:0;top:0;bottom:0}
.btx{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
     font-size:9px;font-weight:700;font-family:'JetBrains Mono',monospace}
.bv-red {border-color:var(--red-b)!important}
.bv-red .bbg{background:var(--red-bg)} .bv-red .bpg{background:var(--red);opacity:.3}
.bv-red .btx{color:var(--red)}
.bv-amb {border-color:var(--amb-b)!important}
.bv-amb .bbg{background:var(--amb-bg)} .bv-amb .bpg{background:var(--amb);opacity:.35}
.bv-amb .btx{color:var(--amb)}
.bv-blue{border-color:var(--blue-b)!important}
.bv-blue .bbg{background:var(--blue-bg)} .bv-blue .bpg{background:var(--blue);opacity:.3}
.bv-blue .btx{color:var(--blue)}
.bv-grn {border-color:var(--grn-b)!important}
.bv-grn .bbg{background:var(--grn-bg)} .bv-grn .bpg{background:var(--grn);opacity:.4}
.bv-grn .btx{color:var(--grn)}
.bv-sl  {border-color:var(--sl-b)!important}
.bv-sl  .bbg{background:var(--sl-bg)} .bv-sl .bpg{background:var(--sl);opacity:.25}
.bv-sl  .btx{color:var(--sl)}

/* COMMENT CELL */
td.comment-td{width:150px;min-width:150px;padding:3px 5px;vertical-align:top}
.comment-cell textarea{
  width:140px;height:44px;resize:none;
  font-size:10px;font-family:'Inter',sans-serif;
  border:1px solid var(--bor);border-radius:4px;
  padding:4px 6px;color:var(--txt);background:#fafafa;outline:none;
  overflow-y:auto;
}
.comment-cell textarea:focus{border-color:var(--blue);background:#fff}

hr.sep{border:none;border-top:1px solid var(--bor);margin:14px 0}

/* ── PRINT / PDF ─────────────────────────────────────────────────────────── */
@media print{
  body{padding:10px;font-size:9.5px;max-width:100%}
  .no-print{display:none!important}
  .tw-wrap{page-break-inside:avoid}
  .proj-sep{page-break-before:always}
  /* En PDF expandir textareas */
  .comment-cell textarea{
    height:auto!important;min-height:44px;
    overflow:visible!important;white-space:pre-wrap;
    border:1px solid #ccc;background:#fff;
  }
  .cto-comment-box{display:block!important}
  .cto-comment-box textarea{
    height:auto!important;min-height:40px;
    overflow:visible!important;white-space:pre-wrap;
    border:1px solid #ccc;background:#fff;
  }
  .cto-comment-toggle{display:none}
  /* Ocultar scrollbar en print */
  .cto-scroll{overflow:visible;flex-wrap:wrap}
}
</style>"""


# ── Render principal ───────────────────────────────────────────────────────────

def render_dashboard(projects: list[dict]) -> str:
    """
    Acepta una lista de dicts (uno por proyecto) y genera un HTML único
    con todos los proyectos en secuencia.
    """
    if isinstance(projects, dict):
        projects = [projects]   # compatibilidad con llamada de un solo proyecto

    css    = _css()
    bodies = []

    for idx, data in enumerate(projects):
        bodies.append(_render_project(data, idx))

    inner = "\n".join(bodies)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Reportes Semanales de Obra</title>
{css}
</head>
<body>
{inner}
{_filter_script()}
</body>
</html>"""


def _render_project(data: dict, proj_idx: int) -> str:
    ref        = data["reference_date"]
    week_start = data["week_start"]
    today_str  = str(ref)
    day_cols   = _day_cols(week_start)

    sep = f'<hr class="proj-sep">' if proj_idx > 0 else ''
    title_line = (
        f'<div class="proj-title">📁 {data["project_name"]}</div>'
        if proj_idx > 0 else ''
    )

    header   = _header(data)
    cto      = _cto_banner(data["cto_items"], data["towers"], ref)
    kpis     = _kpis(data["kpis"])
    legend   = _legend(today_str)
    filt     = _filter_bar(proj_idx)
    sections = _sections(data["towers"], day_cols, today_str, proj_idx)

    return f"{sep}{title_line}{header}{cto}{kpis}{legend}{filt}{sections}"


# ── Header ─────────────────────────────────────────────────────────────────────

def _header(data: dict) -> str:
    ref = data["reference_date"]
    ws  = data["week_start"]
    we  = data["week_end"]
    week_lbl = (
        f"{ws.day} {_MONTHS[ws.month]} – {we.day} {_MONTHS[we.month]} {we.year}"
    )
    prog = data["overall_progress"] * 100
    return f"""
<div class="ph">
  <div>
    <h1>Reporte Semanal de Obra</h1>
    <div class="sub">{data['project_name']} &nbsp;·&nbsp; #{data['project_id']}</div>
  </div>
  <div class="ph-meta">
    <div><strong>Semana:</strong> {week_lbl}</div>
    <div><strong>Fecha de corte:</strong> {_fmt(ref)}/{ref.year}</div>
    <div><strong>Avance general:</strong> {prog:.1f}%</div>
  </div>
</div>"""


# ── CTO Banner ─────────────────────────────────────────────────────────────────

def _cto_banner(cto_items: list, towers: list, ref: date) -> str:
    if not cto_items:
        return ""

    tower_ids = [tw["id"] for tw in towers]

    # Agrupar por torre manteniendo orden por fecha (ya viene ordenado)
    by_tower: dict[str, list] = {}
    for c in cto_items:
        by_tower.setdefault(c["tower"], []).append(c)

    cards = ""
    cto_idx = 0
    for tower_id, items in by_tower.items():
        tidx  = tower_ids.index(tower_id) if tower_id in tower_ids else cto_idx
        color = _tc(tidx)["border"]
        cto_idx += 1

        rows_html = ""
        for item in items:
            diff = item["days_from_reference"]
            if diff > 0:
                diff_txt, diff_color = f"en {diff}d", "#6d28d9"
            elif diff == 0:
                diff_txt, diff_color = "Hoy", "#dc2626"
            else:
                diff_txt, diff_color = f"hace {-diff}d", "#dc2626"

            rows_html += f"""
        <div class="ci">
          <div class="cl">{item['label']}</div>
          <div class="cd">{_fmt(item['date'])}</div>
          <div class="cdiff" style="color:{diff_color}">{diff_txt}</div>
        </div>"""

        uid = f"cto_{tower_id}_{id(items)}"
        cards += f"""
    <div class="cto-card">
      <div class="cto-tw" style="color:{color}">{tower_id}</div>
      <div class="cto-row">{rows_html}</div>
      <div class="cto-comment-toggle" onclick="toggleCtoComment('{uid}')">
        ＋ Agregar comentario
      </div>
      <div class="cto-comment-box" id="{uid}">
        <textarea placeholder="Comentario / compromiso CTO..."></textarea>
      </div>
    </div>"""

    return f"""
<div class="cto-banner">
  <h3>🏛 Certificados Técnicos de Ocupación (CTO)</h3>
  <div class="cto-scroll">{cards}</div>
</div>"""


# ── KPIs ───────────────────────────────────────────────────────────────────────

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


# ── Legend ─────────────────────────────────────────────────────────────────────

def _legend(today_str: str) -> str:
    d = date.fromisoformat(today_str)
    lbl = f"{_DAYS_ES[d.weekday()]} {d.day}"
    return f"""
<div class="legend">
  <div class="li"><div class="ld" style="background:#dc2626"></div> Atrasada (con progreso)</div>
  <div class="li"><div class="ld" style="background:#b45309"></div> En progreso con atraso</div>
  <div class="li"><div class="ld" style="background:#1d4ed8"></div> Programada esta semana</div>
  <div class="li"><div class="ld" style="background:#15803d"></div> Completada</div>
  <div class="li"><div class="ld" style="background:#475569"></div> Pendiente sin atraso</div>
  <div class="l-note no-print">★ Hoy = {lbl} {d.year}</div>
</div>"""


# ── Filter bar ─────────────────────────────────────────────────────────────────

def _filter_bar(proj_idx: int) -> str:
    return f"""
<div class="filter-wrap no-print">
  <input type="text" id="filter_{proj_idx}"
         onkeyup="filterTasks(this, {proj_idx})"
         placeholder="🔍  Filtrar actividades por nombre...">
</div>"""


# ── Sections ───────────────────────────────────────────────────────────────────

def _sections(towers, day_cols, today_str, proj_idx):
    parts = []
    for i, tw in enumerate(towers):
        if i > 0:
            parts.append('<hr class="sep">')
        parts.append(_tower_section(tw, i, day_cols, today_str, proj_idx))
    return "\n".join(parts)


def _tower_section(tower, idx, day_cols, today_str, proj_idx):
    color  = _tc(idx)
    n_del  = sum(1 for t in tower["tasks"] if t["category"] == "delayed")
    n_start= sum(1 for t in tower["tasks"] if t["category"] == "starting")
    alert  = f' &nbsp;·&nbsp;<span class="alert">{n_del} con atraso</span>' if n_del else ""

    day_ths = "".join(
        f'<th class="dc{"  today-th" if d == today_str else ""}">'
        f'{lbl}{"  ★" if d == today_str else ""}</th>'
        for d, lbl in day_cols
    )

    body = _table_body(tower["groups"], day_cols, today_str, proj_idx)

    return f"""
<div class="tw-wrap" data-proj="{proj_idx}">
  <div class="tw-hdr" style="background:{color['bg']};border-left:4px solid {color['border']}">
    <span class="tw-name">{tower['label']}</span>
    <span class="tw-stats">{n_start} programadas{alert}</span>
  </div>
  <div class="gantt-wrap">
    <table>
      <thead><tr>
        <th style="min-width:180px">Actividad</th>
        <th style="min-width:110px">Estado</th>
        <th style="text-align:center">Atraso</th>
        <th style="text-align:center;white-space:nowrap">Ini.</th>
        <th style="text-align:center;white-space:nowrap">Fin</th>
        {day_ths}
        <th class="comment-th">Comentario / Compromisos</th>
      </tr></thead>
      <tbody>{body}</tbody>
    </table>
  </div>
</div>"""


def _table_body(groups, day_cols, today_str, proj_idx):
    rows = []
    days = [d for d, _ in day_cols]
    grp_idx = 0

    for crumb_key, tasks in groups.items():
        parts = crumb_key.split(" › ")
        crumb_html = '<span class="cs">›</span>'.join(
            f"<span>{p}</span>" for p in parts
        )
        n_cols = 6 + len(day_cols)   # act + estado + atraso + ini + fin + días + comment
        gid = f"grp_{proj_idx}_{grp_idx}"
        rows.append(
            f'<tr class="gr" id="{gid}" data-proj="{proj_idx}">'
            f'<td colspan="{n_cols}">{crumb_html}</td></tr>'
        )
        for t in tasks:
            rows.append(_task_row(t, days, today_str, proj_idx, gid))
        grp_idx += 1

    return "\n".join(rows)


def _task_row(task, days, today_str, proj_idx, gid):
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

    # Delay cell
    ds = task["delay_str"]
    delay_cell = (
        f'<span class="dl">{ds}</span>'
        if ds != "—"
        else '<span class="dl none">—</span>'
    )

    # Gantt bars
    ts = str(task["start"])
    te = str(task["end"])
    pct = 100 if task["state"] == "completed" else task["progress"]
    lbl = f"{pct}%" if pct > 0 else "·"

    is_out = task["category"] == "delayed" and te < days[0]
    if is_out:
        gantt = f"""<td class="dc" colspan="{len(days)}" style="padding:2px 5px">
      <div class="bar {bv}">
        <div class="bbg"></div><div class="bpg" style="width:{pct}%"></div>
        <div class="btx">Fuera de sem. · {pct}% · {ds}d</div>
      </div></td>"""
    else:
        bar_s = max(ts, days[0])
        bar_e = min(te, days[-1])
        si = days.index(bar_s) if bar_s in days else -1
        ei = days.index(bar_e) if bar_e in days else -1
        cells = []
        skip = -1
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

    return f"""<tr class="tr" data-name="{task['name'].lower()}" data-proj="{proj_idx}" data-grp="{gid}">
  <td><div class="tn" title="{task['name']}">{task['name']}</div></td>
  <td>{pill}</td>
  <td style="text-align:center">{delay_cell}</td>
  <td style="font-family:'JetBrains Mono',monospace;font-size:9.5px;color:#475569;text-align:center">{sl}</td>
  <td style="font-family:'JetBrains Mono',monospace;font-size:9.5px;color:#475569;text-align:center">{el}</td>
  {gantt}
  <td class="comment-td"><div class="comment-cell">
    <textarea placeholder="Comentario..."></textarea>
  </div></td>
</tr>"""


# ── JavaScript ─────────────────────────────────────────────────────────────────

def _filter_script() -> str:
    return """<script>
function filterTasks(input, projIdx) {
  const query = input.value.toLowerCase().trim();
  const rows  = document.querySelectorAll(`tr.tr[data-proj="${projIdx}"]`);
  const grps  = document.querySelectorAll(`tr.gr[data-proj="${projIdx}"]`);

  // Mostrar/ocultar tareas
  rows.forEach(row => {
    const name  = row.getAttribute('data-name') || '';
    const match = !query || name.includes(query);
    row.classList.toggle('hidden-task', !match);
  });

  // Ocultar agrupadores cuyas tareas quedaron todas ocultas
  grps.forEach(grp => {
    const gid        = grp.id;
    const grpTasks   = document.querySelectorAll(`tr.tr[data-grp="${gid}"]`);
    const anyVisible = Array.from(grpTasks).some(t => !t.classList.contains('hidden-task'));
    grp.classList.toggle('hidden-group', !anyVisible);
  });
}

function toggleCtoComment(uid) {
  const box    = document.getElementById(uid);
  const toggle = box.previousElementSibling;
  if (box.style.display === 'block') {
    box.style.display = 'none';
    toggle.textContent = '＋ Agregar comentario';
  } else {
    box.style.display = 'block';
    toggle.textContent = '－ Ocultar comentario';
    box.querySelector('textarea').focus();
  }
}
</script>"""


# ── Test ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '/home/claude')
    from processor_v2 import process_project
    path = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/uploads/Projecto.txt'
    data = process_project(path, reference_date=date(2026, 2, 23))
    html = render_dashboard([data])
    out  = '/mnt/user-data/outputs/dashboard_v2.html'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"OK → {out}  ({len(html):,} chars)")

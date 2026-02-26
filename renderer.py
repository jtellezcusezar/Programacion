"""
renderer.py
===========
Toma el dict devuelto por processor.process_project()
y genera el HTML completo del dashboard.

Uso:
    from renderer import render_dashboard
    html = render_dashboard(data)          # data viene de process_project()
"""

from datetime import date, timedelta
import json


# ─── Paleta de colores por índice de torre ─────────────────────────────────────
_TOWER_PALETTE = [
    {"border": "#6366f1", "bg": "#eef2ff", "badge": "#6366f1"},  # índigo
    {"border": "#0284c7", "bg": "#e0f2fe", "badge": "#0284c7"},  # azul
    {"border": "#0d9488", "bg": "#f0fdfa", "badge": "#0d9488"},  # teal
    {"border": "#d97706", "bg": "#fffbeb", "badge": "#d97706"},  # ámbar
    {"border": "#dc2626", "bg": "#fef2f2", "badge": "#dc2626"},  # rojo
    {"border": "#7c3aed", "bg": "#faf5ff", "badge": "#7c3aed"},  # violeta
    {"border": "#059669", "bg": "#ecfdf5", "badge": "#059669"},  # verde
    {"border": "#db2777", "bg": "#fdf2f8", "badge": "#db2777"},  # rosa
]


def _tower_color(idx: int) -> dict:
    return _TOWER_PALETTE[idx % len(_TOWER_PALETTE)]


def _fmt_date(d: date) -> str:
    months = ["","Ene","Feb","Mar","Abr","May","Jun",
               "Jul","Ago","Sep","Oct","Nov","Dic"]
    return f"{d.day:02d}/{months[d.month]}"


def _day_labels(week_start: date) -> list[tuple[str, str]]:
    """Retorna lista de (date_str, label) para los 5 días de la semana."""
    days_es = ["Lun","Mar","Mié","Jue","Vie"]
    return [
        (str(week_start + timedelta(days=i)),
         f"{days_es[i]} {(week_start + timedelta(days=i)).day}")
        for i in range(5)
    ]


# ─── Función principal ─────────────────────────────────────────────────────────

def render_dashboard(data: dict) -> str:
    """
    Genera el HTML completo del dashboard a partir del dict de process_project().
    Retorna un string HTML listo para usar en st.components.v1.html() o guardar.
    """
    ref        = data["reference_date"]
    week_start = data["week_start"]
    week_end   = data["week_end"]
    day_cols   = _day_labels(week_start)            # [(date_str, label), ...]
    today_str  = str(ref)

    css      = _build_css()
    header   = _build_header(data)
    cto      = _build_cto_banner(data["cto_items"], data["towers"], ref)
    kpis     = _build_kpis(data["kpis"])
    legend   = _build_legend(today_str, week_start)
    sections = _build_sections(data["towers"], day_cols, today_str)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reporte Semanal — {data['project_name']}</title>
{css}
</head>
<body>
{header}
{cto}
{kpis}
{legend}
{sections}
</body>
</html>"""


# ─── CSS ───────────────────────────────────────────────────────────────────────

def _build_css() -> str:
    return """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*{box-sizing:border-box;margin:0;padding:0}

:root{
  --red:#dc2626;    --red-bg:#fef2f2;    --red-b:#fecaca;
  --amber:#b45309;  --amber-bg:#fffbeb;  --amber-b:#fde68a;
  --blue:#1d4ed8;   --blue-bg:#eff6ff;   --blue-b:#bfdbfe;
  --green:#15803d;  --green-bg:#f0fdf4;  --green-b:#bbf7d0;
  --slate:#475569;  --slate-bg:#f8fafc;  --slate-b:#e2e8f0;
  --purple:#6d28d9;
  --text:#1e293b; --muted:#64748b; --border:#e2e8f0;
}

body{
  font-family:'Inter',sans-serif;
  background:#fff; color:var(--text);
  font-size:12.5px; padding:28px 32px;
  max-width:1120px; margin:0 auto;
}

/* HEADER */
.ph{display:flex;justify-content:space-between;align-items:flex-start;
    padding-bottom:14px;border-bottom:2.5px solid var(--text);margin-bottom:18px}
.ph h1{font-size:19px;font-weight:700;letter-spacing:-.3px}
.ph .sub{font-size:11.5px;color:var(--muted);margin-top:3px}
.ph-meta{text-align:right;font-size:11px;color:var(--muted);
          font-family:'JetBrains Mono',monospace;line-height:1.7}
.ph-meta strong{color:var(--text)}

/* CTO BANNER */
.cto-banner{background:#faf5ff;border:1px solid #ddd6fe;
            border-left:4px solid var(--purple);border-radius:7px;
            padding:12px 16px;margin-bottom:18px}
.cto-banner h3{font-size:10.5px;font-weight:700;text-transform:uppercase;
               letter-spacing:.7px;color:var(--purple);margin-bottom:10px}
.cto-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px}
.cto-card{background:#fff;border:1px solid #e9d5ff;border-radius:6px;padding:9px 12px}
.cto-tw{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}
.cto-row{display:flex;gap:14px;margin-top:6px}
.cto-item .cl{font-size:10.5px;color:var(--muted)}
.cto-item .cd{font-family:'JetBrains Mono',monospace;font-size:12px;
               font-weight:600;color:var(--text);margin-top:1px}
.cto-item .cdiff{font-size:10px;margin-top:1px}

/* KPI */
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:18px}
.kpi{background:var(--slate-bg);border:1px solid var(--border);
     border-radius:7px;padding:11px 14px}
.kpi-lbl{font-size:9.5px;font-weight:600;text-transform:uppercase;
          letter-spacing:.6px;color:var(--muted)}
.kpi-val{font-size:24px;font-weight:700;margin-top:2px;line-height:1.1}
.v-blue{color:var(--blue)} .v-red{color:var(--red)}
.v-amber{color:var(--amber)} .v-green{color:var(--green)}

/* LEGEND */
.legend{display:flex;gap:16px;flex-wrap:wrap;align-items:center;
        margin-bottom:18px;padding:8px 13px;
        background:var(--slate-bg);border:1px solid var(--border);
        border-radius:6px;font-size:10.5px;color:var(--muted)}
.li{display:flex;align-items:center;gap:5px}
.ld{width:10px;height:10px;border-radius:3px;flex-shrink:0}
.l-note{margin-left:auto;font-size:10px;color:var(--blue);
         font-family:'JetBrains Mono',monospace}

/* TOWER */
.tw-wrap{margin-bottom:22px}
.tw-hdr{display:flex;align-items:center;gap:10px;
        padding:8px 14px;border-radius:6px 6px 0 0}
.tw-name{font-size:13px;font-weight:700}
.tw-stats{margin-left:auto;font-size:10.5px;color:var(--muted)}
.tw-stats .alert{color:var(--red);font-weight:600}

/* TABLE */
.gantt-wrap{border:1px solid var(--border);border-top:none;
            border-radius:0 0 6px 6px;overflow:hidden}
table{width:100%;border-collapse:collapse;font-size:11px}
thead tr{background:#f8fafc}
th{padding:6px 9px;font-size:9.5px;font-weight:600;text-transform:uppercase;
   letter-spacing:.5px;color:var(--muted);text-align:left;
   border-bottom:1px solid var(--border);white-space:nowrap}
th.dc{text-align:center;width:80px;min-width:64px}
th.today-th{color:var(--blue)}

/* GROUP ROW */
tr.gr td{padding:4px 9px;background:#f1f5f9;font-size:10px;font-weight:600;
          color:var(--slate);letter-spacing:.3px;
          border-bottom:1px solid var(--border);border-top:1px solid var(--border)}
tr.gr .cs{color:#94a3b8;margin:0 4px}

/* TASK ROW */
tr.tr td{padding:5px 9px;border-bottom:1px solid #f1f5f9;vertical-align:middle}
tr.tr:last-child td{border-bottom:none}
tr.tr:hover td{background:#fafafa}
.tn{font-weight:500;color:var(--text);white-space:nowrap;
    overflow:hidden;text-overflow:ellipsis;max-width:215px}

/* PILL */
.pill{display:inline-block;font-size:9px;font-weight:700;
       padding:2px 6px;border-radius:20px;letter-spacing:.2px;white-space:nowrap}
.p-red  {background:var(--red-bg);  color:var(--red);  border:1px solid var(--red-b)}
.p-amb  {background:var(--amber-bg);color:var(--amber);border:1px solid var(--amber-b)}
.p-blue {background:var(--blue-bg); color:var(--blue); border:1px solid var(--blue-b)}
.p-grn  {background:var(--green-bg);color:var(--green);border:1px solid var(--green-b)}
.p-sl   {background:var(--slate-bg);color:var(--slate);border:1px solid var(--slate-b)}

/* DELAY */
.dl{font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:600;color:var(--red)}
.dl.none{color:#cbd5e1}

/* GANTT CELL */
td.dc{padding:3px 2px;width:80px;min-width:64px}
td.tday{background:#eff6ff!important}
.bar{position:relative;height:20px;border-radius:4px;overflow:hidden;border:1px solid transparent}
.bbg{position:absolute;inset:0}
.bpg{position:absolute;left:0;top:0;bottom:0}
.btx{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
     font-size:9.5px;font-weight:700;font-family:'JetBrains Mono',monospace}

.bv-red  {border-color:var(--red-b)!important}
.bv-red  .bbg{background:var(--red-bg)} .bv-red  .bpg{background:var(--red);opacity:.3}
.bv-red  .btx{color:var(--red)}
.bv-amb  {border-color:var(--amber-b)!important}
.bv-amb  .bbg{background:var(--amber-bg)} .bv-amb .bpg{background:var(--amber);opacity:.35}
.bv-amb  .btx{color:var(--amber)}
.bv-blue {border-color:var(--blue-b)!important}
.bv-blue .bbg{background:var(--blue-bg)} .bv-blue .bpg{background:var(--blue);opacity:.3}
.bv-blue .btx{color:var(--blue)}
.bv-grn  {border-color:var(--green-b)!important}
.bv-grn  .bbg{background:var(--green-bg)} .bv-grn .bpg{background:var(--green);opacity:.4}
.bv-grn  .btx{color:var(--green)}
.bv-sl   {border-color:var(--slate-b)!important}
.bv-sl   .bbg{background:var(--slate-bg)} .bv-sl .bpg{background:var(--slate);opacity:.25}
.bv-sl   .btx{color:var(--slate)}

hr.sep{border:none;border-top:1px solid var(--border);margin:16px 0}

@media print{
  body{padding:14px;font-size:10.5px}
  .tw-wrap{page-break-inside:avoid}
}
</style>"""


# ─── Header ────────────────────────────────────────────────────────────────────

def _build_header(data: dict) -> str:
    ref  = data["reference_date"]
    ws   = data["week_start"]
    we   = data["week_end"]
    prog = data["overall_progress"] * 100
    months = ["","Ene","Feb","Mar","Abr","May","Jun",
               "Jul","Ago","Sep","Oct","Nov","Dic"]

    week_label = (
        f"{ws.day} {months[ws.month]} – {we.day} {months[we.month]} {we.year}"
    )
    return f"""
<div class="ph">
  <div>
    <h1>Reporte Semanal de Obra</h1>
    <div class="sub">{data['project_name']} &nbsp;·&nbsp; Proyecto #{data['project_id']}</div>
  </div>
  <div class="ph-meta">
    <div><strong>Semana:</strong> {week_label}</div>
    <div><strong>Fecha de corte:</strong> {_fmt_date(ref)}/{ref.year}</div>
    <div><strong>Avance general:</strong> {prog:.1f}%</div>
  </div>
</div>"""


# ─── CTO Banner ────────────────────────────────────────────────────────────────

def _build_cto_banner(cto_items: list, towers: list, ref: date) -> str:
    if not cto_items:
        return ""

    # Agrupar por torre
    by_tower: dict[str, list] = {}
    for c in cto_items:
        by_tower.setdefault(c["tower"], []).append(c)

    # Colores de torre
    tower_ids = [tw["id"] for tw in towers]

    cards_html = ""
    for tower_id, items in by_tower.items():
        idx = tower_ids.index(tower_id) if tower_id in tower_ids else 0
        color = _tower_color(idx)["border"]

        items_html = ""
        for item in items:
            d = item["date"]
            diff = item["days_from_reference"]
            if diff > 0:
                diff_str = f"en {diff}d"
                diff_color = "#6d28d9"
            elif diff == 0:
                diff_str = "Hoy"
                diff_color = "#dc2626"
            else:
                diff_str = f"hace {-diff}d"
                diff_color = "#dc2626"

            items_html += f"""
          <div class="cto-item">
            <div class="cl">{item['label']}</div>
            <div class="cd">{_fmt_date(d)}</div>
            <div class="cdiff" style="color:{diff_color}">{diff_str}</div>
          </div>"""

        cards_html += f"""
      <div class="cto-card">
        <div class="cto-tw" style="color:{color}">{tower_id}</div>
        <div class="cto-row">{items_html}</div>
      </div>"""

    return f"""
<div class="cto-banner">
  <h3>🏛 Certificados Técnicos de Ocupación (CTO)</h3>
  <div class="cto-grid">{cards_html}</div>
</div>"""


# ─── KPIs ──────────────────────────────────────────────────────────────────────

def _build_kpis(kpis: dict) -> str:
    return f"""
<div class="kpi-row">
  <div class="kpi">
    <div class="kpi-lbl">Programadas esta semana</div>
    <div class="kpi-val v-blue">{kpis['starting']}</div>
  </div>
  <div class="kpi">
    <div class="kpi-lbl">Con atraso (c/progreso)</div>
    <div class="kpi-val v-red">{kpis['delayed']}</div>
  </div>
  <div class="kpi">
    <div class="kpi-lbl">En progreso</div>
    <div class="kpi-val v-amber">{kpis['in_progress']}</div>
  </div>
  <div class="kpi">
    <div class="kpi-lbl">Completadas</div>
    <div class="kpi-val v-green">{kpis['completed']}</div>
  </div>
</div>"""


# ─── Legend ────────────────────────────────────────────────────────────────────

def _build_legend(today_str: str, week_start: date) -> str:
    days_es = ["Lun","Mar","Mié","Jue","Vie"]
    today_label = f"{days_es[date.fromisoformat(today_str).weekday()]} {date.fromisoformat(today_str).day}"
    return f"""
<div class="legend">
  <div class="li"><div class="ld" style="background:#dc2626"></div> Atrasada (con progreso)</div>
  <div class="li"><div class="ld" style="background:#b45309"></div> En progreso con atraso</div>
  <div class="li"><div class="ld" style="background:#1d4ed8"></div> Programada esta semana</div>
  <div class="li"><div class="ld" style="background:#15803d"></div> Completada</div>
  <div class="li"><div class="ld" style="background:#475569"></div> Pendiente sin atraso</div>
  <div class="l-note">★ Hoy = {today_label} {week_start.year}</div>
</div>"""


# ─── Sections ──────────────────────────────────────────────────────────────────

def _build_sections(towers: list, day_cols: list, today_str: str) -> str:
    parts = []
    for idx, tower in enumerate(towers):
        if idx > 0:
            parts.append('<hr class="sep">')
        parts.append(_build_tower_section(tower, idx, day_cols, today_str))
    return "\n".join(parts)


def _build_tower_section(tower: dict, idx: int, day_cols: list, today_str: str) -> str:
    color   = _tower_color(idx)
    n_del   = sum(1 for t in tower["tasks"] if t["category"] == "delayed")
    n_start = sum(1 for t in tower["tasks"] if t["category"] == "starting")

    alert_html = f' &nbsp;·&nbsp;<span class="alert">{n_del} con atraso</span>' if n_del else ""

    day_ths = "".join(
        f'<th class="dc{"  today-th" if d == today_str else ""}">'
        f'{lbl}{"  ★" if d == today_str else ""}</th>'
        for d, lbl in day_cols
    )

    body = _build_table_body(tower["groups"], day_cols, today_str)

    return f"""
<div class="tw-wrap">
  <div class="tw-hdr" style="background:{color['bg']};border-left:4px solid {color['border']}">
    <span class="tw-name">{tower['label']}</span>
    <span class="tw-stats">{n_start} programadas{alert_html}</span>
  </div>
  <div class="gantt-wrap">
    <table>
      <thead>
        <tr>
          <th style="min-width:185px">Actividad</th>
          <th style="min-width:115px">Estado</th>
          <th style="text-align:center">Atraso</th>
          <th style="text-align:center;white-space:nowrap">Ini. prog.</th>
          <th style="text-align:center;white-space:nowrap">Fin prog.</th>
          {day_ths}
        </tr>
      </thead>
      <tbody>{body}</tbody>
    </table>
  </div>
</div>"""


def _build_table_body(groups: dict, day_cols: list, today_str: str) -> str:
    rows = []
    days_list = [d for d, _ in day_cols]

    for crumb_key, tasks in groups.items():
        # Breadcrumb header row
        parts = crumb_key.split(" › ")
        crumb_html = '<span class="cs">›</span>'.join(
            f"<span>{p}</span>" for p in parts
        )
        n_cols = 5 + len(day_cols)
        rows.append(
            f'<tr class="gr"><td colspan="{n_cols}">{crumb_html}</td></tr>'
        )

        for task in tasks:
            rows.append(_build_task_row(task, days_list, today_str))

    return "\n".join(rows)


def _build_task_row(task: dict, days_list: list, today_str: str) -> str:
    # ── Bar variant ─────────────────────────────────────────────
    if task["state"] == "completed":
        bv = "bv-grn"
    elif task["category"] == "delayed" and task["progress"] > 0:
        bv = "bv-red"
    elif task["delay"] > 0 and task["progress"] > 0:
        bv = "bv-amb"
    elif task["delay"] > 0:
        bv = "bv-sl"
    else:
        bv = "bv-blue"

    # ── Pill ────────────────────────────────────────────────────
    if task["state"] == "completed":
        pill = '<span class="pill p-grn">✓ Completada</span>'
    elif task["category"] == "delayed" and task["progress"] > 0:
        pill = '<span class="pill p-red">Atrasada · en progreso</span>'
    elif task["delay"] > 0 and task["progress"] > 0:
        pill = '<span class="pill p-amb">En progreso</span>'
    elif task["delay"] > 0:
        pill = '<span class="pill p-sl">Pendiente</span>'
    else:
        pill = '<span class="pill p-blue">Programada</span>'

    # ── Delay cell ──────────────────────────────────────────────
    if task["category"] == "delayed" and task["progress"] > 0:
        delay_cell = f'<span class="dl">+{task["delay"]}d</span>'
    else:
        delay_cell = '<span class="dl none">—</span>'

    # ── Gantt bar cells ─────────────────────────────────────────
    task_start_str = str(task["start"])
    task_end_str   = str(task["end"])
    pct = 100 if task["state"] == "completed" else task["progress"]
    lbl = f"{pct}%" if pct > 0 else "·"

    is_out_of_week = task["category"] == "delayed" and task_end_str < days_list[0]

    if is_out_of_week:
        gantt_cells = f"""<td class="dc" colspan="{len(days_list)}" style="padding:3px 6px">
      <div class="bar {bv}" style="max-width:100%">
        <div class="bbg"></div>
        <div class="bpg" style="width:{pct}%"></div>
        <div class="btx">Fuera de sem. · {pct}% · +{task['delay']}d</div>
      </div></td>"""
    else:
        # Calcular índices de inicio y fin dentro de la semana
        bar_start = max(task_start_str, days_list[0])
        bar_end   = min(task_end_str,   days_list[-1])

        try:
            si = days_list.index(bar_start)
            ei = days_list.index(bar_end)
        except ValueError:
            si, ei = -1, -1

        cells = []
        skip_until = -1
        for i, d in enumerate(days_list):
            is_today = d == today_str
            td_cls   = ' tday' if is_today else ''

            if i < skip_until:
                continue

            if si != -1 and ei != -1 and si <= i <= ei:
                if i == si:
                    span = ei - si + 1
                    cells.append(
                        f'<td class="dc{td_cls}" colspan="{span}" style="padding:3px 2px">'
                        f'<div class="bar {bv}">'
                        f'<div class="bbg"></div>'
                        f'<div class="bpg" style="width:{pct}%"></div>'
                        f'<div class="btx">{lbl}</div>'
                        f'</div></td>'
                    )
                    skip_until = ei + 1
            else:
                cells.append(f'<td class="dc{td_cls}"></td>')

        gantt_cells = "".join(cells)

    start_lbl = f"{task['start'].month:02d}/{task['start'].day:02d}"
    end_lbl   = f"{task['end'].month:02d}/{task['end'].day:02d}"

    return f"""<tr class="tr">
  <td><div class="tn" title="{task['name']}">{task['name']}</div></td>
  <td>{pill}</td>
  <td style="text-align:center">{delay_cell}</td>
  <td style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#475569;text-align:center">{start_lbl}</td>
  <td style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#475569;text-align:center">{end_lbl}</td>
  {gantt_cells}
</tr>"""


# ─── Test rápido ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    from processor import process_project

    path = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/uploads/Projecto.txt'
    ref  = date(2026, 2, 23)

    data = process_project(path, reference_date=ref)
    html = render_dashboard(data)

    out = '/mnt/user-data/outputs/dashboard_test.html'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML generado: {out}  ({len(html):,} chars)")

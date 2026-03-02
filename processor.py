"""
processor.py  v4
================
- Soporte para rango de fechas (date_start + date_end)
- Escala adaptativa del Gantt según rango
- Completadas → delay siempre '—'
"""

import json, re
from datetime import date, timedelta
from collections import defaultdict

_SKIP_GROUP_PATTERNS = {
    'CONSTRUCCIÓN','CONSTRUCTION','HITOS IMPORTANTES',
    'CONTRATOS','CONTRACTS','FECHA DE CORTE',
}
_CTO_PREFIX      = 'CTO-'
_CONTRACTS_GROUP = 'CONTRATOS'


# ── Escala del Gantt ──────────────────────────────────────────────────────────

def get_gantt_scale(range_days: int) -> dict:
    """
    Retorna metadatos de escala según el rango de días seleccionado.
    scale:      'day' | 'week' | 'week_month' | 'month' | 'quarter'
    col_width:  ancho en px de cada columna
    col_min:    mínimo de columnas que ocupa una actividad (siempre visible)
    """
    if range_days <= 6:
        return {'scale': 'day',        'col_width': 70,  'col_min': 1}
    elif range_days <= 27:
        return {'scale': 'week',       'col_width': 56,  'col_min': 1}
    elif range_days <= 89:
        return {'scale': 'week_month', 'col_width': 48,  'col_min': 1}
    elif range_days <= 365:
        return {'scale': 'month',      'col_width': 44,  'col_min': 1}
    else:
        return {'scale': 'quarter',    'col_width': 40,  'col_min': 1}


def build_gantt_columns(date_start: date, date_end: date, scale: str) -> list[dict]:
    """
    Construye la lista de columnas del Gantt según la escala.
    Cada columna: {label, col_start (date), col_end (date)}
    """
    cols = []
    _MONTHS = ["","Ene","Feb","Mar","Abr","May","Jun",
                "Jul","Ago","Sep","Oct","Nov","Dic"]
    _QUARTERS = {1:"Q1",2:"Q1",3:"Q1",4:"Q2",5:"Q2",6:"Q2",
                 7:"Q3",8:"Q3",9:"Q3",10:"Q4",11:"Q4",12:"Q4"}

    if scale == 'day':
        d = date_start
        while d <= date_end:
            days_es = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
            cols.append({'label': f"{days_es[d.weekday()]} {d.day}",
                         'col_start': d, 'col_end': d})
            d += timedelta(days=1)

    elif scale in ('week', 'week_month'):
        # Empezar en el lunes de date_start
        d = date_start - timedelta(days=date_start.weekday())
        while d <= date_end:
            week_end = d + timedelta(days=6)
            if scale == 'week_month':
                label = f"S {d.day}/{_MONTHS[d.month]}"
            else:
                label = f"S {d.day}/{d.month}"
            cols.append({'label': label, 'col_start': d,
                         'col_end': min(week_end, date_end)})
            d += timedelta(days=7)

    elif scale == 'month':
        d = date(date_start.year, date_start.month, 1)
        while d <= date_end:
            month_end = date(d.year + (d.month // 12),
                             (d.month % 12) + 1, 1) - timedelta(days=1)
            cols.append({'label': f"{_MONTHS[d.month]} {d.year}",
                         'col_start': d,
                         'col_end': min(month_end, date_end)})
            if d.month == 12:
                d = date(d.year + 1, 1, 1)
            else:
                d = date(d.year, d.month + 1, 1)

    elif scale == 'quarter':
        def quarter_start(dt):
            q = (dt.month - 1) // 3
            return date(dt.year, q * 3 + 1, 1)
        def quarter_end(dt):
            q = (dt.month - 1) // 3
            end_month = q * 3 + 3
            if end_month == 12:
                return date(dt.year, 12, 31)
            return date(dt.year, end_month + 1, 1) - timedelta(days=1)

        d = quarter_start(date_start)
        while d <= date_end:
            qe = quarter_end(d)
            cols.append({'label': f"{_QUARTERS[d.month]} {d.year}",
                         'col_start': d,
                         'col_end': min(qe, date_end)})
            d = qe + timedelta(days=1)

    return cols


# ── Delay ─────────────────────────────────────────────────────────────────────

def compute_delay(task_start: date, task_end: date,
                  reference_date: date, category: str, state: str) -> str:
    if state == 'completed':
        return '—'
    if category == 'delayed':
        days = (reference_date - task_end).days
    elif category == 'starting':
        if task_start < reference_date:
            days = (reference_date - task_start).days
        else:
            return '—'
    else:
        return '—'
    if days <= 0:
        return '—'
    return '+99' if days >= 100 else str(days)


# ── Proceso principal ─────────────────────────────────────────────────────────

def process_project(source,
                    reference_date: date = None,
                    date_end: date = None) -> dict:
    """
    Args:
        source:         JSON de Geniebelt
        reference_date: fecha de inicio / fecha de corte (default: hoy lunes)
        date_end:       fecha fin del rango (default: None → semana única)
    """
    today      = reference_date or date.today()
    week_start = today - timedelta(days=today.weekday())   # lunes

    # Rango de fechas
    is_range  = date_end is not None and date_end > today
    if is_range:
        range_start = week_start
        range_end   = date_end
    else:
        range_start = week_start
        range_end   = week_start + timedelta(days=5)       # sábado

    range_days = (range_end - range_start).days + 1
    gantt_meta = get_gantt_scale(range_days)
    gantt_cols = build_gantt_columns(range_start, range_end, gantt_meta['scale'])

    raw     = _load(source)
    project = raw['project']

    # Mapa project_item id → nombre de grupo
    item_to_group: dict[int, str] = {}
    for item in project['project_items']:
        if 'group' in item:
            item_to_group[item['id']] = item['group']['name'].strip()

    # Detectar torres (nivel índice 2)
    tower_ids: dict[int, str] = {}
    for item in project['project_items']:
        if 'package' not in item: continue
        path = item['path_outline']
        if len(path) >= 3:
            tid = path[2]
            if tid in item_to_group and tid not in tower_ids:
                tower_ids[tid] = item_to_group[tid]

    root_names: set[str] = set()
    for item in project['project_items']:
        if 'package' not in item: continue
        path = item['path_outline']
        if path and path[0] in item_to_group:
            root_names.add(item_to_group[path[0]])

    skip_names     = _SKIP_GROUP_PATTERNS | root_names
    tower_item_ids = set(tower_ids.keys())
    tower_labels   = dict(tower_ids)

    # Mapa miembro id → nombre
    members: dict[int, str] = {}
    for m in project.get('members', []):
        u = m.get('user', {})
        fn = u.get('first_name') or ''
        ln = u.get('last_name')  or ''
        name = f"{fn} {ln}".strip() or u.get('email', '')
        members[m['id']] = name

    # Mapa package_id -> nombre (para resolver dependencias)
    pkg_id_to_name: dict[int, str] = {}
    for item in project['project_items']:
        if 'package' in item:
            pkg_id_to_name[item['package']['id']] = item['package']['name'].strip()

    # Mapa package_id -> sucesoras (quien depende de el)
    pkg_successors: dict[int, list] = defaultdict(list)
    for item in project['project_items']:
        if 'package' not in item: continue
        succ_name = item['package']['name'].strip()
        for dep in (item['package'].get('dependencies') or []):
            prereq_id = dep.get('prerequisite_id')
            if prereq_id:
                pkg_successors[prereq_id].append(succ_name)

    cto_raw:     list[dict] = []
    tower_tasks: dict[int, list] = defaultdict(list)
    seen_keys:   set[str] = set()

    for item in project['project_items']:
        if 'package' not in item: continue
        pkg  = item['package']
        name = pkg['name'].strip()
        path = item['path_outline']

        if name.startswith(_CTO_PREFIX):
            sd = pkg.get('start_date')
            if sd:
                cto_raw.append({'name': name, 'start': date.fromisoformat(sd)})
            continue

        if pkg.get('milestone'): continue

        path_names = [item_to_group.get(pid, '') for pid in path]
        if _CONTRACTS_GROUP in path_names: continue

        sd_str = pkg.get('start_date')
        ed_str = pkg.get('end_date')
        if not sd_str or not ed_str: continue
        try:
            task_start = date.fromisoformat(sd_str)
            task_end   = date.fromisoformat(ed_str)
        except ValueError:
            continue

        progress = float(pkg.get('progress_cache', 0))
        state    = pkg.get('work_state_cache', 'not_started')
        assigned = members.get(pkg.get('assigned_member_id'), '')

        # Resolver predecesoras y sucesoras por nombre
        predecessors = [
            pkg_id_to_name[dep['prerequisite_id']]
            for dep in (pkg.get('dependencies') or [])
            if dep.get('prerequisite_id') in pkg_id_to_name
        ]
        successors = list(pkg_successors.get(pkg['id'], []))

        # Filtro: inicia dentro del rango O atrasada con progreso
        starts_in_range = range_start <= task_start <= range_end
        is_delayed      = task_end < today and 0 < progress < 1.0

        if not starts_in_range and not is_delayed:
            continue

        dedup_key = name + sd_str
        if dedup_key in seen_keys: continue
        seen_keys.add(dedup_key)

        tower_id = None
        for pid in path:
            if pid in tower_item_ids:
                tower_id = pid
                break
        if tower_id is None: continue

        breadcrumb = [
            item_to_group[pid]
            for pid in path
            if pid in item_to_group
            and item_to_group[pid] not in skip_names
            and pid not in tower_item_ids
        ]

        category  = 'delayed' if is_delayed else 'starting'
        delay_str = compute_delay(task_start, task_end, today, category, state)

        tower_tasks[tower_id].append({
            'name':         name,
            'start':        task_start,
            'end':          task_end,
            'progress':     round(progress * 100),
            'delay_str':    delay_str,
            'state':        state,
            'category':     category,
            'breadcrumb':   breadcrumb,
            'assigned':     assigned,
            'predecessors': predecessors,
            'successors':   successors,
        })

    cto_items = _build_cto(cto_raw, tower_labels)

    towers = []
    for tid in sorted(tower_ids.keys(), key=lambda x: tower_labels.get(x, '')):
        tasks = tower_tasks.get(tid, [])
        if not tasks: continue
        groups: dict[str, list] = defaultdict(list)
        for t in tasks:
            key = ' › '.join(t['breadcrumb']) if t['breadcrumb'] else 'Sin grupo'
            groups[key].append(t)
        towers.append({
            'id':     tower_labels[tid],
            'label':  tower_labels[tid],
            'tasks':  tasks,
            'groups': dict(groups),
        })

    all_tasks = [t for tw in towers for t in tw['tasks']]
    kpis = {
        'starting':    sum(1 for t in all_tasks if t['category'] == 'starting'),
        'delayed':     sum(1 for t in all_tasks if t['category'] == 'delayed'),
        'in_progress': sum(1 for t in all_tasks if t['state'] == 'in_progress'),
        'completed':   sum(1 for t in all_tasks if t['state'] == 'completed'),
    }

    return {
        'project_name':     project['name'],
        'project_id':       project['id'],
        'overall_progress': float(project.get('progress_cache', 0)),
        'reference_date':   today,
        'week_start':       range_start,
        'week_end':         range_end,
        'range_days':       range_days,
        'is_range':         is_range,
        'gantt_meta':       gantt_meta,
        'gantt_cols':       gantt_cols,
        'towers':           towers,
        'cto_items':        cto_items,
        'kpis':             kpis,
    }


def _load(source) -> dict:
    if isinstance(source, dict): return source
    if isinstance(source, str):
        s = source.strip()
        if s.startswith('{'): return json.loads(s)
        with open(source, encoding='utf-8') as f: return json.load(f)
    return json.load(source)


def _build_cto(cto_raw, tower_labels) -> list:
    tower_names = set(tower_labels.values())
    result = []
    for c in cto_raw:
        name   = c['name']
        suffix = name[len(_CTO_PREFIX):]
        tower_label = None
        for tname in sorted(tower_names, key=len, reverse=True):
            if suffix.startswith(tname):
                tower_label = tname
                break
        if not tower_label:
            m = re.match(r'^(\S+)', suffix)
            if m: tower_label = m.group(1)
        name_lower = name.lower()
        if 'programación' in name_lower or 'programacion' in name_lower:
            tipo = 'Programación'
        elif 'obra' in name_lower:
            tipo = 'Obra'
        else:
            tipo = suffix.replace(tower_label or '', '').strip()
        result.append({'tower': tower_label or '?', 'label': tipo, 'date': c['start']})
    result.sort(key=lambda x: x['date'])
    return result


if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/uploads/Projecto.txt'
    ref  = date(2026, 2, 23)

    d1 = process_project(path, reference_date=ref)
    print(f"Fecha única: scale={d1['gantt_meta']['scale']} cols={len(d1['gantt_cols'])} tasks={sum(len(t['tasks']) for t in d1['towers'])}")

    d2 = process_project(path, reference_date=ref, date_end=date(2026, 3, 15))
    print(f"3 semanas:   scale={d2['gantt_meta']['scale']} cols={len(d2['gantt_cols'])} tasks={sum(len(t['tasks']) for t in d2['towers'])}")

    d3 = process_project(path, reference_date=ref, date_end=date(2026, 5, 23))
    print(f"3 meses:     scale={d3['gantt_meta']['scale']} cols={len(d3['gantt_cols'])} tasks={sum(len(t['tasks']) for t in d3['towers'])}")

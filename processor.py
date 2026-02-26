"""
processor.py  v3
- Completadas → delay_str siempre '—'
- Semana lun–sáb
- Atraso dinámico por fecha de corte
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


def compute_delay(task_start: date, task_end: date,
                  reference_date: date, category: str, state: str) -> str:
    """
    Reglas:
    - completed → siempre '—'
    - delayed   → reference_date - task_end
    - starting  → reference_date - task_start (solo si task_start < reference_date)
    Tope >= 100 → '+99'. Sin '+' en valores normales.
    """
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


def process_project(source, reference_date: date = None) -> dict:
    today      = reference_date or date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end   = week_start + timedelta(days=5)   # sábado

    raw     = _load(source)
    project = raw['project']

    item_to_group: dict[int, str] = {}
    for item in project['project_items']:
        if 'group' in item:
            item_to_group[item['id']] = item['group']['name'].strip()

    tower_ids: dict[int, str] = {}
    for item in project['project_items']:
        if 'package' not in item:
            continue
        path = item['path_outline']
        if len(path) >= 3:
            tid = path[2]
            if tid in item_to_group and tid not in tower_ids:
                tower_ids[tid] = item_to_group[tid]

    root_names: set[str] = set()
    for item in project['project_items']:
        if 'package' not in item:
            continue
        path = item['path_outline']
        if path and path[0] in item_to_group:
            root_names.add(item_to_group[path[0]])

    skip_names     = _SKIP_GROUP_PATTERNS | root_names
    tower_item_ids = set(tower_ids.keys())
    tower_labels   = dict(tower_ids)

    cto_raw:     list[dict] = []
    tower_tasks: dict[int, list] = defaultdict(list)
    seen_keys:   set[str] = set()

    for item in project['project_items']:
        if 'package' not in item:
            continue
        pkg  = item['package']
        name = pkg['name'].strip()
        path = item['path_outline']

        if name.startswith(_CTO_PREFIX):
            sd = pkg.get('start_date')
            if sd:
                cto_raw.append({'name': name, 'start': date.fromisoformat(sd)})
            continue

        if pkg.get('milestone'):
            continue

        path_names = [item_to_group.get(pid, '') for pid in path]
        if _CONTRACTS_GROUP in path_names:
            continue

        sd_str = pkg.get('start_date')
        ed_str = pkg.get('end_date')
        if not sd_str or not ed_str:
            continue
        try:
            task_start = date.fromisoformat(sd_str)
            task_end   = date.fromisoformat(ed_str)
        except ValueError:
            continue

        progress = float(pkg.get('progress_cache', 0))
        state    = pkg.get('work_state_cache', 'not_started')

        starts_this_week = week_start <= task_start <= week_end
        is_delayed       = task_end < today and 0 < progress < 1.0

        if not starts_this_week and not is_delayed:
            continue

        dedup_key = name + sd_str
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)

        tower_id = None
        for pid in path:
            if pid in tower_item_ids:
                tower_id = pid
                break
        if tower_id is None:
            continue

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
            'name':       name,
            'start':      task_start,
            'end':        task_end,
            'progress':   round(progress * 100),
            'delay_str':  delay_str,
            'state':      state,
            'category':   category,
            'breadcrumb': breadcrumb,
        })

    cto_items = _build_cto(cto_raw, tower_labels)

    towers = []
    for tid in sorted(tower_ids.keys(), key=lambda x: tower_labels.get(x, '')):
        tasks = tower_tasks.get(tid, [])
        if not tasks:
            continue
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
        'week_start':       week_start,
        'week_end':         week_end,
        'towers':           towers,
        'cto_items':        cto_items,
        'kpis':             kpis,
    }


def _load(source) -> dict:
    if isinstance(source, dict):
        return source
    if isinstance(source, str):
        s = source.strip()
        if s.startswith('{'):
            return json.loads(s)
        with open(source, encoding='utf-8') as f:
            return json.load(f)
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
            if m:
                tower_label = m.group(1)
        name_lower = name.lower()
        if 'programación' in name_lower or 'programacion' in name_lower:
            tipo = 'Programación'
        elif 'obra' in name_lower:
            tipo = 'Obra'
        else:
            tipo = suffix.replace(tower_label or '', '').strip()
        result.append({
            'tower': tower_label or '?',
            'label': tipo,
            'date':  c['start'],
        })
    result.sort(key=lambda x: x['date'])
    return result


if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/uploads/Projecto.txt'
    data = process_project(path, reference_date=date(2026, 2, 23))
    print(f"OK: {data['project_name']} | {len(data['towers'])} torres | CTO: {len(data['cto_items'])}")
    for t in data['towers']:
        completed = [x for x in t['tasks'] if x['state']=='completed']
        for c in completed[:2]:
            print(f"  COMPLETADA: {c['name'][:40]} → delay={c['delay_str']}")

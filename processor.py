"""
processor.py
============
Lee el JSON exportado desde Geniebelt y retorna datos estructurados
listos para renderizar. No depende de Streamlit ni de HTML.

Uso:
    from processor import process_project
    data = process_project("proyecto.json")
    data = process_project(json_string)   # también acepta string
"""

import json
from datetime import date, timedelta
from collections import defaultdict


# ─── Constantes internas ───────────────────────────────────────────────────────

# Grupos raíz que nunca queremos mostrar como breadcrumb
_SKIP_GROUP_PATTERNS = {
    'CONSTRUCCIÓN', 'CONSTRUCTION',
    'HITOS IMPORTANTES', 'CONTRATOS', 'CONTRACTS',
    'FECHA DE CORTE',
}

# Prefijo que identifica una tarea como CTO
_CTO_PREFIX = 'CTO-'

# Nombre del grupo que identifica contratos (para excluirlos)
_CONTRACTS_GROUP = 'CONTRATOS'


# ─── Función principal ─────────────────────────────────────────────────────────

def process_project(source, reference_date: date = None) -> dict:
    """
    Procesa el JSON de un proyecto Geniebelt.

    Args:
        source: ruta a archivo .json/.txt  OR  string con el JSON  OR  dict ya parseado
        reference_date: fecha de corte (default: hoy)

    Returns dict con:
        {
          "project_name": str,
          "project_id": int,
          "overall_progress": float,         # 0.0 – 1.0
          "reference_date": date,
          "week_start": date,
          "week_end": date,
          "towers": [                         # lista ordenada de torres detectadas
              {
                "id": str,                   # ej. "T1"
                "label": str,                # ej. "Torre 1" o nombre real del grupo
                "tasks": [                   # tareas agrupadas
                    {
                      "name": str,
                      "start": date,
                      "end": date,
                      "progress": int,       # 0–100
                      "delay": int,          # días según Geniebelt
                      "state": str,          # not_started / in_progress / completed
                      "category": str,       # "starting" | "delayed"
                      "breadcrumb": [str],   # agrupadores sin torre ni raíz
                    }
                ],
                "groups": {                  # tareas indexadas por breadcrumb key
                    "OBRA GRIS › Cubierta": [task, ...]
                }
              }
          ],
          "cto_items": [                     # hitos CTO detectados
              {
                "tower": str,               # "T1", "T2", etc.
                "label": str,               # "Programación" | "Obra" | nombre completo
                "date": date,
                "days_from_reference": int,
              }
          ],
          "kpis": {
              "starting": int,
              "delayed": int,
              "in_progress": int,
              "completed": int,
          }
        }
    """
    today = reference_date or date.today()
    week_start = today - timedelta(days=today.weekday())   # lunes
    week_end   = week_start + timedelta(days=4)            # viernes

    # ── Cargar JSON ────────────────────────────────────────────────────────────
    raw = _load(source)
    project = raw['project']

    # ── Mapa de project_item id → nombre de grupo ─────────────────────────────
    item_to_group: dict[int, str] = {}
    for item in project['project_items']:
        if 'group' in item:
            item_to_group[item['id']] = item['group']['name'].strip()

    # ── Detectar torres dinámicamente ─────────────────────────────────────────
    # Una "torre" es un grupo cuyo padre inmediato es CONSTRUCCIÓN.
    # Lo identificamos como el nivel 3 del path_outline (índice 2).
    # Recorremos todos los package items para encontrar los ids de grupos torre.
    tower_ids: dict[int, str] = {}   # item_id → nombre
    for item in project['project_items']:
        if 'package' not in item:
            continue
        path = item['path_outline']
        if len(path) >= 3:
            tid = path[2]
            if tid in item_to_group and tid not in tower_ids:
                tower_ids[tid] = item_to_group[tid]

    # ── Detectar nombre raíz del proyecto (nivel 0) ───────────────────────────
    root_names: set[str] = set()
    for item in project['project_items']:
        if 'package' not in item:
            continue
        path = item['path_outline']
        if path and path[0] in item_to_group:
            root_names.add(item_to_group[path[0]])

    skip_names = _SKIP_GROUP_PATTERNS | root_names

    # ── Construir set de ids de grupos torre ──────────────────────────────────
    tower_item_ids = set(tower_ids.keys())

    # ── Detectar nombres de torres (limpiar prefijos numéricos si los hay) ────
    # Construir map: tower_item_id → label limpio
    tower_labels: dict[int, str] = {}
    for tid, tname in tower_ids.items():
        tower_labels[tid] = tname  # usamos el nombre real del grupo

    # ── Procesar items ─────────────────────────────────────────────────────────
    cto_raw: list[dict] = []
    tower_tasks: dict[int, list] = defaultdict(list)  # tower_item_id → tasks
    seen_task_keys: set[str] = set()

    for item in project['project_items']:
        if 'package' not in item:
            continue

        pkg   = item['package']
        name  = pkg['name'].strip()
        path  = item['path_outline']

        # ── CTO: capturar y saltar ─────────────────────────────────────────────
        if name.startswith(_CTO_PREFIX):
            sd = pkg.get('start_date')
            if sd:
                cto_raw.append({
                    'name':  name,
                    'start': date.fromisoformat(sd),
                    'tower_path': path,
                })
            continue

        # ── Excluir hitos que no sean CTO ─────────────────────────────────────
        if pkg.get('milestone'):
            continue

        # ── Excluir contratos ──────────────────────────────────────────────────
        path_names = [item_to_group.get(pid, '') for pid in path]
        if _CONTRACTS_GROUP in path_names:
            continue

        # ── Fechas y progreso ──────────────────────────────────────────────────
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
        delay    = int(pkg.get('delay_cache', 0) or 0)
        state    = pkg.get('work_state_cache', 'not_started')

        # ── Filtro: inicia esta semana O atrasada con progreso ─────────────────
        starts_this_week = week_start <= task_start <= week_end
        is_delayed       = task_end < today and 0 < progress < 1.0

        if not starts_this_week and not is_delayed:
            continue

        # ── Deduplicar ─────────────────────────────────────────────────────────
        dedup_key = name + sd_str
        if dedup_key in seen_task_keys:
            continue
        seen_task_keys.add(dedup_key)

        # ── Detectar torre ─────────────────────────────────────────────────────
        tower_id = None
        for pid in path:
            if pid in tower_item_ids:
                tower_id = pid
                break
        if tower_id is None:
            continue   # tarea sin torre conocida, saltar

        # ── Breadcrumb: excluir raíz, construcción y torre ────────────────────
        breadcrumb = [
            item_to_group[pid]
            for pid in path
            if pid in item_to_group
            and item_to_group[pid] not in skip_names
            and pid not in tower_item_ids
        ]

        task = {
            'name':       name,
            'start':      task_start,
            'end':        task_end,
            'progress':   round(progress * 100),
            'delay':      delay,
            'state':      state,
            'category':   'delayed' if is_delayed else 'starting',
            'breadcrumb': breadcrumb,
        }
        tower_tasks[tower_id].append(task)

    # ── Construir CTO items ────────────────────────────────────────────────────
    cto_items = _build_cto(cto_raw, item_to_group, tower_item_ids, tower_labels, today)

    # ── Construir lista de torres ordenada ────────────────────────────────────
    towers = []
    for tid in sorted(tower_ids.keys(), key=lambda x: tower_labels.get(x, '')):
        tasks = tower_tasks.get(tid, [])
        if not tasks:
            continue

        # Agrupar por breadcrumb
        groups: dict[str, list] = defaultdict(list)
        for t in tasks:
            key = ' › '.join(t['breadcrumb']) if t['breadcrumb'] else 'Sin grupo'
            groups[key].append(t)

        towers.append({
            'id':     tower_labels[tid],   # nombre real como id ("T1", "Torre A", etc.)
            'label':  tower_labels[tid],
            'tasks':  tasks,
            'groups': dict(groups),
        })

    # ── KPIs ──────────────────────────────────────────────────────────────────
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


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _load(source) -> dict:
    if isinstance(source, dict):
        return source
    if isinstance(source, str):
        # ¿es ruta o JSON string?
        stripped = source.strip()
        if stripped.startswith('{'):
            return json.loads(stripped)
        with open(source, encoding='utf-8') as f:
            return json.load(f)
    # file-like object (ej. uploaded file de Streamlit)
    return json.load(source)


def _build_cto(cto_raw, item_to_group, tower_item_ids, tower_labels, today) -> list:
    """Estructura los items CTO por torre y tipo."""
    import re

    # Construir set de nombres de torre conocidos para matching
    tower_names = set(tower_labels.values())

    result = []
    for c in cto_raw:
        name = c['name']  # ej. "CTO-T1 Certificado Técnico de Ocupación Programación"

        # 1. Intentar extraer torre desde el nombre: buscar patrón CTO-XXXX
        #    donde XXXX puede ser T1, T2, Torre A, etc.
        tower_label = None
        suffix = name[len(_CTO_PREFIX):]   # "T1 Certificado Técnico..."

        # Buscar si algún nombre de torre conocido aparece al inicio del suffix
        for tname in sorted(tower_names, key=len, reverse=True):  # más largo primero
            if suffix.startswith(tname):
                tower_label = tname
                break

        # Fallback: tomar primera "palabra(s)" antes del primer espacio+mayúscula larga
        if not tower_label:
            m = re.match(r'^(\S+)', suffix)
            if m:
                tower_label = m.group(1)

        # 2. Detectar tipo: Programación / Obra / otro
        name_lower = name.lower()
        if 'programación' in name_lower or 'programacion' in name_lower:
            tipo = 'Programación'
        elif 'obra' in name_lower:
            tipo = 'Obra'
        else:
            tipo = suffix.replace(tower_label or '', '').strip()

        days_diff = (c['start'] - today).days

        result.append({
            'tower':               tower_label or '?',
            'label':               tipo,
            'date':                c['start'],
            'days_from_reference': days_diff,
        })

    # Ordenar por torre y luego por fecha
    result.sort(key=lambda x: (x['tower'], x['date']))
    return result




# ─── Test rápido ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/uploads/Projecto.txt'
    ref  = date(2026, 2, 23)

    data = process_project(path, reference_date=ref)

    print(f"Proyecto : {data['project_name']} (id: {data['project_id']})")
    print(f"Avance   : {data['overall_progress']*100:.1f}%")
    print(f"Semana   : {data['week_start']} → {data['week_end']}")
    print(f"Torres   : {[t['id'] for t in data['towers']]}")
    print()
    for tw in data['towers']:
        nd = sum(1 for t in tw['tasks'] if t['category']=='delayed')
        ns = sum(1 for t in tw['tasks'] if t['category']=='starting')
        print(f"  {tw['id']:6}  {len(tw['tasks']):3} tareas  |  {ns} programadas  |  {nd} atrasadas")
        for grp, tasks in tw['groups'].items():
            print(f"    [{grp}]  → {len(tasks)} tareas")
    print()
    print(f"CTO items: {len(data['cto_items'])}")
    for c in data['cto_items']:
        sign = '+' if c['days_from_reference'] >= 0 else ''
        print(f"  {c['tower']:4} {c['label']:15} {str(c['date'])}  ({sign}{c['days_from_reference']}d)")
    print()
    print(f"KPIs: {data['kpis']}")

# 🏗️ Chronos

Genera reportes semanales de obra a partir de los archivos JSON exportados desde Geniebelt.
Funciona con cualquier proyecto: detecta torres, agrupadores y fechas CTO automáticamente.

---

## Archivos del proyecto

```
app.py            ← Interfaz Streamlit (subida de archivos, tabs, descarga)
processor.py      ← Lógica de datos: lee el JSON y estructura la información
renderer.py       ← Genera el HTML del dashboard
requirements.txt  ← Dependencias (solo streamlit)
```

---

## Cómo correrlo localmente

### 1. Requisitos
- Python 3.10 o superior
- pip

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar

```bash
streamlit run app.py
```

Se abrirá automáticamente en `http://localhost:8501`

---

## Deploy en Streamlit Cloud (acceso desde cualquier lugar)

### Paso 1 — Crear repositorio en GitHub

1. Ve a [github.com](https://github.com) y crea una cuenta si no tienes
2. Crea un nuevo repositorio (puede ser privado)
3. Sube los 4 archivos:
   - `app.py`
   - `processor.py`
   - `renderer.py`
   - `requirements.txt`

Desde la terminal:
```bash
git init
git add app.py processor.py renderer.py requirements.txt
git commit -m "Initial commit"
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

### Paso 2 — Conectar con Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Inicia sesión con tu cuenta de GitHub
3. Clic en **"New app"**
4. Selecciona tu repositorio y rama (`main`)
5. En "Main file path" escribe: `app.py`
6. Clic en **"Deploy"**

En 2-3 minutos tendrás una URL del tipo:
```
https://TU_USUARIO-TU_REPO-app-XXXX.streamlit.app
```

### Paso 3 — Uso semanal

Cada semana:
1. Abre la URL de tu app
2. Exporta los JSON desde Geniebelt (uno por proyecto)
3. Súbelos en el panel izquierdo
4. Selecciona la fecha de corte (lunes de la semana)
5. Descarga el HTML de cada proyecto
6. Abre el HTML en Chrome → `Ctrl+P` → **Guardar como PDF**

---

## Cómo exportar el JSON desde Geniebelt

1. Abre el proyecto en Geniebelt
2. Clic en los **tres puntos (···)** en la esquina superior derecha
3. Selecciona **Exportar**
4. Elige formato **JSON**
5. Descarga el archivo

---

## Lógica del reporte

| Criterio | Incluido |
|---|---|
| Actividades que inician en la semana seleccionada | ✅ |
| Actividades atrasadas con progreso > 0% | ✅ |
| Hitos (milestones) | ❌ excluidos |
| Contratos (grupo CONTRATOS) | ❌ excluidos |
| Actividades sin iniciar aunque estén vencidas | ❌ excluidas |

**Código de colores:**
- 🔵 Azul → programada esta semana, sin atraso
- 🟡 Naranja → en progreso con atraso
- 🔴 Rojo → atrasada con progreso
- 🟢 Verde → completada
- ⚪ Gris → pendiente sin atraso registrado

---

## Actualizar el código

Si necesitas cambiar algo (diseño, lógica, nuevos campos):

```bash
# Edita los archivos localmente
git add .
git commit -m "Descripción del cambio"
git push
```

Streamlit Cloud detecta el cambio y se actualiza automáticamente en ~1 minuto.

# Guía de Contribución — El Faro del Viajero

Gracias por formar parte del equipo. Este documento explica todo lo que necesitas saber para contribuir al proyecto de forma ordenada y sin conflictos con el resto de los equipos.

> **Lee este archivo completo antes de hacer tu primer commit.** Seguir estas reglas es responsabilidad de cada integrante, no solo de los líderes.

---

## Tabla de contenidos

1. [Configuración del entorno local](#1-configuración-del-entorno-local)
2. [Ramas y flujo de trabajo en Git](#2-ramas-y-flujo-de-trabajo-en-git)
3. [Modelos y migraciones](#3-modelos-y-migraciones)

---

## 1. Configuración del entorno local

### 1.1 Requisitos previos

Antes de clonar el repositorio asegúrate de tener instalado:

- Python 3.11+
- PostgreSQL 15+
- Git

### 1.2 Clonar e instalar dependencias

```bash
git clone https://github.com/org/faro-del-viajero.git
cd faro-del-viajero
python -m venv venv
source venv/bin/activate        # Mac / Linux
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

### 1.3 Configurar las variables de entorno

El repositorio incluye un archivo `.env.example` con todas las variables necesarias pero sin valores reales. **Nunca edites ese archivo directamente.**

```bash
# Copia el archivo y llena tus propios valores
cp .env.example .env
```

Edita `.env` con tus credenciales locales:

```env
SECRET_KEY=django-insecure-reemplaza-esto-con-una-clave-larga
DEBUG=True

DB_NAME=faro_viajero_db
DB_USER=tu_usuario_postgres
DB_PASSWORD=tu_password_local
DB_HOST=localhost
DB_PORT=5432
```

> ⚠️ **El archivo `.env` nunca se sube al repositorio.** Ya está en `.gitignore`. Si accidentalmente lo subes, notifica al líder de proyecto de inmediato para rotar las credenciales.

### 1.4 Crear la base de datos local

```bash
# Entra a PostgreSQL
psql -U postgres

# Ejecuta estos comandos dentro de psql
CREATE DATABASE faro_viajero_db;
CREATE USER tu_usuario_postgres WITH PASSWORD 'tu_password_local';
GRANT ALL PRIVILEGES ON DATABASE faro_viajero_db TO tu_usuario_postgres;
\q
```

### 1.5 Aplicar migraciones y verificar

```bash
python manage.py migrate
python manage.py runserver
```

Si el servidor levanta sin errores en `http://127.0.0.1:8000`, tu entorno está listo.

---

## 2. Ramas y flujo de trabajo en Git

### 2.1 Estructura de ramas

```
main                        # Entrega final. Nunca recibe push directo.
└── develop                 # Integración. Nunca recibe push directo.
    ├── common              # Archivos globales (config/, base.html). Solo líder de proyecto.
    ├── feature/modulo-a    # Rama de trabajo del Equipo 1
    ├── feature/modulo-b    # Rama de trabajo del Equipo 2
    └── feature/modulo-c    # Rama de trabajo del Equipo 3
```

| Rama | ¿Quién aprueba el PR? |
|---|---|
| `feature/*` → `develop` | 2 integrantes del equipo dueño del módulo |
| `common` → `develop` | Líder de proyecto |
| `develop` → `main` | Líder de proyecto |

### 2.2 Flujo de trabajo diario

```bash
# 1. Siempre trabaja en tu rama. Verifica antes de empezar.
git checkout feature/mi-modulo
git status

# 2. Sincroniza tu rama antes de empezar a trabajar
git pull origin feature/mi-modulo

# 3. Haz tus cambios, luego agrégalos y haz commit
git add .
git commit -m "[CONTROLADOR] Implementar vista de registro de integrante"

# 4. Sube tus cambios
git push origin feature/mi-modulo

# 5. Cuando el módulo esté listo, abre un Pull Request en GitHub
#    feature/mi-modulo → develop
```

### 2.3 Estándar de commits

Todo commit debe comenzar con una etiqueta entre corchetes:

| Etiqueta | Cuándo usarla |
|---|---|
| `[MODELO]` | Cambios en `models.py` o migraciones |
| `[VISTA]` | Cambios en `templates/`, HTML o CSS |
| `[CONTROLADOR]` | Cambios en `views.py` o `services.py` |
| `[FIX]` | Corrección de errores o bugs |
| `[DOC]` | Actualización de docstrings o comentarios |
| `[UPDATE]` | Cambios estructurales o de configuración |

```bash
# Ejemplos correctos
git commit -m "[MODELO] Agregar campo telefono a PerfilUsuario"
git commit -m "[FIX] Corregir error 500 en endpoint de pagos"
git commit -m "[DOC] Actualizar docstrings en services.py de viajes"
```

### 2.4 Reglas de oro

1. **No hacer push directo a `main` ni a `develop`.** Siempre mediante Pull Request.
2. **No hacer merge manual desde la terminal** en ramas protegidas. GitHub se encarga con el PR aprobado.
3. **No tocar archivos de `config/` ni `templates/base.html`** desde una rama `feature/*`. Si necesitas un cambio global, abre un Issue y notifica al líder de proyecto.
4. **No jalar directamente la rama `feature/*` de otro equipo.** Si dependes de su módulo, espera a que lo integren en `develop` y jala desde ahí.

### 2.5 Incorporar dependencias de otro módulo

Cuando el equipo del que dependes notifique que su módulo está en `develop`:

```bash
# Estando en tu rama de trabajo
git checkout feature/mi-modulo

# Jala los cambios de develop hacia tu rama
git pull origin develop

# Aplica las migraciones nuevas que puedan venir incluidas
python manage.py migrate

# Prueba localmente que todo funciona antes de continuar
python manage.py runserver
```

> Si encuentras un error en el código de otro módulo, **no lo corriges en tu rama**. Abre un Issue en GitHub dirigido al equipo responsable y espera a que ellos hagan el fix y lo suban a `develop`.

### 2.6 Resolver conflictos

```bash
# Después de un pull con conflictos, Git marca los archivos afectados
# Abre el archivo y busca las marcas:

# <<<<<<< HEAD          (tu código)
# tu_version = True
# =======
# version_develop = True
# >>>>>>> origin/develop

# Edita el archivo dejando la versión correcta, luego:
git add archivo_con_conflicto.py
git commit -m "[FIX] Resolver conflicto en models.py al integrar dependencia de auth"
```

---

## 3. Modelos y migraciones

### 3.1 Reglas fundamentales

**Un módulo, un dueño.** Solo el equipo asignado a un módulo genera migraciones para ese módulo. Aunque hayas jalado el código de otro equipo, nunca corras `makemigrations` sobre un módulo que no es tuyo.

**La migración y el modelo van juntos.** Cada vez que modificas `models.py` debes generar su migración en el mismo commit. Nunca subas uno sin el otro.

**Nunca modifiques una migración que ya está en `develop`.** Si necesitas corregir algo, genera una migración nueva encima.

### 3.2 Flujo para crear o modificar un modelo

```bash
# 1. Jala develop antes de cualquier cambio en modelos
git pull origin develop
python manage.py migrate   # Aplica migraciones pendientes de otros módulos

# 2. Modifica tu models.py

# 3. Genera la migración SOLO para tu módulo
python manage.py makemigrations nombre_modulo

# 4. Aplica y verifica localmente
python manage.py migrate
python manage.py runserver

# 5. Sube modelo y migración en el mismo commit
git add apps/nombre_modulo/models.py
git add apps/nombre_modulo/migrations/
git commit -m "[MODELO] Agregar campo direccion a PerfilUsuario"
```

> ⚠️ **Nunca corras `makemigrations` sin especificar el nombre del módulo.** El comando `python manage.py makemigrations` sin argumentos puede generar migraciones en módulos que no son tuyos si detecta cambios en ellos.

### 3.3 ForeignKey entre módulos

Cuando tu modelo necesita referenciar un modelo de otro módulo, usa la referencia como string en lugar de importar directamente. Esto evita importaciones circulares y dependencias frágiles entre apps.

```python
# ❌ Incorrecto — acoplamiento fuerte, puede causar errores de importación
from apps.autenticacion.models import Usuario

class Integrante(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)


# ✅ Correcto — Django resuelve la referencia en tiempo de ejecución
class Integrante(models.Model):
    usuario = models.ForeignKey(
        'autenticacion.Usuario',
        on_delete=models.CASCADE,
        related_name='integrantes',
    )
```

Además, antes de hacer esta referencia el modelo `Usuario` debe estar integrado en `develop`. No hagas `ForeignKey` a código que solo existe en la rama de otro equipo.

### 3.4 Resolver conflictos de migraciones

Si al correr `migrate` Django detecta dos migraciones con el mismo número en el mismo módulo, resuélvelo así:

```bash
# Django indica el conflicto
python manage.py migrate
# CommandError: Conflicting migrations detected in app 'nombre_modulo'

# Genera un archivo de merge automático
python manage.py makemigrations --merge nombre_modulo

# Revisa el archivo generado, aplica y sube
python manage.py migrate
git add apps/nombre_modulo/migrations/
git commit -m "[MODELO] Resolver conflicto de migraciones en nombre_modulo"
```

> El conflicto lo resuelve el **líder del módulo afectado**, no cualquier integrante. Si no es tu módulo, notifica al líder correspondiente.

### 3.5 Datos de prueba (fixtures)

Cada módulo debe incluir un fixture con datos básicos para desarrollo. Esto permite que otros equipos que dependan de tu módulo puedan probar sin crear datos a mano.

```bash
# Crear el fixture desde los datos que tienes en tu base de datos local
python manage.py dumpdata nombre_modulo --indent 2 > apps/nombre_modulo/fixtures/seed.json

# Cargar el fixture (propio o de otro módulo)
python manage.py loaddata apps/nombre_modulo/fixtures/seed.json
```

El fixture se sube al repositorio junto con el módulo. Si el modelo cambia, el fixture debe actualizarse en el mismo PR.

### 3.6 Checklist antes de abrir un PR con cambios en modelos

Antes de abrir un Pull Request que incluya cambios en `models.py`, verifica:

- [ ] Jalé `develop` antes de generar la migración.
- [ ] Corrí `makemigrations nombre_modulo` (con el nombre del módulo, no genérico).
- [ ] Corrí `migrate` localmente y no hay errores.
- [ ] El commit incluye tanto `models.py` como la carpeta `migrations/`.
- [ ] Las referencias a modelos de otros módulos usan string (`'app.Modelo'`), no imports.
- [ ] El fixture del módulo está actualizado si el modelo cambió.
- [ ] El servidor levanta sin errores tras los cambios.

---

*¿Algo no está claro o encontraste un caso que esta guía no cubre? Notifícalo en el canal `#git-y-prs` de Discord o abre un Issue con la etiqueta `documentacion`.*
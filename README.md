# El Faro del Viajero

Aplicación web de turismo cultural desarrollada con **Django** y **PostgreSQL**.

---

## Equipo

| Equipo | Líder | Integrantes |
|---|---|---|
| Equipo 1 | Vladimir González Flores | Miguel Mendez · Erendil Aguilar · Selim Barreto |
| Equipo 2 | Hector Daniel Rodriguez Guarneros | Ethan Wallberg · Gerardo Juárez · José Cervantes |
| Equipo 3 | Alexis Yael Hernández González | Oscar Pallares · Andrea Espitia · Dario Romero |

---

## Estructura de ramas

```
main                        # Entrega final — nunca recibe push directo
└── develop                 # Integración — nunca recibe push directo
    ├── common              # Archivos globales (solo líder de proyecto)
    ├── feature/modulo-a    # Equipo 1
    ├── feature/modulo-b    # Equipo 2
    └── feature/modulo-c    # Equipo 3
```

Cada integrante trabaja exclusivamente en la rama `feature/*` de su equipo. **Ningún equipo toca la rama de otro.**

---

## Reglas de oro

### Push y Pull

- Nunca hacer `push` directo a `main` o `develop`.
- Siempre hacer `git pull origin feature/mi-modulo` antes de empezar a trabajar.
- Para incorporar código de otro módulo: `git pull origin develop` **dentro de tu rama**, nunca cambiarte a `develop`.
- Nunca jalar directamente la rama `feature/*` de otro equipo.

### Pull Requests

- Todo cambio a `develop` o `main` requiere un **Pull Request aprobado**. Sin excepciones.
- Nunca hacer merge manual desde la terminal en ramas protegidas.
- Un PR debe estar **probado localmente** antes de abrirse. `develop` no es un entorno de pruebas.

| PR | Aprobadores requeridos |
|---|---|
| `feature/*` → `develop` | 2 integrantes del equipo dueño del módulo |
| `common` → `develop` | Líder de proyecto |
| `develop` → `main` | Líder de proyecto |

### Archivos globales

- Nadie toca `config/`, `templates/base.html` ni `.env.example` desde una rama `feature/*`.
- Si necesitas un cambio global, abre un Issue y notifica al líder de proyecto.

---

## Commits

Formato obligatorio: `[ETIQUETA] Descripción corta en imperativo`

| Etiqueta | Cuándo |
|---|---|
| `[MODELO]` | Cambios en `models.py` o migraciones |
| `[VISTA]` | Cambios en `templates/` o CSS |
| `[CONTROLADOR]` | Cambios en `views.py` o `services.py` |
| `[FIX]` | Corrección de errores |
| `[DOC]` | Documentación o comentarios |
| `[UPDATE]` | Cambios estructurales o de configuración |

```bash
# Ejemplos
git commit -m "[MODELO] Agregar campo telefono a PerfilUsuario"
git commit -m "[FIX] Corregir error 500 en endpoint de pagos"
git commit -m "[CONTROLADOR] Implementar vista de registro"
```

---

## Flujo de trabajo diario

```bash
# 1. Posicionarte en tu rama
git checkout feature/mi-modulo

# 2. Sincronizar antes de empezar
git pull origin feature/mi-modulo

# 3. Trabajar, agregar y hacer commit
git add .
git commit -m "[ETIQUETA] Descripción"

# 4. Subir cambios
git push origin feature/mi-modulo

# 5. Cuando el módulo esté listo → abrir PR en GitHub hacia develop
```

---

## Configuración del entorno

Consulta [CONTRIBUTING.md](./CONTRIBUTING.md) para el proceso completo de instalación, configuración de `.env`, PostgreSQL y migraciones.

---

## Modelos y migraciones — resumen rápido

- Solo el equipo dueño de un módulo genera sus migraciones.
- Siempre `git pull origin develop` + `python manage.py migrate` antes de modificar un modelo.
- `models.py` y su migración van **siempre en el mismo commit**.
- Las referencias a modelos de otros módulos usan string: `'app.Modelo'`, nunca imports directos.
- Nunca modificar una migración que ya está en `develop`.

---

*Para las reglas completas del proyecto consulta [CONTRIBUTING.md](./CONTRIBUTING.md).*
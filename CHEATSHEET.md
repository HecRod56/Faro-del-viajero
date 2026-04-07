# Git — Referencia Rápida

---

## 1. ¿En qué rama trabajo?

Siempre en la rama de tu equipo. Nunca en `develop` ni en `main`.

```
Equipo 1 → feature/modulo-a
Equipo 2 → feature/modulo-b
Equipo 3 → feature/modulo-c
```

**Antes de empezar a trabajar cada día:**

```bash
git checkout feature/mi-modulo        # Asegúrate de estar en tu rama
git pull origin feature/mi-modulo     # Cambios de tus compañeros de equipo
git pull origin develop               # Cambios de otros módulos (si te avisaron)
python manage.py migrate              # Siempre después de jalar develop
```

---

## 2. ¿Cómo subo mi avance?

```bash
git add .
git commit -m "[ETIQUETA] Descripción corta"
git push origin feature/mi-modulo
```
***Revisa lo que subes antes de subirlo***
```bash
git add .
git status
```
Revisa lo que subes antes de un commit

**Etiquetas:**

| Etiqueta | Cuándo |
|---|---|
| `[MODELO]` | Cambios en `models.py` o migraciones |
| `[VISTA]` | Cambios en `templates/` o CSS |
| `[CONTROLADOR]` | Cambios en `views.py` o `services.py` |
| `[FIX]` | Corrección de errores |
| `[DOC]` | Documentación o comentarios |
| `[UPDATE]` | Configuración o estructura de carpetas |

---

## 3. ¿Cuándo y cómo hago merge a develop?

**Cuándo:** cuando puedas mostrarla funcionando en pantalla sin errores y probada localmente. No antes.

**Cómo:** abriendo un **Pull Request en GitHub**. Nunca con `git merge` desde la terminal.

```
feature/mi-modulo → develop
```

El PR necesita la aprobación de **2 integrantes de tu equipo** antes de hacer merge.

> `develop` no es un entorno de pruebas. Si subes algo roto, bloqueas a los otros equipos.

¿Como sé si mi modulo NO esta roto?
Debe de cumplir al menos lo siguiente:
1. La app corre sin errores
2. Carga en el navegador
3. No rompe otras paginas
---

## 4. ¿Qué hago si hay un error en un módulo que no es mío?

1. **No lo corrijas en tu rama.**
2. Abre un **Issue en GitHub** describiendo el error y asígnalo al equipo responsable.
3. Avisa en el canal `#bugs` de Discord.
4. Espera a que ellos hagan el fix, lo suban a `develop`, y entonces haz
```bash
  git fetch origin
  git merge origin/develop
```
---

## 5. ¿Cuándo uso makemigrations y cuándo migrate?

| Comando | Cuándo |
|---|---|
| `makemigrations nombre_modulo` | Solo cuando **tú** modificaste `models.py` de tu módulo |
| `migrate` | Siempre que jalás `develop`, aunque no hayas tocado modelos |

```bash
# Modificaste tu models.py → genera y aplica
python manage.py makemigrations nombre_modulo
python manage.py migrate

# Jalaste develop → solo aplica
python manage.py migrate
```

> ⚠️ Nunca corras `makemigrations` sin especificar el nombre de tu módulo.
> Nunca subas `models.py` sin su migración, ni una migración sin su `models.py`.

## 6. ¿Qué hago si hay conflictos?

1. No entres en pánico.
2. No hagas push.
3. Pide ayuda a tu equipo o al responsable técnico.
4. No borres código sin entenderlo.

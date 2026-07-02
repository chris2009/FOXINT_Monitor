# OSINT Monitor

Plataforma local de monitoreo de **páginas públicas** de redes sociales (Facebook primero, TikTok en fase futura), inspirada conceptualmente en **Intelion by ISID**. Ingesta vía **APIs oficiales** (Graph API de Meta), bus de analizadores pluggable (keywords, sentimiento, detección de lives), alertas en tiempo real y dashboard web — **todo corriendo en local, sin servicios de nube**.

> Documento de referencia completo (arquitectura, modelo de datos, roadmap, marco legal): [`PROYECTO_OSINT_MONITOR.md`](./PROYECTO_OSINT_MONITOR.md). Este README es la guía práctica de instalación y uso.

---

## ⚠️ Alcance legal (leer antes de usar)

- El sistema **SOLO monitorea Páginas públicas** de Facebook (empresas, medios, instituciones, cuentas verificadas como Página). **NUNCA perfiles personales.**
- La distinción se aplica con una **validación técnica automática**: al registrar un objetivo, el backend llama a la Graph API pidiendo el campo `category`. Si el objetivo no lo expone, es un perfil personal y el registro se **rechaza** — no hay forma de saltarse este control desde la UI.
- No se hace scraping. Todo el acceso a datos pasa por la Graph API oficial de Meta, respetando sus Términos de Servicio.
- Cualquier uso en un contexto de inteligencia estatal/policial en Perú requiere base legal habilitante bajo la **Ley N.º 29733** y validación jurídica previa. Ver sección 10 de `PROYECTO_OSINT_MONITOR.md` para el detalle completo.

---

## Índice

1. [Arquitectura y stack](#arquitectura-y-stack)
2. [Estructura del repositorio](#estructura-del-repositorio)
3. [Requisitos previos](#requisitos-previos)
4. [Instalación paso a paso](#instalación-paso-a-paso)
5. [Levantar el proyecto](#levantar-el-proyecto)
6. [Verificar que todo funciona](#verificar-que-todo-funciona)
7. [Uso de la plataforma](#uso-de-la-plataforma)
8. [Funcionalidades implementadas (estado actual)](#funcionalidades-implementadas-estado-actual)
9. [Variables de entorno](#variables-de-entorno)
10. [Comandos útiles](#comandos-útiles)
11. [Limitaciones conocidas](#limitaciones-conocidas)
12. [Migrar a otro entorno local](#migrar-a-otro-entorno-local)
13. [Troubleshooting](#troubleshooting)
14. [Roadmap](#roadmap)

---

## Arquitectura y stack

```
Facebook Pages (Graph API)
        │
        ▼
  Celery Beat (scheduler, por página, cada poll_interval)
        │
        ▼
  Celery Worker ──► Deduplicador (Postgres) ──► Bus de analizadores
        │                                          ├─ KeywordAnalyzer
        │                                          ├─ SentimentAnalyzer (Ollama)
        │                                          └─ LiveDetector
        ▼
  PostgreSQL + pgvector  ──►  Dashboard (Next.js)
        │
        ▼
  Alertas (Telegram / email)
```

| Capa | Tecnología |
|---|---|
| Frontend | Next.js 15 + React 19 + TypeScript + TailwindCSS |
| Backend / API | FastAPI (Python 3.12) + Pydantic v2 |
| Cola de tareas / scheduler | Celery + Celery Beat + Redis |
| Base de datos | PostgreSQL 16 + pgvector (búsqueda semántica) |
| Media local | MinIO (S3-compatible) |
| IA local | Ollama (LLM para sentimiento + `nomic-embed-text` para embeddings) |
| Alertas | Telegram Bot API |
| Orquestación | Docker Compose sobre WSL2 |

Todo el detalle de modelo de datos, endpoints y bus de analizadores está en [`PROYECTO_OSINT_MONITOR.md`](./PROYECTO_OSINT_MONITOR.md).

---

## Estructura del repositorio

```
Foxint_Monitor/
├── PROYECTO_OSINT_MONITOR.md   # PRD + especificación técnica completa
├── README.md                   # este archivo
├── docker-compose.yml          # orquestación de los 8 servicios
├── .env.example                # plantilla de variables de entorno
├── backend/
│   ├── app/
│   │   ├── main.py             # entrypoint FastAPI
│   │   ├── core/config.py      # settings (pydantic-settings)
│   │   ├── db/                 # sesiones async (API) y sync (Celery)
│   │   ├── models/             # modelos SQLAlchemy (pages, posts, detections, ...)
│   │   ├── schemas/             # esquemas Pydantic de request/response
│   │   ├── api/routes/          # endpoints FastAPI
│   │   ├── services/
│   │   │   ├── graph_api/       # cliente Graph API + validación Página/Perfil
│   │   │   └── telegram.py      # notificador de alertas
│   │   ├── analyzers/           # bus de analizadores (plugin pattern)
│   │   └── workers/             # Celery app + tareas (scheduler, polling, procesamiento)
│   ├── alembic/                 # migraciones de base de datos
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    ├── app/                     # App Router de Next.js
    ├── package.json
    └── Dockerfile
```

---

## Requisitos previos

- **Windows 11** con **WSL2** habilitado (`wsl --install` si no lo tienes).
- **Docker Desktop** con integración WSL2 activada (Settings → Resources → WSL Integration).
- Al menos **8 GB de RAM libres** para Docker (Ollama + Postgres + el resto de servicios consumen memoria; 16 GB totales en la máquina es lo cómodo).
- ~10 GB de disco libres (imágenes Docker + modelos de Ollama).
- Una **App de Meta for Developers** creada en [developers.facebook.com](https://developers.facebook.com/) con `App ID` y `App Secret`, y un **Page Access Token** (ver sección 2.4 de `PROYECTO_OSINT_MONITOR.md` para el detalle de permisos `pages_read_engagement` / `pages_read_user_content`).
- (Opcional pero recomendado) Un **bot de Telegram** creado vía [@BotFather](https://t.me/BotFather) para recibir alertas.

---

## Instalación paso a paso

### 1. Clonar/copiar el proyecto dentro de WSL2

Por rendimiento de Docker, trabaja el proyecto **dentro del filesystem de WSL2** (`/home/tu_usuario/...`), no en `/mnt/c/...` o `/mnt/d/...`:

```bash
# dentro de una terminal WSL2 (Ubuntu, etc.)
cp -r /mnt/d/APRENDIZAJE/PROYECTOS/Foxint_Monitor ~/osint-monitor
cd ~/osint-monitor
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` y completa como mínimo:

```
FB_APP_ID=tu_app_id
FB_APP_SECRET=tu_app_secret
FB_ACCESS_TOKEN=tu_page_access_token
TELEGRAM_BOT_TOKEN=tu_bot_token   # opcional, sin esto no se envían alertas
TELEGRAM_CHAT_ID=tu_chat_id       # opcional
```

**`.env` nunca se sube a git** (está en `.gitignore`) — contiene secretos.

### 3. Construir las imágenes

```bash
docker compose build
```

### 4. Levantar la base de datos y aplicar migraciones

```bash
docker compose up -d postgres redis
docker compose run --rm backend alembic upgrade head
```

### 5. Descargar los modelos de Ollama

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull qwen2.5
```

Esto descarga varios GB la primera vez — solo se hace una vez (quedan en el volumen `ollamadata`).

---

## Levantar el proyecto

```bash
docker compose up -d
```

Esto levanta los 8 servicios: `frontend`, `backend`, `worker`, `beat`, `postgres`, `redis`, `minio`, `ollama`.

| Servicio | URL local |
|---|---|
| Dashboard (frontend) | http://localhost:3000 |
| API (backend) | http://localhost:8000 |
| Documentación interactiva de la API (Swagger) | http://localhost:8000/docs |
| Consola de MinIO | http://localhost:9001 |
| Postgres | `localhost:5432` |
| Redis | `localhost:6379` |
| Ollama | http://localhost:11434 |

Ver logs en vivo de un servicio:

```bash
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f beat
```

---

## Verificar que todo funciona

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

Registrar una página pública de prueba (ejemplo, cualquier Página real de Facebook):

```bash
curl -X POST http://localhost:8000/api/pages \
  -H "Content-Type: application/json" \
  -d '{"fb_page_id": "20531316728", "poll_interval": 300}'
```

- Si el ID corresponde a una **Página** → responde `201` con sus metadatos (`name`, `category`, etc.).
- Si el ID corresponde a un **perfil personal** → responde `422` con un mensaje explicativo de rechazo.

Listar páginas registradas:

```bash
curl http://localhost:8000/api/pages
```

---

## Uso de la plataforma

1. **Registra una página** vía el dashboard (o `POST /api/pages`) dando su ID/URL de Facebook.
2. El sistema **valida automáticamente** que sea una Página pública (nunca un perfil).
3. **Celery Beat** revisa cada 60s qué páginas ya cumplieron su `poll_interval` individual y encola su polling.
4. El **worker** llama a `/posts` + `/live_videos` de la Graph API, **deduplica** contra lo ya visto, y guarda los posts nuevos.
5. Cada post nuevo pasa por el **bus de analizadores**: `KeywordAnalyzer` (reglas que definas), `SentimentAnalyzer` (Ollama), `LiveDetector` (marca lives en curso).
6. Si una regla de keyword coincide, o se detecta un live iniciado, se dispara una **alerta a Telegram** y queda registrada en la tabla `alerts`.
7. El **dashboard** muestra el timeline de posts por página, sus detecciones y el historial de alertas.

---

## Funcionalidades implementadas (estado actual)

Este proyecto se construye **incrementalmente**. Estado real al día de hoy:

**✅ Implementado**
- Monorepo (frontend Next.js 15 + backend FastAPI) y Docker Compose con los 8 servicios.
- Esquema completo de base de datos (7 tablas) + migraciones Alembic (incluye extensión `pgvector`).
- Cliente Graph API async con **validación Página/Perfil** integrada en el endpoint de registro.
- Endpoints `POST /api/pages` y `GET /api/pages`.
- Scheduler de polling (Celery Beat) que respeta el `poll_interval` configurado por página.
- Deduplicador de posts (contra `platform_post_id`).
- Bus de analizadores con **auto-discovery**: `KeywordAnalyzer`, `SentimentAnalyzer` (Ollama), `LiveDetector`.
- Alertas a Telegram cuando se dispara una regla de keyword o se detecta un live.

**🚧 Pendiente (próximos incrementos)**
- Dashboard funcional (hoy el frontend es un placeholder sin páginas reales).
- Endpoints de reglas (`/api/rules`), detecciones (`/api/posts/{id}/detections`), alertas (`/api/alerts`) y búsqueda semántica (`/api/search`).
- Analizadores de Fase 2: `NERAnalyzer` (spaCy), `OCRAnalyzer` (EasyOCR), `EmbeddingAnalyzer` (pgvector).
- RBAC de usuarios (admin/analyst/viewer) — el modelo `users` existe pero no hay auth implementada.
- WebSocket de alertas en tiempo real (`/ws/alerts`).
- Reportes exportables (PDF/CSV).
- Fase 3: TikTok y módulo GIS.

---

## Variables de entorno

Ver [`.env.example`](./.env.example) para la lista completa. Las más relevantes:

| Variable | Descripción |
|---|---|
| `FB_APP_ID` / `FB_APP_SECRET` | Credenciales de tu app de Meta for Developers. |
| `FB_ACCESS_TOKEN` | Page Access Token (o token de sistema con `Page Public Content Access` para páginas de terceros). |
| `GRAPH_API_VERSION` | Versión de la Graph API a usar (default `v25.0`). |
| `DATABASE_URL` | Cadena de conexión async a Postgres (usada por el backend). |
| `REDIS_URL` | Broker/backend de Celery. |
| `OLLAMA_HOST` | URL interna de Ollama dentro de la red Docker. |
| `OLLAMA_LLM_MODEL` / `OLLAMA_EMBED_MODEL` | Modelos usados para sentimiento y embeddings. |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Credenciales del bot de alertas. Si quedan vacías, las alertas simplemente no se envían (no rompe nada). |
| `POLL_DEFAULT_INTERVAL` | Intervalo de polling por defecto en segundos (300 = 5 min) para páginas nuevas. |

---

## Comandos útiles

```bash
# Levantar todo
docker compose up -d

# Apagar todo (sin borrar datos)
docker compose down

# Apagar todo y BORRAR datos (Postgres, Redis, MinIO, Ollama) — usar con cuidado
docker compose down -v

# Reconstruir imágenes tras cambiar dependencias (requirements.txt / package.json)
docker compose build backend frontend

# Crear una nueva migración tras cambiar modelos
docker compose run --rm backend alembic revision --autogenerate -m "descripción del cambio"

# Aplicar migraciones pendientes
docker compose run --rm backend alembic upgrade head

# Revertir la última migración
docker compose run --rm backend alembic downgrade -1

# Entrar a una shell dentro del backend
docker compose exec backend bash

# Ver qué modelos tiene Ollama descargados
docker compose exec ollama ollama list
```

---

## Limitaciones conocidas

1. **Solo páginas, nunca perfiles.** Es una limitación de diseño intencional (ver alcance legal), no un bug.
2. **Rate limits de la Graph API.** Meta limita las llamadas por app/hora. Con muchas páginas y `poll_interval` bajo, se puede topar con el límite — el cliente detecta el código de error pero **no implementa aún backoff/retry automático** (se documenta como pendiente).
3. **`Page Public Content Access`.** Para monitorear páginas de terceros que **no administras**, Meta exige esta feature, que requiere **App Review + Business Verification** — es un trámite que puede tardar semanas. Sin ella, solo puedes monitorear páginas que tu propia cuenta de negocio administra.
4. **Cobertura de páginas.** Las cuentas de negocio de Meta suelen soportar ~100 páginas conectadas; para más, hay que conectar cuentas adicionales.
5. **TikTok no está soportado todavía.** No existe una Graph API equivalente; se evaluará la TikTok Research API en Fase 3 (acceso restringido, no apto para alertas en tiempo real).
6. **Sin autenticación/RBAC todavía.** El modelo `users` existe pero cualquiera con acceso a la red donde corre el dashboard puede usar la API tal cual está hoy. No exponer estos puertos a internet sin agregar auth.
7. **Sentimiento vía LLM local**, no un modelo de clasificación entrenado específicamente — es razonablemente bueno para español pero no reemplaza un modelo fine-tuneado si se necesita alta precisión.
8. **Sin retención/purga automática de media** todavía (mencionado en el documento como requisito legal de minimización) — pendiente de implementar.

---

## Migrar a otro entorno local

El proyecto es **100% portable** entre máquinas con Docker + WSL2:

- El código y `docker-compose.yml` usan rutas relativas y volúmenes nombrados — no hay nada de una máquina específica hardcodeado.
- **Lo que NO viaja solo** (hay que llevarlo aparte):
  - `.env` (está en `.gitignore` por contener secretos) — cópialo manualmente o recréalo desde `.env.example`.
  - Los datos de los volúmenes Docker (`pgdata`, `redisdata`, `miniodata`, `ollamadata`) — si necesitas migrarlos, usa `docker run --rm -v <volumen>:/from -v /ruta/backup:/to alpine cp -a /from/. /to/` o un backup/restore de Postgres (`pg_dump` / `pg_restore`).
  - Los modelos de Ollama — hay que volver a `ollama pull` en la máquina nueva (pesan GB, no se versionan).
- Requisito del entorno destino: Docker + Docker Compose (vía WSL2 en Windows, nativo en Linux/Mac).

---

## Troubleshooting

**`docker compose up` falla en `postgres` con "database is uninitialized"**
Puede pasar si cambiaste `POSTGRES_USER`/`POSTGRES_PASSWORD` después de la primera vez que se creó el volumen. Solución: `docker compose down -v` (borra datos) y vuelve a levantar.

**El backend no conecta a Postgres (`connection refused`)**
Espera a que el healthcheck de `postgres` pase (`docker compose ps` debe mostrarlo `healthy`) antes de que el backend intente conectar. El `docker-compose.yml` ya tiene `depends_on: condition: service_healthy`, pero si reinicias solo el backend muy rápido tras un `down -v`, dale unos segundos.

**Ollama responde muy lento o se queda colgado**
Los modelos LLM corren en CPU si no tienes GPU configurada (ver el bloque comentado de NVIDIA en `docker-compose.yml`). Es esperable que el análisis de sentimiento tarde algunos segundos por post en CPU.

**`alembic upgrade head` falla con "extension vector does not exist"**
Asegúrate de estar usando la imagen `pgvector/pgvector:pg16` (ya configurada en `docker-compose.yml`) y no un `postgres:16` genérico — la migración ejecuta `CREATE EXTENSION IF NOT EXISTS vector`, que requiere que la extensión esté disponible en la imagen.

**Las alertas de Telegram no llegan**
Verifica que `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` estén completos en `.env` y que hayas reconstruido/reiniciado `worker` tras editar `.env` (`docker compose up -d --force-recreate worker beat`). Si quedan vacíos, el sistema los omite silenciosamente (no es un error).

---

## Roadmap

Ver sección 9 de [`PROYECTO_OSINT_MONITOR.md`](./PROYECTO_OSINT_MONITOR.md) para el detalle de fases (Fase 0 a Fase 3). Resumen:

- **Fase 0 — Setup** ✅
- **Fase 1 — MVP Facebook** 🚧 (cliente Graph API, scheduler, dedup y analizadores mínimos ya implementados; falta dashboard, endpoints de reglas/alertas/búsqueda)
- **Fase 2 — Enriquecimiento** (NER, OCR, embeddings, búsqueda semántica, RBAC, reportes)
- **Fase 3 — TikTok + GIS** (nuevo conector de ingesta, geolocalización, transcripción de VODs)

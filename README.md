# ms-ficha-residente

Microservicio **consumidor de APIs**, sin base de datos propia. Devuelve la
**ficha consolidada de un residente** del condominio.

> CS2032 Cloud Computing - UTEC | Proyecto: Sistema de Administracion de Condominios

## Responsable

[@Brisseth-raton](https://github.com/Brisseth-raton) — Backend / Infraestructura. Ver [INTEGRANTE.md](INTEGRANTE.md).

Integrante a cargo de **backend / infraestructura**. Es el unico repositorio que
integra a los demas: las 3 APIs con base de datos se desarrollan por separado y
aqui se juntan por HTTP.

## Dominio

No persiste nada. Recibe el id de un residente y, en paralelo, consulta:

| Microservicio | Que le pide |
|---------------|-------------|
| `ms-residentes` | datos personales del residente y su unidad/edificio |
| `ms-pagos` | estado de cuenta: cuotas pendientes, deuda total, ultimos pagos |
| `ms-incidencias` | incidencias abiertas y proximas reservas de areas comunes |

Con esas tres respuestas arma un solo JSON. Cumple dos requisitos del curso a la
vez: **microservicio sin base de datos** y **microservicio que consume a otros
microservicios**.

```
                        ┌──> ms-residentes  (8001)
web ──> API Gateway ──> ms-ficha-residente ─┼──> ms-pagos       (8002)
                        └──> ms-incidencias (8003)
```

Si alguno de los tres servicios no responde, la ficha se devuelve igual con esa
seccion marcada como no disponible (degradacion controlada), para que el avance
de un integrante no bloquee al resto.

## Stack

| Elemento    | Tecnologia                |
|-------------|---------------------------|
| Lenguaje    | Python 3.12               |
| Framework   | FastAPI                   |
| Base de datos | **Ninguna** (por diseno) |
| Cliente HTTP | httpx (asincrono)        |
| Documentacion | Swagger-UI en `/docs`   |
| Contenedor  | Docker                    |

## Puerto asignado

**8004**

| Microservicio       | Puerto |
|---------------------|--------|
| ms-residentes       | 8001   |
| ms-pagos            | 8002   |
| ms-incidencias      | 8003   |
| ms-ficha-residente  | **8004** |
| ms-analitico        | 8005   |
| web-condominio (dev)| 5173   |

## Endpoints REST planificados

> Andamiaje: aun no implementados.

| # | Metodo | Ruta | Descripcion | Consumido por |
|---|--------|------|-------------|---------------|
| 1 | `GET` | `/ficha/{residente_id}` | Ficha completa: datos + estado de cuenta + incidencias + reservas | **frontend** |
| 2 | `GET` | `/ficha/unidad/{unidad_id}` | Ficha consolidada de una unidad y todos sus residentes | **frontend** |
| 3 | `GET` | `/ficha/{residente_id}/resumen` | Version reducida: nombre, unidad, deuda total, incidencias abiertas | frontend |
| 4 | `GET` | `/dependencias/estado` | Estado de salud de los 3 microservicios consumidos | infra |
| 5 | `GET` | `/health` | Health check del servicio | infra |

Los dos endpoints que consume directamente el **frontend** son
`GET /ficha/{residente_id}` y `GET /ficha/unidad/{unidad_id}`.

Documentacion interactiva: `http://localhost:8004/docs` (Swagger-UI).

## Variables de entorno

Copiar [.env.example](.env.example) a `.env` y completar. **Nunca** commitear `.env`.

| Variable | Descripcion | Ejemplo |
|----------|-------------|---------|
| `APP_NAME` | Nombre del servicio | `ms-ficha-residente` |
| `APP_PORT` | Puerto de escucha | `8004` |
| `APP_ENV` | Entorno de ejecucion | `development` / `production` |
| `LOG_LEVEL` | Nivel de logging | `info` |
| `MS_RESIDENTES_URL` | URL base de ms-residentes | `http://ms-residentes:8001` |
| `MS_PAGOS_URL` | URL base de ms-pagos | `http://ms-pagos:8002` |
| `MS_INCIDENCIAS_URL` | URL base de ms-incidencias | `http://ms-incidencias:8003` |
| `HTTP_TIMEOUT_SECONDS` | Timeout de las llamadas salientes | `5` |
| `HTTP_MAX_RETRIES` | Reintentos ante fallo | `2` |

## Como levantar con Docker

### Solo el microservicio

```bash
cp .env.example .env
docker build -t ms-ficha-residente .
docker run --rm -p 8004:8004 --env-file .env ms-ficha-residente
```

Luego abrir `http://localhost:8004/docs`.

> Para desarrollar en local contra servicios que corren fuera de Docker, apuntar
> las variables a `http://host.docker.internal:8001` (o a las URLs del API
> Gateway) en lugar de los nombres de servicio de Compose.

### En la EC2 (docker compose del proyecto)

```yaml
services:
  ms-ficha-residente:
    build: .
    ports: ["8004:8004"]
    env_file: .env
    depends_on:
      - ms-residentes
      - ms-pagos
      - ms-incidencias
```

```bash
docker compose up --build
```

Como los cinco microservicios comparten la red de Compose, las variables
`MS_*_URL` usan el nombre del servicio y no `localhost`.

## Estructura

```
app/
├── main.py       # instancia FastAPI (stub)
├── routers/      # endpoints de la ficha
├── clients/      # clientes httpx: residentes, pagos, incidencias
├── schemas/      # esquemas Pydantic de la respuesta consolidada
└── config/       # settings, URLs de los microservicios
tests/
```

## Estado

Andamiaje inicial. Sin endpoints ni logica de agregacion implementados.

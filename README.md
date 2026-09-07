# ms-ficha-residente

Microservicio **consumidor de APIs**, sin base de datos propia. Devuelve la
**ficha consolidada de un residente** del condominio.

> CS2032 Cloud Computing - UTEC | Proyecto: Sistema de Administracion de Condominios

## Responsable

[@Brisseth-raton](https://github.com/Brisseth-raton) — Backend / Infraestructura. Ver [INTEGRANTE.md](INTEGRANTE.md).

Es el unico repositorio que integra a los demas: las 3 APIs con base de datos se
desarrollan por separado y aqui se juntan por HTTP.

La infraestructura del proyecto (VPC, Security Groups, VM de produccion gemelas,
VM de base de datos, VM de ingesta y el mapa de puertos) se documenta en
[docs/infra.md](docs/infra.md).

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
                          ┌──> ms-residentes  :9001
web ──> balanceador ──> ms-ficha-residente :9004 ─┼──> ms-pagos       :9002
                          └──> ms-incidencias :9003
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

**9004** publicado · **8004** dentro del contenedor.

El curso asigno el rango **9000-12000** para los microservicios; ese es el puerto
que se habilita en el Security Group.

| Microservicio | Publicado | Interno |
|---------------|-----------|---------|
| ms-residentes | 9001      | 8000    |
| ms-pagos      | 9002      | 8080    |
| ms-incidencias| 9003      | 3003    |
| ms-ficha-residente | **9004** | 8004 |
| ms-analitico  | 9005      | 8005    |
| web-condominio (dev) | 5173 | —     |

Las bases de datos **no** entran en ese rango: PostgreSQL 5432, MySQL 3306,
MongoDB 27017, alcanzables solo desde los Security Groups de la VM de produccion
y la VM de ingesta.

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

Documentacion interactiva: `http://<ip-vm-produccion>:9004/docs` (Swagger-UI).

## Variables de entorno

Copiar [.env.example](.env.example) a `.env` y completar. **Nunca** commitear `.env`.

| Variable | Descripcion | Ejemplo |
|----------|-------------|---------|
| `APP_NAME` | Nombre del servicio | `ms-ficha-residente` |
| `APP_PORT` | Puerto dentro del contenedor | `8004` |
| `PUBLISHED_PORT` | Puerto publicado en la VM | `9004` |
| `APP_ENV` | Entorno de ejecucion | `development` / `production` |
| `LOG_LEVEL` | Nivel de logging | `info` |
| `MS_RESIDENTES_URL` | URL base de ms-residentes | `http://<ip-vm-produccion>:9001` |
| `MS_PAGOS_URL` | URL base de ms-pagos | `http://<ip-vm-produccion>:9002` |
| `MS_INCIDENCIAS_URL` | URL base de ms-incidencias | `http://<ip-vm-produccion>:9003` |
| `HTTP_TIMEOUT_SECONDS` | Timeout de las llamadas salientes | `5` |
| `HTTP_MAX_RETRIES` | Reintentos ante fallo | `2` |

## Como levantar con Docker

### Solo el microservicio

```bash
cp .env.example .env
docker build -t ms-ficha-residente .
docker run --rm -p 9004:8004 --env-file .env ms-ficha-residente
```

Luego abrir `http://localhost:9004/docs`.

### En la VM de produccion

```yaml
services:
  ms-ficha-residente:
    image: <usuario>/ms-ficha-residente:0.1.0
    ports: ["9004:8004"]
    env_file: .env
```

```bash
docker compose up -d
```

Los cinco microservicios corren en la misma VM de produccion, asi que las
variables `MS_*_URL` pueden apuntar a la **IP privada** de esa maquina con el
puerto publicado de cada uno (9001, 9002, 9003). Como hay **dos VM de produccion
gemelas**, el mismo `.env` funciona en las dos.

## Estructura

```
app/
├── main.py       # instancia FastAPI (stub)
├── routers/      # endpoints de la ficha
├── clients/      # clientes httpx: residentes, pagos, incidencias
├── schemas/      # esquemas Pydantic de la respuesta consolidada
└── config/       # settings, URLs de los microservicios
tests/
docs/
└── infra.md      # VPC, Security Groups, VMs y mapa de puertos
```

## Estado

Andamiaje inicial. Sin endpoints ni logica de agregacion implementados.
